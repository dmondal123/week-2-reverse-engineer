#Task 9: Reproduce, sanitize, package, and verify

#Task 9: Reproduce, sanitize, package, and verify

## Dependency and preconditions

Task 8 must be complete, including the reviewed paper, ADR, required diagram/table sources, disclosure, evidence ledger, manifests, source, tests, corpus, evaluation cases, and sanitized artifacts. Mechanical checks may overlap only when they do not mutate the bundle. Use a fresh interactive, short-context, standard-speed session with the assigned Luna model at medium reasoning effort. Work only from 'week2/rag-framework-investigation', where all deliverable paths below are relative. Do not use 'gpt-5.6-sol. Codex is a development assistant only and is never part of the evaluated pipeline; runtime model calls are Ollama-only.

Explicit Human approval is required before creating or committing the final ZIP, any commit, or any upload. Human approval is also required before network access, dependency changes, reserve use, or a rerun.

## Objective and bounded scope

**Worker role:** Act as the Task 9 reproducibility and package-verification worker. Write exact reproduction instructions, verify the completed investigation from a clean shell, and perform only safe, non-destructive package preflight and ZIP verification.

Do not change investigation findings, source behavior, evidence, paper claims, or required bundle content to force a pass. Do not upload. Until explicit Human approval is received, do not create the final ZIP, commit it, or upload it; prepare and report the verified package plan and any blockers instead.

## Deliverables and acceptance checks

Create 'README.md` and `scripts/package_submission.py; the final approved artifact is submission/rag-framework-investigation.zip.

The README must give exact commands for environment creation, Ollama model installation, dependency installation, repository-SHA checkout, unit tests, pipeline build, controlled experiment, failure injection, paper artifact generation, and packaging. From a clean shell, run the complete verification suite:

bash

.venv/bin/python -m pytest -q

venv/bin/python -m rag_compare.run_experiment --config config/experiment.json

Record observed results without claims not supported by output. Required verification is that tests pass, all four conditions finish, no release-consistency failure occurs, and raw/summary artifacts are produced; stop and escalate if any condition is not observed.

Implement safe packaging with Python 'zipfile` and an explicit allowlist. Reject every path containing `.env', `.venv', 'node_modules', caches, credentials, vendor clones, generated build folders, or files above the chosen artifact-size limit. The approved ZIP must include README, manifests/pinned versions and commit SHAs, source/scripts, tests, corpus, cases, evidence ledger, sanitized artifacts, paper, required tables/diagram source, ADR, and AI-use disclosure.

required tables/diagram source,

Before the ZIP is created, perform non-destructive preflight validation of the allowlist and candidate files. Only after explicit Human approval to create the ZIP, use 'ZipFile.testzip()`, assert the required file list, scan member names for exclusions, extract to a temporary directory, parse every JSON/CSV member, and save the ZIP SHA-256 and verification output beside the archive. Perform final scope/integrity review: no fabricated citations/results, README-only architectural claims, missing evidence IDs, secrets, uncommitted required files, or unrelated course material.

## Evidence and safety

Use only local, authorized, sanitized files. Never include secrets, credentials, `.env' files, dependency caches, virtual environments, 'node_modules', vendor clones, generated build folders, personal/customer data, or unrelated course material. Keep verification non-destructive: do not overwrite artifacts or mutate the bundle during mechanical checks. Use a temporary extraction directory for ZIP inspection and retain the recorded SHA-256 and verification output after an approved build.

The Human monitors the exposed Codex counters. At 80% of any task limit, stop scope expansion and run only existing reproduction/package checks. At a hard budget, output, or cached-input limit, stop all further model work. Reserve requires prior Human approval and a collaboration-log entry; do not borrow tokens. Do not use `gpt-5.6-sol.

## Stop and escalate

Stop and report missing Task 8 materials, reproduction failures, absent required files, disallowed content, secret/credential risk, invalid JSON/CSV, failed ZIP integrity check, missing SHA-256/verification output, budget warning/failure, missing approval, or ambiguity about packaging scope. Do not omit, alter, or fabricate required evidence to package around a failure.

Obtain explicit Human approval before creating the final ZIP, committing it, or uploading it. Also obtain approval before network access, dependency changes, reserve use, or any rerun. Never upload without explicit Human approval, and do not commit without explicit Human approval.

## Handoff

Before handoff, ask the Human to record the exact Codex token counters. Add a task-specific, factual AI-assistance entry to 'week2/AI_COLLABORATION.md and update only the Task 9 checkboxes in 'week2/TASKS.md` that are supported by observed evidence. Report those two updates and their paths. Report changed files; commands run and observed results; reproduction, allowlist, ZIP-integrity, exclusion-scan, extraction/parse, SHA-256, and scope-review evidence; unresolved issues; and the next required Human gate. Explicitly state whether Human approval to create the ZIP, commit, and upload has been received. Do not claim unobserved results or authorize a ZIP, commit, or upload.
