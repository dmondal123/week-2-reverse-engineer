# AI Collaboration Log

## Purpose

This file records material human-AI collaboration: decisions, corrections, rejected assumptions, approval gates, and changes in direction. It is not a chat transcript. Entries must stay short, factual, and link to repository evidence.

## Recording rules

Update this file only after a significant decision, correction, failure investigation, changed direction, or reusable learning.

This is not a per-commit or per-task journal. If nothing significant happened, do not update this file.

Link claims to a repository file, evidence-ledger row, source reference, test, or runtime artifact.

Record rejected AI suggestions and human corrections, not just accepted ideas.

The final submission must include at least two cases where the agent was wrong or suboptimal. Each case must state what was wrong, how it was detected, and how it was corrected, with repository evidence.

Never invent token usage or rewrite the historic human-supplied totals below.

The Human records exact exposed task totals in the manual table below after the agent's final response.

Token fields mean: total uncached input tokens, cached input tokens, and output tokens for the material collaboration event being recorded. Use exact exposed metadata or 'unavailable'; never estimate missing values.

## Model and token accounting

Use a fresh interactive Codex session for each task. The task's final response asks the Human to record the exact counters exposed by Codex. The Human records them outside the completed turn and does not reply merely to return the numbers, because that would create additional usage. Material approvals, decisions, and corrections remain in this log.

The historical totals in this section and the decision rows below are preserved exactly as supplied by the Human.

| Field | Current value |
|---|---|
| AI product | OpenAI Codex |
| Model used for all work through 2026-08-18 | gpt-5.6-sol |
| Reasoning effort | Medium |
| Approved implementation models | `gpt-5.6-terra` and `gpt-5.6-luna`; `gpt-5.6-sol` prohibited |
| Implementation cached-input ceiling | 58,500,000 |
| Implementation token ceiling | 9,000,000 input + output: 7,200,000 assigned and 1,800,000 human-approved reserve |
| Token usage through current entry | total 4,23,081; input=3,84,536 (+27,02,643 cached); output=38,545 (reasoning 12,595) |
| Cache hit rate through current entry | 95.4% |
| Input tokens | 3,84,536 |
| Output tokens | 38,545 (including 12,595 reasoning) |
| Cached input tokens | 27,02,643 |

### Manual task token records

Human-maintained task totals belong here. Record `unavailable` when Codex does not expose a field; never infer a value. Reserve approvals remain separate material decision-log entries.

| Task | Model | Uncached input | Cached input | Output including reasoning | Total | Human note |
|---|---|---|---|---|---|---|
| 1 | `gpt-5.6-luna` medium | 95,324 | 21,04,470 | 20,584 (reasoning 7,960) | 1,15,908 | Human-supplied exact counters |
| 2 | `gpt-5.6-luna` medium | 1,15,302 | 15,12,418 | 20,286 (reasoning 5,647) | 1,35,588 | Human-supplied exact counters |
| 3 | `gpt-5.6-terra` medium | 88,081 | 42,78,506 | 21,683 (reasoning 5,331) | 1,09,764 | Human-supplied exact counters |
| 4 | `gpt-5.6-terra` medium | | | | | |
| 5 | `gpt-5.6-terra` medium | | | | | |
| 6 | `gpt-5.6-luna` medium | | | | | |
| 7 | `gpt-5.6-terra` medium | | | | | |
| 8 draft | `gpt-5.6-luna` medium | | | | | |
| 8 review | `gpt-5.6-terra` medium | | | | | |
| 9 | `gpt-5.6-luna` medium | | | | | |

## Decision log

| Date | Type | Human/AI decision or correction | Repository evidence | Model | Input | Cached input | Output |
|---|---|---|---|---|---|---|---|
| 2026-08-18 | Constraint | Human limited the work to approximately 15 hours ending Sunday midnight. AI reduced scope to a thin vertical comparison. | [`PLAN.md`](PLAN.md#milestones) | gpt-5.6-sol (medium) | unavailable | unavailable | unavailable |
| 2026-08-18 | Constraint | Human required Ollama for all model calls. Hosted embedding, generation, reranking, and judge APIs were excluded. | [`ARCHITECTURE.md`](ARCHITECTURE.md#constraints-and-non-goals) | gpt-5.6-sol (medium) | unavailable | unavailable | unavailable |
| 2026-08-18 | Decision | AI proposed comparing equivalent minimal pipelines rather than broad framework-native showcases or source-only analysis; human continued with plan review. | [`PLAN.md`](PLAN.md#strategy) | gpt-5.6-sol (medium) | unavailable | unavailable | unavailable |
| 2026-08-18 | Correction | Plan review found missing reverse-engineering depth: two execution paths, hidden-state audit, provenance matrix, discriminating hypotheses, triangulation, and counterevidence were added. | [`ARCHITECTURE.md`](ARCHITECTURE.md#reverse-engineering-protocol) | gpt-5.6-sol (medium) | unavailable | unavailable | unavailable |
| 2026-08-18 | Rejected assumption | The initial model recommendation was not treated as validated. The final plan requires an Ollama smoke/latency gate and records any fallback. | [`PLAN.md`](PLAN.md#decision-gates) | gpt-5.6-sol (medium) | unavailable | unavailable | unavailable |
| 2026-08-18 | Decision | The controlled variable was fixed as BM25 versus Ollama dense retrieval; reranking, corpus, generator, prompt, and evaluation cases remain constant. | [`ARCHITECTURE.md`](ARCHITECTURE.md#investigation-shape) | gpt-5.6-sol (medium) | unavailable | unavailable | unavailable |
| 2026-08-18 | Decision | Mixed-version prevention was moved outside both frameworks into immutable namespaces, validated manifests, release filtering, and atomic pointer promotion. | [`ARCHITECTURE.md`](ARCHITECTURE.md#release-mechanism) | gpt-5.6-sol (medium) | unavailable | unavailable | unavailable |
| 2026-08-18 | Approval gate | Human requested the reviewed reverse-engineering additions be incorporated into the final plan. | [`TASKS.md`](TASKS.md#final-acceptance-checklist) | gpt-5.6-sol (medium) | unavailable | unavailable | unavailable |
| 2026-08-18 | Correction | Human rejected an immediate commit. Planning files remain uncommitted until explicit approval. | [`AI_COLLABORATION.md`](AI_COLLABORATION.md) | gpt-5.6-sol (medium) | unavailable | unavailable | unavailable |
| 2026-08-18 | Direction change | Human required separate plan, architecture, task checklist, and AI collaboration files under `week2/`; AI reorganized the artifacts accordingly. | [`PLAN.md`](PLAN.md#supporting-documents) | gpt-5.6-sol (medium) | unavailable | unavailable | unavailable |
| 2026-08-18 | Decision | Human limited future updates to significant collaboration events and required at least two evidenced cases where the agent was wrong or suboptimal. | [`AI_COLLABORATION.md`](AI_COLLABORATION.md#recording-rules) | gpt-5.6-sol (medium) | unavailable | unavailable | unavailable |
| 2026-08-18 | Correction | Human identified that hybrid `qwen3:4b` thinks by default and `/no_think` is unreliable. The generator was changed to the dedicated Qwen3 4B Instruct 2507 model. | [`ARCHITECTURE.md`](ARCHITECTURE.md#investigation-shape) | gpt-5.6-sol (medium) | unavailable | unavailable | unavailable |
| 2026-08-18 | Correction | Human supplied the exact model metadata: all artifacts and recommendations through this entry were generated with `gpt-5.6-sol` using medium reasoning effort. | [`AI_COLLABORATION.md`](AI_COLLABORATION.md#model-and-token-accounting) | gpt-5.6-sol (medium) | unavailable | unavailable | unavailable |
| 2026-08-18 | Decision | Human supplied cumulative usage metadata through this entry: total 4,23,081; input=3,84,536 (+27,02,643 cached); output=38,545 (reasoning 12,595), with a 95.4% cache hit rate. | [`AI_COLLABORATION.md`](AI_COLLABORATION.md#model-and-token-accounting) | gpt-5.6-sol (medium) | 3,84,536 | 27,02,643 | 38,545 |
| 2026-08-18 | Constraint | Human reserved a fresh implementation budget for Terra and Luna only. Plan review reduced the initial 10,000,000-token proposal because it could exceed the originating $30 constraint; the enforceable ceiling is 9,000,000 input-plus-output tokens with 7,200,000 assigned, 1,800,000 requiring human approval, and cached input tracked separately. | [`PLAN.md`](PLAN.md#ai-assisted-execution-governance), [`TASKS.md`](TASKS.md#execution-ownership-dependencies-and-token-controls) | not applicable (human constraint) | unavailable | unavailable | unavailable |

## Agent errors and corrections

These cases satisfy the minimum requirement and must remain in the final submission unless stronger evidenced cases replace them.

| Case | What was wrong or suboptimal | How it was caught | Correction | Evidence |
|---|---|---|---|---|
| Incomplete reverse-engineering plan | The first thin-slice proposal covered the pipelines and failure injection but omitted a complete two-path trace, hidden/default-state audit, provenance matrix, hypothesis rejection conditions, and evidence triangulation. | A structured review mapped the proposal against the problem statement and found those reverse-engineering requirements only partially covered or missing. | The architecture and task checklist now require index-time and query-time traces, hidden-state inspection, stage-by-stage provenance, discriminating hypotheses, counterevidence, and balanced source/runtime evidence. | [`ARCHITECTURE.md`](ARCHITECTURE.md#reverse-engineering-protocol), [`TASKS.md`](TASKS.md#task-4-reverse-engineer-both-real-execution-paths-before-adapter-implementation) |
| Incorrect generation-model recommendation | The agent initially recommended hybrid `qwen3:4b` with thinking disabled. That depended on `/no_think` behaving reliably and would add latency and experimental variance if thinking remained active. | The human challenged the recommendation and explained that the dedicated Instruct model is non-thinking by design while the hybrid model defaults to thinking. | The plan now pins `qwen3:4b-instruct-2507-q4_K_M`, verifies non-thinking behavior in the smoke test, and prohibits hybrid `qwen3:4b` as the fallback. | [`PLAN.md`](PLAN.md#decision-gates), [`ARCHITECTURE.md`](ARCHITECTURE.md#investigation-shape), [`TASKS.md`](TASKS.md#task-1-freeze-repositories-runtime-and-ollama-models) |
| Planning artifacts conflated | The initial final plan was primarily a long task checklist, so strategy, architecture, execution steps, and collaboration governance were not independently maintainable. | Human review explicitly identified the plan as a checklist and requested four separate documents. | The material was reorganized into `PLAN.md`, `ARCHITECTURE.md`, `TASKS.md`, and this collaboration log, each with a single responsibility. | [`PLAN.md`](PLAN.md#supporting-documents), [`ARCHITECTURE.md`](ARCHITECTURE.md), [`TASKS.md`](TASKS.md) |

## Entry template

Append future entries using this row shape:

```markdown
| YYYY-MM-DD | Decision / Correction / Rejected assumption / Approval gate / Direction change | One factual sentence describing the material collaboration event. | [Evidence](relative/path#section) | Exact model or 'unavailable' | N or unavailable | N or unavailable | N or unavailable |
```

| 2026-08-22 | Decision | Human confirmed the two approved runtime models are custom Hugging Face imports exposed through Ollama; the accidental `qwen3-4b-hf:latest` model is excluded. | [`config/environment-manifest.json`](rag-framework-investigation/config/environment-manifest.json) | unavailable | unavailable | unavailable | unavailable |
| 2026-08-22 | Evidence | Human supplied successful local smoke output for the approved models: a 768-dimensional numeric embedding and 'OK' generation in 3.51 seconds with thinking: null. | [`config/environment-manifest.json`](rag-framework-investigation/config/environment-manifest.json) | unavailable | unavailable | unavailable | unavailable |
| 2026-08-22 | Decision | Human approved preserving the original laptop freeze and recording a later laptop run as a separate comparative artifact for final submission portability. | [`config/repository-manifest.json`](rag-framework-investigation/config/repository-manifest.json) | unavailable | unavailable | unavailable | unavailable |
| 2026-08-22 | Correction | The execution sandbox could not reach the user's running localhost Ollama service; the freeze artifact records that unavailable observation, and no fresh sandbox failure is represented as a smoke-test pass. | [`artifacts/raw/environment-freeze.txt`](rag-framework-investigation/artifacts/raw/environment-freeze.txt) | unavailable | unavailable | unavailable | unavailable |
| 2026-08-22 | Correction | The supplied framework directories were initially treated as independent clones, but Git inspection showed both resolve to the parent repository's `.git`; the repository manifest now labels their SHA/remote metadata as user-supplied and locally unverified. | [`config/repository-manifest.json`](rag-framework-investigation/config/repository-manifest.json) | unavailable | unavailable | unavailable | unavailable |
| 2026-08-22 | Approval gate | Human chose to defer canonical cloning and dependency verification to the submission laptop; this checkout is reported as a local-only partial Task 1 checkpoint. | [`TASKS.md`](TASKS.md#task-1-freeze-repositories-runtime-and-ollama-models) | unavailable | unavailable | unavailable | unavailable |
| 2026-08-22 | Approval gate | Human approved the Task 2 hypotheses, synthetic corpus, evaluation cases, and environment-freeze refresh after independent structural and source-grounding checks. | [`rag-framework-investigation/evidence/hypotheses.md`](rag-framework-investigation/evidence/hypotheses.md), [`rag-framework-investigation/eval/cases.json`](rag-framework-investigation/eval/cases.json), [`rag-framework-investigation/artifacts/raw/environment-freeze.txt`](rag-framework-investigation/artifacts/raw/environment-freeze.txt) | unavailable | unavailable | unavailable | unavailable |
| 2026-08-22 | Evidence | Task 3 Codex assistance created framework-independent identity, frozen append-only trace, and immutable release contracts; the focused suite passed 105 tests with no runtime model call and no commit. | [`rag-framework-investigation/tests/test_identity.py`](rag-framework-investigation/tests/test_identity.py), [`rag-framework-investigation/tests/test_trace_contract.py`](rag-framework-investigation/tests/test_trace_contract.py), [`rag-framework-investigation/tests/test_release.py`](rag-framework-investigation/tests/test_release.py) | gpt-5.6-terra and gpt-5.6-luna (medium) | unavailable | unavailable | unavailable |
| 2026-08-23 | Correction | The OCR-mangled planning Markdown (PLAN, ARCHITECTURE, TASKS, AI_COLLABORATION, prompts) was conservatively cleaned: broken tables, fences, links, and adjacent duplicate fragments were repaired with meaning preserved. | [`PLAN.md`](PLAN.md), [`ARCHITECTURE.md`](ARCHITECTURE.md), [`TASKS.md`](TASKS.md) | unavailable | unavailable | unavailable |
| 2026-08-23 | Evidence | The four OCR-mangled modules in `src/rag_compare` were reconstructed and verified: all compile, ruff check/format pass, and a smoke exercise of identity, immutable trace lists, JSONL tracing, release validation, atomic promotion, pointer capture, mixed-release rejection, and tampered-hash rejection succeeded. A discovered-path symlink bug in `_discovered_corpus_files` was fixed to relativize against the resolved release directory. | [`src/rag_compare/release.py`](src/rag_compare/release.py), [`src/rag_compare/contracts.py`](src/rag_compare/contracts.py) | unavailable | unavailable | unavailable |
| 2026-08-23 | Decision | Tooling baseline established: populated the empty `pyproject.toml` (src-layout package, pytest and ruff config), added `requirements.txt` (pytest, ruff), created `week2/.venv`, and installed the package editable. Deviation noted: the venv resolved to Python 3.14.6 instead of the planned 3.12.x, so Task 1 Step 1 acceptance remains unclaimed. | [`pyproject.toml`](pyproject.toml), [`requirements.txt`](requirements.txt) | not applicable (local tooling) | unavailable | unavailable | unavailable |
