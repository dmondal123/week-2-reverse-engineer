"""Task 6 controlled-experiment runner: reproducible 2x2 retrieval study.

Conditions (all non-retriever variables held fixed):

    llamaindex x {bm25, ollama_dense}
    haystack   x {bm25, ollama_dense}

Before execution a unique ``run_id`` is assigned and a frozen run manifest
(SHA-256 of repository/environment manifests, experiment configuration,
corpus manifests, evaluation cases, and prompt) is copied under
``artifacts/raw/<run_id>/``. Every condition/case produces sanitized raw
artifacts (trace, candidates, packed context, model output, citations,
per-case metrics). A programmatic control validation compares manifests and
fails the summary closed if any unapproved material difference exists.

Observed values only: nothing here predicts or fabricates results.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

from rag_compare.adapters.haystack_adapter import HaystackAdapter
from rag_compare.adapters.llamaindex_adapter import LlamaIndexAdapter
from rag_compare.contracts import StageEvent
from rag_compare.metrics import evaluate_case
from rag_compare.release import (
    INDEX_INVENTORY_RELPATH,
    build_chunk_inventory,
    canonical_inventory_bytes,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]

LLAMA_COMMIT = "d8021225eb7e7b276d5ceb476b0a4650240f27f8"
HAYSTACK_COMMIT = "c7cb46c0f28ad1984f60e5d3e9404b124a221437"

RETRIEVER_KINDS = ("bm25", "ollama_dense")

# Manifest fields that are permitted to differ BETWEEN frameworks (not within
# a framework pair). Everything else compared must match exactly.
# Build manifests are kind-independent by construction: each framework builds
# ONE index per corpus version and retrieval-kind differences (bm25 vs dense)
# are query-time only, so pairwise comparisons must match exactly for every
# non-framework field. Any difference beyond framework identity fails.
FRAMEWORK_SCOPED_FIELDS = ("framework",)


class JsonlTraceWriter:
    """Append-only trace sink persisting every StageEvent as JSONL."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.events: list[dict] = []
        path.parent.mkdir(parents=True, exist_ok=True)
        self._handle = path.open("a", encoding="utf-8")

    def append(self, event: StageEvent) -> None:
        record = event.to_dict()
        self.events.append(record)
        self._handle.write(json.dumps(record, sort_keys=True) + "\n")
        self._handle.flush()

    def close(self) -> None:
        self._handle.close()


class TeeStream:
    """Duplicate stdout/stderr into both the real stream and a raw file."""

    def __init__(self, original, path: Path) -> None:
        self.original = original
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        self.handle = path.open("a", encoding="utf-8")

    def write(self, text: str) -> int:
        self.original.write(text)
        self.handle.write(text)
        self.handle.flush()
        return len(text)

    def flush(self) -> None:
        self.original.flush()
        self.handle.flush()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha256(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_frozen_manifest(run_id: str, config: dict) -> dict:
    """Hash every controlled input before execution."""
    hashed = {}
    for name in (
        "config/repository-manifest.json",
        "config/environment-manifest.json",
        "config/experiment.json",
        "corpus/v1/manifest.json",
        "corpus/v2/manifest.json",
        "eval/cases.json",
    ):
        hashed[name] = sha256_file(PROJECT_ROOT / name)
    hashed["generation.prompt_template"] = canonical_sha256(
        config["generation"]["prompt_template"]
    )
    return {
        "run_id": run_id,
        "created_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "input_hashes": hashed,
        "experiment_configuration_sha256": canonical_sha256(config),
        "conditions": [
            f"{framework}:{kind}"
            for framework in ("llamaindex", "haystack")
            for kind in RETRIEVER_KINDS
        ],
    }


def make_adapters(config: dict, run_id: str):
    return [
        LlamaIndexAdapter(config, LLAMA_COMMIT, "llama-index-core", run_id=run_id),
        HaystackAdapter(config, HAYSTACK_COMMIT, "haystack-ai", run_id=run_id),
    ]


def build_manifest_view(build_result) -> dict:
    """Comparable view of an observed build manifest."""
    manifest = build_result.manifest
    return {
        key: value
        for key, value in manifest.items()
        if not key.startswith("built_at")  # timestamps never match by design
    }


def validate_controls(
    builds: dict, frozen_manifest: dict, case_count: int, top_k: int
) -> dict:
    """Programmatic control validation; returns a fail-closed report.

    ``builds`` maps condition_id -> observed build manifest view. Because each
    framework builds one kind-independent index per corpus version, the same
    manifest view is recorded for both retriever kinds of a build; allowed
    material differences are therefore ONLY framework-scoped fields across
    frameworks. Any other difference in corpus, parser/chunker configuration,
    embedding, reranker posture, generator, prompt, cases, or active release
    fails validation.
    """
    failures: list[str] = []

    # 1. Frozen-input integrity: re-hash everything and compare.
    config = json.loads(
        (PROJECT_ROOT / "config" / "experiment.json").read_text(encoding="utf-8")
    )
    recomputed = build_frozen_manifest(frozen_manifest["run_id"], config)
    for name, digest in recomputed["input_hashes"].items():
        if frozen_manifest["input_hashes"].get(name) != digest:
            failures.append(f"frozen input changed during run: {name}")

    # 2. Pairwise build-manifest equality within each control group.
    condition_ids = sorted(builds)
    for i, left in enumerate(condition_ids):
        for right in condition_ids[i + 1 :]:
            left_framework, left_kind = left.split(":")
            right_framework, right_kind = right.split(":")
            for field in builds[left]:
                left_value = builds[left][field]
                right_value = builds[right][field]
                if left_value == right_value:
                    continue
                if (
                    field in FRAMEWORK_SCOPED_FIELDS
                    and left_framework != right_framework
                ):
                    continue  # framework identity legitimately differs
                failures.append(
                    f"unapproved material difference between {left} and {right}: "
                    f"manifest field '{field}'"
                )

    # 3. Reranker/generator/prompt posture straight from the pinned config.
    if config["reranking"]["enabled"]:
        failures.append("reranking must be disabled for the controlled run")
    expected_conditions = [
        f"{framework}:{kind}"
        for framework in ("llamaindex", "haystack")
        for kind in RETRIEVER_KINDS
    ]
    if sorted(expected_conditions) != sorted(builds):
        failures.append("condition set does not match the defined 2x2 grid")
    if case_count <= 0 or top_k <= 0:
        failures.append("empty evaluation set or invalid top_k")

    return {
        "passed": not failures,
        "failures": failures,
        "compared_conditions": condition_ids,
    }


def evaluate_quality_gates(csv_rows: list[dict], config: dict) -> dict:
    """Fail-closed quality gates; control validation alone is not enough.

    A run whose controls matched can still be a bad run (empty citations,
    forbidden sources cited, inconsistent releases). Gates come from the
    frozen ``config['quality_gates']`` block so they are pinned before
    execution, never tuned to the results afterwards.
    """
    gates = config.get("quality_gates")
    if not gates:
        return {"passed": True, "failures": [], "note": "no quality gates configured"}
    failures: list[str] = []

    min_recall = float(gates.get("min_recall_at_k_per_case", 0.0))
    for row in csv_rows:
        if float(row["recall_at_k"]) < min_recall:
            failures.append(
                f"{row['condition_id']}/{row['case_id']}: recall_at_k "
                f"{row['recall_at_k']} < gate {min_recall}"
            )

    if "max_forbidden_source_violation_cases" in gates:
        allowed = int(gates["max_forbidden_source_violation_cases"])
        violating = [r for r in csv_rows if float(r["forbidden_source_violation"]) > 0]
        if len(violating) > allowed:
            failures.append(
                f"forbidden-source violation in {len(violating)} case runs "
                f"> gate {allowed}"
            )

    if gates.get("require_release_consistency_all_cases"):
        bad = [r for r in csv_rows if float(r["release_consistency"]) != 1.0]
        if bad:
            failures.append(
                f"release_consistency != 1.0 in {len(bad)} case runs"
            )

    return {"passed": not failures, "failures": failures}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="freeze manifest only")
    args = parser.parse_args(argv)

    config = json.loads(
        (PROJECT_ROOT / "config" / "experiment.json").read_text(encoding="utf-8")
    )
    cases = json.loads((PROJECT_ROOT / "eval" / "cases.json").read_text())
    corpus_manifests = {
        version: json.loads(
            (PROJECT_ROOT / "corpus" / version / "manifest.json").read_text()
        )
        for version in ("v1", "v2")
    }

    run_id = f"task6-{datetime.now(UTC).strftime('%Y%m%dT%H%M%S')}"
    raw_root = PROJECT_ROOT / "artifacts" / "raw" / run_id
    results_root = PROJECT_ROOT / "artifacts" / "results"
    results_root.mkdir(parents=True, exist_ok=True)
    raw_root.mkdir(parents=True, exist_ok=True)

    frozen_manifest = build_frozen_manifest(run_id, config)
    (raw_root / "run-manifest.json").write_text(
        json.dumps(frozen_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"[task6] run_id={run_id}")
    print(f"[task6] frozen manifest written to {raw_root / 'run-manifest.json'}")

    if args.dry_run:
        return 0

    stdout_tee = TeeStream(sys.stdout, raw_root / "stdout.log")
    stderr_tee = TeeStream(sys.stderr, raw_root / "stderr.log")
    sys.stdout, sys.stderr = stdout_tee, stderr_tee

    csv_rows: list[dict] = []
    builds: dict[str, dict] = {}
    condition_artifacts: dict[str, list[str]] = {}

    try:
        started_wall = time.perf_counter()
        adapters = {a.framework: a for a in make_adapters(config, run_id)}
        for framework, adapter in adapters.items():
            for version, manifest in corpus_manifests.items():
                trace = JsonlTraceWriter(
                    raw_root / f"{framework}" / f"build-{version}-trace.jsonl"
                )
                result = adapter.build_release(
                    PROJECT_ROOT / "corpus" / version, manifest, trace
                )
                trace.close()
                # Persist the full release manifest and its index inventory:
                # the deliverable is "a full trace and release manifest", so
                # the manifests cannot live only in memory with only hashes
                # reaching the summary. The inventory MUST be written with the
                # same canonical bytes the manifest hash covers — validation
                # hashes the raw file bytes (release.py), so pretty-printing
                # here would make every persisted release fail its own
                # chunk_inventory_sha256 contract.
                build_dir = raw_root / framework / f"release-{version}"
                build_dir.mkdir(parents=True, exist_ok=True)
                (build_dir / "release-manifest.json").write_text(
                    json.dumps(result.manifest, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                )
                # Persist the inventory derived from the READ-BACK stored
                # chunks (identical to result.stored_chunks used for the
                # manifest hash), so the persisted artifact proves what the
                # framework index actually holds.
                inventory_entries = build_chunk_inventory(result.stored_chunks)
                (build_dir / INDEX_INVENTORY_RELPATH).parent.mkdir(
                    parents=True, exist_ok=True
                )
                (build_dir / INDEX_INVENTORY_RELPATH).write_bytes(
                    canonical_inventory_bytes(inventory_entries)
                )
                for kind in RETRIEVER_KINDS:
                    builds[f"{framework}:{kind}"] = build_manifest_view(result)

        top_k = int(config["retrieval"]["top_k"])
        for framework, adapter in adapters.items():
            for kind in RETRIEVER_KINDS:
                condition_id = f"{framework}:{kind}"
                condition_dir = raw_root / framework / kind
                condition_artifacts[condition_id] = []
                for case in cases:
                    case_id = case["case_id"]
                    active_release = case["corpus_version"]
                    case_dir = condition_dir / f"case-{case_id}"
                    case_dir.mkdir(parents=True, exist_ok=True)

                    trace = JsonlTraceWriter(case_dir / "trace.jsonl")
                    result = adapter.query(case["query"], kind, active_release, trace)
                    trace.close()

                    (case_dir / "candidates.json").write_text(
                        json.dumps(result["candidates"], indent=2) + "\n"
                    )
                    (case_dir / "packed-context.json").write_text(
                        json.dumps(result["context"], indent=2) + "\n"
                    )
                    (case_dir / "output.txt").write_text(result["answer"] + "\n")
                    (case_dir / "citations.json").write_text(
                        json.dumps(result["citations"], indent=2) + "\n"
                    )

                    # Immutable source bytes for byte-level citation-span
                    # verification and claim-support grading: texts are read
                    # fresh from the corpus files, never from packed context.
                    source_texts = {
                        entry["source_id"]: (
                            (PROJECT_ROOT / "corpus" / entry["path"])
                            .read_text(encoding="utf-8")
                        )
                        for entry in corpus_manifests[active_release]["documents"]
                    }
                    metrics = evaluate_case(
                        case, result, trace.events, top_k, source_texts
                    )
                    (case_dir / "metrics.json").write_text(
                        json.dumps(metrics, indent=2, sort_keys=True) + "\n"
                    )

                    artifact_paths = [
                        str(path.relative_to(PROJECT_ROOT))
                        for path in sorted(case_dir.iterdir())
                    ]
                    condition_artifacts[condition_id].extend(artifact_paths)
                    row = {
                        "run_id": run_id,
                        "condition_id": condition_id,
                        "framework": framework,
                        "retriever_kind": kind,
                        "case_id": case_id,
                        "active_release": active_release,
                        **metrics,
                        "build_manifest_sha256": canonical_sha256(builds[condition_id]),
                        "artifact_dir": str(case_dir.relative_to(PROJECT_ROOT)),
                    }
                    csv_rows.append(row)
                    print(
                        f"[task6] {condition_id} {case_id}: "
                        f"recall@{top_k}={metrics['recall_at_k']:.3f} "
                        f"mrr={metrics['mrr']:.3f} "
                        f"forbidden={metrics['forbidden_source_violation']:.0f} "
                        f"total_ms={metrics['total_latency_ms']:.1f}"
                    )
        wall_seconds = time.perf_counter() - started_wall
    finally:
        sys.stdout, sys.stderr = stdout_tee.original, stderr_tee.original
        stdout_tee.handle.close()
        stderr_tee.handle.close()

    control = validate_controls(builds, frozen_manifest, len(cases), top_k)
    gates = evaluate_quality_gates(csv_rows, config)

    metric_keys = [k for k in csv_rows[0] if k.startswith(("recall", "mrr"))]
    metric_keys += [
        k
        for k in csv_rows[0]
        if k.startswith(
            ("forbidden", "citation_", "required_phrase_", "release_", "total_latency")
        )
        or k.startswith("latency_")
    ]
    summaries = []
    for condition_id in sorted({row["condition_id"] for row in csv_rows}):
        rows = [r for r in csv_rows if r["condition_id"] == condition_id]
        means = {
            key: round(sum(r[key] for r in rows) / len(rows), 6)
            for key in metric_keys
            if isinstance(rows[0][key], (int, float))
        }
        summaries.append(
            {
                "condition_id": condition_id,
                "case_count": len(rows),
                "observed_metric_means": means,
                "build_manifest_sha256": rows[0]["build_manifest_sha256"],
                "artifact_dir": str(
                    (raw_root / condition_id.replace(":", "/")).relative_to(
                        PROJECT_ROOT
                    )
                ),
            }
        )

    if control["passed"] and gates["passed"]:
        status = "passed"
    elif not control["passed"]:
        status = "control_failed"
    else:
        status = "quality_gates_failed"
    summary = {
        "run_id": run_id,
        "status": status,
        "observation_kind": "observed",
        "created_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "wall_clock_seconds": round(wall_seconds, 3),
        "run_manifest": str((raw_root / "run-manifest.json").relative_to(PROJECT_ROOT)),
        "input_hashes": frozen_manifest["input_hashes"],
        "conditions": summaries,
        "control_validation": control,
        "quality_gates": gates,
        "cases": [c["case_id"] for c in cases],
        "results_csv": "artifacts/results/controlled-results.csv",
        "results_json": "artifacts/results/controlled-summary.json",
        "raw_artifacts_root": str(raw_root.relative_to(PROJECT_ROOT)),
    }

    fieldnames = list(csv_rows[0].keys())
    with (results_root / "controlled-results.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(csv_rows)

    (results_root / "controlled-summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"[task6] control_validation passed={control['passed']}")
    print(f"[task6] quality_gates passed={gates['passed']}")
    for failure in control["failures"] + gates["failures"]:
        print(f"[task6] FAILURE: {failure}", file=sys.stderr)
    print(f"[task6] wrote controlled-results.csv ({len(csv_rows)} rows)")
    print(f"[task6] wrote controlled-summary.json status={summary['status']}")
    return 0 if control["passed"] and gates["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
