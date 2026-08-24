# Task Prompt → Artifact Map

Each row links the material task prompt in this directory to the artifacts it
produced inside `week2/rag-framework-investigation/` (paths relative to that
directory unless noted). Model and token records for every task are maintained
in [`../AI_COLLABORATION.md`](../AI_COLLABORATION.md) (section "Model and
token accounting"); fields not exposed by the tool are marked `unavailable`
there rather than estimated.

| Prompt | Task | Primary artifacts produced |
|---|---|---|
| [task-1.md](task-1.md) | Freeze repositories, runtime, and Ollama models | `pyproject.toml`, `requirements.txt`, `scripts/freeze_environment.sh`, `config/environment-manifest.json`, `config/repository-manifest.json`, `artifacts/raw/environment-freeze.txt` |
| [task-2.md](task-2.md) | Hypotheses, ledger, corpus, evaluation contract | `evidence/hypotheses.md`, `evidence/ledger.csv`, `corpus/v1/` + `corpus/v1/manifest.json`, `corpus/v2/` + `corpus/v2/manifest.json`, `eval/cases.json`, refreshed `artifacts/raw/environment-freeze.txt` |
| [task-3.md](task-3.md) | Shared identity, trace, release contracts | `src/rag_compare/contracts.py`, `src/rag_compare/identity.py`, `src/rag_compare/trace.py`, `src/rag_compare/release.py`; `tests/test_identity.py`, `tests/test_trace_contract.py`, `tests/test_release.py` |
| [task-4.md](task-4.md) | Reverse-engineer both execution paths | `evidence/provenance-matrix.csv`, `evidence/source-references.md`, updated `evidence/hypotheses.md`, adapter design recorded in `ARCHITECTURE.md` (week2 root) |
| [task-5.md](task-5.md) | Framework adapters and observable stages | `src/rag_compare/adapters/base.py`, `src/rag_compare/adapters/haystack_adapter.py`, `src/rag_compare/adapters/llamaindex_adapter.py`, `src/rag_compare/metrics.py`, `src/rag_compare/ollama.py`, `src/rag_compare/rerank.py`, `tests/test_adapters.py`, `tests/test_rerank.py`, corrected model tags in `config/environment-manifest.json`, `artifacts/raw/environment-freeze-post-task5.txt` |
| [task-6.md](task-6.md) | Controlled experiment | `artifacts/results/controlled-results.csv`, `artifacts/results/controlled-summary.json`, canonical run `artifacts/raw/task6-20260824T064738/` (plus retained runs `task6-20260824T052921/`, `task6-20260823T190633/`, `task6-20260823T202231/`, `task6-20260823T203946/`), superseded lineage under `artifacts/raw/archive-*` |
| [task-7.md](task-7.md) | Partial-release failure injection | `artifacts/results/failure-injection.json`, `artifacts/results/failure-injection-haystack.json`, `artifacts/results/failure-injection-llamaindex.json`, traces `artifacts/raw/failure-injection-trace.jsonl`, `failure-injection-post-recovery-trace.jsonl`, per-adapter `failure-injection-haystack*-trace.jsonl` / `failure-injection-llamaindex*-trace.jsonl`; `tests/test_failure_injection.py` |
| [task-8-draft.md](task-8-draft.md) | Paper draft | `paper/insights-paper.md`, `paper/decision.adr.md`, `paper/architecture.mmd`, `paper/hypothesis-evidence.md`, `paper/experiment-results.md`, `paper/risk-control.md`, ledger rows EV-T8/EV-T9 |
| [task-8-review.md](task-8-review.md) | Paper review + citation-provenance corrections | Corrections applied to all `paper/*` files and ADR against canonical `artifacts/results/*` and pinned prompt hash in `config/experiment.json`; remediation commits recorded in [`../AI_COLLABORATION.md`](../AI_COLLABORATION.md#decision-log) |
| [task-9.md](task-9.md) | Reproduce, sanitize, package, verify | `README.md` (reproduction commands), `submission/rag-framework-investigation.zip`, `submission/verification.json`, clean-shell verification run `artifacts/raw/task6-20260823T203946/`, packaging script `scripts/package_submission.py` |

Supporting week2-root documents referenced by the prompts:
[`../PROBLEM_STATEMENT.md`](../PROBLEM_STATEMENT.md),
[`../PLAN.md`](../PLAN.md),
[`../ARCHITECTURE.md`](../ARCHITECTURE.md),
[`../TASKS.md`](../TASKS.md),
[`../AI_COLLABORATION.md`](../AI_COLLABORATION.md).
