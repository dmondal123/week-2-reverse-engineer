# Architecture Decision Record: Framework choice and framework-independent release mechanism

- **Status:** Proposed (draft — requires Human approval)
- **Decision:** **combine** — combine one framework for pipeline ergonomics with a framework-independent release/identity layer; do not rely on either framework alone for reproducibility.
- **Date:** 2026-08-24 (draft)

## Context

We needed a production answer to two questions: (1) which RAG framework should own our index/query pipelines, and (2) how mixed-version corpus answers can be prevented during reindexing. Evidence: pinned source tracing at llama_index@d8021225 and haystack@c7cb46c0 (EV-T4-001..012, `evidence/source-references.md`), the controlled 2×2 experiment (`artifacts/results/controlled-summary.json`), and failure injection (`artifacts/results/failure-injection.json`).

## Decision drivers

1. LlamaIndex resolves embed model, LLM, chunk size, top-k, and callbacks from a lazily-initialized global singleton unless overridden everywhere (EV-T4-002, EV-T4-003, EV-T4-004, EV-T4-005, EV-T4-007/LI-7). This is a documented usability trade-off with recorded migration hazards in its changelog (REF-T6).
2. Haystack's explicit pipeline graph makes component boundaries observable (EV-T4-010), and its defaults are constructor-local and inspectable (EV-T4-009), but its splitter regenerates child document identities from content+embedding fingerprints and drops parent ids (EV-T4-007, EV-T4-008) — counterevidence against assuming graph visibility prevents identity drift.
3. Neither framework has any native concept of an immutable, validated, atomically-promoted corpus release: provenance matrix rows for `corpus_release_version` are "lost" at index-time for both; Haystack offers only DuplicatePolicy (HS-2).
4. Controlled runtime results show no retrieval-quality difference between frameworks under fixed configuration (recall 1.0, MRR 0.87–0.90 across all four conditions); generation dominates latency (~95–99% of total).

## Considered alternatives

- **adopt (single framework as-is):** Rejected. Hidden ambient state (driver 1) or silent identity transformation at split time (driver 2) makes reproducible answers unprovable without external controls either way.
- **avoid both / hand-roll pipelines:** Rejected for this scope. Both frameworks provided working BM25/dense/Ollama paths that passed control validation with zero configuration drift; rebuilding them adds risk without addressing driver 3 anyway.
- **investigate further before deciding:** Partially adopted — see "next evidence worth buying". The runtime sample (5 cases × 4 conditions × 1 repetition) is too small to justify a hard framework lock-in on quality grounds.
- **adapt:** Not selected because we did not fork or materially reshape either framework; adapters wrap public APIs only.

## Decision

**Combine**: use one framework (either satisfies our measured requirements; Haystack preferred marginally for inspectable defaults and explicit graph observability, per EV-T4-009/EV-T4-010) **and** keep identity, trace, release validation, and atomic promotion outside both frameworks, as implemented and exercised (`src/rag_compare/{identity,trace,release}.py`; failure-injection run 9/9 assertions true).

**Framework-independent release recommendation (separate from framework findings):** adopt immutable per-version index namespaces, manifest validation of file hashes/counts/schema/embedding identity, single-capture release filtering at query start, and atomic pointer promotion. This mechanism is what actually prevented partial-v2 answers (H3 supported by runtime evidence); no framework choice substitutes for it.

## Consequences

- Positive: provenance fields survive framework-native id regeneration (citation_span_correctness = 1.0 in all conditions); failed promotions leave the active pointer untouched; mixed releases provably cannot reach answers.
- Negative/cost: an adapter layer must be maintained against pinned SHAs (both frameworks rename components across releases — REF-T5, REF-T6); every new retrieval-affecting knob must be added to the explicit-configuration snapshot.
- Reversibility: high. Adapters implement one shared contract (`adapters/base.py`); swapping frameworks touches only the adapter package plus build manifests. The release layer is already framework-free.

## Next evidence worth buying

1. Diagnose the citation_source_correctness ≈ 0.28 pattern (all four conditions) — currently an unexplained artifact behavior, not attributable to either framework.
2. Repeat runs (≥3) and more evaluation cases before any latency-based claims; generation latency dominates and is host-dependent.
3. Test promotion/concurrent-query interleaving under real concurrency (atomicity was tested sequentially).
