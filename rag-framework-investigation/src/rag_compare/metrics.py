"""Deterministic, per-case evaluation metrics for the controlled experiment.

Every function is pure and depends only on observed artifacts (retrieval
candidates, citations, trace events) plus the evaluation case definition.
No metric collapses results into a single score; each value is persisted
per case by ``run_experiment.py``.

Metric definitions (deterministic):

- ``recall_at_k``: |relevant ∩ top-k retrieved source_ids| / |relevant|
- ``mrr``: 1/rank of the first relevant retrieved source_id, else 0.0
- ``forbidden_source_violation``: 1.0 if any forbidden source_id appears in
  the grounded context actually packed for generation (the emitted
  citations), else 0.0. Per ``config/experiment.json`` retrieval.metadata_filter,
  obsolete sources are intentionally indexed so the trap is answerable;
  exclusion is enforced at citation scoring, not at retrieval.
- ``citation_source_correctness``: correct citations / total citations,
  where a citation is correct iff its source_id is in the case's relevant
  set (0.0 when no citations were emitted)
- ``citation_span_correctness``: citations whose [start, end] span exactly
  matches the indexed candidate span for the cited chunk_id / total
  citations (0.0 when no citations were emitted)
- ``stage_latencies_ms``: observed wall-clock duration per traced stage
- ``total_latency_ms``: sum of per-stage durations
- ``release_consistency``: 1.0 iff every candidate and citation carries the
  active release id captured at query start, else 0.0
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence


def recall_at_k(
    relevant_source_ids: Sequence[str], retrieved_source_ids: Sequence[str], k: int
) -> float:
    """Fraction of relevant sources present in the first k retrieved sources."""
    if not relevant_source_ids:
        return 0.0
    top_k = set(retrieved_source_ids[:k])
    hits = sum(1 for source_id in relevant_source_ids if source_id in top_k)
    return hits / len(relevant_source_ids)


def mrr(
    relevant_source_ids: Sequence[str], retrieved_source_ids: Sequence[str]
) -> float:
    """Reciprocal rank of the first relevant retrieved source_id."""
    relevant = set(relevant_source_ids)
    for rank, source_id in enumerate(retrieved_source_ids, start=1):
        if source_id in relevant:
            return 1.0 / rank
    return 0.0


def forbidden_source_violation(
    forbidden_source_ids: Sequence[str],
    citation_source_ids: Sequence[str],
) -> float:
    """1.0 if a forbidden source reached the packed/grounded context, else 0.0."""
    forbidden = set(forbidden_source_ids)
    violated = set(citation_source_ids)
    return 1.0 if forbidden & violated else 0.0


def citation_source_correctness(
    relevant_source_ids: Sequence[str], citations: Iterable[Mapping]
) -> float:
    """Share of emitted citations whose source_id is a relevant source."""
    citations = list(citations)
    if not citations:
        return 0.0
    relevant = set(relevant_source_ids)
    correct = sum(1 for c in citations if c.get("source_id") in relevant)
    return correct / len(citations)


def citation_span_correctness(
    candidates: Sequence[Mapping], citations: Iterable[Mapping]
) -> float:
    """Share of citations whose span matches the indexed candidate's span."""
    citations = list(citations)
    if not citations:
        return 0.0
    span_by_chunk = {
        candidate["chunk_id"]: list(candidate["span"]) for candidate in candidates
    }
    correct = sum(
        1
        for c in citations
        if c.get("chunk_id") in span_by_chunk
        and list(c.get("span", [])) == span_by_chunk[c["chunk_id"]]
    )
    return correct / len(citations)


def stage_latencies_ms(trace_events: Sequence[Mapping]) -> dict:
    """Observed duration in milliseconds keyed by stage name, in trace order."""
    latencies: dict[str, float] = {}
    for event in trace_events:
        stage = event["stage"]
        # Query-time stages can repeat across nested emits; keep the observed
        # order and accumulate so nothing silently overwrites anything.
        latencies[stage] = round(latencies.get(stage, 0.0) + event["duration_ms"], 6)
    return latencies


def total_latency_ms(stage_latencies: Mapping[str, float]) -> float:
    return round(sum(stage_latencies.values()), 6)


def release_consistency(
    active_release: str,
    candidates: Sequence[Mapping],
    citations: Sequence[Mapping],
) -> float:
    """1.0 iff every candidate and citation belongs to the active release."""
    items = [(c.get("release_id"), c.get("chunk_id")) for c in candidates]
    items += [(c.get("release_id"), c.get("chunk_id")) for c in citations]
    if not items:
        return 0.0
    consistent = all(release == active_release for release, _ in items)
    return 1.0 if consistent else 0.0


def evaluate_case(
    case: Mapping,
    result: Mapping,
    trace_events: Sequence[Mapping],
    top_k: int,
) -> dict:
    """Compute every deterministic metric for one case-condition pair.

    ``result`` is the adapter's observed query output; ``trace_events`` are
    that query's stage events. All values are persisted individually.
    """
    relevant = list(case["relevant_source_ids"])
    forbidden = list(case["forbidden_source_ids"])
    candidates = result["candidates"]
    citations = result["citations"]
    retrieved_sources = [c["source_id"] for c in candidates]
    citation_sources = [c["source_id"] for c in citations]

    latencies = stage_latencies_ms(trace_events)

    metrics = {
        "recall_at_k": recall_at_k(relevant, retrieved_sources, top_k),
        "mrr": mrr(relevant, retrieved_sources),
        "forbidden_source_violation": forbidden_source_violation(
            forbidden, citation_sources
        ),
        "citation_source_correctness": citation_source_correctness(relevant, citations),
        "citation_span_correctness": citation_span_correctness(candidates, citations),
        "release_consistency": release_consistency(
            result["active_release"], candidates, citations
        ),
        "total_latency_ms": total_latency_ms(latencies),
    }
    for stage, duration in sorted(latencies.items()):
        metrics[f"latency_{stage}_ms"] = duration
    metrics["citation_count"] = len(citations)
    metrics["candidate_count"] = len(candidates)
    return metrics
