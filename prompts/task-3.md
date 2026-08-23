#Task 3: Implement shared identity, trace, and release contracts with tests

#lask 3: Implement shared identity, trace, and release contracts with tests

## Dependency and preconditions

where -Task 2 must be complete: its corpus manifests, experiment configuration, and evaluation contract are the inputs to these shared contracts. Use a fresh interactive, short-context, standard-speed session with the assigned Terra model at medium reasoning effort. Perform all Task 3 work from 'week2/rag-framework-investigation', paths such as 'src/rag_compare/contracts.py` and `tests/test_identity.py are relative and `.venv refers to `week2/rag-framework-investigation/.venv'. Do not use 'gpt-5.6-sol'. Runtime model calls are Ollama only, and Codex is never part of the evaluated pipeline.

Use test-first implementation. Human approval is required before contract changes that affect the experiment, and before any network, dependency change, reserve use, or commit. Stop at any Human-reported token-budget warning.

## Objective and bounded scope

**Worker role:** Act as the Task 3 shared-contracts worker. Execute only this bounded identity, trace, and release-contract task and preserve all approval gates for the task owner.

Implement and test only the framework-independent identity, append-only trace, and immutable-release contracts. These contracts must prevent mixed-version answers; they are not adapters, retrievers, rerankers, or a controlled runtime experiment.

## Deliverables

-src/rag_compare/contracts.py

-src/rag_compare/identity.py`

-`src/rag_compare/trace.py`

src/rag_compare/release.py`

`tests/test_identity.py'

`tests/test_trace_contract.py

`tests/test_release.py

## Method and acceptance checks

1. First write failing identity tests. Prove that identical source ID and bytes yield the same document/chunk IDs; changed bytes change content and chunk IDs; the source ID remains stable; and IDs do not depend on framework name.

2. Implement identity functions using canonical UTF-8 and SHA-256: `digest(*parts) joins parts with `"\\x1f"`; `document_id(source_id, source_bytes_sha256)` digests `"document", source ID, and bytes SHA; `chunk_id (document_id_value, start, end, text) digests `"chunk", document ID, span, and text.

3. Before trace implementation, write tests constructing one event for every required stage. Require all fields: 'run_id', 'framework', `framework_commit`, `path', 'stage`, `component', 'source_reference`, started_at`, `duration_ms', 'resolved_config`, `input_ids', 'output_ids`, `metadata_delta`, score_rank_delta', 'release_id`, `artifact_path', 'status', and 'error'. Assert 'duration_ms >= 0, ID fields are lists, resolved configuration is serializable, and 'release_id` is non-empty.

4. Implement an append-only JSONL trace with a frozen 'StageEvent' dataclass. Serialize events using sorted JSON keys; flush and call 'os.fsync' after every event so failure preserves evidence. 5. Before release implementation, write tests for: complete v1 validation; partial v2 failing expected file/hash/count validation; schema or embedding identity mismatch failure; failed validation never changing 'active. json; successful promotion using exactly one atomic replacement; and a query capturing one active release then rejecting chunks from all other releases.

5. Before release implementation, write tests for: complete v1 validation; partial v2 failing expected file/hash/count validation; schema or embedding identity mismatch failure; failed validation never changing 'active. json; successful promotion using exactly one atomic replacement; and a query capturing one active release then rejecting chunks from all other releases.

6. Implement immutable release namespaces and manifest validation. Require corpus file hashes/list, corpus/schema versions, parser and chunker identities/configuration (including chunk size/overlap/config hash), embedding name/Ollama digest/dimensions/distance metric, framework commit/package/adapter identity, document/chunk counts, build timestamp, and 'validation_status'. Refuse promotion unless validation is 'passed and manifest fields match observed build artifacts.

7. Promote only by writing a temporary pointer in the same directory, flushing and fsyncing it, then calling `os.replace(temp_path, active_path). Query construction must capture the active release once and every retrieval branch must filter on that release ID.

8. Run.venv/bin/python -m pytest tests/test_identity.py tests/test_trace_contract.py tests/test_release.py

-q. Acceptance is that all focused tests pass, with no mixed-release behavior and no trace-contract failure.

## Evidence and safety

Keep normalized trace evidence append-only, deterministic, and distinct from AI assistance. Do not include secrets, production data, credentials, hosted APIs, external vector databases, or additional frameworks. Runtime calls are Ollama-only; no model call is required for this bounded contract task. Do not silently change Task 2's experiment contract.

The Human monitors the exposed Codex counters. At 80% of any task limit, stop expanding scope and run only the focused acceptance tests. At a hard budget, output, or cached-input limit, stop all further model work. Reserve requires prior Human approval and required collaboration-log detail; do not borrow allocation.

## Stop and escalate

Stop and obtain Human approval before a contract change affecting the experiment, network access, dependency changes, reserve use, or commit. Escalate if tests require a semantic change to the fixed corpus/experiment contract, if manifest/artifact validation cannot prove release completeness, if an active pointer changes after failed validation, if a query can mix releases, or if a token-budget warning/failure occurs. Do not commit without explicit Human approval.

When any requirement, dependency, or interpretation is ambiguous, stop and report the ambiguity to the task owner; do not assume a resolution.

## Handoff

Before handoff, ask the Human to record the exact Codex token counters. Add a task-specific, factual AI-assistance entry to 'week2/AI_COLLABORATION.md and update only the Task 3 checkboxes in 'week2/TASKS.md that are supported by observed evidence. Report those two updates and their paths. Report changed files; commands run and their results; evidence recorded; unresolved issues; and the next required Human gate. Also report the created contract/test paths, focused-test outcome, whether all identity/trace/release invariants passed, and any approval gate reached. State unresolved failures precisely, preserve first-failure evidence, do not claim unobserved runtime results, and do not authorize a commit.
