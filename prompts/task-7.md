1 2

#Task 7: Execute the partial-release failure injection

> abc #Task 7: Execute the partial-release failure injection

## Dependency and preconditions

Task 5 must be complete, and Task 6 must have released the serialized runtime slot before Task 7 runtime execution begins. Test preparation may overlap Task 6 preparation only; runtime execution must follow Task 6. A validated v1 release, Task 3 release controls, Task 5 adapters, fixed evaluation cases, and Ollama availability are required. Use a fresh interactive, short-context, standard-speed session with the assigned Terra model at medium reasoning effort. Work from 'week2/rag-framework-investigation'. Do not use 'gpt-5.6-sol'. Runtime model calls are Ollama-only; Codex is never part of the evaluated pipeline.

Human approval is required to preserve and inspect the first failure and before any rerun, network access, dependency change, reserve use, or commit.

## Objective and bounded scope

**Worker role:** Act as the Task 7 failure-injection worker. Execute only the controlled partial-release. failure injection that demonstrates the release mechanism prevents mixed-version answers and promotes a complete v2 atomically.

Do not alter the controlled experiment, use production data, or replace the immutable-release design. The failure case must index only half of v2 into a staging namespace, attempt promotion, and query all fixed evaluation cases against the captured active release.

## Deliverables

`tests/test_failure_injection.py

`artifacts/results/failure-injection.json`

`artifacts/raw/failure-injection-trace.jsonl

## Method and acceptance checks

1. Write the end-to-end test first. Activate v1, index only the first half of v2 into staging, attempt promotion, query every evaluation case, and assert promotion fails, the active pointer remains v1, and every returned chunk is v1.

2. Run this test before any corrective change. If mixed-version data or another failure occurs, preserve the first failure and its trace as the runtime failure-injection artifact. Never overwrite or replace that first-failure evidence with a later passing trace.

3. Apply only the Task 3 release controls: require expected file hashes/counts/schema/embedding identity during validation and filter every retrieval branch by the release captured at query start.

4. Prove rejection, recovery, and atomic promotion: observe partial-v2 rejection; complete v2; validate it; promote with the one atomic pointer replacement defined by Task 3; query again; assert every result is v2 and deleted v1 content cannot be returned. A failed validation must never change the active pointer.

5. Save a sanitized result JSON including expected and observed behavior, commands, pointer values before/after, manifest hashes, assertion results, and artifact paths. Keep the first-failure trace distinct from the post-recovery trace.

6. Acceptance: the initial partial release is rejected; v1 remains queryable until complete v2 passes validation; no query mixes release IDs; promotion changes the active pointer only through the atomic release behavior; recovery serves only v2; and the complete evidence record is retained.

6. Acceptance: the initial partial release is rejected; v1 remains queryable until complete v2 passes "validation; no query mixes release IDs; promotion changes the active pointer only through the atomic release behavior; recovery serves only v2; and the complete evidence record is retained.

## Evidence and safety

Use only local, authorized, synthetic/versioned corpus data and sanitized artifacts. Preserve the first failure exactly enough to inspect it; do not fabricate, discard, overwrite, or conceal failures. Runtime calls are Ollama-only. Do not use production accounts, personal/customer data, live credentials, hosted APIs, external vector databases, destructive tests outside the local staging namespace, or extra frameworks.

The Human monitors the exposed Codex counters. At 80% of any task limit, stop expanding scope and run only the existing failure-injection acceptance checks. At a hard budget, output, or cached-input limit, stop all further model work. Reserve requires prior Human approval and a collaboration-log entry; do not borrow tokens. No commit without explicit Human approval.

## Stop and escalate

Stop and report missing Task 5/Task 6 runtime-slot prerequisites, v1 validation, manifest/release controls, Ollama runtime, artifact storage, dependency, approval, budget warning/failure, or ambiguity. Stop immediately if the active pointer changes after failed validation, a query mixes releases, the first failure cannot be preserved, or atomic promotion cannot be demonstrated; do not overwrite evidence or retry without Human approval.

Obtain Human approval before preserving/inspecting the first failure, any rerun, network access, dependency changes, reserve use, or commit. Do not commit without explicit Human approval.

## Handoff

Before handoff, ask the Human to record the exact Codex token counters. Add a task-specific, factual AI-assistance entry to `week2/AI_COLLABORATION.md and update only the Task 7 checkboxes in 'week2/TASKS.md that are supported by observed evidence. Report those two updates and their paths. Report changed files; commands run and results; first-failure and recovery evidence/artifact paths; unresolved issues; and the next required Human gate. Include pointer values before/after, manifest hashes, assertion outcomes, release-filter/atomic-promotion outcomes, and whether a rerun approval is required. Preserve all first-failure evidence, do not claim unobserved results, and do not authorize a commit.
