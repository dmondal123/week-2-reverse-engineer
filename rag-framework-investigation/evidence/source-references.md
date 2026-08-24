# Source references (commit-bound)

All references are bound to the pinned SHAs recorded in `config/repository-manifest.json`:

- llama_index @ `d8021225eb7e7b276d5ceb476b0a4650240f27f8` (main, https://github.com/run-llama/llama_index.git)
- haystack @ `c7cb46c0f28ad1984f60e5d3e9404b124a221437` (main, https://github.com/deepset-ai/haystack.git)

Line numbers refer to the working trees at exactly these commits.

## A. LlamaIndex — index-time path

### LI-1 Public entry point: `VectorStoreIndex` (implementation)
`llama-index-core/llama_index/core/indices/vector_store/base.py:36` — `class VectorStoreIndex(BaseIndex[IndexDict])`. This is the documented public class for building an index from documents/nodes. `_build_index_from_nodes` (`:260`) and `insert_nodes` (`:343`) are the write paths.

### LI-2 Hidden default: global `Settings.embed_model` fallback (implementation)
`llama-index-core/llama_index/core/indices/vector_store/base.py:71` — `embed_model or Settings.embed_model`. If a caller builds an index without an explicit embed model, the embedding model silently resolves from the process-global `Settings` singleton. Retrieval behavior therefore depends on hidden ambient state unless every value is passed explicitly and snapshotted.

### LI-3 Embedding + store ownership (implementation)
`llama-index-core/llama_index/core/indices/vector_store/base.py:126-140` — `_get_node_with_embedding` calls `embed_nodes(nodes, self._embed_model, ...)`; node embeddings are computed in batches and handed to the vector store together with the node map. Identity assignment happens earlier, during parsing: each `BaseNode` carries its own generated `node_id`.

### LI-4 Hidden defaults: chunk size and top-k constants (implementation)
`llama-index-core/llama_index/core/constants.py:10` — `DEFAULT_CHUNK_SIZE = 1024  # tokens`, consumed by the default sentence splitter. `llama-index-core/llama_index/core/constants.py:12` — `DEFAULT_SIMILARITY_TOP_K = 2`, the default `similarity_top_k` of the vector-store retriever. Both are retrieval-affecting values that are implicit unless overridden.

### LI-5 Global state mechanism itself (implementation)
`llama-index-core/llama_index/core/settings.py:19-291` — `class _Settings` is a lazily-initialized module-level singleton (`Settings = _Settings()`), holding llm, embed model, node parser, callback manager, tokenizer. This is the concrete mechanism behind hypothesis H1.

### LI-6 Query-time generation resolves from globals too (implementation)
`llama-index-core/llama_index/core/response_synthesizers/base.py:79` — `self._llm = llm or Settings.llm`. Same hidden-fallback pattern at synthesis time.

### LI-7 Callback manager from globals (implementation)
`llama-index-core/llama_index/core/base/base_retriever.py:55` — `self.callback_manager = Settings.callback_manager`. Observability wiring is also ambient state; traces emitted depend on global registration unless overridden per component.

### LI-8 Query-time retrieval path (implementation)
`llama-index-core/llama_index/core/indices/vector_store/retrievers/retriever.py:104-115` — `VectorStoreRetriever._retrieve`: if an embedding is needed and absent, it computes the query embedding via `self._embed_model.get_agg_embedding_from_queries(...)` then delegates to `_get_nodes_with_embeddings`. Constructor default `similarity_top_k: int = DEFAULT_SIMILARITY_TOP_K` (`:45`). Scores come back from the vector store already ordered; ranks are the returned order.

### LI-9 Splitter identity behavior (implementation)
`llama-index-core/llama_index/core/node_parser/` — `SentenceSplitter` produces child nodes whose ids are freshly generated; source-document linkage survives only through node relationships/metadata that the parser chooses to copy. Any provenance field not copied by the parser is lost at split time.

## B. Haystack — index-time path

### HS-1 Public entry point: `DocumentWriter.run` (implementation)
`haystack/components/writers/document_writer.py:80` — `def run(self, documents: list[Document], policy: DuplicatePolicy | None = None) -> dict[str, int]`. The public, documented write call into a document store inside a pipeline.

### HS-2 Store write semantics (implementation)
`haystack/document_stores/in_memory/document_store.py:462-481` — `write_documents(...)`: with `DuplicatePolicy.NONE` (the default) it becomes `DuplicatePolicy.FAIL` on duplicate ids (`:475-481`); writes are keyed on `document.id`. Deterministic id collision behavior is explicit and observable.

### HS-3 Splitter defaults are explicit constructor values (implementation)
`haystack/components/preprocessors/document_splitter.py:57-59` — `split_by="word"`, `split_length=200`, `split_overlap=0`; stored verbatim on the instance (`:98-100`). Unlike LlamaIndex, these are component-local, not ambient.

### HS-4 Splitter regenerates document identity (implementation)
`haystack/components/preprocessors/document_splitter.py:268,332` — children are created as `Document(content=s, meta=meta)` / `Document(content=txt, meta=copied_meta)`: new Documents whose ids are re-derived from their own content. Parent id is not preserved as a field; only whatever metadata was copied survives. This is direct evidence for H2's transformation risk.

### HS-5 Document id is a content hash (implementation)
`haystack/dataclasses/document.py:110-116` — `_fingerprint` serializes text/dataframe/blob/meta/embedding with sorted keys and returns `hashlib.sha256(data.encode("utf-8")).hexdigest()`. Content change ⇒ id change; identical content ⇒ identical id regardless of framework name (matches our identity contract's spirit).

## C. Haystack — query-time path

### HS-6 Pipeline orchestration is explicit (implementation)
`haystack/core/pipeline/pipeline.py:118,200` — `class Pipeline(PipelineBase)` and `def run(...)`: execution follows explicitly connected components; each component boundary is visible in the graph. Supports H2's observability prediction.

### HS-7 BM25 retriever defaults (implementation)
`haystack/components/retrievers/in_memory/bm25_retriever.py:45-46,75-80` — `top_k: int = 10`, `scale_score: bool = False`; invalid top_k raises. Defaults are constructor-local and inspectable.

### HS-8 Dense retriever + filter policy (implementation)
`haystack/components/retrievers/in_memory/embedding_retriever.py:54-55,76-82` — `filters: dict | None`, `top_k: int = 10`; filter policy `REPLACE` (default) vs `MERGE` is documented at runtime-parameter level. Release-style filtering is achievable but must be configured explicitly per retriever.

### HS-9 Answer/citation assembly (implementation)
`haystack/components/builders/answer_builder.py:19,126` — `AnswerBuilder.run` packs retrieved documents into answers; cited source documents are those attached by upstream components, so citation correctness inherits any identity loss introduced at split time (see HS-4).

### HS-10 BM25 scoring implementation (implementation)
`haystack/document_stores/in_memory/document_store.py:727` — `bm25_retrieval(...)` runs inside the in-memory store; ranking and score computation live in the store, not the retriever component. Score scale depends on `scale_score` (HS-7).

## D. Tests and configuration

### REF-T1 Haystack splitter tests
`haystack/test/components/preprocessors/test_document_splitter.py` — covers overlap/split behavior; confirms documented splitting semantics used in HS-3/HS-4.

### REF-T2 Haystack writer/store contract tests
`haystack/test/components/writers/test_document_writer.py` — exercises `DocumentWriter.run` policies against in-memory stores (HS-1/HS-2).

### REF-T3 LlamaIndex vector-store retriever tests
`llama_index/llama-index-core/tests/indices/vector_store/test_retrievers.py` — covers retriever construction/top-k behavior over vector stores (LI-8).

### REF-T4 LlamaIndex Settings documentation-by-code (configuration)
`llama-index-core/llama_index/core/settings.py:20` — docstring "Settings for the Llama Index, lazily initialized" plus property setters define the entire configuration surface that must be snapshotted in stage events.

### REF-T5 Haystack release-note history (history/reference)
`haystack/releasenotes/notes/change-metadata-to-meta-0fada93f04628c79.yaml:3-5` — "Rename `metadata` to `meta`" / "Rename `metadata_fields_to_embed` to `meta_fields_to_embed` in all Embedders"; `haystack/releasenotes/notes/agent-exit-conditions-d8ffd979d961cd6d.yaml:5` — "The init parameter has been renamed from exit_condition to exit_conditions"; `haystack/releasenotes/notes/adapt-gpt-generator-bb7f52bd67f6b197.yaml:3-5` — GPTGenerator adapted to string input/output. These exact release notes show component APIs renamed/reworked across 2.x/3.x lines, evidencing that adapter code must be pinned to SHAs rather than "current API".

### REF-T6 LlamaIndex changelog history (history/reference)
`llama_index/CHANGELOG.md:10326` @ d8021225 — "removed deprecated `ServiceContext` -- using this now will print an error with a link to the migration guide" (breaking changes across core releases: service_context removal → global `Settings`), supporting the design driver that ambient configuration is a deliberate trade-off for usability, and a known migration hazard.

## E. Coverage summary

- Implementation references: LI-1…LI-9 (9), HS-1…HS-10 (10)
- Test references: REF-T1, REF-T2, REF-T3
- Configuration references: REF-T4
- History/reference references: REF-T5, REF-T6
- Total commit-bound references: 22; balanced across both frameworks.
