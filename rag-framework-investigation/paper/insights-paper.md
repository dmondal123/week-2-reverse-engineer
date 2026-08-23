# Insights paper: LlamaIndex vs Haystack under a framework-independent release contract

> **DRAFT** — produced by the Task 8 draft writer from verified Task 4/6/7 evidence. Every claim cites an evidence ID or artifact path. Items marked UNKNOWN or LIMITATION require review before this draft is released.

## 1. Executive claim (150–250 words)

**Production decision: combine — run RAG pipelines on a single framework while keeping identity, release validation, and atomic promotion outside both frameworks.** Under fixed configuration, LlamaIndex and Haystack delivered statistically indistinguishable retrieval quality in our controlled experiment (recall@5 = 1.0 and MRR 0.87–0.90 across all four framework × retriever conditions, run `task6-20260823T190633`, `artifacts/results/controlled-summary.json`). Framework choice is therefore not the decisive risk; **the most important finding is that neither framework prevents mixed-version answers on its own** — both lack any native immutable-release concept (provenance matrix rows `corpus_release_version` = lost at index-time for both) — while an external release layer rejected a partial v2 promotion with the active pointer untouched and provably served only one release per query (`artifacts/results/failure-injection.json`, 9/9 assertions true). Confidence is high for the release finding (source + runtime evidence converge), medium for framework preference (single repetition, five synthetic cases). Consequence: invest engineering in the release mechanism and explicit-configuration discipline, not in framework switching; buy further runtime repetitions only after diagnosing the unexplained citation-source-correctness pattern (~0.28 in all conditions).

*(Word count of this claim block: ≈195.)*

## 2. Decision context and scope

The organization must choose how to build retrieval-augmented answering over versioned internal policies where a stale or mixed corpus version producing a wrong answer is a compliance incident, not an inconvenience. Two candidate frameworks were compared: LlamaIndex and Haystack, pinned at llama_index@d8021225eb7e7b276d5ceb476b0a4650240f27f8 and haystack@c7cb46c0f28ad1984f60e5d3e9404b124a221437 respectively (`config/repository-manifest.json`; EV-T2-001, EV-T2-002). All model calls ran locally through Ollama using `nomic-embed-text` (digest `0a109f422b47…`, EV-T5-001) and `qwen3:4b-instruct-2507-q4_K_M` (digest `0edcdef34593…`, EV-T5-002); no hosted APIs were used.

The investigation design follows one rule that shaped everything downstream: **every claim must be bound to either a pinned source line or a saved runtime artifact**. Source tracing preceded any conclusion about framework internals; the three hypotheses were written and timestamped before any implementation file was opened (`evidence/hypotheses.md`), so the paper can distinguish what was predicted from what was found. The evaluation contract (`eval/cases.json`) contains five deliberately discriminating cases: a multi-fact case requiring three sources at once, an exact-identifier case (rule AP-50 / $50 threshold), a semantic paraphrase case, an obsolete-source trap where the superseded memo must not ground the answer, and a version-change case whose correct answer differs between v1 ($25/day) and v2 ($30/day). The trap case is what makes corpus-version mixing observable in answers rather than only in metadata.

Scope was deliberately narrow: six-document v1 corpus derived to five-document v2, five discriminating evaluation cases, one shared pipeline contract implemented by two adapters, one controlled variable (retriever kind: BM25 vs dense), and one injected failure mode (partial reindex promotion). Out of scope: UIs, external vector databases, hosted services, additional frameworks, and statistical generalization beyond the synthetic corpus. This scope decision is itself an interpretation: we treat pipeline equivalence under identical configuration as the fair comparison target, not framework-native showcases, because production reproducibility requires knowing exactly what each stage does. A consequence of this narrowness is honesty about transferability: results describe these pinned commits, this synthetic policy corpus, and this local Ollama host — nothing more.

## 3. Competing hypotheses

Three hypotheses were written before any source tracing (`evidence/hypotheses.md`, timestamped 2026-08-22T10:50:42Z):

- **H1 — LlamaIndex hidden convenience state:** global `Settings` and convenience defaults conceal material retrieval behavior unless every resolved value is captured.
- **H2 — Haystack graph visibility vs transformation risk:** the explicit component graph improves observability while converters/splitters may still invisibly transform identity/metadata.
- **H3 — frameworks do not provide atomic reproducible releases alone:** neither validates complete versioned manifests nor atomically promotes a query-visible pointer without external logic.

Outcome after tracing and runtime: H1's mechanism was confirmed at source level (EV-T4-002, EV-T4-003, EV-T4-004, EV-T4-005) and mitigated in our adapters by explicit configuration plus settings snapshots; H1 remains OPEN because the hypothesis concerns framework behavior, not our mitigation. **H2 was WEAKENED by counterevidence**: the observability half held (explicit graph execution, EV-T4-010), but transformation risk proved stronger than predicted — Haystack children are new Documents whose ids are re-derived from content including the embedding vector, with the parent id dropped (EV-T4-007, EV-T4-008). H3 remains OPEN with strong converging support: source tracing found no native release concept in either write path, and the failure injection demonstrated both failure prevention and recovery through external controls only. Full table: `paper/hypothesis-evidence.md`.

A methodological note on discrimination: each hypothesis was written with a rejection condition before tracing, which forced the investigation to look for disconfirming evidence rather than confirmatory patterns. For H3 this meant actively searching both frameworks' write paths for any native manifest-validation or atomic-pointer mechanism; finding only Haystack's DuplicatePolicy as the closest construct (HS-2/EV-T4-006) is negative evidence recorded in the provenance matrix's `corpus_release_version` rows ("lost" for both frameworks at index-time), not merely an absence of mention.

The required rejected/weakened explanation is the pre-trace reading that "graph visibility makes identity transformations low-risk." The pinned source shows visibility and identity safety are independent properties: the graph exposes component boundaries while id regeneration driven by embedding fingerprints happens inside a visible component yet is invisible unless its fingerprint inputs are inspected (EV-T4-007, EV-T4-008).

## 4. Architecture reconstruction

Both index-time paths were traced from their public entry points to storage; line references are commit-bound at the SHAs above (`evidence/source-references.md`).

**LlamaIndex index-time (fact):** `VectorStoreIndex` is the public entry point; `_build_index_from_nodes` and `insert_nodes` are the write paths (LI-1, EV-T4-001). Embedding falls back to the process-global `Settings.embed_model` when not passed explicitly (LI-2/EV-T4-002), default chunk size is 1024 tokens and default top-k is 2 via module constants (LI-4/EV-T4-003), and `Settings` itself is a lazily-initialized singleton holding llm/embed/parser/callbacks/tokenizer (LI-5/EV-T4-004). Node ids are freshly generated during parsing; provenance survives only if the parser copies it (LI-9). The response synthesizer repeats the same fallback pattern for the LLM (LI-6/EV-T4-005).

**Haystack index-time (fact):** `DocumentWriter.run` is the public write path into an in-memory store where DuplicatePolicy.NONE becomes FAIL on duplicate ids (HS-1, HS-2/EV-T4-006). Splitter defaults are constructor-local — word/200/0 — unlike LlamaIndex's ambient constants (HS-3/EV-T4-009 context). Splitting creates new Documents whose ids are re-hashed from child content; parent ids do not survive as fields (HS-4/EV-T4-007). Document.id is a SHA-256 fingerprint over text/meta/embedding with sorted keys (HS-5/EV-T4-008).

**Query time:** LlamaIndex resolves query embeddings and callback managers from the same ambient state and returns store-ordered scores (LI-7, LI-8); `VectorStoreRetriever._retrieve` computes the aggregate query embedding when absent and delegates to the vector store, with constructor default `similarity_top_k = DEFAULT_SIMILARITY_TOP_K = 2` unless overridden (LI-8/EV-T4-003 context) — meaning a caller that forgets top-k silently retrieves two chunks, a failure mode our five-chunk experiment configuration would have exposed only through the resolved-settings snapshot. Haystack executes an explicitly connected graph (HS-6/EV-T4-010) with BM25 ranking computed inside the document store itself rather than in the retriever component, `scale_score=False` by default so raw BM25 scores flow through unchanged (HS-7, HS-10/EV-T4-009), dense retrieval with configurable runtime filters and REPLACE/MERGE filter policies (HS-8), and citation assembly via `AnswerBuilder` that inherits whatever identity survived splitting (HS-9).

Documented behavior in both frameworks is corroborated by their own test suites at the pinned SHAs — splitter and writer tests on the Haystack side (REF-T1, REF-T2) and vector-store retriever tests on the LlamaIndex side (REF-T3) — which satisfies the triangulation requirement that architectural claims rest on more than one evidence form (EV-T4-011).

**Adapter normalization:** because native ids and provenance diverge as described above, both adapters normalize every candidate to the shared contract fields — source/document/chunk ids derived from source bytes and spans (`src/rag_compare/identity.py`), text, span, score, original rank, metadata, and release ID — and emit one frozen-schema stage event per boundary into an append-only, fsync-per-event JSONL trace (`src/rag_compare/trace.py`). This wrapper-level bookkeeping is precisely why citation spans resolve correctly even though neither framework preserves span offsets natively in both paths (provenance matrix rows `span_offsets`: lost for LlamaIndex, preserved only optionally for Haystack).

**The release boundary (fact, external to both):** neither framework appears anywhere in the release mechanism. Our layer validates file sets, SHA-256 hashes, counts, schema, and embedding identity against a manifest, then promotes with one atomic pointer replacement (`src/rag_compare/release.py`). Query callers capture the active release once and every retrieval branch filters chunks by the captured release, raising on any foreign chunk. Diagram: `paper/architecture.mmd`. Provenance classification for all 12 required fields at both stages: `evidence/provenance-matrix.csv`.

## 5. Experiment design

Run `task6-20260823T190633` executed a 2×2 design — {llamaindex, haystack} × {bm25, ollama_dense} — over all five evaluation cases with everything else frozen: token-window chunking 200/40, top-k 5, temperature 0, seed 0, prompt hash `cba6cea2…`, context budget 1200 tokens, tie-break score-desc-then-chunk-id-asc (`config/experiment.json`; input hashes recorded in the summary's `input_hashes`). The run manifest was hashed before execution and copied to `artifacts/raw/task6-20260823T190633/`. Control validation programmatically compared manifests across conditions: within each framework pair the build-manifest SHA-256 is identical (llamaindex `9432f801…`, haystack `ad3cfa31…`), so the only material difference was retriever kind; `control_validation.failures = []`.

Two defects were discovered and fixed during Task 6 preparation, both recorded in `week2/AI_COLLABORATION.md`: the Haystack splitter drops embedding vectors from split children, so vectors had to be re-asserted before writing to the store; and the forbidden-source metric was redefined to score the packed/grounded context rather than raw retriever output, matching the metadata-filter note in `config/experiment.json`. Both fixes were applied identically in spirit across frameworks to preserve control symmetry, though the embedding re-assertion is inherently adapter-specific — itself a small demonstration of the transformation-risk theme of H2.

Metrics were computed per case and never collapsed into one score: recall@k, MRR, forbidden-source handling over the packed context, citation source/span correctness, per-stage latencies including capture-release, release-filter, rerank, pack, and generate stages, total latency, and release consistency (`artifacts/results/controlled-results.csv`; 20 case rows). Wall clock was 27.885 s for all four conditions.

The failure injection (Task 7, run `failure-injection-20260823T193859`) activated v1, indexed half of v2 into staging, attempted promotion, queried all cases, completed v2, validated, promoted atomically, and re-queried — preserving separate first-failure and post-recovery traces (`artifacts/raw/failure-injection-trace.jsonl`, 40 events; `-post-recovery-`, 35 events).

## 6. Results and evidence

**Retrieval quality (fact):** recall@k = 1.0 in every condition and case; MRR = 0.90 everywhere except BM25 on the obsolete-source trap case (0.333 for llamaindex:bm25, haystack:bm25, and haystack:ollama_dense), where the obsolete memo outranks the current policy. Dense retrieval avoided that trap on the llamaindex branch (MRR 1.0). With n=1 repetition this is an observation, not a conclusion (LIMITATION).

**Latency (fact):** generation dominates — mean generate latency 1218–1575 ms versus retrieval 4.4–27.3 ms per condition; total means ranged 1245 ms (haystack:dense) to 1580 ms (llamaindex:bm25). Differences between frameworks are small relative to generation variance and single-host conditions.

**Citations (fact + unknown):** citation span correctness = 1.0 in all 20 runs — cited spans always resolve to real corpus spans, which validates the external identity contract against native id regeneration. Citation source correctness ≈ 0.28 in all four conditions: answers cite valid sources but frequently include distractor documents beyond each case's `relevant_source_ids`. **UNKNOWN:** root cause undiagnosed; present identically across frameworks, so it is not attributable to either framework. Flagged for review.

**Failure injection (fact):** partial v2 promotion was rejected ("corpus file set does not match the release directory"); the active pointer remained byte-identical (`{"release_id": "v1"}`); all Phase A queries returned only v1 chunks on both retrieval branches with no v2 leakage; the mixed-release filter raised on a foreign chunk; complete v2 promoted atomically to `{"release_id": "v2"}`; Phase B queries returned only v2 chunks and deleted v1 content (office-snacks) never resurfaced. All nine assertions true (`artifacts/results/failure-injection.json`). No unexpected mixed-version failure occurred, so no corrective release-control change was needed.

Full tables: `paper/experiment-results.md`; risk/control mapping: `paper/risk-control.md`.

## 7. Production analysis

*Interpretation:* three findings matter for production more than the framework comparison itself.

First, **identity is not preserved natively end-to-end in either framework.** The provenance matrix shows content_sha256 synthesized at index-time in both, chunk/document ids transformed or synthesized in both, and span offsets lost entirely in LlamaIndex. Any audit requirement ("show me the exact policy text behind this answer") therefore depends on wrapper-level bookkeeping. Our contract assigned stable ids from source bytes and spans, achieving citation-span correctness 1.0 — but that correctness belongs to the wrapper, not the framework (fact: matrix rows; interpretation: attribution).

Second, **ambient configuration is a reproducibility hazard specific in degree, not in kind.** LlamaIndex concentrates it in one singleton (EV-T4-004); Haystack distributes it across constructor defaults (EV-T4-009). Both are manageable with explicit configuration plus snapshots, which is exactly what made the controlled experiment's control validation pass. A team unwilling to enforce that discipline should treat LlamaIndex convenience APIs as a standing risk (H1).

Third, **release safety came exclusively from the external mechanism**, confirming H3's prediction against both write paths. The practical consequence is organizational: corpus rollout procedures should be owned by the platform layer and tested by failure injection, independent of whichever framework renders the answers.

Fourth, a note on what the latency data does and does not license. Per-condition means differ by up to ~287 ms total (1245–1580 ms), but the spread sits almost entirely inside the generation stage, whose variance across individual cases in the same condition exceeds several hundred milliseconds (per-case rows in `artifacts/results/controlled-results.csv`). With one repetition, no ranking of frameworks or retrievers by speed is defensible; the only robust latency statement is structural: retrieval and all wrapper stages (release capture, filtering, packing) are together two to three orders of magnitude cheaper than generation, so end-to-end optimization effort belongs in the generation budget, not the retrieval path. This is an interpretation grounded in the recorded stage decomposition, not a benchmark result.

Fifth, the version-change case demonstrates end-to-end correctness of the whole stack in the positive direction: after v2 promotion, the model answered "$30 per travel day" citing `travel-wifi-current`, whereas Phase A against captured v1 answered "$25" — the same query returning version-correct answers purely because the release pointer moved atomically between runs (`artifacts/results/failure-injection.json`, phases A/B excerpts). That is the observable payoff of the release mechanism.

## 8. Decision and ADR

Decision: **combine** — detailed alternatives, consequences, reversibility, and next-evidence analysis are recorded in `paper/decision.adr.md`. Summary: adopt one framework for pipeline ergonomics (Haystack preferred marginally for inspectable defaults and explicit graph observability, per EV-T4-009/EV-T4-010; the measured quality difference is nil), and adopt the framework-independent release recommendation separately: immutable namespaces, manifest validation, single-capture release filtering, atomic promotion. Reversibility is high because both adapters implement one shared contract and the release layer is already framework-free. Next evidence worth buying: diagnose the citation-source-correctness pattern, add repetitions/cases before latency claims, and test promotion under concurrent queries.

## 9. Limitations and unknowns

- **LIMITATION:** five evaluation cases, one repetition per condition, synthetic six-document corpus, single local host. No statistical significance is claimed for any cross-framework difference.
- **UNKNOWN:** root cause of citation_source_correctness ≈ 0.28 uniformly across conditions; undiagnosed in Task 6 and deliberately not interpreted here.
- **LIMITATION:** the forbidden-source metric semantics were revised during Task 6 to score the packed context (`config/experiment.json` metadata_filter note); the ledger records the change, but reviewers should confirm the final definition matches intent.
- **LIMITATION:** repository SHA/remote metadata in `config/repository-manifest.json` is labeled user-supplied and locally unverified in the working checkout (recorded correction in `week2/AI_COLLABORATION.md`).
- **UNKNOWN:** behavior under concurrent query/promotion interleaving; atomicity was exercised sequentially.
- **LIMITATION:** Task 7 reruns occurred without explicit human approval (protocol deviation, logged in `week2/AI_COLLABORATION.md`); retained artifacts come from the single complete execution.
- Latencies reflect one Ollama host and the pinned qwen3:4b quantization; they are not transferable figures.

## 10. AI-use disclosure

Material assistance: plan/architecture drafting used `gpt-5.6-sol` (medium effort) under prior governance entries; Tasks 3–7 implementation assistance used `gpt-5.6-terra`/`gpt-5.6-luna` (medium) and later sessions used `ox-alpha` (undisclosed organization) with counters recorded in `week2/AI_COLLABORATION.md`. This draft was written by an AI coding assistant (`ox-alpha`) from local Task 4/6/7 files only; no network access was used and no experiments were rerun.

Accepted suggestions (AI-origin, human-approved): comparing equivalent minimal pipelines rather than framework showcases; moving mixed-version prevention outside both frameworks; pinning the dedicated non-thinking Instruct generator instead of hybrid `qwen3:4b` + `/no_think` (human-initiated correction). Rejected/corrected: the initial incorrect model tags (`nomic-embed-text-hf:latest`, `qwen3-4b-instruct-2507-hf:latest`) were voided by runtime verification (EV-T5-001/002 superseding EV-T2-003/004); the thin-slice plan lacking reverse-engineering depth was rejected in plan review.

Verification method: every architectural claim traces to a commit-bound reference in `evidence/source-references.md` or a row in `evidence/ledger.csv`; every experimental claim traces to `artifacts/results/*`; tables in the companion files were generated from those artifacts rather than reconstructed from memory. Residual uncertainty: the unknowns listed in Section 9, plus the possibility that adapter snapshots miss an unaudited ambient read despite the Task 4 hidden-state audit. **No AI output is presented as source or runtime evidence; AI-produced text is limited to synthesis of the recorded human-verifiable artifacts above.**

---

### Appendix A: Evidence minimums checklist (self-check, draft)

| Requirement | Met | Where |
|---|---|---|
| ≥12 commit-bound references | ✅ 22 (9 LI + 10 HS impl/test/config/history refs) | `evidence/source-references.md`, EV-T4-001..012 |
| ≥2 controlled-experiment runtime artifacts | ✅ summary JSON + results CSV (+ raw per-case dirs) | `artifacts/results/controlled-summary.json`, `artifacts/results/controlled-results.csv`, `artifacts/raw/task6-20260823T190633/` |
| One failure-injection result | ✅ 9 assertions, distinct first-failure trace | `artifacts/results/failure-injection.json`, `artifacts/raw/failure-injection-trace.jsonl` |
| ≥2 history/issue/ADR references | ✅ REF-T5 (release-note yaml), REF-T6 (CHANGELOG breaking changes) | `evidence/source-references.md` § D |
| Counterexample / counterevidence | ✅ H2 weakening (EV-T4-007, EV-T4-008) | `paper/hypothesis-evidence.md` |
| Rejected explanation | ✅ "graph visibility ⇒ identity safety" weakened | § 3 above |
