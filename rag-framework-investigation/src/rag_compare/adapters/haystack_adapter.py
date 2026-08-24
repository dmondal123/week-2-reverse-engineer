"""Haystack adapter using the components traced in Task 4 (HS-1..HS-10).

Components are wired explicitly (converter/splitter, in-memory store,
BM25/dense retrieval, filters, Ollama embedding); one stage event is emitted
at each component boundary. Document identity lost by the splitter (HS-4) is
chunks are indexed exactly as derived by the shared splitter (HS-1/HS-2).
"""

from __future__ import annotations

import time
from collections.abc import Mapping
from pathlib import Path

from haystack import Pipeline, component
from haystack.components.retrievers.in_memory import (
    InMemoryBM25Retriever,
    InMemoryEmbeddingRetriever,
)
from haystack.components.writers import DocumentWriter
from haystack.dataclasses import Document
from haystack.document_stores.in_memory import InMemoryDocumentStore
from haystack.document_stores.types import DuplicatePolicy

from rag_compare.adapters.base import (
    BaseAdapter,
    BuildResult,
    ReleaseNamespaceError,
    make_candidate,
)


@component
class OllamaTextEmbedder:
    """Explicit Haystack embedding component backed by the shared Ollama client."""

    def __init__(self, client, model: str) -> None:
        self._client = client
        self._model = model

    @component.output_types(embedding=list[float])
    def run(self, text: str):
        return {"embedding": self._client.embed(self._model, [text])[0]}


class HaystackAdapter(BaseAdapter):
    framework = "haystack"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        # release_id namespace -> {"store": InMemoryDocumentStore}
        self._stores: dict[str, dict] = {}
        self._latest_vectors: list[list[float]] = []

    def adapter_name(self) -> str:
        return "haystack_adapter"

    def store_component_name(self) -> str:
        return "DocumentWriter.run -> InMemoryDocumentStore.write_documents"

    def store_source_reference(self) -> str:
        return "HS-1 haystack/components/writers/document_writer.py:80"

    # ---- build ---------------------------------------------------------------

    def build_release(
        self,
        corpus_path: str | Path,
        manifest: Mapping[str, object],
        trace,
    ) -> BuildResult:
        release_id = str(manifest["corpus_version"])

        def embed_stage(chunks, rid):
            result = self._embed_chunks(chunks, rid, trace)
            # Vectors are needed again at store time to attach embeddings to
            # the Haystack documents (dense retrieval requires them).
            self._latest_vectors = result.vectors
            return result

        def store_stage(chunks, rid):
            vectors = self._latest_vectors
            if len(vectors) != len(chunks):
                raise ValueError("embed stage did not return one vector per chunk")
            documents = []
            for chunk, vector in zip(chunks, vectors, strict=True):
                document = Document(
                    id=chunk["chunk_id"],
                    content=chunk["text"],
                    embedding=list(vector),
                    meta={
                        "source_id": chunk["source_id"],
                        "document_id": chunk["document_id"],
                        "release_id": chunk["release_id"],
                        "span": chunk["span"],
                    },
                )
                documents.append(document)

            # Chunks arrive from the shared real token-window splitter, so no
            # framework-native splitting runs here; identities are written
            # exactly as derived (HS-4 regeneration is never triggered).
            store = InMemoryDocumentStore()
            writer = DocumentWriter(store, policy=DuplicatePolicy.FAIL)  # HS-2
            writer.run(documents=documents)
            self._stores[rid] = {
                "store": store,
                "vectors": [list(vector) for vector in vectors],
                "chunk_ids": [chunk["chunk_id"] for chunk in chunks],
            }

        return self._build_release_common(
            corpus_path, manifest, trace, embed_stage, store_stage, release_id
        )

    def read_back_stored_chunks(self, release_id: str) -> list[dict]:
        """Enumerate the InMemoryDocumentStore contents for a release."""
        namespace = self._stores.get(release_id)
        if namespace is None:
            raise ReleaseNamespaceError(release_id)
        documents = namespace["store"].filter_documents()
        return [
            {
                "chunk_id": document.id,
                "source_id": document.meta["source_id"],
                "document_id": document.meta["document_id"],
                "span": list(document.meta["span"]),
                "text": document.content or "",
            }
            for document in documents
        ]

    # ---- query -----------------------------------------------------------------

    def drop_release(self, release_id: str) -> None:
        """Delete a release namespace, as a completed release retirement would."""
        self._stores.pop(release_id, None)

    def _release_filter(self, active_release: str) -> dict:
        return {
            "field": "release_id",
            "operator": "==",
            "value": active_release,
        }

    def retrieve_candidates(
        self, query_text: str, retriever_kind: str, active_release: str, trace
    ) -> list[dict]:
        started = time.perf_counter()
        namespace = self._stores.get(active_release)
        if namespace is None:
            raise ReleaseNamespaceError(active_release)
        store = namespace["store"]

        if retriever_kind == "bm25":
            pipeline = Pipeline()  # HS-6 explicit wiring
            retriever = InMemoryBM25Retriever(store, top_k=self.top_k)  # HS-7
            pipeline.add_component("retriever", retriever)
            results = pipeline.run(
                {
                    "retriever": {
                        "query": query_text,
                        "filters": self._release_filter(active_release),  # HS-8
                    }
                }
            )["retriever"]["documents"]
            component = "InMemoryBM25Retriever(InMemoryDocumentStore)"
            reference = "HS-7/HS-10 bm25_retriever.py:45-46; scoring lives in the store"
            method = "bm25"
        elif retriever_kind == "ollama_dense":
            pipeline = Pipeline()
            embedder = OllamaTextEmbedder(self.client, self.embedding_model)
            retriever = InMemoryEmbeddingRetriever(store, top_k=self.top_k)
            pipeline.add_component("embedder", embedder)
            pipeline.add_component("retriever", retriever)
            pipeline.connect("embedder.embedding", "retriever.query_embedding")
            results = pipeline.run(
                {
                    "embedder": {"text": query_text},
                    "retriever": {
                        "filters": self._release_filter(active_release),
                    },
                }
            )["retriever"]["documents"]
            component = "OllamaTextEmbedder -> InMemoryEmbeddingRetriever"
            reference = "HS-8 embedding_retriever.py:54-55,76-82"
            method = "dense"
        else:
            raise ValueError(f"unsupported retriever kind: {retriever_kind}")

        candidates = []
        for rank, document in enumerate(results, start=1):
            candidates.append(
                make_candidate(
                    source_id=document.meta["source_id"],
                    document_id=document.meta["document_id"],
                    chunk_id=document.id,
                    text=document.content or "",
                    span=list(
                        document.meta.get("span", [0, len(document.content or "")])
                    ),
                    score=float(document.score or 0.0),
                    rank=rank,
                    metadata=dict(document.meta),
                    release_id=document.meta["release_id"],
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
                "top_k": self.top_k,
                "filters": self._release_filter(active_release),
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
