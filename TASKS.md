# LlamaIndex vs Haystack Task Checklist

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and document a reproducible LlamaIndex-versus-Haystack investigation that traces both RAG pipelines, runs a controlled retriever experiment, and proves an immutable release mechanism prevents mixed-version answers.

**Architecture:** Two framework-native adapters implement one shared pipeline contract and emit normalized JSONL stage events. Immutable index namespaces and validated release manifests sit outside both frameworks; a single atomic pointer selects the queryable release. A synthetic, versioned corpus and fixed evaluation set make retrieval, provenance, citation, and failure behavior reproducible.

**Tech Stack:** Python 3.12, pytest, LlamaIndex, Haystack, Ollama, `nomic-embed-text`, `qwen3:4b-instruct-2507-q4_K_M`, JSON/JSONL/CSV, Mermaid, standard-library ZIP tooling.

**Architecture document:** `week2/ARCHITECTURE.md`

## Locked scope and stopping rules

Total working budget: 15 hours.

RAG runtime model calls: Ollama only; Codex Terra/Luna are permitted solely as AI development assistants and are never part of the evaluated pipeline.

AI-assisted development: `gpt-5.6-terra` and `gpt-5.6-luna` only. Do not use `gpt-5.6-sol` for any implementation task.

AI token ceiling: 9,000,000 input-plus-output tokens, comprising 7,200,000 assigned tokens and a human-approved reserve of 1,800,000. Cached input is tracked separately and may not exceed 58,500,000 tokens.

Per-task output, including reasoning, may not exceed 10% of that task's cap.

Use standard speed and a fresh short-context session for every task. Pause for human approval if Codex reports long-context or fast-mode pricing.

Corpus: six documents and five or six evaluation cases.

Runtime conditions: two frameworks x two retrievers x evaluation cases.

Do not add a UI, external vector database, hosted API, generalized plugin system, or more frameworks.

If behind schedule, reduce cases to five and runtime repetitions to one. Never remove source tracing, either framework, the controlled experiment, failure injection, evidence ledger, AI disclosure, or final verification.

Target file structure:

```text
week2/rag-framework-investigation/
README.md
pyproject.toml
config/experiment.json
config/environment-manifest.json
config/repository-manifest.json
corpus/v1/*.md
corpus/v2/*.md
corpus/v1/manifest.json
corpus/v2/manifest.json
eval/cases.json
evidence/hypotheses.md
evidence/ledger.csv
evidence/provenance-matrix.csv
evidence/source-references.md
../AI_COLLABORATION.md
src/rag_compare/contracts.py
src/rag_compare/identity.py
src/rag_compare/trace.py
src/rag_compare/release.py
src/rag_compare/ollama.py
src/rag_compare/rerank.py
src/rag_compare/metrics.py
src/rag_compare/adapters/base.py
src/rag_compare/adapters/llamaindex_adapter.py
src/rag_compare/adapters/haystack_adapter.py
src/rag_compare/run_experiment.py
tests/test_identity.py
tests/test_release.py
tests/test_trace_contract.py
tests/test_rerank.py
tests/test_adapters.py
tests/test_failure_injection.py
artifacts/raw/.gitkeep
artifacts/results/.gitkeep
paper/insights-paper.md
paper/decision.adr.md
paper/architecture.mmd
paper/hypothesis-evidence.md
paper/experiment-results.md
paper/risk-control.md
scripts/freeze_environment.sh
scripts/package_submission.py
```

## Execution ownership, dependencies, and token controls

| Task | Depends on | Safe concurrency | Model allocation | Input + output cap | Human gate |
|---|---|---|---|---|---|
| 1 | None | Repository clones and independent smoke checks may overlap | Luna 400,000 | 400,000 | Network, fallback, dependency, and commit approval |
| 2 | Task 1 | Corpus, evaluation, and ledger drafting may overlap after hypotheses are written | Luna 600,000 | 600,000 | Approve hypotheses, corpus, and cases |
| 3 | Task 2 | May run alongside Task 4; identity, trace, and release files have separate owners | Terra 850,000 | 850,000 | Approve contract changes affecting the experiment |
| 4 | Tasks 1-2 | LlamaIndex and Haystack research may overlap; shared evidence writes are serialized | Terra 1,300,000 | 1,300,000 | Verify sampled source references and provenance |
| 5 | Tasks 3-4 | Adapter files may diverge after the shared contract is frozen | Terra 1,400,000 | 1,400,000 | Approve API deviations or dependency changes |
| 6 | Task 5 | Metric code may overlap Task 7 preparation; runtime conditions are sequential | Luna 600,000 | 600,000 | Accept run manifest and controlled artifacts |
| 7 | Task 5 and the Task 6 runtime slot | Test preparation may overlap Task 6; runtime execution follows Task 6 | Terra 650,000 | 650,000 | Preserve and inspect first failure; approve reruns |
| 8 | Tasks 4, 6, and 7 | Evidence-bound sections may overlap; executive claim and ADR are last | Luna 600,000 + Terra 450,000 | 1,050,000 | Approve recommendation, ADR, and disclosure |
| 9 | Task 8 | Mechanical checks may overlap only when they do not mutate the bundle | Luna 350,000 | 350,000 | Approve ZIP, commit, and upload |
| **Assigned** | | | **Terra 4,650,000 + Luna 2,550,000** | **7,200,000** | |
| **Reserve** | Human approval | No automatic use | **Terra 1,650,000 + Luna 150,000** | **1,800,000** | Record amount and reason before use |

The critical sequence is Task 1 -> Task 2 -> Tasks 3 and 4 -> Task 5 -> serialized Task 6 and Task 7 execution -> Task 8 -> Task 9. Parallel workers must not write the same ledger, hypothesis, results, or bundle file concurrently.

Before each task:

1. Start a fresh interactive Codex session with the task's exact assigned model, medium reasoning effort, standard speed, and short context.

2. In the final response, the agent asks the Human to record the exact Codex token counters for the completed task.

3. The Human records the exact exposed counters outside the completed turn: uncached input, cached input, output including reasoning, and task total. Use `unavailable` for any field the product does not expose; never estimate it.

4. At 80%, stop expanding scope and run only the task's existing acceptance checks. At 100%, stop all further model work for that task.

5. Do not reply merely to return token counters, because that creates another uncounted turn that is not included in the counters just reported.

Reserve tokens require explicit human approval and a collaboration-log entry naming the blocked task, reason, approved token amount, model, and remaining global headroom. Do not borrow from another task. The cached-input ceiling, `gpt-5.6-sol` remain in force. All commits also require explicit human approval.

## Task 1: Freeze repositories, runtime, and Ollama models

**Time box:** 60 minutes

**Files:**

Create: `week2/rag-framework-investigation/pyproject.toml`

Create: `week2/rag-framework-investigation/scripts/freeze_environment.sh`

Create: `week2/rag-framework-investigation/config/environment-manifest.json`

Create: `week2/rag-framework-investigation/config/repository-manifest.json`

- [x] **Step 1: Create the investigation directory and isolated environment**

Run:

```bash
mkdir -p week2/rag-framework-investigation/{config,corpus/{v1,v2},eval,evidence,src/rag_compare/adapters,tests,artifacts/{raw,results},paper,scripts}
python3 -m venv week2/rag-framework-investigation/.venv
```

Expected: `.venv/bin/python --version` reports Python 3.12.x.

- [x] **Step 2: Smoke-test the only permitted models**

Run:

```bash
ollama pull nomic-embed-text
ollama pull qwen3:4b-instruct-2507-q4_K_M
ollama list
curl -s http://127.0.0.1:11434/api/embed -d '{"model": "nomic-embed-text", "input": "release manifest"}'
curl -s http://127.0.0.1:11434/api/generate -d '{"model":"qwen3:4b-instruct-2507-q4_K_M", "prompt": "Reply with OK only", "stream":false}'
```

Expected: the embedding response has a non-empty numeric vector and generation returns a response without a thinking phase. If the 4B Instruct model exceeds 20 seconds for the smoke prompt, stop and request human approval to use the corresponding 1.7B Instruct variant. After approval, record its exact Ollama tag and digest in the ledger. Do not fall back to hybrid `qwen3:4b` plus `/no_think`.

- [x] **Step 3: Pin the supplied source repositories without selecting files by folder-tree inspection**

Run from `week2/rag-framework-investigation`:

```bash
git clone https://github.com/run-llama/llama_index.git vendor/llama_index
git clone https://github.com/deepset-ai/haystack.git vendor/haystack
git -C vendor/llama_index rev-parse HEAD
git -C vendor/haystack rev-parse HEAD
...
```

Expected: two 40-character SHAs. Record access date, remote URL, SHA, license path, and default branch in `config/repository-manifest.json`.

- [x] **Step 4: Install editable framework packages and test tools**

Use package locations confirmed from each repository's root packaging metadata. Install only the core packages and integrations needed for in-memory document stores, BM25, Ollama embeddings/generation, and tests. Immediately run:

```bash
.venv/bin/python -c 'import llama_index; import haystack; print("imports-ok")'
.venv/bin/python -m pip freeze --all
...
```

Expected: `imports-ok`; save the complete freeze and packaging paths in the environment manifest. Do not continue if either import resolves outside `.venv`.

- [x] **Step 5: Create `freeze_environment.sh`**

The script must emit Python/platform details, `pip freeze`, Ollama version/list, model inspection output, repository SHAs/remotes, and SHA-256 hashes of experiment configuration. Run it once and save stdout as `artifacts/raw/environment-freeze.txt`.

- [x] **Step 6: Commit the frozen setup**

```bash
git add week2/rag-framework-investigation/{pyproject.toml,config,scripts/freeze_environment.sh}
git commit -m "chore(rag-study): freeze framework and Ollama environment"
```

## Task 2: Create hypotheses, ledger, corpus, and evaluation contract

**Time box:** 90 minutes

**Files:**

Create: `evidence/hypotheses.md`

Create: `evidence/ledger.csv`

Create: `corpus/v1/*.md`, `corpus/v2/*.md`, and both corpus manifests

Create: `eval/cases.json`

Create: `config/experiment.json`

- [x] **Step 1: Write the three pre-trace hypotheses**

Copy the three hypotheses from the design into `evidence/hypotheses.md`. For each add `prediction`, `supporting evidence`, `rejection condition`, `status=OPEN`, and confidence before trace. Timestamp this before opening implementation files.

- [x] **Step 2: Initialize the evidence ledger**

Create a CSV with this exact header:

```csv
evidence_id, timestamp, framework, commit_sha, evidence_type, claim, source_or_command, artifact_path, interpretation, confidence, contradicts, verification_status
...
```

Add one fact for each pinned repository and Ollama model. Do not put secrets, model-generated guesses, or unsaved terminal observations in the ledger.

- [x] **Step 3: Write corpus version 1**

Create six short Markdown policies with explicit front matter containing `source_id`, `title`, `policy_version`, `status`, and `effective_date`. Include a current Wi-Fi reimbursement rule, an obsolete contradictory memo, contractor scope, an approval threshold, and two distractors.

- [x] **Step 4: Derive corpus version 2**

Change the current rule, remove one distractor, and rename `policy_version` to `source_version` under schema version 2. Keep `source_id` stable for updated documents; content hashes and chunk IDs must change.

- [x] **Step 5: Create five discriminating evaluation cases**

Each JSON object must contain:

```json
{
  "case_id": "multi_fact_wifi",
  "query": "Can contractors expense hotel Wi-Fi and when is approval required?",
  "relevant_source_ids": ["travel-current", "contractor-scope", "approval-matrix"],
  "forbidden_source_ids": ["finance-memo-obsolete"],
  "required_phrases": ["contractor", "$50"],
  "corpus_version": "v1"
}
```

Include one multi-fact case, one exact identifier, one semantic paraphrase, one obsolete-source trap, and one version-change case.

- [x] **Step 6: Define the fixed experiment configuration**

`config/experiment.json` must explicitly name chunk size/overlap, top-k, rerank-k, context budget, stable tie-break rule, embedding model, generation model, temperature 0, prompt hash, and active `release_id`. No framework default that can affect results may remain implicit.

- [x] **Step 7: Verify and commit**

Run JSON parsing and SHA-256 checks over every corpus/config/eval file. Confirm v1 has six files and v2 has five. Commit:

```bash
git add week2/rag-framework-investigation/{config,corpus,eval,evidence}
git commit -m "testdata(rag-study): add hypotheses and versioned corpus"
```

## Task 3: Implement shared identity, trace, and release contracts with tests

**Time box:** 90 minutes

**Files:**

Create: `src/rag_compare/contracts.py`

Create: `src/rag_compare/identity.py`

Create: `src/rag_compare/trace.py`

Create: `src/rag_compare/release.py`

Test: `tests/test_identity.py`

Test: `tests/test_trace_contract.py`

Test: `tests/test_release.py`

- [x] **Step 1: Write failing stable-identity tests**

Assert that the same source ID and bytes produce the same document/chunk IDs; changed bytes change content and chunk IDs; source ID remains stable; and IDs do not depend on framework name.

- [x] **Step 2: Implement identity functions**

Use SHA-256 over canonical UTF-8 inputs:

```python
def digest(*parts: str) -> str:
    payload = "\x1f".join(parts).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()

def document_id(source_id: str, source_bytes_sha256: str) -> str:
    return digest("document", source_id, source_bytes_sha256)

def chunk_id(document_id_value: str, start: int, end: int, text: str) -> str:
    return digest("chunk", document_id_value, str(start), str(end), text)
```

- [x] **Step 3: Write the trace schema test before implementation**

Construct one event for every required stage and assert all fields from the design are present, `duration_ms >= 0`, IDs are lists, resolved configuration is serializable, and a release ID cannot be empty.

- [x] **Step 4: Implement append-only JSONL tracing**

Use a frozen `StageEvent` dataclass and write each event with sorted JSON keys. Flush and `os.fsync` after every event so a failed run preserves evidence.

- [x] **Step 5: Write release validation tests**

Tests must cover:

complete v1 validates;

half of v2 fails expected-file/hash/count validation;

schema or embedding identity mismatch fails;

failed validation never changes `active.json`;

successful promotion uses one atomic replacement;

a query captures one active release and rejects chunks from any other release.

- [x] **Step 6: Implement release validation and atomic promotion**

Promotion must write a temporary pointer in the same directory, flush and fsync, then call `os.replace(temp_path, active_path)`. It must refuse promotion unless validation_status == "passed" and all manifest fields match observed build artifacts.

- [x] **Step 7: Run focused tests and commit**

```bash
.venv/bin/python -m pytest tests/test_identity.py tests/test_trace_contract.py tests/test_release.py -q
```

Expected: all tests pass. Commit only these contracts and tests.

## Task 4: Reverse-engineer both real execution paths before adapter implementation

**Files:**

Create: `evidence/source-references.md`

Create: `evidence/provenance-matrix.csv`

Update: `evidence/ledger.csv`

Update: `evidence/hypotheses.md`

- [x] **Step 1: Start from one public observable capability per path**

For each framework, locate the documented/public call that indexes documents and the call that executes retrieval. Record these entry points first; do not begin with directory summaries.

- [x] **Step 2: Trace index-time ownership**

Follow public call -> parser/converter -> splitter -> identity assignment -> embedding -> store. Record class/function, exact SHA-linked line, input/output types, defaults, configuration resolution, state writes, tests, callbacks, and recovery behavior.

- [x] **Step 3: Trace query-time ownership**

Follow public query call -> configuration -> retrieval/filtering/scoring -> reranking -> packing -> generation -> citation. Record the same evidence fields.

- [x] **Step 4: Audit hidden/default state explicitly**

Search and inspect LlamaIndex `Settings`, transformations, callbacks, storage context, caches, and serialization. Inspect Haystack component defaults, pipeline wiring, stores, filters, concurrency, serialization, and tracing. Record environment-variable reads and defaults for chunking, top-k, scores, embeddings, and metadata filters.

- [x] **Step 5: Complete the provenance matrix**

Create one row per framework/stage/field. Mark each of the design's 12 identity and provenance fields as `preserved`, `transformed`, `synthesized`, or `lost`, with an evidence ID.

- [x] **Step 6: Reach the minimum evidence breadth**

Capture at least 12 commit-bound references, balanced across frameworks and spanning implementation, tests, and configuration. Capture two history, issue, or ADR references. Triangulate every paper-level architectural claim with two evidence forms when possible.

- [x] **Step 7: Record counterevidence**

Actively test the rejection condition for the current favored hypothesis. Update at least one hypothesis to `WEAKENED` or `REJECTED` only when a cited source or runtime artifact justifies it.

- [x] **Step 8: Commit the source reconstruction**

```bash
git add week2/rag-framework-investigation/evidence
git commit -m "docs(rag-study): trace framework execution and provenance"
...
```

## Task 5: Implement the framework adapters and observable stages

**Time box:** 120 minutes

**Files:**

Create: `src/rag_compare/adapters/base.py`

Create: `src/rag_compare/adapters/llamaindex_adapter.py`

Create: `src/rag_compare/adapters/haystack_adapter.py`

Create: `src/rag_compare/ollama.py`

Create: `src/rag_compare/rerank.py`

Test: `tests/test_rerank.py`

Test: `tests/test_adapters.py`

- [ ] **Step 1: Define the shared adapter contract**

Both adapters must implement `build_release(corpus_path, manifest, trace)` and `query(query_text, retriever_kind, active_release, trace)`. Returned candidates must normalize to source/document/chunk IDs, text, span, score, rank, metadata, and release ID.

- [ ] **Step 2: Test deterministic reranking before implementation**

Test lowercase tokenization, query-term coverage score, stable tie-break by incoming rank then chunk ID, and preservation of original retrieval score/rank.

- [ ] **Step 3: Implement the fixed reranker and context packer**

The reranker may only reorder retrieved candidates. The packer admits complete chunks until the configured character/token approximation budget is reached and records rejection reasons; it must not truncate chunks.

- [ ] **Step 4: Implement the LlamaIndex adapter using verified source APIs**

Use the exact public classes traced in Task 4. Set every retrieval-affecting value explicitly rather than relying on `Settings`; snapshot resolved settings into each stage event. Support BM25 and dense retrieval over the same normalized chunks and enforce `release_id` filtering.

- [ ] **Step 5: Implement the Haystack adapter using verified source APIs**

Use the exact components traced in Task 4. Configure converter/splitter, in-memory stores, BM25, dense retrieval, filters, and Ollama components explicitly. Emit one stage event at each component boundary and enforce the same release filter.

- [ ] **Step 6: Test contract equivalence**

For both adapters assert stage order is identical, all trace fields exist, all chunks carry active release and provenance fields, citations resolve to corpus spans, and changing the active release between query start and retrieval cannot mix releases.

- [ ] **Step 7: Run adapter tests and commit**

```bash
.venv/bin/python -m pytest tests/test_rerank.py tests/test_adapters.py -q
```

Expected: all pass with Ollama running.

## Task 6: Run the controlled experiment

**Time box:** 60 minutes

**Files:**

Create: `src/rag_compare/metrics.py`

Create: `src/rag_compare/run_experiment.py`

Create: `artifacts/results/controlled-results.csv`

Create: `artifacts/results/controlled-summary.json`

- [ ] **Step 1: Implement deterministic metrics**

Compute recall@k, MRR, forbidden-source violation, citation source correctness, citation span correctness, per-stage latency, total latency, and release consistency. Persist per-case values; do not collapse them into one score.

- [ ] **Step 2: Freeze the run manifest before execution**

Hash repository/environment manifests, experiment configuration, corpus manifest, evaluation cases, and prompt. Give the run a unique `run_id`; copy the resolved manifest into `artifacts/raw/<run_id>/`.

- [ ] **Step 3: Execute the 2x2 experiment**

Run both frameworks with BM25 and dense retrieval while holding every other variable fixed. Save raw stdout/stderr, JSONL traces, retrieved candidates, packed context, model output, citations, and metrics for every case.

- [ ] **Step 4: Verify the experiment control**

Compare run manifests programmatically. The only allowed material differences within a framework pair are `retriever_kind` and retriever-specific index data. Fail the run summary if corpus, parser/chunker config, reranker, generator, prompt, cases, or active release differs.

- [ ] **Step 5: Commit code and sanitized result summaries**

Raw artifacts may be included if small and sanitized; never commit model caches, virtual environments, or vendor repositories.

## Task 7: Execute the partial-release failure injection

**Time box:** 60 minutes

**Files:**

Create: `tests/test_failure_injection.py`

Create: `artifacts/results/failure-injection.json`

Create: `artifacts/raw/failure-injection-trace.jsonl`

- [ ] **Step 1: Write the failing end-to-end test**

The test activates v1, indexes only the first half of v2 into a staging namespace, attempts promotion, queries all evaluation cases, and asserts promotion fails, the pointer remains v1, and every returned chunk is v1.

- [ ] **Step 2: Run the test before any corrective change**

If mixed-version data appears, preserve that first failure as the runtime failure-injection artifact. Do not overwrite it with the later passing trace.

- [ ] **Step 3: Apply the release controls from Task 3**

Require expected file hashes/counts/schema/embedding identity and filter every retrieval branch by the release captured at query start.

- [ ] **Step 4: Prove rejection, recovery, and promotion**

Run partial v2 and observe rejection; complete v2; validate; promote atomically; query again; assert every result is v2 and deleted v1 content cannot be returned.

- [ ] **Step 5: Save evidence and commit**

The result JSON must include expected behavior, observed behavior, commands, pointer values before/after, manifest hashes, assertion results, and artifact paths.

## Task 8: Write the decision-ready paper and required visuals

**Time box:** 210 minutes

**Files:**

Create: `paper/insights-paper.md`

Create: `paper/decision.adr.md`

Create: `paper/architecture.mmd`

Create: `paper/hypothesis-evidence.md`

Create: `paper/experiment-results.md`

Create: `paper/risk-control.md`

Update: `week2/AI_COLLABORATION.md`

- [ ] **Step 1: Write the executive claim last, but place it first**

Keep it 150-250 words and state the production decision, most important finding, confidence, and consequence. Do not open with framework history.

- [ ] **Step 2: Complete every required paper section**

Use the exact required order from the problem statement. Every architectural or experimental claim must cite an evidence ID or artifact. Explicitly distinguish facts, interpretations, hypotheses, counterevidence, and unknowns.

- [ ] **Step 3: Produce the four required visuals/tables**

The architecture sequence must show index-time and query-time ownership plus the release boundary. The other three artifacts must be generated from the ledger or result files, not reconstructed from memory.

- [ ] **Step 4: Write the ADR**

Choose `adopt`, `adapt`, `combine`, `avoid`, or `investigate`; state alternatives, consequences, reversibility, and next evidence worth buying. Separate framework findings from the framework-independent release recommendation.

- [ ] **Step 5: Complete the AI-use disclosure**

Record material prompts/instructions, tools/models, suggestions accepted or rejected, verification method, and residual uncertainty. Do not claim AI output as source or runtime evidence.

- [ ] **Step 6: Validate word count and evidence minimums**

The paper body must be 3,000-4,500 words excluding appendices. Check for at least 12 commit-bound references, two runtime artifacts, one failure result, two history/issue/ADR references, one counterexample, and one rejected explanation.

## Task 9: Reproduce, sanitize, package, and verify

**Time box:** 60 minutes plus 30-minute buffer

**Files:**

Create: `README.md`

Create: `scripts/package_submission.py`

Create: `submission/rag-framework-investigation.zip`

- [ ] **Step 1: Write exact reproduction commands**

README must cover environment creation, Ollama model installation, dependency installation, repository SHA checkout, unit tests, pipeline build, controlled experiment, failure injection, paper artifact generation, and packaging.

- [ ] **Step 2: Run the complete verification suite from a clean shell**

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m rag_compare.run_experiment --config config/experiment.json
```

Expected: all tests pass, all four conditions finish, no release-consistency failure, and raw/summary artifacts are produced.

- [ ] **Step 3: Implement safe packaging**

Use Python zipfile with an explicit allowlist. Reject any path containing `.env`, `.venv`, `node_modules`, caches, credentials, vendor clones, generated build folders, or files above the chosen artifact-size limit. Include the README, manifests, source, tests, corpus, cases, evidence, sanitized artifacts, paper, tables/diagram source, ADR, and disclosure.

- [ ] **Step 4: Verify the ZIP mechanically**

Open it with `ZipFile.testzip()`, assert the required file list, scan member names for exclusions, extract to a temporary directory, and parse every JSON/CSV file. Save the ZIP SHA-256 and verification output beside the archive.

- [ ] **Step 5: Perform final scope and integrity review**

Confirm no fabricated citations/results, no README-only architectural claims, no missing evidence IDs, no secrets, no uncommitted required files, and no unrelated course materials in the archive.

- [ ] **Step 6: Commit the completed investigation**

```bash
git add week2/rag-framework-investigation
git commit -m "feat(rag-study): complete LlamaIndex and Haystack investigation"
```

## Final acceptance checklist

- [ ] Exact URLs, SHAs, access date, licenses, Python/package/Ollama versions and model digests are recorded.

- [ ] Three hypotheses predate source tracing and include rejection conditions.

- [ ] Both index-time and query-time paths are traced with concrete ownership.

- [ ] Hidden configuration/default state is audited for both frameworks.

- [ ] Provenance is classified at every stage for all 12 required fields.

- [ ] 12+ balanced commit-bound references span implementation/tests/config.

- [ ] 2+ history/issue/ADR references support inferred design drivers.

- [ ] Controlled experiment changes only the retriever.

- [ ] At least two raw runtime artifacts and per-case metrics are preserved.

- [ ] Partial v2 cannot promote or appear in answers; complete v2 can.

- [ ] One hypothesis is rejected or weakened by counterevidence.

- [ ] Paper, ADR, four required visuals/tables, and AI disclosure are complete.

- [ ] Another engineer can trace one answer from source bytes to final citation.

- [ ] All tests and reproduction commands pass.

- [ ] ZIP opens, contains required artifacts, excludes prohibited content, and has a recorded SHA-256.
