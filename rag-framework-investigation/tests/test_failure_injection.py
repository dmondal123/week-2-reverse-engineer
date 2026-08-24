"""Task 7: controlled partial-release failure injection (end-to-end).

Scenario (single runtime execution, Ollama-only):

Phase A — first-failure injection
    1. Activate v1: build the full v1 release, validate it, and publish it
       through the Task 3 atomic pointer replacement.
    2. Index ONLY the first half of v2 (3 of 5 documents) into a staging
       namespace, then attempt promotion with a manifest claiming the full
       v2 document set (the naive partial-release mistake).
    3. Expected: ``validate_release`` rejects the partial release, the active
       pointer still reads v1 byte-for-byte, and querying every fixed
       evaluation case against the captured active release returns only v1
       chunks — no mixed-version answer is possible.

Phase B — recovery and atomic promotion
    4. Complete v2 (all five documents), validate the completed release,
       promote it with exactly one atomic pointer replacement, and query all
       cases again: every chunk must be v2 and deleted v1 content (e.g.
       office-snacks, absent from v2) cannot be returned even after the v1
       namespace is removed.

Evidence:
    - Phase A trace -> artifacts/raw/failure-injection-trace.jsonl
      (first-failure evidence; never overwritten by Phase B)
    - Phase B trace -> artifacts/raw/failure-injection-post-recovery-trace.jsonl
    - Summary       -> artifacts/results/failure-injection.json

The scenario executes once per pytest session (module-scoped fixture); each
test asserts one acceptance facet against the recorded evidence.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from datetime import UTC, datetime
from pathlib import Path

import pytest

from rag_compare.adapters.base import STAGE_ORDER
from rag_compare.adapters.haystack_adapter import HaystackAdapter
from rag_compare.adapters.llamaindex_adapter import LlamaIndexAdapter
from rag_compare.contracts import StageEvent
from rag_compare.metrics import evaluate_case
from rag_compare.release import (
    BuildArtifacts,
    ReleaseValidationError,
    capture_active_release,
    filter_chunks_for_release,
    promote_release,
    write_index_inventory,
)

FRAMEWORK_COMMITS = {
    "haystack": ("c7cb46c0f28ad1984f60e5d3e9404b124a221437", "haystack"),
    "llamaindex": ("d8021225eb7e7b276d5ceb476b0a4650240f27f8", "llama_index"),
}

PROJECT_ROOT = Path(__file__).resolve().parents[1]

V1_RELEASE_ID = "v1"
V2_RELEASE_ID = "v2"

# Dense retrieval is exercised once per phase so both retrieval branches are
# proven release-filtered without duplicating every generation call.
DENSE_PROBE_CASE = "multi_fact_wifi"

# The acceptance checks each expected behavior in the evidence record maps to.
EXPECTED_BEHAVIOR = {
    "partial_promotion_rejected": (
        "promoting a staging release whose directory holds only half of v2 "
        "while its manifest claims all five documents must raise "
        "ReleaseValidationError"
    ),
    "pointer_unchanged_after_failure": (
        "a failed validation must leave the active pointer byte-identical "
        '(still {"release_id": "v1"})'
    ),
    "phase_a_all_results_v1": (
        "every evaluation case queried against the captured active release "
        "must return only v1 chunks on both retrieval branches"
    ),
    "phase_a_no_v2_chunk_returned": (
        "no chunk from the incomplete v2 build may reach any Phase A query"
    ),
    "complete_v2_validated_and_promoted": (
        "the completed v2 release passes validation and promotion succeeds"
    ),
    "phase_b_all_results_v2": (
        "after atomic promotion every queried chunk belongs to v2 only"
    ),
    "deleted_v1_content_not_returned": (
        "with the v1 namespace removed, deleted v1 content cannot be returned"
    ),
    "office_snacks_absent_after_v2": (
        "office-snacks exists only in v1 and must never be served under v2"
    ),
    "mixed_release_filter_raises": (
        "filter_chunks_for_release must raise MixedReleaseError when a branch "
        "carries a chunk from another release"
    ),
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class TraceWriter:
    """Append-only JSONL trace sink; one instance per phase."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.events: list[dict] = []
        self.count = 0
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            path.unlink()  # fresh trace for this run id
        self._handle = path.open("a", encoding="utf-8")

    def append(self, event: StageEvent) -> None:
        record = event.to_dict()
        self.events.append(record)
        self._handle.write(json.dumps(record, sort_keys=True) + "\n")
        self._handle.flush()
        self.count += 1

    def close(self) -> None:
        self._handle.close()


def load_json(relative: str):
    return json.loads((PROJECT_ROOT / relative).read_text(encoding="utf-8"))


def copy_corpus_files(
    corpus_version: str,
    target_dir: Path,
    source_ids: set[str] | None = None,
) -> list[dict]:
    """Copy corpus files into a release directory; return manifest file entries."""
    corpus_target = target_dir / "corpus" / corpus_version
    corpus_target.mkdir(parents=True, exist_ok=True)
    entries = []
    version_dir = PROJECT_ROOT / "corpus" / corpus_version
    for path in sorted(version_dir.glob("*.md")):
        if source_ids is not None and path.stem not in source_ids:
            continue
        shutil.copy2(path, corpus_target / path.name)
        entries.append(
            {
                "path": f"corpus/{corpus_version}/{path.name}",
                "sha256": sha256_file(corpus_target / path.name),
            }
        )
    return entries


def make_adapter(config: dict, framework: str):
    """Build the adapter for one framework; the scenario is framework-generic."""
    commit, package = FRAMEWORK_COMMITS[framework]
    adapter_cls = {
        "haystack": HaystackAdapter,
        "llamaindex": LlamaIndexAdapter,
    }[framework]
    return adapter_cls(
        config,
        framework_commit=commit,
        framework_package=package,
        run_id=f"failure-injection-{datetime.now(UTC).strftime('%Y%m%dT%H%M%S')}",
    )


def first_half_source_ids(v2_documents: list[dict]) -> set[str]:
    """The first half (rounded up: 3 of 5) of v2's documents, by manifest order.

    Rounding up keeps the partial build strictly smaller than the full corpus
    while still indexing a contiguous prefix of the release manifest.
    """
    count = len(v2_documents) // 2 + len(v2_documents) % 2
    return {doc["source_id"] for doc in v2_documents[:count]}


def query_all_cases(
    adapter: HaystackAdapter,
    config: dict,
    captured_release: str,
    trace: TraceWriter,
    dense_probe: str = DENSE_PROBE_CASE,
) -> list[dict]:
    """Query every fixed evaluation case against the captured release."""
    results = []
    top_k = int(config["retrieval"]["top_k"])
    for case in load_json("eval/cases.json"):
        kind = "ollama_dense" if case["case_id"] == dense_probe else "bm25"
        outcome = adapter.query(case["query"], kind, captured_release, trace)
        recent_events = trace.events[-len(STAGE_ORDER) * 2 :]
        evaluation = evaluate_case(case, outcome, recent_events, top_k)
        release_ids = {c["release_id"] for c in outcome["candidates"]} | {
            c["release_id"] for c in outcome["citations"]
        }
        results.append(
            {
                "case_id": case["case_id"],
                "retriever_kind": kind,
                "captured_release": captured_release,
                "returned_release_ids": sorted(release_ids),
                "chunk_ids": [c["chunk_id"] for c in outcome["candidates"]],
                "source_ids": [
                    c.get("source_id") for c in outcome["context"]["packed"]
                ],
                "answer_excerpt": outcome["answer"][:200],
                "metrics": evaluation,
                "no_mixed_release": release_ids <= {captured_release},
            }
        )
    return results


# ---- Scenario phases --------------------------------------------------------


def activate_v1(
    adapter: HaystackAdapter, pointer_path: Path, v1_dir: Path, trace: TraceWriter
) -> dict:
    """Build, validate, and atomically publish the full v1 release."""
    build_v1 = adapter.build_release(
        PROJECT_ROOT / "corpus/v1",
        load_json("corpus/v1/manifest.json"),
        trace,
    )
    copy_corpus_files("v1", v1_dir)
    write_index_inventory(v1_dir, build_v1.chunks)
    validated = promote_release(
        v1_dir, build_v1.manifest, build_v1.observed, pointer_path
    )
    assert validated.release_id == V1_RELEASE_ID
    return build_v1


def inject_partial_v2(
    adapter: HaystackAdapter,
    tmp_path: Path,
    v2_staging_dir: Path,
    pointer_path: Path,
    trace: TraceWriter,
) -> dict:
    """Index half of v2 into staging and attempt promotion with a full claim.

    Returns observed evidence: the rejection error and pointer bytes before
    and after the failed validation.
    """
    v2_manifest = load_json("corpus/v2/manifest.json")
    half_ids = first_half_source_ids(v2_manifest["documents"])
    partial_docs = [
        doc for doc in v2_manifest["documents"] if doc["source_id"] in half_ids
    ]
    assert len(partial_docs) < len(v2_manifest["documents"])

    # Index ONLY the staged half through the normal adapter build path.
    staging_corpus = tmp_path / "index-input" / V2_RELEASE_ID
    staging_corpus.mkdir(parents=True)
    for doc in partial_docs:
        shutil.copy2(
            PROJECT_ROOT / "corpus" / doc["path"],
            staging_corpus / Path(doc["path"]).name,
        )
    partial_input = {**v2_manifest, "documents": partial_docs}
    partial_build = adapter.build_release(staging_corpus, partial_input, trace)

    # Stage the release directory with ONLY the files that were indexed; the
    # claimed manifest below asserts the FULL v2 document set anyway.
    staged_files = copy_corpus_files(V2_RELEASE_ID, v2_staging_dir, source_ids=half_ids)
    assert len(staged_files) == len(partial_docs)
    # A realistic partial build also stores only what it indexed.
    write_index_inventory(v2_staging_dir, partial_build.chunks)

    claimed_files = [
        {
            "path": f"corpus/v2/{Path(doc['path']).name}",
            "sha256": sha256_file(PROJECT_ROOT / "corpus" / doc["path"]),
        }
        for doc in v2_manifest["documents"]
    ]
    # Naive partial-release claim: parser/chunker/embedding/framework are
    # copied as a real build would report them; corpus/files/counts claim ALL
    # of v2 while the staged directory holds only half.
    shared = claim_partial_v2_sections(adapter)
    claimed_manifest = {
        "release_id": V2_RELEASE_ID,
        "schema_version": v2_manifest["schema_version"],
        "built_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "validation_status": "passed",
        **shared,
        "corpus": {"version": "v2", "files": claimed_files},
        "document_count": len(v2_manifest["documents"]),
        "chunk_count": len(v2_manifest["documents"]),
        # Naive index claim: the partial build's own inventory digest, while
        # chunk_count claims the FULL v2 set. Validation must reject this.
        "index": {
            "chunk_inventory_sha256": partial_build.manifest["index"][
                "chunk_inventory_sha256"
            ],
            "chunk_count": len(v2_manifest["documents"]),
        },
        "query_contract": {
            "retrieval": {"conditions": ["bm25"], "top_k": 5,
                          "score_order": "descending",
                          "tie_break_rule": "score_desc_then_chunk_id_asc"},
            "reranking": {"enabled": False, "method": "none"},
            "context": {"budget_tokens": 1200},
            "generation_model": "test-gen",
            "generation_ollama_id": "deadbeef",
            "prompt_sha256": "p" * 64,
            "generation_options": {"temperature": 0},
        },
    }
    claimed_observed = BuildArtifacts(
        corpus=claimed_manifest["corpus"],
        schema_version=claimed_manifest["schema_version"],
        parser=claimed_manifest["parser"],
        chunker=claimed_manifest["chunker"],
        embedding=claimed_manifest["embedding"],
        framework=claimed_manifest["framework"],
        document_count=claimed_manifest["document_count"],
        chunk_count=claimed_manifest["chunk_count"],
        index=claimed_manifest["index"],
    )

    pointer_bytes_before = pointer_path.read_bytes()
    rejection_error = None
    try:
        promote_release(
            v2_staging_dir, claimed_manifest, claimed_observed, pointer_path
        )
    except ReleaseValidationError as error:
        rejection_error = str(error)

    return {
        "partial_promotion_error": rejection_error,
        "assertions": {
            "partial_promotion_rejected": rejection_error is not None,
            "pointer_unchanged_after_failure": (
                pointer_path.read_bytes() == pointer_bytes_before
            ),
        },
        "pointer_after_failed_promotion": json.loads(
            pointer_path.read_text(encoding="utf-8")
        ),
        "active_release_captured_phase_a": capture_active_release(pointer_path),
    }


def claim_partial_v2_sections(adapter: HaystackAdapter) -> dict:
    """Shared manifest sections (parser/chunker/embedding/framework) as a
    real build reports them; the naive partial release copies these verbatim."""
    return {
        "parser": {"identity": "markdown_front_matter_v1", "config": {}},
        "chunker": {
            "identity": "token_window_cl100k_base_v2",
            "size": int(adapter.config["chunking"]["chunk_size_tokens"]),
            "overlap": int(adapter.config["chunking"]["chunk_overlap_tokens"]),
            "config_sha256": "0" * 64,
        },
        "embedding": {
            "name": str(adapter.config["models"]["embedding_model"]),
            "ollama_digest": "0" * 64,
            "dimensions": 768,
            "distance_metric": "cosine",
        },
        "framework": {
            "commit": adapter.framework_commit,
            "package": adapter.framework_package,
            "adapter": adapter.adapter_name(),
        },
    }


def recover_and_promote_v2(
    adapter: HaystackAdapter,
    v2_staging_dir: Path,
    pointer_path: Path,
    trace: TraceWriter,
) -> tuple[object, dict]:
    """Complete v2, validate it, and promote it with one atomic replacement."""
    v2_manifest = load_json("corpus/v2/manifest.json")
    build_v2 = adapter.build_release(
        PROJECT_ROOT / "corpus" / V2_RELEASE_ID, v2_manifest, trace
    )
    copy_corpus_files(V2_RELEASE_ID, v2_staging_dir)
    write_index_inventory(v2_staging_dir, build_v2.chunks)
    promoted = promote_release(
        v2_staging_dir, build_v2.manifest, build_v2.observed, pointer_path
    )
    evidence = {
        "pointer_after_recovery_promotion": json.loads(
            pointer_path.read_text(encoding="utf-8")
        ),
        "active_release_captured_phase_b": capture_active_release(pointer_path),
        "assertions": {
            "complete_v2_validated_and_promoted": promoted.release_id == V2_RELEASE_ID,
        },
    }
    return build_v2, evidence


# ---- Session scenario -------------------------------------------------------


@pytest.fixture(scope="module", params=["llamaindex", "haystack"])
def scenario(tmp_path_factory, request):
    framework = request.param
    tmp_path = tmp_path_factory.mktemp("failure-injection")
    config = load_json("config/experiment.json")

    # Preconditions: Ollama availability is required before any runtime call.
    adapter = make_adapter(config, framework)
    evidence: dict = {
        "run_id": adapter.run_id,
        "started_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "ollama_version": adapter.client.version(),
        "framework": framework,
        "commands": ["pytest tests/test_failure_injection.py -v"],
        "expected_behavior": EXPECTED_BEHAVIOR,
        "assertions": {},
    }
    trace_a = TraceWriter(
        PROJECT_ROOT / f"artifacts/raw/failure-injection-{framework}-trace.jsonl"
    )
    trace_b = TraceWriter(
        PROJECT_ROOT
        / f"artifacts/raw/failure-injection-{framework}-post-recovery-trace.jsonl"
    )

    try:
        pointer_path = tmp_path / "active-release.json"
        releases = tmp_path / "releases"

        # ---- Phase A -------------------------------------------------------
        build_v1 = activate_v1(adapter, pointer_path, releases / V1_RELEASE_ID, trace_a)
        evidence["pointer_before_partial_attempt"] = json.loads(
            pointer_path.read_text(encoding="utf-8")
        )

        failure = inject_partial_v2(
            adapter, tmp_path, releases / V2_RELEASE_ID, pointer_path, trace_a
        )
        merge_evidence(evidence, failure)

        captured_a = capture_active_release(pointer_path)
        evidence["phase_a_queries"] = query_all_cases(
            adapter, config, captured_a, trace_a
        )
        queries = evidence["phase_a_queries"]
        evidence["assertions"]["phase_a_all_results_v1"] = all(
            q["no_mixed_release"] and q["returned_release_ids"] == [V1_RELEASE_ID]
            for q in queries
        )
        v1_chunk_ids = {c["chunk_id"] for c in build_v1.chunks}
        evidence["assertions"]["phase_a_no_v2_chunk_returned"] = all(
            set(q["chunk_ids"]) <= v1_chunk_ids for q in queries
        )

        # ---- Phase B -------------------------------------------------------
        build_v2, recovery = recover_and_promote_v2(
            adapter, releases / V2_RELEASE_ID, pointer_path, trace_b
        )
        merge_evidence(evidence, recovery)

        # Deleted-v1 content cannot be returned: retire the v1 namespace via
        # the public drop_release method, then the release filter must still
        # isolate queries to v2 only.
        adapter.drop_release(V1_RELEASE_ID)

        captured_b = capture_active_release(pointer_path)
        evidence["phase_b_queries"] = query_all_cases(
            adapter, config, captured_b, trace_b
        )
        queries = evidence["phase_b_queries"]
        evidence["assertions"]["phase_b_all_results_v2"] = all(
            q["no_mixed_release"] and q["returned_release_ids"] == [V2_RELEASE_ID]
            for q in queries
        )
        v2_chunk_ids = {c["chunk_id"] for c in build_v2.chunks}
        evidence["assertions"]["deleted_v1_content_not_returned"] = all(
            set(q["chunk_ids"]) <= v2_chunk_ids for q in queries
        )
        evidence["assertions"]["office_snacks_absent_after_v2"] = all(
            "office-snacks" not in q["source_ids"] for q in queries
        )

        # Mixed-release defense-in-depth at the filter itself.
        mixed_raised = False
        try:
            poisoned = dict(build_v2.chunks[0], release_id=V1_RELEASE_ID)
            filter_chunks_for_release(V2_RELEASE_ID, [[poisoned]])
        except Exception as error:
            mixed_raised = type(error).__name__ == "MixedReleaseError"
        evidence["assertions"]["mixed_release_filter_raises"] = mixed_raised

        evidence["manifest_sha256"] = {
            name: sha256_file(PROJECT_ROOT / name)
            for name in (
                "corpus/v1/manifest.json",
                "corpus/v2/manifest.json",
                "config/experiment.json",
                "eval/cases.json",
            )
        }
        evidence["trace_event_counts"] = {
            "first_failure_trace": trace_a.count,
            "post_recovery_trace": trace_b.count,
        }
    finally:
        trace_a.close()
        trace_b.close()

    finalize_evidence(evidence)
    return evidence


def merge_evidence(evidence: dict, phase: dict) -> None:
    """Merge a phase result; nested ``assertions`` dicts combine, not replace."""
    assertions = {**evidence["assertions"], **phase.pop("assertions")}
    evidence.update(phase)
    evidence["assertions"] = assertions


def finalize_evidence(evidence: dict) -> None:
    """Stamp completion metadata and persist the sanitized result summaries.

    One per-framework result file plus a combined ``failure-injection.json``
    holding both frameworks under their names (pytest executes the parametrized
    scenarios sequentially in one process, so read-modify-write is safe).
    """
    framework = evidence["framework"]
    evidence["completed_at"] = datetime.now(UTC).isoformat(timespec="seconds")
    evidence["artifact_paths"] = {
        "first_failure_trace": (
            f"artifacts/raw/failure-injection-{framework}-trace.jsonl"
        ),
        "post_recovery_trace": (
            f"artifacts/raw/failure-injection-{framework}-post-recovery-trace.jsonl"
        ),
        "result_summary": f"artifacts/results/failure-injection-{framework}.json",
    }
    results_dir = PROJECT_ROOT / "artifacts/results"
    results_dir.mkdir(parents=True, exist_ok=True)
    (results_dir / f"failure-injection-{framework}.json").write_text(
        json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    combined_path = results_dir / "failure-injection.json"
    combined = {}
    if combined_path.exists():
        try:
            loaded = json.loads(combined_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict) and set(loaded) <= {"llamaindex", "haystack"}:
                combined = loaded
        except (UnicodeDecodeError, json.JSONDecodeError):
            pass  # legacy single-framework artifact; replaced below
    combined[framework] = {
        key: value for key, value in evidence.items() if not key.startswith("_")
    }
    combined_path.write_text(
        json.dumps(combined, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    evidence["_summary_path"] = str(combined_path)


# ---- Acceptance assertions --------------------------------------------------


def test_first_failure_partial_promotion_is_rejected(scenario):
    assert scenario["assertions"]["partial_promotion_rejected"] is True
    assert scenario["partial_promotion_error"]


def test_active_pointer_remains_v1_after_failed_validation(scenario):
    assert scenario["assertions"]["pointer_unchanged_after_failure"] is True
    assert scenario["pointer_before_partial_attempt"] == {"release_id": V1_RELEASE_ID}
    assert scenario["pointer_after_failed_promotion"] == {"release_id": V1_RELEASE_ID}


def test_phase_a_every_query_returns_only_v1(scenario):
    assert scenario["assertions"]["phase_a_all_results_v1"] is True
    assert scenario["assertions"]["phase_a_no_v2_chunk_returned"] is True
    assert len(scenario["phase_a_queries"]) == 5


def test_complete_v2_promotes_atomically_and_pointer_moves_to_v2(scenario):
    assert scenario["assertions"]["complete_v2_validated_and_promoted"] is True
    assert scenario["pointer_after_recovery_promotion"] == {"release_id": V2_RELEASE_ID}


def test_phase_b_every_query_returns_only_v2(scenario):
    assert scenario["assertions"]["phase_b_all_results_v2"] is True
    assert scenario["assertions"]["deleted_v1_content_not_returned"] is True
    assert scenario["assertions"]["office_snacks_absent_after_v2"] is True
    assert len(scenario["phase_b_queries"]) == 5


def test_both_retrieval_branches_were_exercised_per_phase(scenario):
    for phase in ("phase_a_queries", "phase_b_queries"):
        kinds = {q["retriever_kind"] for q in scenario[phase]}
        assert kinds == {"bm25", "ollama_dense"}, phase


def test_mixed_release_filter_raises(scenario):
    assert scenario["assertions"]["mixed_release_filter_raises"] is True


def test_evidence_artifacts_written(scenario):
    assert Path(scenario["_summary_path"]).is_file()
    assert (
        PROJECT_ROOT / "artifacts/raw/failure-injection-trace.jsonl"
    ).stat().st_size > 0
    assert (
        PROJECT_ROOT / "artifacts/raw/failure-injection-post-recovery-trace.jsonl"
    ).stat().st_size > 0
