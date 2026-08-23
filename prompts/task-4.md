# Task 4: Reverse-engineer both real execution paths before adapter implementation

## Dependency and preconditions

Tasks 1 and 2 must be complete, with pinned repository/environment manifests, corpus, evaluation cases, hypotheses, and evidence ledger available. Use a fresh interactive, short-context, standard-speed session with the assigned Terra model at medium reasoning effort. Work from `week2/rag-framework-investigation`, where all deliverable paths below are relative. Do not use `gpt-5.6-sol`. Runtime model calls are Ollama-only; Codex is never part of the evaluated pipeline.

The LlamaIndex and Haystack research paths may proceed independently, but serialize edits to shared evidence files. Do not begin adapter implementation in this task. Human approval is required before network access, a dependency change, reserve use, or a commit.

## Objective and bounded scope

**Worker role:** Act as the Task 4 source-reconstruction and provenance worker. Execute only the bounded evidence investigation needed to reconstruct each framework's real index-time and query-time execution paths.

Start from one public observable capability per framework: a documented/public call that indexes documents and a call that executes retrieval. Trace from those calls rather than beginning with directory summaries. Produce source-bound evidence for parsing, chunking, identity, embedding, storage, configuration, retrieval, filtering/scoring, reranking, packing, generation, citation, state, telemetry, and recovery. Do not make paper-level architectural claims from a README, marketing page, AI answer, or repository popularity alone.

## Deliverables

`evidence/source-references.md`

`evidence/provenance-matrix.csv`

Updated `evidence/ledger.csv`

Updated `evidence/hypotheses.md`

## Method and acceptance checks

1. Record the public index and retrieval entry point for each framework first, with repository URL, exact commit SHA, access date, and source location.

2. Trace each index path: public call -> parser/converter -> splitter -> identity assignment -> embedding -> store. For each ownership boundary record class/function, SHA-linked line, input/output types, defaults and configuration resolution, state writes, tests, callbacks, telemetry, and recovery behavior.

3. Trace each query path: public query call -> configuration -> retrieval/filtering/scoring -> reranking -> packing -> generation -> citation. Record the same evidence fields and identify which abstractions obscure the actual execution path.

4. Audit hidden/default state. Inspect LlamaIndex `Settings`, transformations, callbacks, storage context, caches, serialization, environment-variable reads, and defaults. Inspect Haystack component defaults, pipeline wiring, stores, filters, concurrency, serialization, tracing, environment-variable reads, and defaults. Cover chunking, top-k, scores, embeddings, and metadata filters explicitly.

5. Create a provenance-matrix row for every framework/stage/field. For each of the design's 12 identity and provenance fields, classify it as `preserved`, `transformed`, `synthesized`, or `lost`, and cite its evidence ID.

6. Collect at least 12 commit-bound references, balanced across LlamaIndex and Haystack and spanning implementation, tests, and configuration. Add at least two history, issue, or ADR references when inferring design drivers. Triangulate each paper-level architectural claim with two evidence forms where practical.

7. Actively seek counterevidence for the currently favored hypothesis. Update a hypothesis to `WEAKENED` or `REJECTED` only when a cited source or runtime artifact supports that change; otherwise retain the uncertainty rather than inventing a result.

8. Acceptance: source references are commit-bound and balanced; the matrix covers all required fields; ledger entries distinguish facts, interpretations, hypotheses, counterevidence, and unknowns; and every claim is traceable to cited source evidence.

## Evidence and safety

Maintain the evidence ledger and source references as auditable, sanitized records. Preserve exact source provenance and label unknowns; do not fabricate source, history, issue, ADR, execution, or runtime evidence. Do not use production accounts, real personal/customer data, live credentials, unauthorized targets, destructive testing, hosted APIs, an external vector database, or extra frameworks.

The Human monitors the exposed Codex counters. At 80% of any task limit, stop expanding scope and run only existing acceptance checks. At a hard budget, output, or cached-input limit, stop all further model work. Reserve requires prior Human approval and a collaboration-log entry; do not borrow tokens. No commit without explicit Human approval.

## Stop and escalate

Stop and report missing repository access, pinned commit/source provenance, required history/issue/ADR evidence, or an unresolved ambiguity about a framework's public capability or ownership boundary. Stop for any missing dependency, approval, token-budget warning/failure, or ambiguity rather than assuming a resolution.

Obtain Human approval before network access, dependency changes, reserve use, or commit. Escalate conflicting source evidence and any required evidence that cannot be commit-bound. Do not commit without explicit Human approval.

## Handoff

Before handoff, ask the Human to record the exact Codex token counters. Add a task-specific, factual AI-assistance entry to `week2/AI_COLLABORATION.md` and update only the Task 4 checkboxes in `week2/TASKS.md` that are supported by observed evidence. Report those two updates and their paths. Report changed files; commands run and results; commit-bound source/history/issue/ADR evidence recorded; unresolved issues; and the next required Human gate. State the public entry points, reference counts/balance, provenance-matrix coverage, counterevidence outcome, and any source gaps without claiming unobserved runtime results. Preserve evidence and do not authorize a commit.
