"""Immutable release validation, promotion, and query-isolation contracts."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from rag_compare import identity


class ReleaseValidationError(ValueError):
    """Raised when a release manifest does not match its build artifacts."""


class MixedReleaseError(ValueError):
    """Raised when query branches contain a chunk from another release."""


@dataclass(frozen=True)
class BuildArtifacts:
    """The values observed while building a release, excluding its pointer metadata.

    ``index`` describes the stored index contents via a chunk-inventory
    artifact: without it, validation could accept a release whose corpus
    files are complete but whose index is empty or partial.
    """

    corpus: dict
    schema_version: object
    parser: dict
    chunker: dict
    embedding: dict
    framework: dict
    document_count: int
    chunk_count: int
    index: dict


@dataclass(frozen=True)
class ValidatedRelease:
    """A release identifier whose manifest and corpus have been validated."""

    release_id: str


_OBSERVED_FIELDS = (
    "corpus",
    "schema_version",
    "parser",
    "chunker",
    "embedding",
    "framework",
    "document_count",
    "chunk_count",
    "index",
)

_REQUIRED_FIELDS = (
    "release_id",
    *_OBSERVED_FIELDS,
    "built_at",
    "validation_status",
)

_REQUIRED_NESTED_FIELDS = {
    "corpus": ("version", "files"),
    "parser": ("identity", "config"),
    "chunker": ("identity", "size", "overlap", "config_sha256"),
    "embedding": ("name", "ollama_digest", "dimensions", "distance_metric"),
    "framework": ("commit", "package", "adapter"),
    "index": ("chunk_inventory_sha256", "chunk_count"),
}

_LOWER_HEX = frozenset("0123456789abcdef")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _safe_release_id(value: object) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value in (".", "..")
        or "/" in value
        or "\\" in value
    ):
        raise ReleaseValidationError(
            "release_id must be a safe release namespace component"
        )
    return value


def _require_nonempty_string(value: object, field: str) -> None:
    if not isinstance(value, str) or not value:
        raise ReleaseValidationError(f"{field} must be a nonempty string")


def _require_positive_int(value: object, field: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ReleaseValidationError(f"{field} must be an integer greater than zero")


def _require_nonnegative_int(value: object, field: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ReleaseValidationError(f"{field} must be a non-negative integer")


def _require_lower_sha256(value: object, field: str) -> None:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in _LOWER_HEX for character in value)
    ):
        raise ReleaseValidationError(f"{field} must be a lowercase SHA-256 hex digest")


def _validate_nested_manifest_fields(manifest: Mapping[str, object]) -> None:
    for section, fields in _REQUIRED_NESTED_FIELDS.items():
        value = manifest[section]
        if not isinstance(value, Mapping):
            raise ReleaseValidationError(f"manifest {section} must be a mapping")
        missing = [field for field in fields if field not in value]
        if missing:
            raise ReleaseValidationError(
                f"manifest {section} is missing required fields: {', '.join(missing)}"
            )

    corpus = manifest["corpus"]
    _require_nonempty_string(corpus["version"], "corpus.version")

    parser = manifest["parser"]
    _require_nonempty_string(parser["identity"], "parser.identity")
    if not isinstance(parser["config"], Mapping):
        raise ReleaseValidationError("parser.config must be a mapping")

    chunker = manifest["chunker"]
    _require_nonempty_string(chunker["identity"], "chunker.identity")
    _require_positive_int(chunker["size"], "chunker.size")
    _require_nonnegative_int(chunker["overlap"], "chunker.overlap")
    if chunker["overlap"] >= chunker["size"]:
        raise ReleaseValidationError("chunker.overlap must be less than chunker.size")
    _require_lower_sha256(chunker["config_sha256"], "chunker.config_sha256")

    embedding = manifest["embedding"]
    _require_nonempty_string(embedding["name"], "embedding.name")
    _require_nonempty_string(embedding["ollama_digest"], "embedding.ollama_digest")
    _require_positive_int(embedding["dimensions"], "embedding.dimensions")
    _require_nonempty_string(embedding["distance_metric"], "embedding.distance_metric")

    framework = manifest["framework"]
    for field in ("commit", "package", "adapter"):
        _require_nonempty_string(framework[field], f"framework.{field}")


def _release_file_path(value: object) -> str:
    if not isinstance(value, str) or not value:
        raise ReleaseValidationError("corpus file path must be a nonempty string")
    path = PurePosixPath(value)
    if (
        path.is_absolute()
        or not path.parts
        or path.parts[0] != "corpus"
        or any(part in (".", "..") for part in path.parts)
        or path.as_posix() != value
    ):
        raise ReleaseValidationError(
            f"corpus file path is not relative to release: {value!r}"
        )
    return value


def _corpus_root(release_dir: Path) -> Path:
    corpus_dir = release_dir / "corpus"
    if corpus_dir.is_symlink():
        raise ReleaseValidationError("release corpus directory must not be a symlink")
    if not corpus_dir.is_dir():
        raise ReleaseValidationError("release corpus directory is missing")
    return corpus_dir.resolve(strict=True)


def _require_path_beneath_corpus(path: Path, corpus_dir: Path) -> None:
    if path.is_symlink():
        raise ReleaseValidationError("release corpus files must not be symlinks")
    try:
        path.resolve(strict=False).relative_to(corpus_dir)
    except ValueError as error:
        raise ReleaseValidationError(
            "corpus file resolves outside the release corpus"
        ) from error


def _expected_corpus_files(
    manifest: Mapping[str, object], release_dir: Path, corpus_dir: Path
) -> dict[str, str]:
    corpus = manifest["corpus"]
    if not isinstance(corpus, Mapping):
        raise ReleaseValidationError("corpus must be a mapping")

    files = corpus.get("files")
    if not isinstance(files, list):
        raise ReleaseValidationError("corpus.files must be a list")

    expected: dict[str, str] = {}
    for entry in files:
        if not isinstance(entry, Mapping):
            raise ReleaseValidationError("each corpus file must be a mapping")

        path = _release_file_path(entry.get("path"))
        _require_path_beneath_corpus(release_dir / PurePosixPath(path), corpus_dir)

        sha256 = entry.get("sha256")
        try:
            _require_lower_sha256(sha256, f"corpus file hash for {path}")
        except ReleaseValidationError as error:
            raise ReleaseValidationError(
                f"corpus file hash is invalid for {path}"
            ) from error

        if path in expected:
            raise ReleaseValidationError(f"duplicate corpus file path: {path}")

        expected[path] = sha256

    return expected


def _discovered_corpus_files(release_dir: Path, corpus_dir: Path) -> dict[str, str]:
    discovered: dict[str, str] = {}
    resolved_release_dir = corpus_dir.parent
    for path in sorted(corpus_dir.rglob("*")):
        _require_path_beneath_corpus(path, corpus_dir)
        if path.is_file():
            discovered[path.relative_to(resolved_release_dir).as_posix()] = _sha256(
                path
            )
    return discovered


INDEX_INVENTORY_RELPATH = "index/chunk-inventory.json"


def build_chunk_inventory(chunks: list[dict]) -> list[dict]:
    """Deterministic per-chunk inventory of what an index build stored."""
    entries = [
        {
            "chunk_id": chunk["chunk_id"],
            "source_id": chunk["source_id"],
            "document_id": chunk["document_id"],
            "span": list(chunk["span"]),
            "text_sha256": identity.sha256_bytes(chunk["text"].encode("utf-8")),
        }
        for chunk in chunks
    ]
    entries.sort(key=lambda entry: entry["chunk_id"])
    return entries


def canonical_inventory_bytes(entries: list[dict]) -> bytes:
    payload = json.dumps(entries, sort_keys=True, separators=(",", ":"))
    return payload.encode("utf-8")


def write_index_inventory(release_dir: str | Path, chunks: list[dict]) -> str:
    """Write the chunk-inventory artifact into a release directory.

    Returns the SHA-256 recorded in the manifest's ``index`` block. A release
    whose directory lacks this file cannot pass validation, so an empty or
    partial index can never be promoted even when its corpus files match.
    """
    entries = build_chunk_inventory(chunks)
    inventory_path = Path(release_dir) / INDEX_INVENTORY_RELPATH
    inventory_path.parent.mkdir(parents=True, exist_ok=True)
    payload = canonical_inventory_bytes(entries)
    inventory_path.write_bytes(payload)
    return hashlib.sha256(payload).hexdigest()


def validate_release(
    release_dir: str | Path,
    manifest: Mapping[str, object],
    observed: BuildArtifacts,
) -> ValidatedRelease:
    """Validate a release manifest against its observed build and on-disk corpus."""
    if not isinstance(manifest, Mapping):
        raise ReleaseValidationError("manifest must be a mapping")

    missing = [field for field in _REQUIRED_FIELDS if field not in manifest]
    if missing:
        raise ReleaseValidationError(
            f"manifest is missing required fields: {', '.join(missing)}"
        )

    release_id = _safe_release_id(manifest["release_id"])
    release_dir_path = Path(release_dir)
    if release_id != release_dir_path.name:
        raise ReleaseValidationError("release_id must match the release directory name")

    if manifest["validation_status"] != "passed":
        raise ReleaseValidationError("validation_status must be passed")

    _require_nonempty_string(manifest["built_at"], "built_at")
    _require_positive_int(manifest["schema_version"], "schema_version")
    _require_nonnegative_int(manifest["document_count"], "document_count")
    _require_nonnegative_int(manifest["chunk_count"], "chunk_count")

    _validate_nested_manifest_fields(manifest)

    for field in _OBSERVED_FIELDS:
        actual = manifest[field]
        expected = getattr(observed, field)
        if actual != expected:
            raise ReleaseValidationError(
                f"manifest {field} does not match observed build"
            )

    corpus_dir = _corpus_root(release_dir_path)
    expected_files = _expected_corpus_files(manifest, release_dir_path, corpus_dir)
    discovered_files = _discovered_corpus_files(release_dir_path, corpus_dir)

    if set(expected_files) != set(discovered_files):
        raise ReleaseValidationError(
            "corpus file set does not match the release directory"
        )

    if len(discovered_files) != manifest["document_count"]:
        raise ReleaseValidationError("corpus file count does not match document_count")

    for path, expected_hash in expected_files.items():
        if discovered_files[path] != expected_hash:
            raise ReleaseValidationError(f"corpus file hash does not match for {path}")

    _validate_index_inventory(release_dir_path, manifest)

    return ValidatedRelease(release_id)


def _validate_index_inventory(release_dir_path: Path, manifest: Mapping) -> None:
    """Validate the stored index contents, not just the corpus files.

    Checks, in order:

    1. the inventory artifact exists and matches its manifest hash;
    2. its entry count equals both declared counts;
    3. every entry's identity recomputes from the on-disk corpus under the
       same contract the adapters used at build time — so stale or foreign
       chunk ids cannot pass even when hashes happen to line up.
    """
    from rag_compare import identity as identity_module
    from rag_compare.adapters import base as _adapter_base

    index_block = manifest["index"]
    inventory_rel = INDEX_INVENTORY_RELPATH
    inventory_path = release_dir_path / inventory_rel
    if not inventory_path.is_file():
        raise ReleaseValidationError(
            "index chunk inventory is missing: "
            "the release directory stores no verifiable index artifact"
        )
    payload = inventory_path.read_bytes()
    if hashlib.sha256(payload).hexdigest() != index_block["chunk_inventory_sha256"]:
        raise ReleaseValidationError("index chunk inventory hash does not match")
    try:
        entries = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ReleaseValidationError("index chunk inventory is unreadable") from error
    if not isinstance(entries, list) or not all(
        isinstance(entry, Mapping) for entry in entries
    ):
        raise ReleaseValidationError("index chunk inventory must be a list of mappings")
    if len(entries) != int(manifest["chunk_count"]):
        raise ReleaseValidationError(
            "index chunk inventory count does not match manifest chunk_count"
        )
    if len(entries) != int(index_block["chunk_count"]):
        raise ReleaseValidationError(
            "index chunk inventory count does not match manifest index.chunk_count"
        )
    chunk_ids = [entry.get("chunk_id") for entry in entries]
    if len(set(chunk_ids)) != len(chunk_ids):
        raise ReleaseValidationError(
            "index chunk inventory contains duplicate chunk ids"
        )

    # Recompute expected identities from the validated corpus files.
    corpus_dir = _corpus_root(release_dir_path)
    version_field = (
        "source_version"
        if int(manifest["schema_version"]) == 2
        else "policy_version"
    )
    expected_by_source: dict[str, list] = {}
    size_tokens = int(manifest["chunker"]["size"])
    overlap_tokens = int(manifest["chunker"]["overlap"])
    for relative in sorted(_discovered_corpus_files(release_dir_path, corpus_dir)):
        absolute = release_dir_path / PurePosixPath(relative)
        parsed = _adapter_base.parse_markdown_file(absolute)
        expected_by_source[parsed.source_id] = (
            _adapter_base.make_normalized_chunks(
                parsed,
                manifest["release_id"],
                version_field,
                size_tokens=size_tokens,
                overlap_tokens=overlap_tokens,
            )
        )

    declared_sources = {entry.get("source_id") for entry in entries}
    if declared_sources != set(expected_by_source):
        raise ReleaseValidationError(
            "index chunk inventory source set does not match the corpus files"
        )
    for entry in entries:
        expected_chunks = expected_by_source[entry["source_id"]]
        chunk = next(
            (c for c in expected_chunks if c["chunk_id"] == entry.get("chunk_id")),
            None,
        )
        if chunk is None:
            raise ReleaseValidationError(
                "inventory chunk id does not match the contract-derived id for "
                + str(entry["source_id"])
            )
        expected_text_sha = identity_module.sha256_bytes(
            chunk["text"].encode("utf-8")
        )
        if entry.get("text_sha256") != expected_text_sha:
            raise ReleaseValidationError(
                "inventory text hash does not match the corpus body for "
                + str(entry["source_id"])
            )
        if list(entry.get("span", [])) != list(chunk["span"]):
            raise ReleaseValidationError(
                "inventory span does not match the corpus body for "
                + str(entry["source_id"])
            )


def promote_release(
    release_dir: str | Path,
    manifest: Mapping[str, object],
    observed: BuildArtifacts,
    active_path: str | Path,
) -> ValidatedRelease:
    """Validate and atomically publish a release as the active release."""
    validated = validate_release(release_dir, manifest, observed)

    pointer_path = Path(active_path)
    serialized = json.dumps(
        {"release_id": validated.release_id},
        sort_keys=True,
        separators=(",", ":"),
    )

    with tempfile.NamedTemporaryFile(
        dir=pointer_path.parent,
        delete=False,
        mode="w",
        encoding="utf-8",
    ) as pointer_file:
        pointer_file.write(serialized)
        pointer_file.flush()
        os.fsync(pointer_file.fileno())
        temporary_path = pointer_file.name

    os.replace(temporary_path, pointer_path)
    return validated


def capture_active_release(active_path: str | Path) -> str:
    """Read and validate the active release pointer exactly once."""
    try:
        pointer = json.loads(Path(active_path).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ReleaseValidationError("active release pointer is unreadable") from error

    if not isinstance(pointer, dict) or set(pointer) != {"release_id"}:
        raise ReleaseValidationError(
            "active release pointer must contain only release_id"
        )

    return _safe_release_id(pointer["release_id"])


def filter_chunks_for_release(
    release_id: str,
    branches: Iterable[Iterable[Mapping[str, object]]],
) -> list[Mapping[str, object]]:
    """Flatten branches only when every chunk belongs to the captured release."""
    if not isinstance(release_id, str) or not release_id:
        raise MixedReleaseError("captured release_id must be nonempty")

    chunks: list[Mapping[str, object]] = []
    for branch in branches:
        for chunk in branch:
            if not isinstance(chunk, Mapping) or chunk.get("release_id") != release_id:
                raise MixedReleaseError(
                    "query branches contain a chunk from another release"
                )
            chunks.append(chunk)
    return chunks
