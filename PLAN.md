# LlamaIndex vs Haystack Investigation Plan

## Outcome

Deliver a reproducible, decision-ready investigation answering:

> Which framework makes retrieval behavior, provenance, and immutable index releases easier to observe and control without permitting mixed-version answers?

The final bundle must satisfy every requirement and grade cap in [`PROBLEM_STATEMENT.md`](PROBLEM_STATEMENT.md), use Ollama exclusively for model calls, and be complete by Sunday midnight.

## Strategy

Use a thin vertical slice rather than a broad framework survey. Build equivalent LlamaIndex and Haystack pipelines over one small versioned corpus, expose every stage, and collect source plus runtime evidence at each boundary.

The investigation has three proof obligations:

1. **Execution ownership:** reconstruct the real index-time and query-time paths, including defaults, global state, dependencies, storage, telemetry, and recovery boundaries.

2. **Controlled comparison:** swap only BM25 versus Ollama dense retrieval while keeping corpus, parsing, chunking, reranking, packing, generation, prompts, and evaluation cases fixed.

3. **Release safety:** partially build corpus version 2 and prove validation plus atomic promotion prevents any mixed-version answer.

## Milestones

| Milestone | Outcome | Evidence gate | Budget |
|---|---|---|---|
| 1. Freeze | Repositories, runtime, packages, configuration, and Ollama model digests pinned; environment and repository manifests reproduce exact identities | 1.0 h |
| 2. Contract | Hypotheses, ledger, versioned corpus, cases, trace/release schemas | Three pre-trace hypotheses and machine-readable fixtures exist | 1.5 h |
| 3. Foundations | Stable IDs, trace events, manifest validation, atomic pointer | Unit tests prove incomplete releases cannot promote | 1.5 h |
| 4. Reconstruct | Both index-time and query-time implementations traced | 12+ balanced commit-bound references and provenance matrix | 2.0 h |
| 5. Build | Equivalent observable framework adapters run locally | Identical stage contract and active-release invariant pass | 2.0 h |
| 6. Experiment | BM25/dense controlled runs complete | Only retriever differs; per-case metrics and raw traces saved | 1.0 h |
| 7. Inject failure | Partial v2 rejected; complete v2 promoted safely | Pointer and query traces prove no mixed state | 1.0 h |
| 8. Synthesize | Paper, ADR, required visuals/tables, disclosure completed | Every material claim links to source/runtime evidence | 3.5 h |
| 9. Package | Reproduction and submission bundle verified | Tests pass and sanitized ZIP opens with required contents | 1.0 h |
| Buffer | Absorb model/setup or writing variance | Core proof obligations remain intact | 0.5 h |
| **Total** | | | **15.0 h** |

## AI-assisted execution governance

The implementation receives a fresh AI budget that excludes all planning usage recorded before this section was approved.

The 9,000,000-token ceiling preserves the originating $30 constraint with headroom: at the maximum 70% Terra / 30% Luna mix, 10% output share, and 6.5x cached-input ceiling, it is approximately $28.25 at OpenAI's standard short-context rates as of 2026-08-18. This is a planning bound, not a billing guarantee. Human records the exact exposed counters after each task, and any pricing-tier change triggers the human budget gate.

| Task | AI role | Model and effort | Input/output cap | Cached-input ceiling |
|---|---|---|---|---|
| 1. Freeze | Execute setup checks and record manifests | gpt-5.6-luna medium | 400,000 | 2,600,000 |
| 2. Contract | Draft hypotheses, fixtures, and validation checks | gpt-5.6-luna medium | 600,000 | 3,900,000 |
| 3. Foundations | Design and test identity, trace, and release contracts | gpt-5.6-terra medium | 850,000 | 5,525,000 |
| 4. Reconstruct | Trace source paths and challenge hypotheses | gpt-5.6-terra medium | 1,300,000 | 8,450,000 |
| 5. Build | Implement and verify both adapters | gpt-5.6-terra medium | 1,400,000 | 9,100,000 |
| 6. Experiment | Implement metrics and execute the frozen matrix | gpt-5.6-luna medium | 600,000 | 3,900,000 |
| 7. Inject failure | Implement, diagnose, and verify failure behavior | gpt-5.6-terra medium | 650,000 | 4,225,000 |
| 8. Synthesize | Luna drafts evidence-bound sections; Terra reviews the decision | Luna 600,000; Terra 450,000, both medium | 1,050,000 | 6,825,000 |
| 9. Package | Run mechanical checks and package the allowlisted bundle | gpt-5.6-luna medium | 350,000 | 2,275,000 |
| **Assigned** | | **Terra 4,650,000; Luna 2,550,000** | **7,200,000** | **46,800,000** |
| **Reserve** | Only after human approval | **Terra 1,650,000; Luna 150,000** | **1,800,000** | **11,700,000** |
| **Hard ceiling** | Stop rather than exceed | **No `gpt-5.6-sol`** | **9,000,000** | **58,500,000** |

The input-plus-output cap includes reasoning tokens because reasoning is part of model output. Output must remain at or below 10% of each task's cap. Use standard speed and short-context sessions. If Codex reports long-context or fast-mode pricing, stop and obtain human approval before continuing because the token-to-cost assumption has changed.

### Dependency and concurrency map

```text
Task 1 ->
Task 2
|-- Task 3: shared contracts
|-- Task 4: source reconstruction
|   |-- LlamaIndex read-only trace
|   |-- Haystack read-only trace
|-> Task 5
|-- LlamaIndex adapter
|-- Haystack adapter
-> shared contract tests
Task 6 preparation
|--- Task 7 preparation
serialize Task 6 and Task 7 runtime execution
Task 8 final synthesis
Task 9 package and verify
```

Tasks 3 and 4 may run concurrently after Task 2 is approved.

The two Task 4 framework traces may be researched concurrently, but they are read-only branches; updates to the shared ledger, provenance matrix, and hypothesis file are merged serially.

In Task 5, shared interfaces, reranking, and Ollama wrappers are frozen first; the two adapter files may then be implemented concurrently and are merged only after the same contract tests pass for each.

Task 6 and Task 7 code preparation may overlap, but all Ollama experiment and failure-injection runs are serialized. Concurrent local model runs would invalidate latency comparisons and compete for memory on the 24 GB laptop. Evidence-bound paper sections may be drafted as evidence arrives. The executive claim, ADR, and final recommendation remain sequential and wait for Tasks 6 and 7.

### Human approval gates

1. **Environment change:** approve network access, dependency changes, any Ollama fallback, and every commit.

2. **Pre-trace contract:** approve the hypotheses, rejection conditions, corpus, and evaluation cases before Task 4 opens implementation source.

3. **Evidence integrity:** sample and verify commit-bound references and the provenance matrix before adapter findings become paper claims.

4. **Budget change:** approve every reserve withdrawal. No task borrows from another task, increases reasoning effort, or changes model silently.

5. **Experiment acceptance:** inspect control-manifest equality, raw artifacts, and the preserved first failure before authorizing a rerun or synthesis.

6. **Decision ownership:** approve the production recommendation, ADR, AI-use disclosure, final ZIP, commit, and upload.

### Token accounting and stop rules

Run each task in a fresh interactive Codex session with the exact assigned model, medium reasoning effort, standard speed, and short context. In the final task response, the agent asks the Human to record the exact Codex token counters. The Human records the exact exposed counters outside the completed agent turn: uncached input, cached input, output including reasoning, and the task total. If a field is not exposed, record 'unavailable'; never estimate or invent it.

The Human compares the recorded totals with the task and global limits. At 80%, stop expanding scope and run only the task's existing acceptance checks. At 100%, stop all further model work for that task. Do not send the counters back into the completed agent thread merely to record them, because that would add another uncounted turn.

No task borrows from another task. Reserve use requires prior human approval and records the task, reason, approved amount, model, and remaining global headroom. The existing 10% output cap and 58,500,000 cached-input ceiling remain hard limits. Use standard speed with the exact configured Terra or Luna model; `gpt-5.6-sol` remains prohibited. Success never overrides a breached budget.

## Schedule

**Tuesday, 2 hours:** milestones 1 and the first hour of milestone 2.

**Wednesday, 2 hours:** finish milestone 2 and implement the critical release contract in milestone 3.

**Thursday, 2 hours:** complete milestone 3 and trace LlamaIndex.

**Friday, 2 hours:** trace Haystack and begin the adapters.

**Saturday/Sunday, 7 hours:** finish adapters, run both experiments, write the paper and ADR, verify evidence minimums, and package the ZIP.

Write observations and paper paragraphs as evidence is produced; do not defer all writing until Sunday.

## Decision gates

1. **Model gate:** `nomic-embed-text` must return embeddings locally.

   `qwen3:4b-instruct-2507-q4_K_M` must pass the smoke prompt within 20 seconds; otherwise pin the corresponding 1.7B Instruct variant and log the correction.

   Do not use the hybrid `qwen3:4b` with `/no_think` as a substitute.

2. **Environment gate:** both runtime packages must resolve inside the isolated virtual environment and map to recorded source/package versions.

3. **Trace gate:** do not run the comparison until both adapters emit every required stage and provenance field.

4. **Control gate:** reject experiment output if anything besides the retriever and its index changes within a framework pair.

5. **Release gate:** an incomplete manifest must fail before the active pointer can change.

6. **Evidence gate:** do not make a paper-level architectural claim without commit-bound or runtime evidence; use two evidence forms where possible.

7. **Submission gate:** do not upload until the ZIP passes integrity, contents, exclusions, and parse checks.

## Scope protection

Do not add a UI, production vector database, hosted model API, extra framework, large corpus, generalized plugin layer, or broad performance benchmark. If time slips, reduce evaluation cases from six to five and use one runtime repetition; do not cut either framework, failure injection, provenance tracking, AI-use disclosure, or final verification.

## Definition of done

Another engineer can reproduce one answer from source bytes through its final citation and identify every configuration value that affected it.

Both frameworks have complete index-time and query-time ownership traces.

Hidden/default state and provenance preservation/loss are explicitly audited.

The controlled experiment and partial-release injection produce sanitized raw runtime evidence.

At least one initial explanation is rejected or weakened by counterevidence.

The 3,000-4,500 word paper provides a reversible production recommendation and names the next evidence worth buying.

The complete ZIP opens, contains all required artifacts, excludes prohibited content, and has a recorded SHA-256.

## Supporting documents

[`ARCHITECTURE.md`](ARCHITECTURE.md): component boundaries, data contracts, trace design, provenance, controlled experiment, and release protocol.

[`TASKS.md`](TASKS.md): executable checklist, files, commands, tests, and acceptance checks.

[`AI_COLLABORATION.md`](AI_COLLABORATION.md): concise human-AI decision and correction log.
