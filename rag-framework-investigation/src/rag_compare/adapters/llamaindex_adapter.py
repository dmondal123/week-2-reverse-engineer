"""LlamaIndex adapter using the public classes traced in Task 4 (LI-1..LI-9).

Every retrieval-affecting value (embed model, similarity_top_k, filters,
chunking) is passed explicitly; nothing resolves from the global ``Settings``
singleton (LI-2/LI-5/LI-6). Resolved values are snapshotted into stage events.
"""

from __future__ import annotations

import time
from collections.abc import Mapping
from pathlib import Path

from llama_index.core import VectorStoreIndex
from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core.schema import TextNode
from llama_index.core.vector_stores import (
    FilterOperator,
    MetadataFilter,
    MetadataFilters,
)
from llama_index.retrievers.bm25 import BM25Retriever

from rag_compare.adapters.base import (
    BaseAdapter,
    BuildResult,
    ReleaseNamespaceError,
    make_candidate,
)


class OllamaEmbeddingModel(BaseEmbedding):
    """Explicit embed_model wired to the shared Ollama HTTP client."""

    _model: str

    def __init__(self, client, model: str, **kwargs) -> None:
        super().__init__(model_name=model, **kwargs)
        self._client = client
        self._model = model

    @classmethod
    def class_name(cls) -> str:
        return "OllamaEmbeddingModel"

    def _get_query_embedding(self, query: str) -> list[float]:
        return self._client.embed(self._model, [query])[0]

    async def _aget_query_embedding(self, query: str) -> list[float]:
        return self._get_query_embedding(query)

    def _get_text_embedding(self, text: str) -> list[float]:
        return self._client.embed(self._model, [text])[0]

    async def _aget_text_embedding(self, text: str) -> list[float]:
        return self._get_text_embedding(text)


class LlamaIndexAdapter(BaseAdapter):
    framework = "llamaindex"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._embed_model = OllamaEmbeddingModel(
            self.client, self.embedding_model
        )
        # release_id namespace -> {"index": VectorStoreIndex, "nodes": [TextNode]}
        self._indexes: dict[str, dict] = {}

    def adapter_name(self) -> str:
        return "llamaindex_adapter"

    def store_component_name(self) -> str:
        return "VectorStoreIndex(_build_index_from_nodes)"

    def store_source_reference(self) -> str:
        return "LI-1 llama_index/core/indices/vector_store/base.py:36"

    # ---- build ---------------------------------------------------------------

    def build_release(
        self,
        corpus_path: str | Path,
        manifest: Mapping[str, object],
        trace,
    ) -> BuildResult:
        release_id = str(manifest["corpus_version"])

        def embed_stage(chunks, rid):
            return self._embed_chunks(chunks, rid, trace)

        def store_stage(chunks, rid):
            nodes = [
                TextNode(
                    id_=chunk["chunk_id"],
                    text=chunk["text"],
                    metadata={
                        "source_id": chunk["source_id"],
                        "document_id": chunk["document_id"],
                        "release_id": chunk["release_id"],
                        "span": chunk["span"],
                    },
                )
                for chunk in chunks
            ]
            # Explicit embed_model: avoids Settings.embed_model fallback (LI-2).
            index = VectorStoreIndex(
                nodes,
                embed_model=self._embed_model,
                insert_context=False,
                show_progress=False,
            )
            self._indexes[rid] = {"index": index, "nodes": nodes}

        return self._build_release_common(
            corpus_path, manifest, trace, embed_stage, store_stage, release_id
        )


    # ---- retrieval -------------------------------------------------------------

    def _release_filter(self, active_release: str) -> MetadataFilters:
        return MetadataFilters(
            filters=[
                MetadataFilter(
                    key="release_id",
                    value=active_release,
                    operator=FilterOperator.EQ,
                )
            ]
        )

    def retrieve_candidates(
        self, query_text: str, retriever_kind: str, active_release: str, trace
    ) -> list[dict]:
        started = time.perf_counter()
        namespace = self._indexes.get(active_release)
        if namespace is None:
            raise ReleaseNamespaceError(active_release)

        if retriever_kind == "bm25":
            # BM25Retriever over the same normalized nodes (explicit top_k/filters).
            retriever = BM25Retriever.from_defaults(
                nodes=namespace["nodes"],
                similarity_top_k=self.top_k,
                filters=self._release_filter(active_release),
            )
            sources = retriever.retrieve(query_text)
            component = "BM25Retriever.from_defaults"
            reference = (
                "LI-8 + rank_bm25 ext package "
                "(llama-index-retrievers-bm25), explicit similarity_top_k"
            )
            method = "bm25"
        elif retriever_kind == "ollama_dense":
            index = namespace["index"]
            retriever = index.as_retriever(
                similarity_top_k=self.top_k,
                filters=self._release_filter(active_release),
            )
            sources = retriever.retrieve(query_text)
            component = "VectorStoreIndex.as_retriever(VectorStoreRetriever)"
            reference = (
                "LI-8 llama_index/core/indices/vector_store/retrievers/"
                "retriever.py:104-115"
            )
            method = "dense"
        else:
            raise ValueError(f"unsupported retriever kind: {retriever_kind}")

        node_map = {node.node_id: node for node in namespace["nodes"]}
        candidates = []
        for rank, source in enumerate(sources, start=1):
            meta = node_map[source.node_id].metadata
            candidates.append(
                make_candidate(
                    source_id=meta["source_id"],
                    document_id=meta["document_id"],
                    chunk_id=source.node_id,
                    text=source.text or "",
                    span=list(meta.get("span", [0, len(source.text or "")])),
                    score=float(source.score or 0.0),
                    rank=rank,
                    metadata=dict(meta),
                    release_id=meta["release_id"],
                    method=method,
                )
            )

        self._emit(
            trace,
            stage="retrieve",
            component=component,
            source_reference=reference,
            duration_ms=(time.perf_counter() - started) * 1000.0,
            resolved_config={
                "method": method,
                "similarity_top_k": self.top_k,
                "filters": {"release_id": active_release},
            },
            input_ids=[query_text],
            release_id=active_release,
            output_ids=[c["chunk_id"] for c in candidates],
            score_rank_delta=[
                {"chunk_id": c["chunk_id"], "score": c["score"], "rank": c["rank"]}
                for c in candidates
            ],
        )
        return candidates
