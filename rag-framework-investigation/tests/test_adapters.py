"""Contract-equivalence and release-isolation tests for both adapters.

Dense retrieval and generation call the local Ollama server; these tests are
skipped automatically when Ollama is not reachable (the plan expects them to
pass with Ollama running).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rag_compare import identity
from rag_compare.adapters.base import STAGE_ORDER, load_corpus
from rag_compare.adapters.haystack_adapter import HaystackAdapter
from rag_compare.adapters.llamaindex_adapter import LlamaIndexAdapter
from rag_compare.contracts import StageEvent
from rag_compare.release import MixedReleaseError

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((PROJECT_ROOT / "config" / "experiment.json").read_text())
V1_MANIFEST = json.loads((PROJECT_ROOT / "corpus" / "v1" / "manifest.json").read_text())
V2_MANIFEST = json.loads((PROJECT_ROOT / "corpus" / "v2" / "manifest.json").read_text())

LLAMA_COMMIT = "d8021225eb7e7b276d5ceb476b0a4650240f27f8"
HAYSTACK_COMMIT = "c7cb46c0f28ad1984f60e5d3e9404b124a221437"

try:
    import requests as _requests

    _requests.post(
        "http://127.0.0.1:11434/api/embed",
        json={"model": "nomic-embed-text", "input": ["ping"]},
        timeout=5,
    ).raise_for_status()
    OLLAMA_AVAILABLE = True
except Exception:  # pragma: no cover - depends on local environment
    OLLAMA_AVAILABLE = False

needs_ollama = pytest.mark.skipif(
    not OLLAMA_AVAILABLE, reason="Ollama is not running on 127.0.0.1:11434"
)


def make_adapters(tmp_path: Path):
    llama = LlamaIndexAdapter(
        CONFIG,
        LLAMA_COMMIT,
        "llama-index-core",
        run_id="test-li",
    )
    haystack = HaystackAdapter(
        CONFIG,
        HAYSTACK_COMMIT,
        "haystack-ai",
        run_id="test-hs",
    )
    return llama, haystack


def build_v1(adapter, tmp_path: Path):
    trace_path = tmp_path / f"{adapter.framework}-build.jsonl"
    trace = JsonlTraceSpy(trace_path)
    result = adapter.build_release(PROJECT_ROOT / "corpus" / "v1", V1_MANIFEST, trace)
    return result, trace


class JsonlTraceSpy:
    """Trace sink that validates each event via StageEvent before writing."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.events: list[dict] = []

    def append(self, event: StageEvent) -> None:
        self.events.append(event.to_dict())
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event.to_dict(), sort_keys=True) + "\n")

    def stage_order(self) -> list[str]:
        return [event["stage"] for event in self.events]


def query_with_trace(adapter, tmp_path: Path, retriever_kind: str, release_id: str):
    trace = JsonlTraceSpy(
        tmp_path / f"{adapter.framework}-query-{retriever_kind}.jsonl"
    )
    result = adapter.query(
        "Can contractors expense hotel Wi-Fi and when is approval required?",
        retriever_kind,
        release_id,
        trace,
    )
    return result, trace


def test_both_adapters_implement_shared_contract():
    from rag_compare.adapters.base import BaseAdapter

    for adapter_cls in (LlamaIndexAdapter, HaystackAdapter):
        assert issubclass(adapter_cls, BaseAdapter)
        for method in ("build_release", "query"):
            assert callable(getattr(adapter_cls, method))


@pytest.mark.parametrize("adapter_cls", [LlamaIndexAdapter, HaystackAdapter])
@needs_ollama
def test_build_release_produces_validatable_manifest(tmp_path, adapter_cls):
    from rag_compare.release import validate_release

    adapter = adapter_cls(CONFIG, LLAMA_COMMIT, "pkg")
    result, trace = build_v1(adapter, tmp_path)

    manifest = result.manifest
    assert manifest["release_id"] == V1_MANIFEST["corpus_version"]
    assert manifest["validation_status"] == "passed"
    assert manifest["document_count"] == 6
    assert manifest["chunk_count"] == 6
    assert manifest["embedding"]["dimensions"] > 0

    # Stage the release namespace on disk exactly as promotion expects:
    # <release_dir>/corpus/v1/*.md
    import shutil

    release_dir = tmp_path / "releases" / "v1"
    (release_dir / "corpus" / "v1").mkdir(parents=True)
    for md_file in (PROJECT_ROOT / "corpus" / "v1").glob("*.md"):
        shutil.copy(md_file, release_dir / "corpus" / "v1" / md_file.name)

    # The index artifact is part of the release: write the chunk inventory.
    from rag_compare.release import write_index_inventory

    write_index_inventory(release_dir, result.chunks)

    # Manifest must validate against observed artifacts and on-disk corpus.
    validated = validate_release(release_dir, manifest, result.observed)
    assert validated.release_id == "v1"

    # Identity contract holds: recomputed IDs equal stored ones.
    parsed_docs = {
        doc.source_id: doc for doc in load_corpus(
            PROJECT_ROOT / "corpus" / "v1", V1_MANIFEST
        )
    }
    for chunk in result.chunks:
        parsed = parsed_docs[chunk["source_id"]]
        content_hash = identity.sha256_bytes(parsed.raw_text.encode("utf-8"))
        document_id = identity.document_id(chunk["source_id"], content_hash)
        assert chunk["document_id"] == document_id
        start, end = chunk["span"]
        assert chunk["chunk_id"] == identity.chunk_id(
            document_id, start, end, chunk["text"]
        )
        # The span resolves to the exact body text inside the raw file.
        assert parsed.raw_text[start:end].strip() == chunk["text"]

    # Build emits parse/split/identity/embed/store in order.
    assert trace.stage_order() == ["parse", "split", "identity", "embed", "store"]


@needs_ollama
def test_stage_order_is_identical_across_frameworks(tmp_path):
    llama, haystack = make_adapters(tmp_path)
    build_v1(llama, tmp_path)
    build_v1(haystack, tmp_path)

    expected_query_stages = [
        "capture_release",
        "retrieve",
        "release_filter",
        "rerank",
        "pack",
        "generate",
        "citation",
    ]
    assert STAGE_ORDER == expected_query_stages

    for kind in ("bm25", "ollama_dense"):
        _, llama_trace = query_with_trace(llama, tmp_path, kind, "v1")
        _, hs_trace = query_with_trace(haystack, tmp_path, kind, "v1")
        assert llama_trace.stage_order() == expected_query_stages
        assert hs_trace.stage_order() == expected_query_stages


@needs_ollama
def test_all_trace_fields_present_and_serializable(tmp_path):
    llama, haystack = make_adapters(tmp_path)
    build_v1(llama, tmp_path)
    build_v1(haystack, tmp_path)

    required_fields = set(StageEvent.__dataclass_fields__)
    for adapter in (llama, haystack):
        for kind in ("bm25", "ollama_dense"):
            result, trace = query_with_trace(adapter, tmp_path, kind, "v1")
            for event in trace.events:
                assert set(event) == required_fields
                assert event["duration_ms"] >= 0
                assert isinstance(event["input_ids"], list)
                assert isinstance(event["output_ids"], list)
                json.dumps(event["resolved_config"])
            assert result["active_release"] == "v1"


@pytest.mark.parametrize("kind", ["bm25", "ollama_dense"])
@needs_ollama
def test_candidates_carry_active_release_and_provenance(tmp_path, kind):
    llama, haystack = make_adapters(tmp_path)
    build_v1(llama, tmp_path)
    build_v1(haystack, tmp_path)

    for adapter in (llama, haystack):
        result, _ = query_with_trace(adapter, tmp_path, kind, "v1")
        for candidate in result["candidates"]:
            assert candidate["release_id"] == "v1"
            for field in (
                "source_id",
                "document_id",
                "chunk_id",
                "text",
                "span",
                "score",
                "rank",
                "metadata",
            ):
                assert field in candidate
        # Citations resolve back to corpus spans.
        corpus_dir = PROJECT_ROOT / "corpus" / "v1"
        parsed_docs = {
            doc.source_id: doc for doc in load_corpus(corpus_dir, V1_MANIFEST)
        }
        for citation in result["citations"]:
            parsed = next(
                doc
                for doc in parsed_docs.values()
                if identity.document_id(
                    doc.source_id,
                    identity.sha256_bytes(doc.raw_text.encode()),
                )
                == citation["document_id"]
            )
            start, end = citation["span"]
            assert 0 <= start < end <= len(parsed.raw_text)


@needs_ollama
def test_second_release_does_not_mix_into_first(tmp_path):
    llama, haystack = make_adapters(tmp_path)
    for adapter in (llama, haystack):
        build_v1(adapter, tmp_path)
        adapter.build_release(
            PROJECT_ROOT / "corpus" / "v2", V2_MANIFEST, JsonlTraceSpy(
                tmp_path / f"{adapter.framework}-build-v2.jsonl"
            )
        )
        # v2 exists in-process but v1 remains the captured active release.
        result, _ = query_with_trace(adapter, tmp_path, "bm25", "v1")
        releases = {c["release_id"] for c in result["candidates"]}
        assert releases == {"v1"}
        packed_releases = {c["release_id"] for c in result["context"]["packed"]}
        assert packed_releases == {"v1"}


@needs_ollama
def test_foreign_chunk_injected_into_branch_raises_mixed_release_error(tmp_path):
    """Changing the release between capture and retrieval cannot mix versions."""
    llama, haystack = make_adapters(tmp_path)
    for adapter in (llama, haystack):
        build_v1(adapter, tmp_path)

        original = adapter.retrieve_candidates

        def inject_foreign(query_text, kind, release_id, trace, _original=original):
            candidates = _original(query_text, kind, release_id, trace)
            if candidates:
                foreign = dict(candidates[0])
                foreign["release_id"] = "synthetic-policy-v2"
                candidates.append(foreign)
            return candidates

        adapter.retrieve_candidates = inject_foreign  # type: ignore[method-assign]
        with pytest.raises(MixedReleaseError):
            adapter.query("hotel wifi limit", "bm25", "v1", JsonlTraceSpy(
                tmp_path / f"{adapter.framework}-mixed.jsonl"
            ))
