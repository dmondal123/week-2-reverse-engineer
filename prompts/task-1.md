# Task 1: Freeze repositories, runtime, and Ollama models

## Dependency and preconditions

Task 1 has no task dependency. Use a fresh interactive, short-context, standard-speed session with the assigned Luna model at medium reasoning effort. Execute the initial directory creation/layout from the repository root; then change to `week2/rag-framework-investigation` for every subsequent Task 1 command, where `.venv` refers to `week2/rag-framework-investigation/.venv`. Codex is a development assistant only and must never be part of the evaluated pipeline. Do not use `gpt-5.6-sol`.

Human approval is required before any network access, fallback model selection, dependency change, or commit. Stop if Codex reports long-context or fast-mode pricing. Runtime model calls must use Ollama only.

## Objective and bounded scope

**Worker role:** Act as the Task 1 environment-freeze worker. Execute only this bounded setup task and preserve all approval gates for the task owner.

Freeze the reproducible local environment for the LlamaIndex-versus-Haystack investigation. Create only the Task 1 setup artifacts and the required directory layout. This task does not trace either framework, build adapters, run the experiment, or alter the assignment scope.

## Deliverables

`week2/rag-framework-investigation/pyproject.toml`

`week2/rag-framework-investigation/scripts/freeze_environment.sh`

`week2/rag-framework-investigation/config/environment-manifest.json`

`week2/rag-framework-investigation/config/repository-manifest.json`

Required supporting directory layout and the one saved environment-freeze artifact at `artifacts/raw/environment-freeze.txt`.

## Method and acceptance checks

1. From the repository root, create the investigation layout and its isolated `.venv`; then change to `week2/rag-framework-investigation` and verify `.venv/bin/python --version` is Python 3.12.x.

2. With Human approval for network access, pull and smoke-test only `nomic-embed-text` and `qwen3:4b-instruct-2507-q4_K_M` via Ollama. Verify a non-empty numeric embedding vector and a generation response without a thinking phase. If the 4B smoke prompt exceeds 20 seconds, stop and request Human approval before using the corresponding 1.7B Instruct variant; record its exact Ollama tag and digest in `config/environment-manifest.json` and defer the required evidence-ledger entry to Task 2. Never substitute hybrid `qwen3:4b` with `/no_think`.

3. With Human approval for network access, clone the LlamaIndex and Haystack source repositories without selecting files by folder-tree inspection. Record access date, remote URL, exact 40-character SHA, license path, and default branch in `config/repository-manifest.json`.

4. From packaging metadata confirmed at each repository root, install only the core packages and integrations necessary for in-memory stores, BM25, Ollama embeddings/generation, and tests. With Human approval for dependency changes, verify `import llama_index; import haystack` resolves inside `.venv`, then record the complete pip freeze --all and packaging paths in the environment manifest.

5. Make `freeze_environment.sh` emit Python/platform details, `pip freeze`, Ollama version/list and model-inspection output, repository SHAs/remotes, and SHA-256 hashes of experiment configuration. Because Task 2 creates `config/experiment.json`, the first Task 1 freeze must explicitly record that the experiment-config hash is unavailable rather than inventing one. Run it once and save stdout at `artifacts/raw/environment-freeze.txt`; after Task 2, require an approved re-run to capture the actual configuration hash.

6. Acceptance is the expected Python version, successful in-venv imports, two pinned repository SHAs, the successful Ollama smoke checks, complete manifests, and the saved freeze artifact.

## Evidence and safety

Record only observed, reproducible facts with exact commands and artifacts; do not represent AI suggestions or unsaved terminal observations as evidence. Use no production accounts, credentials, personal/customer data, hosted model APIs, external vector databases, or additional frameworks. Keep all RAG runtime calls local through Ollama. Preserve exact repository/model/runtime identities and do not rely on implicit defaults.

The Human monitors the exposed Codex counters. At 80% of any task limit, stop expanding scope and perform only the acceptance checks above; at a hard budget, output, or cached-input limit, stop further model work. Reserve tokens require prior Human approval and the required collaboration-log entry; do not borrow task allocation.

## Stop and escalate

Stop and request Human approval before network use, installing or changing dependencies, selecting the 1.7B fallback, using reserve tokens, the required post-Task-2 freeze re-run, or committing. Record any approved fallback model's exact tag and digest in `config/environment-manifest.json`; defer its required evidence-ledger entry to Task 2. Escalate if Python is not 3.12.x, either model smoke check fails, the model exceeds the latency gate, a framework import resolves outside `.venv`, a pinned SHA/digest cannot be obtained, or required evidence cannot be saved. Do not commit without explicit Human approval.

When any requirement, dependency, or interpretation is ambiguous, stop and report the ambiguity to the task owner; do not assume a resolution.

## Handoff

Before handoff, ask the Human to record the exact Codex token counters. Add a task-specific, factual AI-assistance entry to `week2/AI_COLLABORATION.md` and update only the Task 1 checkboxes in `week2/TASKS.md` that are supported by observed evidence. Report those two updates and their paths. Report changed files; commands run and their results; evidence recorded; unresolved issues; and the next required Human gate. Also report pinned repository SHAs and Ollama tags/digests, smoke-check/import outcomes, manifest/freeze-artifact paths, the explicitly unavailable experiment-config hash, and the required approved post-Task-2 re-run. State unambiguously whether each approval gate was obtained; do not claim results that were not observed and do not authorize a commit.
