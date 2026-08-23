import dataclasses
import hashlib
import json

import pytest

from rag_compare.release import (
    BuildArtifacts,
    MixedReleaseError,
    ReleaseValidationError,
    capture_active_release,
    filter_chunks_for_release,
    promote_release,
    validate_release,
)


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def complete_release(tmp_path, release_id):
    release_dir = tmp_path / release_id
    corpus_dir = release_dir / "corpus"
    corpus_dir.mkdir(parents=True)

    (corpus_dir / "first.md").write_text("first policy", encoding="utf-8")
    (corpus_dir / "second.md").write_text("second policy", encoding="utf-8")

    files = [
        {"path": f"corpus/{path.name}", "sha256": _sha256(path)}
        for path in sorted(corpus_dir.iterdir())
    ]

    manifest = {
        "release_id": release_id,
        "corpus": {"version": "v1", "files": files},
        "schema_version": 1,
        "parser": {"identity": "markdown-parser-v1", "config": {"front_matter": True}},
        "chunker": {
            "identity": "token-window-v1",
            "size": 200,
            "overlap": 40,
            "config_sha256": "b" * 64,
        },
        "embedding": {
            "name": "nomic-embed-text-hf:latest",
            "ollama_digest": "c" * 64,
            "dimensions": 768,
            "distance_metric": "cosine",
        },
        "framework": {
            "commit": "abc123",
            "package": "rag-compare",
            "adapter": "test-adapter-v1",
        },
        "document_count": 2,
        "chunk_count": 2,
        "built_at": "2026-08-22T00:00:00Z",
        "validation_status": "passed",
    }

    observed = BuildArtifacts(
        corpus=manifest["corpus"],
        schema_version=manifest["schema_version"],
        parser=manifest["parser"],
        chunker=manifest["chunker"],
        embedding=manifest["embedding"],
        framework=manifest["framework"],
        document_count=manifest["document_count"],
        chunk_count=manifest["chunk_count"],
    )

    return release_dir, manifest, observed


def test_complete_v1_validates(tmp_path):
    release_dir, manifest, observed = complete_release(tmp_path, "synthetic-policy-v1")

    assert validate_release(release_dir, manifest, observed).release_id == (
        "synthetic-policy-v1"
    )


def test_partial_v2_is_rejected_for_missing_file_hash_and_count(tmp_path):
    release_dir, manifest, observed = complete_release(tmp_path, "synthetic-policy-v2")

    (release_dir / "corpus" / "second.md").unlink()

    with pytest.raises(ReleaseValidationError):
        validate_release(release_dir, manifest, observed)


def test_corpus_file_paths_must_be_relative_to_the_release(tmp_path):
    release_dir, manifest, observed = complete_release(tmp_path, "synthetic-policy-v1")

    invalid_corpus = {
        **manifest["corpus"],
        "files": [{"path": ".", "sha256": "a" * 64}],
    }
    manifest = {**manifest, "corpus": invalid_corpus}
    observed = dataclasses.replace(observed, corpus=invalid_corpus)

    with pytest.raises(ReleaseValidationError, match="relative to release"):
        validate_release(release_dir, manifest, observed)


@pytest.mark.parametrize(
    "release_id", ["", ".", "..", "nested/release", r"nested\\release"]
)
def test_release_id_must_be_a_safe_namespace_component(tmp_path, release_id):
    release_dir, manifest, observed = complete_release(tmp_path, "synthetic-policy-v1")

    with pytest.raises(ReleaseValidationError, match="release_id"):
        validate_release(release_dir, {**manifest, "release_id": release_id}, observed)


def test_release_id_must_match_the_release_directory_name(tmp_path):
    release_dir, manifest, observed = complete_release(tmp_path, "synthetic-policy-v1")

    renamed_release_dir = tmp_path / "different-release"
    release_dir.rename(renamed_release_dir)

    with pytest.raises(ReleaseValidationError, match="directory name"):
        validate_release(renamed_release_dir, manifest, observed)


def _symlink_or_skip(link, target, *, target_is_directory=False):
    try:
        link.symlink_to(target, target_is_directory=target_is_directory)
    except (NotImplementedError, OSError) as error:
        pytest.skip(f"symlinks are unavailable: {error}")


def test_symlinked_corpus_root_is_rejected(tmp_path):
    release_dir, manifest, observed = complete_release(tmp_path, "synthetic-policy-v1")

    external_corpus = tmp_path / "external-corpus"
    external_corpus.mkdir()

    corpus_dir = release_dir / "corpus"
    for path in corpus_dir.iterdir():
        path.unlink()
    corpus_dir.rmdir()

    _symlink_or_skip(corpus_dir, external_corpus, target_is_directory=True)

    with pytest.raises(ReleaseValidationError, match="symlink"):
        validate_release(release_dir, manifest, observed)


def test_symlinked_corpus_file_is_rejected(tmp_path):
    release_dir, manifest, observed = complete_release(tmp_path, "synthetic-policy-v1")

    linked_file = release_dir / "corpus" / "first.md"
    external_file = tmp_path / "external.md"
    external_file.write_text(linked_file.read_text(encoding="utf-8"), encoding="utf-8")
    linked_file.unlink()

    _symlink_or_skip(linked_file, external_file)

    with pytest.raises(ReleaseValidationError, match="symlink"):
        validate_release(release_dir, manifest, observed)


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("schema_version", True),
        ("schema_version", 0),
        ("document_count", False),
        ("document_count", -1),
        ("chunk_count", True),
        ("chunk_count", -1),
        ("corpus.version", ""),
        ("parser.identity", ""),
        ("parser.config", []),
        ("chunker.identity", ""),
        ("chunker.size", True),
        ("chunker.size", 0),
        ("chunker.overlap", -1),
        ("chunker.config_sha256", "A" * 64),
        ("embedding.name", ""),
        ("embedding.ollama_digest", ""),
        ("embedding.dimensions", False),
        ("embedding.dimensions", 0),
        ("embedding.distance_metric", ""),
        ("framework.commit", ""),
        ("framework.package", ""),
        ("framework.adapter", ""),
    ),
)
def test_manifest_metadata_requires_safe_types_and_values(tmp_path, field, value):
    release_dir, manifest, observed = complete_release(tmp_path, "synthetic-policy-v1")

    if "." in field:
        section, nested_field = field.split(".")
        changed_section = {**manifest[section], nested_field: value}
        manifest = {**manifest, section: changed_section}
        observed = dataclasses.replace(observed, **{section: changed_section})
    else:
        manifest = {**manifest, field: value}
        observed = dataclasses.replace(observed, **{field: value})

    with pytest.raises(ReleaseValidationError):
        validate_release(release_dir, manifest, observed)


@pytest.mark.parametrize(
    ("section", "field"),
    (
        ("corpus", "version"),
        ("parser", "identity"),
        ("parser", "config"),
        ("chunker", "identity"),
        ("chunker", "size"),
        ("chunker", "overlap"),
        ("chunker", "config_sha256"),
        ("embedding", "name"),
        ("embedding", "ollama_digest"),
        ("embedding", "dimensions"),
        ("embedding", "distance_metric"),
        ("framework", "commit"),
        ("framework", "package"),
        ("framework", "adapter"),
    ),
)
def test_manifest_requires_every_nested_release_contract_field(
    tmp_path, section, field
):
    release_dir, manifest, observed = complete_release(tmp_path, "synthetic-policy-v1")

    changed_section = {
        key: value for key, value in manifest[section].items() if key != field
    }
    manifest = {**manifest, section: changed_section}
    observed = dataclasses.replace(observed, **{section: changed_section})

    with pytest.raises(ReleaseValidationError, match="missing required fields"):
        validate_release(release_dir, manifest, observed)


@pytest.mark.parametrize("field", ["schema_version", "embedding"])
def test_schema_or_embedding_mismatch_is_rejected(tmp_path, field):
    release_dir, manifest, observed = complete_release(tmp_path, "synthetic-policy-v1")

    changed = (
        dataclasses.replace(observed, schema_version=observed.schema_version + 1)
        if field == "schema_version"
        else dataclasses.replace(
            observed,
            embedding={**observed.embedding, "dimensions": 769},
        )
    )

    with pytest.raises(ReleaseValidationError):
        validate_release(release_dir, manifest, changed)


def test_failed_validation_never_changes_active_pointer(tmp_path):
    release_dir, manifest, observed = complete_release(tmp_path, "synthetic-policy-v2")
    pointer = tmp_path / "active.json"

    pointer.write_text('{"release_id":"synthetic-policy-v1"}', encoding="utf-8")

    with pytest.raises(ReleaseValidationError):
        promote_release(
            release_dir,
            {**manifest, "validation_status": "failed"},
            observed,
            pointer,
        )

    assert json.loads(pointer.read_text(encoding="utf-8"))["release_id"] == (
        "synthetic-policy-v1"
    )


def test_promotion_uses_one_atomic_replacement(tmp_path, monkeypatch):
    release_dir, manifest, observed = complete_release(tmp_path, "synthetic-policy-v1")

    replacements = []
    monkeypatch.setattr(
        "rag_compare.release.os.replace",
        lambda source, target: replacements.append((source, target)),
    )

    promote_release(release_dir, manifest, observed, tmp_path / "active.json")

    assert len(replacements) == 1


@pytest.mark.parametrize("release_id", [".", "..", "branch/v2", r"branch\\v2"])
def test_active_pointer_requires_a_safe_release_namespace(tmp_path, release_id):
    pointer = tmp_path / "active.json"
    pointer.write_text(json.dumps({"release_id": release_id}), encoding="utf-8")

    with pytest.raises(ReleaseValidationError, match="release_id"):
        capture_active_release(pointer)


@pytest.mark.parametrize("pointer_contents", [b"\xff", b"[]", b"null"])
def test_active_pointer_rejects_malformed_bytes_and_non_objects(
    tmp_path, pointer_contents
):
    pointer = tmp_path / "active.json"
    pointer.write_bytes(pointer_contents)

    with pytest.raises(ReleaseValidationError):
        capture_active_release(pointer)


def test_query_rejects_chunks_from_any_release_other_than_captured_one(tmp_path):
    (tmp_path / "active.json").write_text('{"release_id":"v2"}', encoding="utf-8")
    captured = capture_active_release(tmp_path / "active.json")

    with pytest.raises(MixedReleaseError):
        filter_chunks_for_release(
            captured,
            [[{"release_id": "v2"}], [{"release_id": "v1"}]],
        )


def test_query_returns_every_chunk_from_the_captured_release_in_input_order(tmp_path):
    (tmp_path / "active.json").write_text('{"release_id":"v2"}', encoding="utf-8")
    captured = capture_active_release(tmp_path / "active.json")

    branches = [
        [{"release_id": "v2", "id": "a"}],
        [{"release_id": "v2", "id": "b"}, {"release_id": "v2", "id": "c"}],
    ]

    assert filter_chunks_for_release(captured, branches) == [
        {"release_id": "v2", "id": "a"},
        {"release_id": "v2", "id": "b"},
        {"release_id": "v2", "id": "c"},
    ]
