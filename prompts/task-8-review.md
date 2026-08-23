Task 8: Write the decision-ready paper and required visuals

RB: Write the decision-ready paper and required visuals

##Phase: review

## Dependency and preconditions

Tasks 4, 6, and 7 must be complete, and the complete Task 8 draft plus its evidence ledger, pinned references, runtime artifacts, failure-injection evidence, tables, diagram source, ADR, and AI collaboration record must be available. Use a fresh interactive, short-context, standard-speed session with the assigned Terra model at medium reasoning effort. Work only from 'week2/rag-framework-investigation', where deliverable paths below are relative. Do not use 'gpt-5.6-sol. Codex is a development assistant only and is never part of the evaluated pipeline; runtime model calls are Ollama-only.

Human approval is required before reserve budget, network access, dependency changes, a commit, or approval of the final recommendation, ADR, or disclosure.

## Objective and bounded scope

**Worker role:** Act as the Task 8 evidence and rubric reviewer. Audit the Task 8 draft for citation provenance, required-paper/rubric coverage, AI-use disclosure completeness, and recommendation/ADR gates; correct only evidence-backed drafting defects.

Do not run or rerun experiments, create evidence, backfill missing facts, change Task 1-7 implementation, commit, or approve the recommendation/ADR/disclosure. A missing proof is a review finding, not permission to infer or invent it.

## Deliverables and acceptance checks

Review the required Task 8 files:

paper/insights-paper.md`

`paper/decision.adr.md

paper/architecture.mmd`

paper/hypothesis-evidence.md`

paper/experiment-results.md

paper/risk-control.md`

../AI_COLLABORATION.md`

Verify the paper has its exact required order, an executive claim of 150-250 words, and a 3,000-4,500-word body excluding appendices. Verify every architectural or experimental claim has an evidence ID or artifact, fact/interpretation/hypothesis/counterevidence/unknown labels are not conflated, and no claim rests only on a README, marketing page, AI answer, or popularity.

Verify the evidence minimums: 12+ commit-bound references spanning implementation, tests, and configuration; 2+ controlled-experiment runtime artifacts; 1 failure-injection result; 2+ history/issue/ADR references when design drivers are inferred; 1 counterexample/counterevidence item; and 1 rejected explanation or weakened hypothesis. Verify the four required visual/table sources represent the ledger/results rather than reconstructed memory and that the architecture view shows index-time and query-time ownership plus the release boundary.

Audit every grading-rubric gate: decision framing and three competing falsifiable hypotheses; real architecture reconstruction across context, data, state, model, tools, policy, execution, telemetry, and recovery; controlled

KS

Audit every grading-rubric gate: decision framing and three competing falsifiable hypotheses; real architecture reconstruction across context, data, state, model, tools, policy, execution, telemetry, and recovery; controlled and failure-injection experiment rigor; evidence-linked production reasoning; decision alternatives/consequences/reversibility/next evidence; limitations/unknowns; reproducibility; and communication clarity. Verify the ADR uses exactly one permitted decision (`adopt`, `adapt', 'combine', `avoid, or 'investigate') and keeps framework findings separate from the framework-independent release recommendation. Verify the AI disclosure records material prompts/instructions, tools/models, accepted/rejected suggestions, verification methods, and residual uncertainty without laundering AI output into evidence.

Record review findings and make only traceable, evidence-backed corrections. Any unresolved gate must remain explicit for Human decision; no result claim is permitted unless already supported by the cited record.

## Evidence and safety

Use only verified, sanitized local evidence. Preserve citations, artifact paths, failures, counterevidence, and unknowns; do not fabricate, delete, conceal, or recast them. Do not perform network activity, production-impacting work, external-vector-database use, credential handling, destructive tests, or evaluation runtime changes. No commit without explicit Human approval.

The Human monitors the exposed Codex counters. At 80% of any task limit, stop scope expansion and complete only existing review checks. At a hard budget, output, or cached-input limit, stop all further model work. Reserve requires prior Human approval and a collaboration-log entry; do not borrow tokens.

## Stop and escalate

Stop and report missing draft files, missing pinned citations/artifacts, citation-provenance failures, rubric or word/evidence threshold failures, incomplete disclosure, unsupported recommendation/ADR claim, missing approval, budget warning/failure, or any ambiguity. Do not repair an evidence gap by source browsing, runtime execution, or inference.

Obtain Human approval before reserve use, network access, dependency changes, a commit, or approving/releasing the final recommendation, ADR, or disclosure. Do not use `gpt-5.6-sol`.

## Handoff

Before handoff, ask the Human to record the exact Codex token counters. Add a task-specific, factual AI-assistance entry to 'week2/AI_COLLABORATION.md and update only the Task 8 review/approval checkboxes in `week2/TASKS.md that are supported by observed evidence. Report those two updates and their paths. Report changed files; commands run and results; citation/rubric/disclosure/recommendation-gate findings with evidence IDs and artifact paths; unresolved issues; and the next required Human gate. Include word-count and evidence-threshold results, all unsupported claims removed or flagged, and every remaining approval decision. Do not claim unobserved results or authorize a commit.
