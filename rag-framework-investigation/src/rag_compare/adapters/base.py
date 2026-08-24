"""Shared adapter contract and framework-independent pipeline helpers.

Both framework adapters implement the same two operations:

- ``build_release(corpus_path, manifest, trace)`` — parse the corpus into
  normalized chunks with contract-stable identities, index them inside the
  framework, and return a release manifest plus observed build artifacts.
- ``query(query_text, retriever_kind, active_release, trace)`` — retrieve,
  enforce release isolation, pack context, generate an answer, and emit one
  trace event per stage boundary.

The corpus parsing, identity assignment, reranking/packing calls, stage
ordering, and generation are shared here so that the only differences between
frameworks are the traced framework-specific index/retrieve components.
"""

from __future__ import annotations

import hashlib
import json
import re
import time
from abc import ABC, abstractmethod
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath

from rag_compare import identity
from rag_compare.contracts import StageEvent
from rag_compare.ollama import OllamaClient, embedding_identity_digest
from rag_compare.release import (
    BuildArtifacts,
    build_chunk_inventory,
    canonical_inventory_bytes,
)
from rag_compare.rerank import pack_context

# Identical stage order is asserted for both adapters by tests/test_adapters.py.
STAGE_ORDER = [
    "capture_release",
    "retrieve",
    "release_filter",
    "rerank",
    "pack",
    "generate",
    "citation",
]

FRONT_MATTER_PATTERN = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?", re.DOTALL)

PARSER_IDENTITY = "markdown_front_matter_v1"
CHUNKER_IDENTITY = "token_window_cl100k_base_v2"


class AdapterError(ValueError):
    """Raised for adapter contract violations."""


class ReleaseNamespaceError(LookupError):
    """Raised when querying a release this adapter instance never built."""

    def __init__(self, release_id: str) -> None:
        super().__init__(f"release not built in this adapter instance: {release_id}")


def make_candidate(
    *,
    source_id: str,
    document_id: str,
    chunk_id: str,
    text: str,
    span: list[int],
    score: float,
    rank: int,
    metadata: dict,
    release_id: str,
    method: str,
) -> dict:
    """Build the normalized retrieval candidate both adapters must return."""
    return {
        "source_id": source_id,
        "document_id": document_id,
        "chunk_id": chunk_id,
        "text": text,
        "span": span,
        "score": score,
        "rank": rank,
        "metadata": metadata,
        "release_id": release_id,
        "method": method,
    }


@dataclass(frozen=True)
class ParsedDocument:
    """One parsed Markdown policy with its front matter and body span."""

    source_id: str
    title: str
    status: str
    front_matter: dict
    raw_text: str
    body_start: int
    body_end: int
    content_sha256: str

    @property
    def body(self) -> str:
        return self.raw_text[self.body_start : self.body_end]


@dataclass(frozen=True)
class EmbedStageResult:
    """Outcome of the embed stage: vectors plus a derived identity digest."""

    vectors: list[list[float]]
    embedding_digest: str


@dataclass
class BuildResult:
    """What ``build_release`` returns: manifest plus observed build artifacts."""

    manifest: dict
    observed: BuildArtifacts
    chunks: list[dict] = field(default_factory=list)
    # Chunks read BACK from the framework's own store after the store stage.
    # The release inventory is derived from these, not from the in-memory
    # input chunks, so validation proves what the index actually holds.
    stored_chunks: list[dict] = field(default_factory=list)


def parse_front_matter(raw_text: str) -> tuple[dict, int, int]:
    """Split YAML-ish front matter from the body; return (meta, start, end)."""
    match = FRONT_MATTER_PATTERN.match(raw_text)
    if not match:
        raise AdapterError("document is missing front matter")
    meta: dict = {}
    for line in match.group(1).splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        meta[key.strip()] = value.strip().strip('"')
    body_start = match.end()
    body = raw_text[body_start:].strip()
    body_end = raw_text.find(body, body_start) + len(body)
    return meta, body_start, body_end


def parse_markdown_file(path: Path) -> ParsedDocument:
    """Parse one corpus Markdown file into a ParsedDocument."""
    raw_text = path.read_text(encoding="utf-8")
    meta, body_start, body_end = parse_front_matter(raw_text)
    source_id = meta.get("source_id")
    if not source_id:
        raise AdapterError(f"{path} has no source_id in front matter")
    content_bytes = raw_text.encode("utf-8")
    return ParsedDocument(
        source_id=source_id,
        title=meta.get("title", ""),
        status=meta.get("status", ""),
        front_matter=meta,
        raw_text=raw_text,
        body_start=body_start,
        body_end=body_end,
        content_sha256=identity.sha256_bytes(content_bytes),
    )


def load_corpus(
    corpus_path: str | Path, corpus_manifest: Mapping[str, object]
) -> list[ParsedDocument]:
    """Load and hash every manifest-listed document, ordered by source_id."""
    corpus_dir = Path(corpus_path)
    documents: list[ParsedDocument] = []
    for entry in corpus_manifest["documents"]:  # type: ignore[index]
        relative = entry["path"]  # e.g. v1/approval-matrix.md
        path = corpus_dir.parent / relative
        parsed = parse_markdown_file(path)
        expected_hash = entry.get("content_sha256")
        if expected_hash and parsed.content_sha256 != expected_hash:
            raise AdapterError(
                f"content hash mismatch for {relative}: "
                f"{parsed.content_sha256} != {expected_hash}"
            )
        if parsed.source_id != entry.get("source_id"):
            raise AdapterError(f"source_id mismatch for {relative}")
        documents.append(parsed)
    documents.sort(key=lambda doc: doc.source_id)
    return documents


def token_char_offsets(text: str) -> list[int]:
    """Char offset of every cl100k_base token start in ``text`` (exact spans)."""
    import tiktoken  # deferred: only needed when real splitting runs

    encoding = tiktoken.get_encoding("cl100k_base")
    tokens = encoding.encode(text)
    offsets = [0] * len(tokens)
    for index in range(1, len(tokens)):
        offsets[index] = len(encoding.decode(tokens[:index]))
    return offsets


def token_window_structures(
    parsed: ParsedDocument,
    release_id: str,
    version_field: str,
    size_tokens: int,
    overlap_tokens: int,
) -> list[dict]:
    """Real cl100k_base token-window chunking with exact character spans.

    Implements the declared ``chunking`` configuration: windows of at most
    ``size_tokens`` tokens advancing by ``size_tokens - overlap_tokens``.
    Spans are exact char offsets into the raw file so the identity contract
    (chunk ids over span+text) and later byte-level citation verification
    remain well-defined. One whole-document chunk is produced only when the
    body fits inside a single window.
    """
    if size_tokens < 1 or overlap_tokens < 0 or overlap_tokens >= size_tokens:
        raise AdapterError("invalid token window configuration")
    import tiktoken  # deferred: only needed when real splitting runs

    encoding = tiktoken.get_encoding("cl100k_base")
    tokens = encoding.encode(parsed.body)
    offsets = token_char_offsets(parsed.body)
    total = len(tokens)
    step = size_tokens - overlap_tokens
    metadata = {
        "title": parsed.title,
        "status": parsed.status,
        version_field: parsed.front_matter.get(version_field, ""),
        "effective_date": parsed.front_matter.get("effective_date", ""),
    }
    structures: list[dict] = []
    start = 0
    while start < total or (start == 0 and total == 0):
        end = min(start + size_tokens, total)
        window_start = parsed.body_start + offsets[start]
        window_end = parsed.body_start + (
            offsets[end] if end < total else len(parsed.body)
        )
        structures.append(
            {
                "source_id": parsed.source_id,
                "text": parsed.raw_text[window_start:window_end],
                "span": [window_start, window_end],
                "content_sha256": parsed.content_sha256,
                "score": 0.0,
                "rank": 0,
                "metadata": dict(metadata),
                "release_id": release_id,
            }
        )
        if end >= total:
            break
        start += step
    return structures


def make_normalized_chunks(
    parsed: ParsedDocument,
    release_id: str,
    version_field: str,
    size_tokens: int = 200,
    overlap_tokens: int = 40,
) -> list[dict]:
    """Split-stage + identity-stage output for one document: all windows."""
    return [
        assign_identity(structure)
        for structure in token_window_structures(
            parsed,
            release_id,
            version_field,
            size_tokens=size_tokens,
            overlap_tokens=overlap_tokens,
        )
    ]


def assign_identity(structure: dict) -> dict:
    """Identity-stage output: contract-stable document/chunk ids on a structure."""
    document_id = identity.document_id(
        structure["source_id"], structure["content_sha256"]
    )
    start, end = structure["span"]
    text = structure["text"]
    return {
        "source_id": structure["source_id"],
        "document_id": document_id,
        "chunk_id": identity.chunk_id(document_id, start, end, text),
        "text": text,
        "span": [start, end],
        "score": structure["score"],
        "rank": structure["rank"],
        "metadata": structure["metadata"],
        "release_id": structure["release_id"],
    }


class BaseAdapter(ABC):
    """Common configuration, tracing, and pipeline flow for both adapters."""

    framework: str = "abstract"

    def __init__(
        self,
        config: Mapping[str, object],
        framework_commit: str,
        framework_package: str,
        run_id: str | None = None,
        ollama_base_url: str | None = None,
    ) -> None:
        self.config = dict(config)
        self.framework_commit = framework_commit
        self.framework_package = framework_package
        self.run_id = run_id or f"run-{datetime.now(UTC).strftime('%Y%m%dT%H%M%S')}"
        self.client = OllamaClient(base_url=ollama_base_url or "http://127.0.0.1:11434")

    # ---- configuration accessors (every retrieval-affecting value explicit) --

    @property
    def embedding_model(self) -> str:
        return str(self.config["models"]["embedding_model"])  # type: ignore[index]

    @property
    def generation_model(self) -> str:
        return str(self.config["models"]["generation_model"])  # type: ignore[index]

    @property
    def top_k(self) -> int:
        return int(self.config["retrieval"]["top_k"])  # type: ignore[index]

    @property
    def budget_tokens(self) -> int:
        return int(self.config["context"]["budget_tokens"])  # type: ignore[index]

    @property
    def prompt_template(self) -> str:
        return str(self.config["generation"]["prompt_template"])  # type: ignore[index]

    @property
    def generation_options(self) -> dict:
        generation = self.config["generation"]  # type: ignore[index]
        return {
            "temperature": float(generation["temperature"]),
            "top_p": float(generation["top_p"]),
            "num_predict": int(generation["max_output_tokens"]),
            "seed": int(generation["seed"]),
        }

    @property
    def reranking_enabled(self) -> bool:
        return bool(self.config["reranking"]["enabled"])  # type: ignore[index]

    def resolved_settings_snapshot(self) -> dict:
        """Snapshot every retrieval-affecting value; no implicit defaults remain."""
        return {
            "chunking": self.config["chunking"],  # type: ignore[index]
            "retrieval_top_k": self.top_k,
            "retriever_conditions": self.config["retrieval"]["retriever_conditions"],  # type: ignore[index]
            "reranking": self.config["reranking"],  # type: ignore[index]
            "context_budget_tokens": self.budget_tokens,
            "packing_order": self.config["context"]["packing_order"],  # type: ignore[index]
            "embedding_model": self.embedding_model,
            "generation_model": self.generation_model,
            "generation_options": self.generation_options,
            "prompt_template": self.prompt_template,
            "ollama_base_url": self.client.base_url,
        }

    # ---- build-time shared stages -------------------------------------------

    def _prepare_chunks(
        self,
        corpus_path: str | Path,
        corpus_manifest: Mapping[str, object],
        trace: object,
        release_id: str,
    ) -> list[dict]:
        """Run parse/split/identity stages shared verbatim by both frameworks."""

        # parse: timer covers the real file reads and front-matter parsing.
        started = time.perf_counter()
        documents = load_corpus(corpus_path, corpus_manifest)
        parse_ms = (time.perf_counter() - started) * 1000.0
        self._emit(
            trace,
            stage="parse",
            component="rag_compare.adapters.base.parse_markdown_file",
            source_reference="corpus/v1/manifest.json identity_contract",
            duration_ms=parse_ms,
            resolved_config={"include_front_matter_in_body": False},
            input_ids=[doc.source_id for doc in documents],
            output_ids=[doc.source_id for doc in documents],
            release_id=release_id,
        )

        version_field = (
            "source_version"
            if corpus_manifest.get("schema_version") == 2  # type: ignore[attr-defined]
            else "policy_version"
        )
        # split: real cl100k_base token windows per the declared chunking
        # config — boundaries, text, spans, and metadata; no identities yet.
        started = time.perf_counter()
        chunking = self.config["chunking"]  # type: ignore[index]
        size_tokens = int(chunking["chunk_size_tokens"])
        overlap_tokens = int(chunking["chunk_overlap_tokens"])
        structures: list[dict] = []
        for doc in documents:
            structures.extend(
                token_window_structures(
                    doc,
                    release_id,
                    version_field,
                    size_tokens=size_tokens,
                    overlap_tokens=overlap_tokens,
                )
            )
        split_ms = (time.perf_counter() - started) * 1000.0
        self._emit(
            trace,
            stage="split",
            component="token_window_cl100k_base",
            source_reference="config/experiment.json chunking",
            duration_ms=split_ms,
            resolved_config={
                "splitter": chunking["splitter"],
                "tokenizer": chunking["tokenizer"],
                "chunk_size_tokens": size_tokens,
                "chunk_overlap_tokens": overlap_tokens,
            },
            input_ids=[doc.source_id for doc in documents],
            output_ids=[structure["source_id"] for structure in structures],
            release_id=release_id,
        )
        # identity: contract-stable document/chunk id assignment only.
        started = time.perf_counter()
        chunks = [assign_identity(structure) for structure in structures]
        identity_ms = (time.perf_counter() - started) * 1000.0
        self._emit(
            trace,
            stage="identity",
            component="rag_compare.identity",
            source_reference="src/rag_compare/identity.py",
            duration_ms=identity_ms,
            resolved_config={
                "document_id_rule": self.config["identity"]["document_id_rule"],  # type: ignore[index]
                "chunk_id_rule": self.config["identity"]["chunk_id_rule"],  # type: ignore[index]
            },
            input_ids=[doc.source_id for doc in documents],
            output_ids=[chunk["chunk_id"] for chunk in chunks],
            metadata_delta={"version_field": version_field},
            release_id=release_id,
        )
        return chunks

    def _corpus_files(self, corpus_manifest: Mapping[str, object]) -> list[dict]:
        files = []
        for entry in sorted(
            corpus_manifest["documents"], key=lambda item: item["path"]  # type: ignore[index]
        ):
            raw = (self.corpus_root / entry["path"]).read_bytes()
            files.append(
                {
                    "path": PurePosixPath("corpus", entry["path"]).as_posix(),
                    "sha256": identity.sha256_bytes(raw),
                }
            )
        return files

    def _build_release_common(
        self,
        corpus_path: str | Path,
        corpus_manifest: Mapping[str, object],
        trace: object,
        embed_stage_callback: Callable[[list[dict], str], EmbedStageResult],
        store_stage_callback: Callable[[list[dict], str], object],
        release_id: str,
    ) -> BuildResult:
        """Shared build flow; framework callbacks supply embed/store behavior."""
        # Manifest paths (v1/*.md) are relative to the corpus directory.
        self.corpus_root = Path(corpus_path).resolve().parent
        chunks = self._prepare_chunks(corpus_path, corpus_manifest, trace, release_id)

        embed_delta = embed_stage_callback(chunks, release_id)

        started = time.perf_counter()
        store_stage_callback(chunks, release_id)
        # Read the stored contents back OUT of the framework's own store and
        # build the inventory from those, so the manifest hash binds to what
        # is actually queryable, not merely to what was handed to the writer.
        stored_chunks = self.read_back_stored_chunks(release_id)
        expected_ids = sorted(chunk["chunk_id"] for chunk in chunks)
        stored_ids = sorted(chunk["chunk_id"] for chunk in stored_chunks)
        if stored_ids != expected_ids:
            raise AdapterError(
                "stored-index read-back does not match the built chunks: "
                f"expected {len(expected_ids)} chunks, read back "
                f"{len(stored_ids)} (missing="
                f"{sorted(set(expected_ids) - set(stored_ids))}, extra="
                f"{sorted(set(stored_ids) - set(expected_ids))})"
            )
        input_by_id = {chunk["chunk_id"]: chunk for chunk in chunks}
        for stored in stored_chunks:
            original = input_by_id[stored["chunk_id"]]
            if stored["text"] != original["text"]:
                raise AdapterError(
                    "stored text differs from built text for chunk "
                    f"{stored['chunk_id']}"
                )
        store_ms = (time.perf_counter() - started) * 1000.0
        inventory_entries = build_chunk_inventory(stored_chunks)
        inventory_sha256 = hashlib.sha256(
            canonical_inventory_bytes(inventory_entries)
        ).hexdigest()
        self._emit(
            trace,
            stage="store",
            component=self.store_component_name(),
            source_reference=self.store_source_reference(),
            duration_ms=store_ms,
            resolved_config={
                "namespace": release_id,
                "duplicate_policy": "reject",
                "chunk_inventory_sha256": inventory_sha256,
                "chunk_count": len(inventory_entries),
            },
            input_ids=[chunk["chunk_id"] for chunk in chunks],
            output_ids=[chunk["chunk_id"] for chunk in chunks],
            release_id=release_id,
        )

        manifest = self._assemble_manifest(
            corpus_manifest, chunks, release_id, embed_delta
        )
        manifest["index"] = {
            "chunk_inventory_sha256": inventory_sha256,
            "chunk_count": len(inventory_entries),
        }
        # Query-time dependencies are part of the release definition: the
        # retriever, reranker, packing, generator, prompt, and sampling
        # parameters must version together with the index for answers to be
        # reproducible.
        generation = self.config["generation"]  # type: ignore[index]
        retrieval = self.config["retrieval"]  # type: ignore[index]
        manifest["query_contract"] = {
            "retrieval": {
                "conditions": list(retrieval["retriever_conditions"]),
                "top_k": self.top_k,
                "score_order": retrieval["score_order"],
                "tie_break_rule": retrieval["tie_break_rule"],
            },
            "reranking": dict(self.config["reranking"]),  # type: ignore[index]
            "context": dict(self.config["context"]),  # type: ignore[index]
            "generation_model": self.generation_model,
            "generation_ollama_id": self.config["models"]["generation_ollama_id"],  # type: ignore[index]
            "prompt_sha256": identity.sha256_bytes(
                str(generation["prompt_template"]).encode("utf-8")
            ),
            "generation_options": self.generation_options,
        }
        observed = BuildArtifacts(
            corpus={
                "version": manifest["corpus"]["version"],
                "files": manifest["corpus"]["files"],
            },
            schema_version=manifest["schema_version"],
            parser=manifest["parser"],
            chunker=manifest["chunker"],
            embedding=manifest["embedding"],
            framework=manifest["framework"],
            document_count=manifest["document_count"],
            chunk_count=manifest["chunk_count"],
            index=manifest["index"],
            query_contract=manifest["query_contract"],
        )
        return BuildResult(
            manifest=manifest, observed=observed, chunks=chunks,
            stored_chunks=stored_chunks,
        )

    def _assemble_manifest(
        self,
        corpus_manifest: Mapping[str, object],
        chunks: list[dict],
        release_id: str,
        embed_delta: dict,
    ) -> dict:
        vectors = embed_delta.vectors
        return {
            "release_id": release_id,
            "schema_version": corpus_manifest.get("schema_version", 1),
            "corpus": {
                "version": corpus_manifest.get("corpus_version", ""),  # type: ignore[attr-defined]
                "files": self._corpus_files(corpus_manifest),
            },
            "built_at": datetime.now(UTC).isoformat(timespec="seconds"),
            "validation_status": "passed",
            "parser": {"identity": PARSER_IDENTITY, "config": {}},
            "chunker": {
                "identity": CHUNKER_IDENTITY,
                "size": int(self.config["chunking"]["chunk_size_tokens"]),  # type: ignore[index]
                "overlap": int(self.config["chunking"]["chunk_overlap_tokens"]),  # type: ignore[index]
                "config_sha256": identity.sha256_bytes(
                    json.dumps(  # type: ignore[arg-type]
                        dict(self.config["chunking"]), sort_keys=True
                    ).encode("utf-8")
                ),
            },
            "embedding": {
                "name": self.embedding_model,
                "ollama_digest": embed_delta.embedding_digest,
                "dimensions": len(vectors[0]) if vectors else 0,
                "distance_metric": "cosine",
            },
            "framework": {
                "commit": self.framework_commit,
                "package": self.framework_package,
                "adapter": self.adapter_name(),
            },
            "document_count": len(corpus_manifest["documents"]),  # type: ignore[index]
            "chunk_count": len(chunks),
        }

    def _embed_chunks(self, chunks: list[dict], release_id: str, trace: object) -> dict:
        """Embedding stage shared by both adapters (identical vectors)."""


        started = time.perf_counter()
        vectors = self.client.embed(
            self.embedding_model, [chunk["text"] for chunk in chunks]
        )
        digest = embedding_identity_digest(self.embedding_model, vectors)
        self._emit(
            trace,
            stage="embed",
            component=f"OllamaClient.embed({self.embedding_model})",
            source_reference="artifacts/raw/environment-freeze.txt approved_models",
            duration_ms=(time.perf_counter() - started) * 1000.0,
            resolved_config={
                "model": self.embedding_model,
                "dimensions": len(vectors[0]) if vectors else 0,
            },
            input_ids=[chunk["chunk_id"] for chunk in chunks],
            output_ids=[chunk["chunk_id"] for chunk in chunks],
            metadata_delta={"embedding_digest": digest[:16]},
            release_id=release_id,
        )
        return EmbedStageResult(vectors=vectors, embedding_digest=digest)

    # ---- query-time shared pipeline -----------------------------------------

    def query(
        self,
        query_text: str,
        retriever_kind: str,
        active_release: str,
        trace: object,
    ) -> dict:
        """Execute the shared query pipeline against the captured release."""


        allowed = set(self.config["retrieval"]["retriever_conditions"])  # type: ignore[index]
        if retriever_kind not in allowed:
            raise AdapterError(f"unknown retriever_kind: {retriever_kind}")

        started = time.perf_counter()
        self._emit(
            trace,
            stage="capture_release",
            component="rag_compare.release.capture_active_release",
            source_reference="src/rag_compare/release.py",
            duration_ms=(time.perf_counter() - started) * 1000.0,
            resolved_config={"captured_release": active_release},
            input_ids=[],
            output_ids=[active_release],
            release_id=active_release,
        )

        candidates = self.retrieve_candidates(
            query_text, retriever_kind, active_release, trace
        )

        started = time.perf_counter()
        filtered = self._enforce_release(active_release, [candidates])
        self._emit(
            trace,
            stage="release_filter",
            component="rag_compare.release.filter_chunks_for_release",
            source_reference="src/rag_compare/release.py",
            duration_ms=(time.perf_counter() - started) * 1000.0,
            resolved_config={"release_id": active_release},
            input_ids=[c["chunk_id"] for c in candidates],
            output_ids=[c["chunk_id"] for c in filtered],
            release_id=active_release,
        )

        started = time.perf_counter()
        if self.reranking_enabled:
            from rag_compare.rerank import rerank_candidates

            ordered = rerank_candidates(query_text, filtered)
            method = "coverage_rerank"
        else:
            ordered = sorted(filtered, key=lambda c: (int(c["rank"]), c["chunk_id"]))
            method = "none_passthrough_rank_then_chunk_id"
        self._emit(
            trace,
            stage="rerank",
            component=f"rag_compare.rerank.{method}",
            source_reference="src/rag_compare/rerank.py",
            duration_ms=(time.perf_counter() - started) * 1000.0,
            resolved_config={"method": method, "enabled": self.reranking_enabled},
            release_id=active_release,
            input_ids=[c["chunk_id"] for c in filtered],
            output_ids=[c["chunk_id"] for c in ordered],
            score_rank_delta=[
                {"chunk_id": c["chunk_id"], "score": c["score"], "rank": c["rank"]}
                for c in ordered
            ],
        )

        started = time.perf_counter()
        packed = pack_context(ordered, budget_tokens=self.budget_tokens)
        self._emit(
            trace,
            stage="pack",
            component="rag_compare.rerank.pack_context",
            source_reference="src/rag_compare/rerank.py",
            duration_ms=(time.perf_counter() - started) * 1000.0,
            resolved_config={
                "budget_tokens": self.budget_tokens,
                "truncation": "never",
            },
            release_id=active_release,
            input_ids=[c["chunk_id"] for c in ordered],
            output_ids=[c["chunk_id"] for c in packed["packed"]],
            metadata_delta={
                "rejected": packed["rejected"],
                "used_tokens": packed["used_tokens"],
            },
        )

        started = time.perf_counter()
        answer = self._generate(query_text, packed["packed"])
        generate_ms = (time.perf_counter() - started) * 1000.0
        self._emit(
            trace,
            stage="generate",
            component=f"OllamaClient.generate({self.generation_model})",
            source_reference="config/experiment.json generation",
            duration_ms=generate_ms,
            resolved_config=self.generation_options,
            input_ids=[c["chunk_id"] for c in packed["packed"]],
            output_ids=[],
            metadata_delta={"answer_chars": len(answer)},
            artifact_path="",
            release_id=active_release,
        )

        # Citation extraction is its own observable stage: the model's [n]
        # markers are parsed and resolved to contract-stable chunks here, so
        # trace consumers can audit citation provenance independently of
        # generation.
        started = time.perf_counter()
        citations = self.extract_citations(answer, packed["packed"])
        self._emit(
            trace,
            stage="citation",
            component="rag_compare.adapters.base.extract_citations",
            source_reference="config/experiment.json context.citation_mode",
            duration_ms=(time.perf_counter() - started) * 1000.0,
            resolved_config={
                "citation_mode": self.config["context"]["citation_mode"],  # type: ignore[index]
                "marker_pattern": "[n] first-mention order",
            },
            input_ids=[c["chunk_id"] for c in packed["packed"]],
            output_ids=[c["chunk_id"] for c in citations],
            metadata_delta={"citations": citations},
            release_id=active_release,
        )

        return {
            "query": query_text,
            "retriever_kind": retriever_kind,
            "active_release": active_release,
            "candidates": candidates,
            "context": packed,
            "answer": answer,
            "citations": citations,
        }

    def _generate(self, query_text: str, packed: list[dict]) -> str:
        blocks = []
        for position, chunk in enumerate(packed, start=1):
            blocks.append(
                f"[{position}] source_id={chunk['source_id']} "
                f"chunk_id={chunk['chunk_id']}\n{chunk['text']}"
            )
        prompt = (
            f"{self.prompt_template}\n\nContext:\n"
            + "\n\n".join(blocks)
            + "\n\nQuestion: "
            + query_text
        )
        return self.client.generate(
            self.generation_model, prompt, **self.generation_options
        )

    @staticmethod
    def extract_citations(answer: str, packed: list[dict]) -> list[dict]:
        """Resolve the model's [n] markers into contract-stable citations.

        Citations are model-derived: only blocks the answer actually cites
        become citations, in first-mention order. An answer citing nothing
        produces no citations, so downstream metrics measure what the model
        cited — not what was packed.
        """
        by_position = {
            position: chunk for position, chunk in enumerate(packed, start=1)
        }
        citations = []
        seen = set()
        for marker in re.findall(r"\[(\d+)\]", answer):
            position = int(marker)
            if position in seen or position not in by_position:
                continue
            seen.add(position)
            chunk = by_position[position]
            citations.append(
                {
                    "position": position,
                    "source_id": chunk["source_id"],
                    "document_id": chunk["document_id"],
                    "chunk_id": chunk["chunk_id"],
                    "span": chunk["span"],
                    "release_id": chunk["release_id"],
                }
            )
        return citations

    def _enforce_release(self, active_release, branches):
        from rag_compare.release import filter_chunks_for_release

        return filter_chunks_for_release(active_release, branches)

    # ---- tracing -------------------------------------------------------------

    def _emit(
        self,
        trace: object,
        *,
        stage: str,
        component: str,
        source_reference: str,
        duration_ms: float,
        resolved_config: object,
        input_ids: list,
        output_ids: list,
        metadata_delta: object = None,
        score_rank_delta: object = None,
        release_id: str,
        artifact_path: str = "",
        status: str = "ok",
        error: object = None,
    ) -> None:
        event = StageEvent(
            run_id=self.run_id,
            framework=self.framework,
            framework_commit=self.framework_commit,
            path=f"src/rag_compare/adapters/{self.adapter_name()}.py",
            stage=stage,
            component=component,
            source_reference=source_reference,
            started_at=datetime.now(UTC).isoformat(timespec="milliseconds"),
            duration_ms=max(duration_ms, 0.0),
            resolved_config=resolved_config,
            input_ids=list(input_ids),
            output_ids=list(output_ids),
            metadata_delta=metadata_delta,
            score_rank_delta=score_rank_delta,
            release_id=release_id,
            artifact_path=artifact_path,
            status=status,
            error=error,
        )
        trace.append(event)

    # ---- framework-specific surface ------------------------------------------

    @abstractmethod
    def adapter_name(self) -> str: ...

    @abstractmethod
    def store_component_name(self) -> str: ...

    @abstractmethod
    def store_source_reference(self) -> str: ...

    @abstractmethod
    def build_release(self, corpus_path, manifest, trace) -> BuildResult: ...

    @abstractmethod
    def read_back_stored_chunks(self, release_id: str) -> list[dict]:
        """Read every stored chunk of a release back from the framework store.

        Each entry carries chunk_id, source_id, document_id, span and text as
        actually persisted by the framework, so the release inventory can be
        derived from real index contents rather than in-memory inputs.
        """

    @abstractmethod
    def retrieve_candidates(
        self, query_text: str, retriever_kind: str, active_release: str, trace
    ) -> list[dict]: ...
