# LlamaIndex vs Haystack Architecture

## Objective

Produce a reproducible, decision-ready comparison of LlamaIndex and Haystack that answers one production question:

> Which framework makes retrieval behavior, provenance, and immutable index releases easier to observe and control without permitting mixed-version answers?

The investigation must fit within 15 working hours, use only Ollama for model calls, and produce the complete bundle required by `week2/PROBLEM_STATEMENT.md`.

## Constraints and non-goals

Runtime: Apple M2 laptop with 24 GB memory.

Models: local Ollama only. No hosted embedding, generation, reranking, or judge APIs.

Time: 15 hours before Sunday midnight.

Data: small synthetic policy corpus; no production accounts, credentials, or personal/customer data.

Both repositories and all model/runtime identities must be pinned exactly.

The experiment compares observability and release behavior, not every feature, connector, vector store, or benchmark supported by either framework.

No UI, production vector database, distributed deployment, or model-quality benchmark is in scope.

## Investigation shape

Build one thin vertical pipeline in each framework:

```text
versioned corpus
-> parse -> chunk -> embed -> index
-> retrieve -> rerank -> pack
-> generate -> cite
```

Every arrow is an observable boundary. Each stage emits a JSONL trace event with its input identities, output identities, resolved configuration, duration, ownership, and source location. Framework-native parsing, chunking, indexing, and retrieval are used so the comparison reveals their real abstractions. A small normalization layer converts framework outputs into shared trace records.

The controlled experiment changes only the retriever:

- baseline: BM25 lexical retrieval;
- treatment: dense retrieval using Ollama `nomic-embed-text`;
- fixed: corpus version, parser/chunker settings, reranker, packer, generation model, prompt, evaluation cases, and metrics.

The deterministic reranker uses token coverage with stable tie-breaking. This keeps reranking separately observable without introducing a second model or an uncontrolled stochastic variable. Generation uses the dedicated non-thinking Ollama model `qwen3:4b-instruct-2507-q4_K_M`, subject to an installation and latency smoke test. The hybrid `qwen3:4b` is excluded because thinking is enabled by default and `/no_think` is not a sufficiently reliable experimental control. Exact Ollama tags and digests are captured.

## Corpus and evaluation contract

Create six short synthetic policy documents. Version 1 contains a current rule, an obsolete but lexically attractive rule, a scope document, an approval threshold, and two distractors. Version 2:

updates the current rule;

deletes one document;

changes one metadata field under schema version 2;

preserves stable source identity while changing content identity.

Each corpus release includes expected document paths, SHA-256 hashes, schema version, parser/chunker configuration hash, embedding identity, expected document count, and expected chunk count after a successful build.

Five to six evaluation cases specify the query, relevant source IDs, required supporting spans, and forbidden obsolete source IDs. At least one case requires combining a rule, scope, and exception; at least one exact identifier favors BM25; and at least one semantic paraphrase favors dense retrieval.

## Reverse-engineering protocol

### Pre-trace hypotheses

Write these before following the implementation:

1. LlamaIndex convenience abstractions and global `Settings` allow material retrieval behavior to change silently without appearing in the top-level pipeline.

2. Haystack's explicit component graph makes stage ownership and replacement more observable, but converters or splitters may still transform identity and metadata invisibly.

3. Neither framework alone guarantees an atomic, reproducible RAG release; immutable release namespaces and external promotion control dominate the framework choice.

For every hypothesis record a prediction, discriminating evidence, rejection condition, and final status. At least one favored explanation must be weakened or rejected by counterevidence.

### Two-path trace per framework

Trace both paths from an observable capability rather than from the folder tree:

1. Index-time: public ingestion call -> parser/converter -> splitter -> identity assignment -> embedding -> document/index store.

2. Query-time: public query call -> configuration resolution -> retrieval -> filtering/scoring -> reranking -> context packing -> generation -> citation.

At every boundary record:

concrete class/function and commit-bound source line;

input and output object types;

source, document, chunk, corpus, and release identities;

scores, ranks, ordering, and source spans;

metadata added, transformed, defaulted, or lost;

configuration and global/default state consulted;

state read or written;

owning process/runtime boundary;

relevant tests and telemetry or callbacks;

recovery behavior after partial failure.

### Hidden-state audit

Explicitly inspect:

LlamaIndex `Settings`, service/context defaults, transformations, callbacks, storage context, document/index stores, caches, and serialization;

Haystack component defaults, pipeline wiring, document stores, filters, async/concurrency behavior, serialization, and tracing hooks;

environment variables, model defaults, embedding dimensions, distance metric, chunk size/overlap, top-k, score normalization, and metadata filters for both.

### Provenance invariant matrix

For every stage, mark each field as preserved, transformed, synthesized, or lost:

```text
source_id, document_id, chunk_id, source_version, corpus_version, release_id, schema_version, embedding_id, score, rank, source_span, citation_id
```

Major architectural claims should be triangulated using at least two evidence forms where possible: implementation source, tests/configuration, runtime trace, or history/issue/ADR.

## Trace and evidence contracts

Each stage event contains:

```text
run_id, framework, framework_commit, path, stage, component, source_reference, started_at, duration_ms, resolved_config, input_ids, output_ids, metadata_delta, score_rank_delta, release_id, artifact_path, status, error
```

The evidence ledger contains:

```text
evidence_id, timestamp, framework, commit_sha, evidence_type, claim, source_or_command, artifact_path, interpretation, confidence, contradicts, verification_status ...
```

`evidence_type` is one of `fact`, `interpretation`, `hypothesis`, `counterevidence`, or `unknown`. Runtime output is saved before being summarized; AI-generated text is never treated as execution evidence.

## Release mechanism

Every index is built in an immutable namespace keyed by `release_id`. A release manifest binds together:

corpus file list and hashes;

corpus and schema versions;

parser identity and resolved configuration;

chunker identity, size, overlap, and configuration hash;

embedding model name, Ollama digest, dimensions, and distance metric;

framework name, commit, package version, and adapter version;

document and chunk counts;

build timestamp and validation status.

The active release is a small pointer file updated atomically only after manifest validation. Query construction reads the active release once and filters every retrieval branch by that `release_id`.

The failure injection builds only half of version 2 in a staging namespace. The validator must reject it because hashes/counts do not match; the active pointer must remain on version 1; and query traces must contain no version-2 chunks. A completed version 2 is then validated and promoted, proving recovery and normal promotion. Deletes, schema changes, or embedding changes always create a new release rather than mutating an active index.

## Measurements and acceptance criteria

For every framework/retriever/case combination record:

recall@k and MRR against relevant source IDs;

obsolete-source violation;

citation source/span correctness;

retrieved, reranked, and packed ordering;

per-stage duration and total latency;

release consistency across all returned chunks.

The investigation is complete only when:

both index-time and query-time paths are reproducible from exact commands;

another engineer can follow one answer from source bytes to final citation;

every material runtime setting is explicit or documented as an unknown;

12 or more balanced commit-bound source/test/config references are captured;

two or more history/issue/ADR references support design-driver inferences;

two or more controlled-experiment runtime artifacts exist;

the partial-release failure is observed and the mixed-version invariant passes;

at least one hypothesis is rejected or weakened with counterevidence;

the paper, ADR, four required diagrams/tables, disclosure, commands, and sanitized raw artifacts are present;

the final ZIP excludes secrets/caches/environments and successfully opens.
