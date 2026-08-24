# LlamaIndex vs Haystack: decision-ready RAG framework investigation

Reproducible investigation comparing two RAG frameworks under one shared pipeline contract, with an
immutable, externally-validated release mechanism that provably prevents mixed-version answers.

- **Paper:** [`paper/insights-paper.md`](paper/insights-paper.md) (executive claim first)
- **ADR:** [`paper/decision.adr.md`](paper/decision.adr.md)
- **Visuals/tables:** [`paper/architecture.mmd`](paper/architecture.mmd),
  [`paper/hypothesis-evidence.md`](paper/hypothesis-evidence.md),
  [`paper/experiment-results.md`](paper/experiment-results.md),
  [`paper/risk-control.md`](paper/risk-control.md)
- **Evidence:** [`evidence/ledger.csv`](evidence/ledger.csv),
  [`evidence/source-references.md`](evidence/source-references.md),
  [`evidence/provenance-matrix.csv`](evidence/provenance-matrix.csv),
  [`evidence/hypotheses.md`](evidence/hypotheses.md)

All commands below are run from `week2/rag-framework-investigation` unless noted.

## 1. Environment creation

Python 3.12+ virtual environment:

```bash
python3 -m venv .venv
.venv/bin/python --version   # must report 3.12+
```

## 2. Ollama installation and models

Install Ollama (https://ollama.com), start the server, then pull the two approved models:

```bash
ollama pull nomic-embed-text
ollama pull qwen3:4b-instruct-2507-q4_K_M
curl -s http://127.0.0.1:11434/api/embed -d '{"model":"nomic-embed-text","input":["ping"]}'
curl -s http://127.0.0.1:11434/api/generate -d '{"model":"qwen3:4b-instruct-2507-q4_K_M","prompt":"Reply with OK only","stream":false}'
```

Expected: a numeric embedding vector and a non-thinking "OK" response. The server must be running on
`127.0.0.1:11434`; every runtime model call in this project is Ollama-only.

## 3. Framework repositories at pinned SHAs

The adapters call public APIs verified at exact commits (`config/repository-manifest.json`):

```bash
git clone https://github.com/run-llama/llama_index.git ../llama_index
git clone https://github.com/deepset-ai/haystack.git ../haystack
git -C ../llama_index checkout d8021225eb7e7b276d5ceb476b0a4650240f27f8
git -C ../haystack    checkout c7cb46c0f28ad1984f60e5d3e9404b124a221437
```

## 4. Dependency installation

```bash
.venv/bin/pip install -e '.[dev,frameworks]'   # includes tiktoken + requests (direct deps of the shared layer)
.venv/bin/pip install -e '../llama_index'      # llama-index core + integrations
.venv/bin/pip install -e '../haystack'         # haystack-ai
```

Verify imports resolve inside `.venv` only:

```bash
.venv/bin/python -c 'import llama_index, haystack, requests, tiktoken; print("imports-ok")'
```

## 5. Unit tests

```bash
.venv/bin/python -m pytest -q
```

Expected: all tests pass. Adapter and failure-injection tests require a running Ollama server and are
skipped automatically when it is unreachable.

## 6. Pipeline build and controlled experiment (Task 6)

```bash
.venv/bin/python -m rag_compare.run_experiment
```

Runs all four conditions — `{llamaindex, haystack} × {bm25, ollama_dense}` — over the five fixed
evaluation cases, freezing a run manifest first and validating controls plus quality gates after.
Expected output: `status=passed`, `control_validation passed=True`, `quality_gates passed=True`,
and sanitized artifacts written to `artifacts/raw/task6-<run_id>/`,
`artifacts/results/controlled-results.csv`, `artifacts/results/controlled-summary.json`.

Optional manifest-freeze dry run: `.venv/bin/python -m rag_compare.run_experiment --dry-run`.

## 7. Failure injection (Task 7)

```bash
.venv/bin/python -m pytest tests/test_failure_injection.py -v
```

Executes the partial-v2 promotion attempt end-to-end (Ollama required), asserts rejection with the
active pointer untouched, proves single-release query isolation, then completes/promotes v2 atomically
and verifies deleted v1 content cannot resurface. Evidence lands in
`artifacts/results/failure-injection.json` and `artifacts/raw/failure-injection-trace*.jsonl`.

## 8. Paper artifact generation

Paper tables/diagram sources are generated from ledger/result artifacts (not from memory):

- `paper/experiment-results.md` ← `artifacts/results/*.json|csv`
- `paper/hypothesis-evidence.md` ← `evidence/hypotheses.md` + `evidence/ledger.csv`
- `paper/risk-control.md` ← failure-injection result + release source
- `paper/architecture.mmd` — Mermaid sequence diagram (render with any Mermaid tool,
  e.g. `npx -y @mermaid-js/mermaid-cli -i paper/architecture.mmd -o architecture.svg`)

## 9. Packaging

```bash
.venv/bin/python scripts/package_submission.py
```

Builds `submission/rag-framework-investigation.zip` from an explicit allowlist, rejects prohibited
paths (`.env`, `.venv`, caches, credentials, vendor clones, oversized files), verifies the archive
mechanically (`testzip()`, required-file list, exclusion scan, JSON/CSV parse of every member), and
writes `submission/verification.json` including the ZIP SHA-256.

## Layout

```
config/     frozen experiment + repository/environment manifests
corpus/     versioned synthetic corpus (v1: 6 docs, v2: 5 docs) with manifests
eval/       five discriminating evaluation cases
src/        rag_compare package (identity, trace, release, ollama, rerank, metrics,
            adapters/{base,llamaindex,haystack}, run_experiment)
tests/      unit + contract-equivalence + failure-injection suites
evidence/   pre-trace hypotheses, evidence ledger, provenance matrix, commit-bound references
artifacts/  raw traces/builds per run; sanitized results summaries
paper/      insights paper, ADR, diagram + table sources
scripts/    freeze_environment.sh, package_submission.py
```
