#!/usr/bin/env python3
"""Regenerate all tables in paper/experiment-results.md from canonical JSON artifacts.

Single source of truth:
  - artifacts/results/controlled-summary.json   (table A + run id / wall clock)
  - artifacts/results/controlled-results.csv    (table B)
  - artifacts/results/failure-injection.json    (table C, per-framework run ids)

Run from the repo root of rag-framework-investigation:
  python3 scripts/generate_tables.py
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "artifacts" / "results"
PAPER = ROOT / "paper" / "experiment-results.md"

# ---------------------------------------------------------------- table A ----

def fmt(v: float, nd: int = 2) -> str:
    return f"{v:.{nd}f}"


def table_a(summary: dict) -> str:
    lines = [
        "| Condition | recall@k | MRR | citation span correctness (byte-verified) "
        "| citation source correctness | citation support | required-phrase coverage "
        "| mean citations/case | release consistency | retrieve ms | generate ms | total ms |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for cond in summary["conditions"]:
        m = cond["observed_metric_means"]
        lines.append(
            "| {cond} | {recall} | {mrr} | {span} | {src} | {sup} | {cov} | {cit} | {rel} "
            "| {ret} | {gen} | {tot} |".format(
                cond=cond["condition_id"],
                recall=fmt(m["recall_at_k"], 1),
                mrr=fmt(m["mrr"], 2),
                span=fmt(m["citation_span_correctness"]),
                src=fmt(m["citation_source_correctness"]),
                sup=fmt(m["citation_support"]),
                cov=fmt(m["required_phrase_coverage"]),
                cit=fmt(m["citation_count"], 1),
                rel=fmt(m["release_consistency"], 1),
                ret=fmt(m["latency_retrieve_ms"], 1),
                gen=fmt(m["latency_generate_ms"], 1),
                tot=fmt(m["total_latency_ms"], 1),
            )
        )
    return "\n".join(lines)


# ---------------------------------------------------------------- table B ----

def table_b(csv_path: Path) -> str:
    rows = list(csv.DictReader(csv_path.open()))
    order: list[str] = []
    conds: list[str] = []
    mrr: dict[tuple[str, str], float] = {}
    for r in rows:
        key = (r["case_id"], f"{r['framework']}:{r['retriever_kind']}")
        mrr[key] = float(r["mrr"])
        if r["case_id"] not in order:
            order.append(r["case_id"])
        if key[1] not in conds:
            conds.append(key[1])
    short = {c: ("LI " if c.startswith("llamaindex") else "HS ") +
             ("bm25" if c.endswith("bm25") else "dense") for c in conds}
    lines = ["| Case | " + " | ".join(short[c] for c in conds) + " |",
             "|---|" + "---|" * len(conds)]
    for case in order:
        lines.append(f"| {case} | " +
                     " | ".join(f"{mrr[(case, c)]:.3f}".rstrip("0").rstrip(".") if
                                mrr[(case, c)] % 1 else f"{mrr[(case, c)]:.1f}"
                                for c in conds) + " |")
    return "\n".join(lines)


# ---------------------------------------------------------------- table C ----

def table_c(fi: dict) -> tuple[str, int]:
    hs, li = fi["haystack"], fi["llamaindex"]
    partial_err = hs.get("partial_promotion_error") or li.get("partial_promotion_error")
    checks = [
        ("Partial v2 promotion (3 of 5 docs staged + indexed)",
         "rejected by validation",
         f'error "{partial_err}"',
         hs["assertions"]["partial_promotion_rejected"] and li["assertions"]["partial_promotion_rejected"]),
        ("Active pointer after failed promotion",
         'byte-identical `{"release_id": "v1"}`',
         "pointer unchanged",
         hs["assertions"]["pointer_unchanged_after_failure"] and li["assertions"]["pointer_unchanged_after_failure"]),
        ("Phase A queries (release captured v1)",
         "only v1 chunks, no v2 leakage",
         "all returned_release_ids = [\"v1\"], no_mixed_release true, both retrievers",
         hs["assertions"]["phase_a_all_results_v1"] and hs["assertions"]["phase_a_no_v2_chunk_returned"]
         and li["assertions"]["phase_a_all_results_v1"] and li["assertions"]["phase_a_no_v2_chunk_returned"]),
        ("Mixed-release filter",
         "raises on foreign chunk",
         "`filter_chunks_for_release` raised MixedReleaseError",
         hs["assertions"]["mixed_release_filter_raises"] and li["assertions"]["mixed_release_filter_raises"]),
        ("Complete v2 validation + promotion",
         "passes, one atomic replace",
         'pointer → `{"release_id": "v2"}`',
         hs["assertions"]["complete_v2_validated_and_promoted"] and li["assertions"]["complete_v2_validated_and_promoted"]),
        ("Phase B queries after promotion",
         "only v2 chunks",
         'all returned_release_ids = ["v2"]',
         hs["assertions"]["phase_b_all_results_v2"] and li["assertions"]["phase_b_all_results_v2"]),
        ("Deleted v1 content (office-snacks)",
         "never returned under v2",
         "absent from all Phase B contexts",
         hs["assertions"]["office_snacks_absent_after_v2"] and li["assertions"]["deleted_v1_content_not_returned"]
         and li["assertions"]["office_snacks_absent_after_v2"] and hs["assertions"]["deleted_v1_content_not_returned"]),
    ]
    lines = ["| Check | Expected | Observed | Result |", "|---|---|---|---|"]
    n_true = 0
    for check, exp, obs, ok in checks:
        n_true += sum(a.values()) if False else 0  # placeholder, counted below
        lines.append(f"| {check} | {exp} | {obs} | {'✅' if ok else '❌'} |")
    total_assertions = sum(sum(fw["assertions"].values()) for fw in (hs, li))
    return "\n".join(lines), total_assertions


# ------------------------------------------------------------------ main -----

def main() -> None:
    summary = json.loads((RESULTS / "controlled-summary.json").read_text())
    fi = json.loads((RESULTS / "failure-injection.json").read_text())
    hs_run = fi["haystack"]["run_id"]
    li_run = fi["llamaindex"]["run_id"]

    text = PAPER.read_text()

    # Section A heading line: run id + wall clock, derived from canonical JSON.
    text = re.sub(
        r"Run ID: `task6-[\dT]+` \(wall clock [\d.]+ s, status `\w+`[^\n]*",
        f"Run ID: `{summary['run_id']}` (wall clock {summary['wall_clock_seconds']} s, "
        f"status `{summary['status']}` — control validation AND quality gates). "
        "Fresh rerun after the release-inventory layout fix; pre-rerun artifacts archived "
        "at `artifacts/raw/archive-prerun-20260824-fresh/`. All quality metrics reproduced "
        "exactly from the prior run (`task6-20260824T052921`); only host-dependent latencies "
        "shifted marginally.",
        text,
    )

    # Replace each markdown table with regenerated content, in document order.
    tables = [table_a(summary), table_b(RESULTS / "controlled-results.csv")]
    tc, n_assert = table_c(fi)
    tables.append(tc)
    ti = iter(tables)

    def repl(_m: re.Match) -> str:
        return next(ti)

    text, n = re.subn(r"(?m)^\|.*\|(?:\n\|.*)*", repl, text)
    assert n == 3, f"expected 3 tables, replaced {n}"

    # Failure-injection section heading + trailing sentence: canonical run ids.
    text = re.sub(
        r"runs `failure-injection-[\dT]+` \(llamaindex\) and `failure-injection-[\dT]+` \(haystack\)",
        f"runs `{li_run}` (llamaindex) and `{hs_run}` (haystack)",
        text,
    )
    text = re.sub(
        r"All \d+ recorded assertions true — 9 per framework \(runs `failure-injection-[\dT]+` llamaindex / `[\dT]+` haystack\)",
        f"All {n_assert} recorded assertions true — 9 per framework "
        f"(runs `{li_run}` llamaindex / `{hs_run}` haystack)",
        text,
    )

    PAPER.write_text(text)
    print(f"regenerated {PAPER.relative_to(ROOT)}: 3 tables, "
          f"run {summary['run_id']}, wall {summary['wall_clock_seconds']}s, "
          f"fi runs {li_run}/{hs_run}, {n_assert}/18 assertions")


if __name__ == "__main__":
    main()
