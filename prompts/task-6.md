#Task 6: Run the controlled experiment

Task 6: Run the controlled experiment

## Dependency and preconditions

Task 5 must be complete with both adapters and observable stages passing their focused tests. Runtime conditions are serialized: Task 6 must use the Task 6 runtime slot and cannot overlap Task 7 runtime execution. Use a fresh interactive, short-context, standard-speed session with the assigned Luna model at medium reasoning effort. Work from week2/rag-framework-investigation'. Do not use 'gpt-5.6-sol'. Runtime model calls are Ollama-only; Codex is never part of the evaluated pipeline.

Ollama, the pinned manifests, fixed corpus/evaluation cases, validated active release, and Task 5 adapter contract are required before execution. Human approval is required to accept the run manifest and controlled artifacts, and before network access, dependency changes, reserve use, or a commit.

## Objective and bounded scope

**Worker role:** Act as the Task 6 controlled-experiment worker. Implement deterministic metrics and execute only the reproducible 2x2 retrieval experiment: LlamaIndex and Haystack, each with BM25 and dense retrieval.

Hold corpus, parser/chunker configuration, embedding/generator, reranker, prompt, evaluation cases, active release, and all non-retriever conditions fixed. Change one material variable at a time: within a framework pair, only retriever_kind and retriever-specific index data may differ. Do not add reranker variants, frameworks, corpus cases, or uncontrolled repetitions.

## Deliverables

src/rag_compare/metrics.py

*src/rag_compare/run_experiment.py

artifacts/results/controlled-results.csv

`artifacts/results/controlled-summary.json'

Frozen run-manifest copies and sanitized raw artifacts under 'artifacts/raw/<run_id>/

## Method and acceptance checks

1. Implement deterministic, per-case metrics: recall@k, MRR, forbidden-source violation, citation source correctness, citation span correctness, per-stage latency, total latency, and release consistency. Persist each value; do not collapse results into one score.

2. Before execution, assign a unique 'run_id and freeze a manifest that hashes the repository/environment manifests, experiment configuration, corpus manifest, evaluation cases, and prompt. Copy the resolved manifest into 'artifacts/raw/<run_id>/*.

3. Run all four controlled conditions: each framework with BM25 and dense retrieval. Save sanitized raw stdout/stderr, JS0NL traces, retrieved candidates, packed context, model output, citations, and per-case metrics for every condition and evaluation case.

4. Programmatically compare manifests and fail the run summary if corpus, parser/chunker configuration, reranker, generator, prompt, cases, or active release differs. The only permitted material differences within a

framework pair are retriever_kind and retriever-specific index data.

5. Write the CSV and JSON summary from observed artifacts, preserving condition identifiers, hashes, metric values, validation results, and artifact paths. Do not present predictions as observations.

6. Acceptance: the four conditions are present; every case has required raw artifacts and per-case metrics; the frozen manifest is available; programmatic control validation passes; and the summary fails closed for any unapproved material difference.

acceptance checks

reranker, generator, prompt, cases, or active release differs. The only permitted material differences within a framework pair are 'retriever_kind and retriever-specific index data.

5. Write the CSV and JSON summary from observed artifacts, preserving condition identifiers, hashes, metric values, validation results, and artifact paths. Do not present predictions as observations.

6. Acceptance: the four conditions are present; every case has required raw artifacts and per-case metrics; the frozen manifest is available; programmatic control validation passes; and the summary fails closed for any unapproved material difference.

## Evidence and safety

Use sanitized local artifacts only. Preserve raw evidence sufficient to reproduce observations, distinguish observed results from interpretations, and do not fabricate results, citations, timing, or model outputs. Runtime generation/embedding calls must use Ollama only. Do not use production accounts, personal/customer data, credentials, hosted APIs, unauthorized targets, external vector databases, or destructive tests. Do not commit model caches, virtual environments, or vendor repositories.

The Human monitors the exposed Codex counters. At 80% of any task limit, stop expanding scope and run only the defined execution/acceptance checks. At a hard budget, output, or cached-input limit, stop all further model work. Reserve requires prior Human approval and a collaboration-log entry; do not borrow tokens. No commit without explicit Human approval.

## Stop and escalate

Stop and report missing Task 5 acceptance evidence, Ollama/runtime availability, active-release validation, frozen inputs, raw-artifact storage, dependency, approval, budget warning/failure, or ambiguity. Stop if more than one material variable changes, any manifest comparison fails, or a condition cannot produce its required artifact set; do not silently rerun or normalize away the discrepancy.

Obtain Human approval before accepting the run manifest and controlled artifacts, network access, dependency changes, reserve use, or commit. Do not commit without explicit Human approval.

## Handoff

Before handoff, ask the Human to record the exact Codex token counters. Add a task-specific, factual AI-assistance entry to 'week2/AI_COLLABORATION.md and update only the Task 6 checkboxes in 'week2/TASKS.md that are supported by observed evidence. Report those two updates and their paths. Report changed files; commands run and results; run ID/manifests/hashes and artifact paths; unresolved issues; and the next required Human gate. List every completed or blocked 2x2 condition, control-validation outcome, per-case evidence availability, and any deviation without claiming results that were not observed. Do not authorize a commit.
