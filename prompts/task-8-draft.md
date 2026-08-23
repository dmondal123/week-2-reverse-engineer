abc #Task 8: Write the decision-ready paper and required visuals

Task 8: Write the decision-ready paper and required visuals -draft.md >

## Dependency and preconditions

Tasks 4, 6, and 7 must be complete, with their pinned source, controlled-experiment, failure-injection, evidence-ledger, provenance, and sanitized artifact records available. Use a fresh interactive, short-context, standard-speed session with the assigned Luna model at medium reasoning effort. Work only from 'week2/rag-framework-investigation', where deliverable paths below are relative. Do not use 'gpt-5.6-sol. Codex is a development assistant only and is never part of the evaluated pipeline; runtime model calls are Ollama-only.

Human approval is required before using reserve budget, network access, dependency changes, a commit, or any recommendation/ADR/disclosure release decision.

## Objective and bounded scope

**Worker role:** Act as the Task 8 draft writer. Produce an evidence-bound, decision-ready draft and its required visual/table sources from verified Task 4, 6, and 7 material only.

Write only the required Task 8 deliverables. Do not run or rerun experiments, reinterpret missing evidence as a result, create new source/runtime evidence, change adapters or release controls, commit, or make final recommendation/ADR/disclosure approval decisions. Mark unsupported material as an unknown, limitation, or hypothesis rather than claiming a result.

## Deliverables and acceptance checks

Create all of the following:

`paper/insights-paper.md

`paper/decision.adr.md

paper/architecture.mmd`

`paper/hypothesis-evidence.md`

`paper/experiment-results.md

`paper/risk-control.md`

Update only`../AI_COLLABORATION.md for the required AI-use disclosure record.

Draft paper/insights-paper.md in this exact order: executive claim (150-250 words, written last but placed

first); decision context and scope; competing hypotheses; architecture reconstruction; experiment design; results and evidence; production analysis; decision and ADR; limitations and unknowns; AI-use disclosure. The paper body must be 3,000-4,500 words excluding appendices. Use the evidence ledger/artifacts to provide at least 12 commit-bound source references across implementation, tests, and configuration; at least two controlled-experiment runtime artifacts; one failure-injection result; at least two history/issue/ADR references when design drivers are inferred; one counterexample/counterevidence item; and one explicit rejected explanation or weakened hypothesis.

Produce the four required visual/table sources: an architecture or sequence diagram showing real index-time and query-time ownership plus the release boundary; a hypothesis/evidence table; an experiment-results table; and a risk/control or failure/recovery table. Generate tables from ledger/result files rather than memory. Every architectural or experimental claim must cite an evidence ID or artifact and distinguish fact, interpretation, hypothesis, counterevidence, and unknown. The ADR must select only 'adopt`, `adapt', 'combine`, `avoid, or `investigate', and state alternatives, consequences, reversibility, the next evidence worth buying, and the framework-independent release recommendation separately from framework findings.

explicit rejected

Produce the four required visual/table sources: an architecture or sequence diagram showing real index-time and query-time ownership plus the release boundary; a hypothesis/evidence table; an experiment-results table; and a risk/control or failure/recovery table. Generate tables from ledger/result files rather than memory. Every architectural or experimental claim must cite an evidence ID or artifact and distinguish fact, interpretation, hypothesis, counterevidence, and unknown. The ADR must select only 'adopt'`, `adapt`, `combine`, `avoid, or `investigate', and state alternatives, consequences, reversibility, the next evidence worth buying, and the framework-independent release recommendation separately from framework findings.

## Evidence and safety

Use verified, sanitized, local Task 4/6/7 evidence only. Do not fabricate citations, execution, runtime results, provenance, approval, or AI disclosure. Do not treat a README, marketing page, repository popularity, or an AI answer as architectural evidence. Preserve exact commit-bound references and artifact paths; disclose material prompts/instructions, tools/models, accepted/rejected suggestions, verification method, and residual uncertainty. Do not claim AI output as source or runtime evidence.

The Human monitors the exposed Codex counters. At 80% of any task limit, stop expanding the draft and run only existing word-count/evidence checks. At a hard budget, output, or cached-input limit, stop all further model work. Reserve requires prior Human approval and a collaboration-log entry; do not borrow tokens. No commit without explicit Human approval.

## Stop and escalate

Stop and report any missing Task 4, 6, or 7 deliverable; missing evidence ID, pinned reference, runtime artifact, failure result, history/issue/ADR reference, or disclosure detail; word/evidence-threshold shortfall; budget warning/failure; missing approval; or ambiguity about a claim, citation, required-paper section, or visual. Do not fill a gap by inference or rerun work.

Obtain Human approval before reserve use, network access, dependency changes, a commit, or releasing the recommendation, ADR, or disclosure. Do not use 'gpt-5.6-sol`.

## Handoff

Before handoff, ask the Human to record the exact Codex token counters. Add a task-specific, factual AI-assistance entry to 'week2/AI_COLLABORATION.md and update only the Task 8 drafting checkboxes in 'week2/TASKS.md that are supported by observed evidence. Report those two updates and their paths. Report changed files; commands run and results; evidence IDs, pinned citations, artifact paths, word count, and threshold-check results; unresolved issues; and the next required Human gate. State explicitly that this is a draft and list every unknown, missing evidence item, and claim requiring review. Do not claim unobserved results or authorize a commit.
