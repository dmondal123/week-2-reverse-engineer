#Task 2: Create hypotheses, ledger, corpus, and evaluation contract

#Task 2: Create hypotheses, ledger, corpus, and evaluation contract

## Dependency and preconditions

Task 1 must be complete with pinned runtime and repository identities available. Use a fresh interactive, short-context, standard-speed session with the assigned Luna model at medium reasoning effort. Perform all Task 2 work from 'week2/rag-framework-investigation', so paths such as 'evidence/ledger.csv' and 'config/experiment.

json are relative to that directory. Codex may assist development only; it is not part of the evaluated pipeline. Do not use 'gpt-5.6-sol`; all runtime model calls are Ollama only.

Human approval is required for the hypotheses, corpus, and evaluation cases before treating them as accepted. Human approval is also required for any network, dependency change, reserve use, or commit. Stop at the Human's token-budget warning and never use a Codex model as the RAG runtime.

## Objective and bounded scope

**Worker role:** Act as the Task 2 corpus-and-evaluation-contract worker. Execute only this bounded data/configuration task and preserve all approval gates for the task owner.

Create the versioned synthetic corpus and fixed evaluation/experiment contract needed for a controlled retriever comparison. Limit work to Task 2 data/configuration/evidence artifacts; do not implement identity, tracing, release logic, adapters, framework traces, or execute the runtime experiment.

## Deliverables

-`evidence/hypotheses.md`

-evidence/ledger.csv'

Six corpus/v1/*.md files and five corpus/v2/*.md files

corpus/v1/manifest.json' and `corpus/v2/manifest.json'

eval/cases.json'

config/experiment.json'

## Method and acceptance checks

1. Before opening implementation files, copy the three pre-trace hypotheses into 'evidence/hypotheses.md":

LlamaIndex convenience/global 'Settings' can hide material retrieval behavior; Haystack's explicit graph improves observability but converters/splitters can invisibly transform identity/metadata; neither framework alone supplies atomic reproducible releases. For each include a timestamp, prediction, supporting/discriminating evidence, rejection condition, 'status=OPEN', and confidence before trace.

2. Initialize 'evidence/ledger.csv with exactly this header: 'evidence_id, timestamp, framework,commit_sha, evidence_type, claim, source_or_command, artifact_path, interpretation, confidence, contradicts, verification_status". Add one verified fact for each pinned repository and Ollama model, including any approved fallback model tag/digest recorded in Task 1's 'config/environment-manifest.json'. Exclude secrets, model-generated guesses, and unsaved terminal observations.

3. Create six short v1 Markdown policies with front matter for 'source_id', 'title', 'policy_version', 'status', and 'effective_date. Include a current Wi-Fi reimbursement rule, an obsolete contradictory memo, contractor scope, an approval threshold, and two distractors.

4. Derive v2 by changing the current rule, removing one distractor, and changing the relevant field from policy_version' to 'source_version' under schema version 2. Stable 'source_id' values must remain stable for updated documents; content hashes and later chunk IDs must change.

5. Create exactly five discriminating evaluation cases. Each JSON object includes 'case_id', 'query', `relevant_source_ids', 'forbidden_source_ids', 'required_phrases', and 'corpus_version'. Cover one multi-fact case, exact identifier, semantic paraphrase, obsolete-source trap, and version-change case.

content hashes and later chunk IDs must change.

5. Create exactly five discriminating evaluation cases. Each JSON object includes 'case_id`, `query', relevant_source_ids`, `forbidden_source_ids`, `required_phrases`, and `corpus_version'. Cover one multi-fact case, exact identifier, semantic paraphrase, obsolete-source trap, and version-change case.

6. Make 'config/experiment.json explicitly set chunk size/overlap, top-k, rerank-k, context budget, stable tie-break rule, embedding model, generation model, temperature `0`, prompt hash, and active 'release_id`. Do not leave any framework default that affects results implicit.

7. After config/experiment.json' exists, refresh the Task 1 freeze artifact only if the relevant Task 2 Human approval was pre-granted. If it was not pre-granted, stop and obtain approval; do not claim approval occurs inside an already-completed turn. Continue in the same interactive Task 2 session after approval. Run from `week2/rag-framework-investigation': 'scripts/freeze_environment.sh > artifacts/raw/environment-freeze.txt'. Require the refreshed artifact to contain the observed SHA-256 of `config/experiment.json', rather than an unavailable placeholder.

8. Parse every JSON artifact and run SHA-256 checks over every corpus/config/eval file. Confirm v1 contains six files and v2 contains five. Acceptance requires all checks to pass, the refreshed freeze artifact to record the observed experiment-configuration SHA-256, and the approval gate for hypotheses/corpus/cases (including the approved refresh) to be satisfied.

## Evidence and safety

Use only small synthetic policy content-never personal/customer data, credentials, production accounts, or live/unauthorized targets. Keep facts, hypotheses, interpretations, counterevidence, and unknowns distinct. Runtime model calls, if any become necessary later, are Ollama-only; Codex remains a development assistant only.

The Human monitors the exposed Codex counters. At 80% of any task limit, stop scope expansion and run only the stated acceptance checks. Stop all further model work at any hard budget, output, or cached-input limit. Reserve use needs prior Human approval and its required collaboration-log record; no borrowing from another task.

## Stop and escalate

Stop for Human approval of the hypotheses, corpus, and cases before acceptance, and before network/dependency changes, reserve use, or any commit. Escalate if the requirements conflict, a required field/manifest/hash cannot be determined, the corpus counts differ from six v1/five v2, a framework-affecting default remains implicit, or runner accounting warns or fails. Do not commit without explicit Human approval.

When any requirement, dependency, or interpretation is ambiguous, stop and report the ambiguity to the task owner; do not assume a resolution.

## Handoff

Before handoff, ask the Human to record the exact Codex token counters. Add a task-specific, factual AI-assistance entry to 'week2/AI_COLLABORATION.md and update only the Task 2 checkboxes in 'week2/TASKS.md` that are supported by observed evidence. Report those two updates and their paths. Report changed files; commands run and their results; evidence recorded; unresolved issues; and the next required Human gate. Also report approval status for hypotheses/corpus/cases and JSON/hash/count check results. Do not claim execution evidence beyond observed checks and do not authorize a commit.
