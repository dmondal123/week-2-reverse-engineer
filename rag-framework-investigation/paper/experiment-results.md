# Experiment results table

Generated mechanically from `artifacts/results/controlled-summary.json`, `artifacts/results/controlled-results.csv`, and `artifacts/results/failure-injection.json`.

> **Remediation note (2026-08-24):** an external review found that citations were previously synthesized from all packed chunks rather than derived from the answer, and that declared corpus-manifest chunk IDs did not match runtime IDs. The pipeline was corrected (model-derived `[n]` citations, regenerated manifest IDs, index chunk-inventory validation, honest trace timers, single LlamaIndex embedding pass, frozen quality gates) and both runs were re-executed with Human approval. The superseded pre-remediation artifacts are preserved at `artifacts/raw/archive-pre-remediation-20260824/`. The previous unexplained citation_source_correctness ≈ 0.28 was an artifact of the synthetic citation list, not a model behavior.

## A. Controlled 2×2 experiment — per-condition means (5 cases each)

Run ID: `task6-20260824T064738` (wall clock 26.787 s, status `passed` — control validation AND quality gates). Fresh rerun after the release-inventory layout fix; pre-rerun artifacts archived at `artifacts/raw/archive-prerun-20260824-fresh/`. All quality metrics reproduced exactly from the prior run (`task6-20260824T052921`); only host-dependent latencies shifted marginally.

| Condition | recall@k | MRR | citation span correctness (byte-verified) | citation source correctness | citation support | required-phrase coverage | mean citations/case | release consistency | retrieve ms | generate ms | total ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| llamaindex:bm25 | 1.0 | 0.90 | 1.00 | 1.00 | 0.73 | 0.80 | 1.0 | 1.0 | 3.3 | 1236.9 | 1240.3 |
| llamaindex:ollama_dense | 1.0 | 0.90 | 1.00 | 1.00 | 0.73 | 0.80 | 1.2 | 1.0 | 22.9 | 1468.5 | 1491.5 |
| haystack:bm25 | 1.0 | 0.87 | 1.00 | 1.00 | 0.73 | 0.73 | 1.0 | 1.0 | 11.4 | 1175.8 | 1187.3 |
| haystack:ollama_dense | 1.0 | 0.90 | 1.00 | 1.00 | 0.73 | 0.80 | 1.2 | 1.0 | 27.2 | 1304.0 | 1331.3 |

Full release manifests and chunk inventories are persisted at `artifacts/raw/task6-20260824T064738/<framework>/release-{v1,v2}/index/`.

Build-manifest SHA-256 is identical within each framework pair, so only `retriever_kind` and retriever-specific index data differ (`control_validation.failures = []`). Quality gates (frozen in `config/experiment.json` before the rerun): recall@k ≥ 0.5 per case, zero forbidden-source violations, release consistency 1.0 everywhere — all met.

## B. Per-case MRR by condition (from controlled-results.csv)

| Case | LI bm25 | LI dense | HS bm25 | HS dense |
|---|---|---|---|---|
| multi_fact_wifi | 1.0 | 1.0 | 1.0 | 1.0 |
| exact_identifier_ap50 | 1.0 | 1.0 | 1.0 | 1.0 |
| semantic_travel_connectivity | 1.0 | 1.0 | 1.0 | 1.0 |
| obsolete_source_trap | 0.5 | 0.5 | 0.333 | 0.5 |
| version_change_wifi_limit | 1.0 | 1.0 | 1.0 | 1.0 |

Fact: the obsolete memo still outranks the current policy on the trap case for most conditions (MRR 0.333–0.5), yet every answer cites only correct sources (citation source correctness = 1.0 in all 20 case runs) and no forbidden source is ever cited — the prompt's citation discipline holds even when lexical ranking misleads.

## C. Failure injection — both frameworks, runs `failure-injection-20260824T065054` (llamaindex) and `failure-injection-20260824T065107` (haystack)

The identical partial-v2 promotion scenario was executed through each framework's adapter; every check below holds for BOTH frameworks (18/18 recorded assertions true; per-framework summaries at `artifacts/results/failure-injection-{llamaindex,haystack}.json`).

| Check | Expected | Observed | Result |
|---|---|---|---|
| Partial v2 promotion (3 of 5 docs staged + indexed) | rejected by validation | error "corpus file set does not match the release directory" | ✅ |
| Active pointer after failed promotion | byte-identical `{"release_id": "v1"}` | pointer unchanged | ✅ |
| Phase A queries (release captured v1) | only v1 chunks, no v2 leakage | all returned_release_ids = ["v1"], no_mixed_release true, both retrievers | ✅ |
| Mixed-release filter | raises on foreign chunk | `filter_chunks_for_release` raised MixedReleaseError | ✅ |
| Complete v2 validation + promotion | passes, one atomic replace | pointer → `{"release_id": "v2"}` | ✅ |
| Phase B queries after promotion | only v2 chunks | all returned_release_ids = ["v2"] | ✅ |
| Deleted v1 content (office-snacks) | never returned under v2 | absent from all Phase B contexts | ✅ |

All 18 recorded assertions true — 9 per framework (runs `failure-injection-20260824T065054` llamaindex / `20260824T065107` haystack); traces preserved at `artifacts/raw/failure-injection-{llamaindex,haystack}-trace.jsonl` and `artifacts/raw/failure-injection-{llamaindex,haystack}-post-recovery-trace.jsonl`.

**New since remediation:** promotion now additionally validates a stored index artifact (`index/chunk-inventory.json`, hash-bound in the build manifest). Unit-level negative tests prove a release whose corpus files are complete but which stores **no inventory**, an **empty inventory**, or a **stale-ID inventory** cannot be validated (`tests/test_release.py`) — closing the original gap where validation proved corpus completeness but not index completeness. The partial-promotion rejection itself is still triggered first by the file-set check because the injected scenario stages exactly what it indexed; the decoupled failure modes are covered by the new unit tests.

## D. Known result caveats

- **Limitation:** five cases, single repetition per condition, synthetic corpus, one local Ollama host; latencies are host-dependent.
- **Observation:** required-phrase coverage 0.73–0.80 shows the generator sometimes omits an expected fact even when citing correctly — reported per case, not gated, pending diagnosis.
- **Observation (new metric):** citation support 0.73 in every condition — the cited spans' source text does not always carry every required phrase, consistent with the coverage gap above; graded per case, not gated.
