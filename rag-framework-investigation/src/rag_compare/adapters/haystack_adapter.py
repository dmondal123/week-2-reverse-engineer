"""Haystack adapter using the components traced in Task 4 (HS-1..HS-10).

Components are wired explicitly (converter/splitter, in-memory store,
BM25/dense retrieval, filters, Ollama embedding); one stage event is emitted
at each component boundary. Document identity lost by the splitter (HS-4) is
restored by re-asserting contract IDs before the write (HS-1/HS-2).
"""

from __future__ import annotations

import dataclasses
import time
from collections.abc import Mapping
from pathlib import Path

from haystack import Pipeline, component
from haystack.components.preprocessors import DocumentSplitter
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
    ) -> dict:
        release_id = str(manifest["corpus_version"])

        def embed_stage(chunks, rid):
            return self._embed_chunks(chunks, rid, trace)

        def store_stage(chunks, rid):
            documents = []
            for chunk in chunks:
                document = Document(
                    id=chunk["chunk_id"],
                    content=chunk["text"],
                    meta={
                        "source_id": chunk["source_id"],
                        "document_id": chunk["document_id"],
                        "release_id": chunk["release_id"],
                        "span": chunk["span"],
                    },
                )
                documents.append(document)

            # Explicit splitter honoring the traced defaults (HS-3). Chunks are
            # already below the window, so splitting must not change identity;
            # any child id regeneration (HS-4) is reverted before the write.
            splitter = DocumentSplitter(
                split_by="word",
                split_length=int(self.config["chunking"]["chunk_size_tokens"]),  # type: ignore[index]
                split_overlap=int(self.config["chunking"]["chunk_overlap_tokens"]),  # type: ignore[index]
            )
            expected_ids = {document.id for document in documents}
            by_content = {d.content or "": d for d in documents}
            split_documents = splitter.run(documents=documents)["documents"]
            restored = []
            for child in split_documents:
                original = by_content.get(child.content or "")
                if original is not None and child.id != original.id:
                    child = dataclasses.replace(
                        child, id=original.id, meta=dict(original.meta)
                    )
                restored.append(child)
            if {doc.id for doc in restored} != expected_ids:
                raise ValueError("splitter changed normalized chunk identities")

            store = InMemoryDocumentStore()
            writer = DocumentWriter(store, policy=DuplicatePolicy.FAIL)  # HS-2
            writer.run(documents=restored)
            self._stores[rid] = {"store": store}

        return self._build_release_common(
            corpus_path, manifest, trace, embed_stage, store_stage, release_id
        )

    # ---- query -----------------------------------------------------------------

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
