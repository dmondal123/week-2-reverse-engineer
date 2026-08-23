# Experiment results table

Generated mechanically from `artifacts/results/controlled-summary.json`, `artifacts/results/controlled-results.csv`, and `artifacts/results/failure-injection.json`. Run ID: `task6-20260823T190633` (wall clock 27.885 s, status `passed`).

## A. Controlled 2×2 experiment — per-condition means (5 cases each)

| Condition | recall@k | MRR | citation span correctness | citation source correctness | release consistency | forbidden-source compliance¹ | retrieve ms | generate ms | total ms |
|---|---|---|---|---|---|---|---|---|---|
| llamaindex:bm25 | 1.0 | 0.90 | 1.00 | 0.28 | 1.0 | 1.00 | 4.42 | 1575.07 | 1579.53 |
| llamaindex:ollama_dense | 1.0 | 0.90 | 1.00 | 0.28 | 1.0 | 1.00 | 21.91 | 1271.41 | 1293.36 |
| haystack:bm25 | 1.0 | 0.87 | 1.00 | 0.28 | 1.0 | 1.00 | 10.70 | 1282.88 | 1293.61 |
| haystack:ollama_dense | 1.0 | 0.90 | 1.00 | 1.00 | 1.0 | 1.00 | 27.26 | 1217.83 | 1245.13 |

¹ `forbidden_source_violation` in the artifacts is scored over the packed/grounded context per the note in `config/experiment.json` (`metadata_filter.note`); 1.0 means no forbidden source entered any packed context. Interpretation of what this metric should mean is flagged as a review item, not a fact.

Build-manifest SHA-256 per framework pair: llamaindex both conditions `9432f801…b63b9d6d8`; haystack both conditions `ad3cfa31…97fe797bb` — identical within each framework, so only `retriever_kind` and retriever-specific index data differ (`control_validation.failures = []`).

## B. Per-case MRR by condition (from controlled-results.csv)

| Case | LI bm25 | LI dense | HS bm25 | HS dense |
|---|---|---|---|---|
| multi_fact_wifi | 1.0 | 1.0 | 1.0 | 1.0 |
| exact_identifier_ap50 | 1.0 | 1.0 | 1.0 | 1.0 |
| semantic_travel_connectivity | 1.0 | 1.0 | 1.0 | 1.0 |
| obsolete_source_trap | 0.333 | 1.0 | 0.333 | 0.333 |
| version_change_wifi_limit | 1.0 | 1.0 | 1.0 | 1.0 |

Fact: BM25 ranks the obsolete memo first on `obsolete_source_trap` for three of four conditions (MRR 0.333); LlamaIndex dense avoids that on one branch. With n=1 per cell this is an observation, not a statistically supported conclusion.

## C. Failure injection — run `failure-injection-20260823T193859`

| Check | Expected | Observed | Result |
|---|---|---|---|
| Partial v2 promotion (3 of 5 docs staged) | rejected by validation | error "corpus file set does not match the release directory" | ✅ |
| Active pointer after failed promotion | byte-identical `{"release_id": "v1"}` | pointer unchanged | ✅ |
| Phase A queries (release captured v1) | only v1 chunks, no v2 leakage | all returned_release_ids = ["v1"], no_mixed_release true, both retrievers | ✅ |
| Mixed-release filter | raises on foreign chunk | `filter_chunks_for_release` raised MixedReleaseError | ✅ |
| Complete v2 validation + promotion | passes, one atomic replace | pointer → `{"release_id": "v2"}` | ✅ |
| Phase B queries after promotion | only v2 chunks | all returned_release_ids = ["v2"] | ✅ |
| Deleted v1 content (office-snacks) | never returned under v2 | absent from all Phase B contexts | ✅ |

All 9 recorded assertions true; traces preserved at `artifacts/raw/failure-injection-trace.jsonl` (40 events) and `artifacts/raw/failure-injection-post-recovery-trace.jsonl` (35 events).

## D. Known result caveats

- **Unknown / limitation:** citation_source_correctness ≈ 0.28 across all four conditions while span correctness is 1.0 — answers cite valid spans but frequently attach source ids beyond the eval case's `relevant_source_ids` (e.g., distractors like `device-security`). Root cause was not diagnosed in Task 6 and must not be interpreted as a framework difference.
- **Limitation:** five cases, single repetition per condition, synthetic corpus, one local Ollama host; latencies are host-dependent.
