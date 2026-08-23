# Task 5: Implement the framework adapters and observable stages

## Dependency and preconditions

Tasks 3 and 4 must be complete. The shared identity/trace/release contract must be frozen, and Task 4 must provide verified public APIs and provenance evidence for both frameworks. Use a fresh interactive, short-context, standard-speed session with the assigned Terra model at medium reasoning effort. Work from `week2/rag-framework-investigation`. Do not use `gpt-5.6-sol`. Runtime model calls are Ollama-only; Codex is never part of the evaluated pipeline.

Adapter files may diverge only after the shared contract is frozen. Human approval is required for API deviations from the verified Task 4 evidence, network access, dependency changes, reserve use, or a commit.

## Objective and bounded scope

**Worker role:** Act as the Task 5 adapter implementation worker. Implement and test only the two framework-native adapters, fixed reranker/context packer, Ollama integration, and observable stage behavior required by the frozen shared contract.

Do not alter the corpus/evaluation contract, introduce a UI, hosted API, external vector database, generalized plugin system, or additional framework. Make every stage observable and enforce release consistency in every retrieval branch.

## Deliverables

`src/rag_compare/adapters/base.py`

`src/rag_compare/adapters/llamaindex_adapter.py`

`src/rag_compare/adapters/haystack_adapter.py`

`src/rag_compare/ollama.py`

`src/rag_compare/rerank.py`

`tests/test_rerank.py`

`tests/test_adapters.py`

## Method and acceptance checks

1. Use test-first work. Before implementation, write and run failing tests for the frozen shared adapter contract and deterministic reranking behavior.

2. Both adapters must implement `build_release(corpus_path, manifest, trace)` and `query(query_text, retriever_kind, active_release, trace)`. Normalize every returned candidate to source/document/chunk IDs, text, span, score, rank, metadata, and release ID.

3. Test and then implement the fixed reranker: lowercase tokenization, query-term coverage score, stable tie-break by incoming rank then chunk ID, and preservation of original retrieval score/rank. It may only reorder candidates.

4. Implement the context packer so it admits complete chunks only until the configured character/token approximation budget is reached, records rejection reasons, and never truncates a chunk.

5. Implement the LlamaIndex adapter using only public classes verified in Task 4. Explicitly set every retrieval-affecting value rather than relying on `Settings`; snapshot resolved settings in each stage event. Support BM25 and dense retrieval over the same normalized chunks and filter every branch by `release_id`.

6. Implement the Haystack adapter using only components verified in Task 4. Explicitly configure converter/splitter, in-memory stores, BM25, dense retrieval, filters, and Ollama components. Emit one stage event at every component boundary and enforce the same release filter.

7. Test contract equivalence for both adapters: identical stage order, all trace fields present, all chunks carrying active-release and provenance fields, citations resolving to corpus spans, and no mixed releases if the active release changes between query start and retrieval. Apply release validation filters before permitting runtime execution.

8. Run `.venv/bin/python -m pytest tests/test_rerank.py tests/test_adapters.py -q`. Acceptance requires the focused tests to pass with Ollama running, both adapter paths exposing all required stages, and all release filters rejecting mixed-release candidates.

## Evidence and safety

Keep tests, traces, and resolved settings auditable and sanitized. Do not claim a framework API works unless verified by source evidence and focused tests. Do not silently revise the frozen shared contract or Task 2 experiment contract. Use Ollama only for runtime calls; do not send corpus/evaluation data to hosted APIs. Do not use production data, credentials, external vector databases, extra frameworks, or model caches in version control.

The Human monitors the exposed Codex counters. At 80% of any task limit, stop expanding scope and run only required focused tests. At a hard budget, output, or cached-input limit, stop all further model work. Reserve requires prior Human approval and a collaboration-log entry; do not borrow tokens. No commit without explicit Human approval.

## Stop and escalate

Stop and report any missing frozen contract, verified framework API, dependency, or Ollama runtime; any API deviation; a failing contract-equivalence/release-filter test; an approval requirement; token-budget warning/failure; or ambiguity in required stage behavior. Do not substitute unverified APIs or relax observability/release filters.

Obtain Human approval before network access, dependency changes, reserve use, shared-contract/experiment-contract changes, or commit. Do not commit without explicit Human approval.

## Handoff

Before handoff, ask the Human to record the exact Codex token counters. Add a task-specific, factual AI-assistance entry to `week2/AI_COLLABORATION.md` and update only the Task 5 checkboxes in `week2/TASKS.md` that are supported by observed evidence. Report those two updates and their paths. Report changed files; commands run and results; source/test/trace evidence; unresolved issues; and the next required Human gate. List the frozen contract used, adapter stage order, release-filter outcomes, focused-test outcome, any API deviation request, and the Ollama prerequisite status. Preserve first-failure evidence and do not claim unobserved runtime results or authorize a commit.
