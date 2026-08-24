"""Deterministic, per-case evaluation metrics for the controlled experiment.

Every function is pure and depends only on observed artifacts (retrieval
candidates, citations, trace events) plus the evaluation case definition.
No metric collapses results into a single score; each value is persisted
per case by ``run_experiment.py``.

Metric definitions (deterministic):

- ``recall_at_k``: |relevant ∩ top-k retrieved source_ids| / |relevant|
- ``mrr``: 1/rank of the first relevant retrieved source_id, else 0.0
- ``forbidden_source_violation``: 1.0 if any forbidden source_id appears
  among the sources the ANSWER actually cited (model-derived citations),
  else 0.0. Per ``config/experiment.json`` retrieval.metadata_filter,
  obsolete sources are intentionally indexed so the trap is answerable;
  a violation is citing one, not merely retrieving it.
- ``citation_source_correctness``: correct citations / total citations,
  where a citation is correct iff its source_id is in the case's relevant
  set (0.0 when no citations were emitted)
- ``citation_span_correctness``: citations whose [start, end] span, when
  re-sliced from the IMMUTABLE SOURCE BYTES on disk, reproduces the chunk
  text bound to the cited chunk_id / total citations (0.0 when none). The
  span is verified against the corpus file itself — never against the packed
  candidate the citation was copied from.
- ``citation_support``: fraction of required phrases present in the union of
  cited spans' source text (case-insensitive); measures whether what the
  answer CITED actually carries the expected facts
- ``required_phrase_coverage``: fraction of the case's required_phrases
  present in the generated answer (case-insensitive); measures whether the
  answer itself carries the expected facts
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
    """1.0 if any forbidden source appears among the sources the ANSWER
    actually cited (model-derived citations), else 0.0.
    """
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
    candidates: Sequence[Mapping],
    citations: Iterable[Mapping],
    source_texts: Mapping[str, str] | None = None,
) -> float:
    """Share of citations whose span verifies against immutable source bytes.

    ``source_texts`` maps source_id -> the full raw text read directly from
    the on-disk corpus. When provided, a citation counts as correct iff
    re-slicing those bytes at the cited [start, end] yields exactly the text
    bound to the cited chunk id (matched via the candidate table). Without
    it the check degenerates to comparing the citation against the packed
    candidate it was copied from — self-confirming — so the experiment
    pipeline always supplies source texts.
    """
    citations = list(citations)
    if not citations:
        return 0.0
    candidate_by_chunk = {
        candidate["chunk_id"]: candidate for candidate in candidates
    }

    def _verify(citation: Mapping) -> bool:
        chunk_id = citation.get("chunk_id")
        candidate = candidate_by_chunk.get(chunk_id)
        if candidate is None:
            return False
        if list(citation.get("span", [])) != list(candidate["span"]):
            return False
        if source_texts is None:
            # Degraded mode: self-confirming comparison only.
            return True
        start, end = citation["span"]
        source_text = source_texts.get(citation.get("source_id"))
        if source_text is None or len(source_text) < end:
            return False
        # The cited span re-sliced from immutable source bytes must reproduce
        # exactly the text bound to the cited chunk id.
        return source_text[start:end] == candidate["text"]

    correct = sum(1 for c in citations if _verify(c))
    return correct / len(citations)


def citation_support(
    required_phrases: Sequence[str],
    citations: Iterable[Mapping],
    source_texts: Mapping[str, str],
) -> float:
    """Fraction of required phrases present in cited spans' source text.

    Independent claim-to-citation support grading: the union of cited spans,
    re-sliced from immutable source bytes, must carry each expected fact.
    """
    if not required_phrases:
        return 0.0
    cited_text_parts: list[str] = []
    for citation in citations:
        start, end = citation["span"]
        source_text = source_texts.get(citation.get("source_id"))
        if source_text is not None and len(source_text) >= end:
            cited_text_parts.append(source_text[start:end])
    lowered = "\n".join(cited_text_parts).lower()
    hits = sum(1 for phrase in required_phrases if phrase.lower() in lowered)
    return hits / len(required_phrases)


def required_phrase_coverage(required_phrases: Sequence[str], answer: str) -> float:
    """Fraction of required phrases present in the answer, case-insensitively."""
    if not required_phrases:
        return 0.0
    lowered = answer.lower()
    hits = sum(1 for phrase in required_phrases if phrase.lower() in lowered)
    return hits / len(required_phrases)


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
    source_texts: Mapping[str, str] | None = None,
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
                "citation_span_correctness": citation_span_correctness(
            candidates, citations, source_texts
        ),
        "citation_support": citation_support(
            list(case.get("required_phrases", [])),
            citations,
            source_texts if source_texts is not None else {},
        ),
        "release_consistency": release_consistency(
            result["active_release"], candidates, citations
        ),
        "required_phrase_coverage": required_phrase_coverage(
            list(case.get("required_phrases", [])), str(result.get("answer", ""))
        ),
        "total_latency_ms": total_latency_ms(latencies),
    }
    for stage, duration in sorted(latencies.items()):
        metrics[f"latency_{stage}_ms"] = duration
    metrics["citation_count"] = len(citations)
    metrics["candidate_count"] = len(candidates)
    return metrics
