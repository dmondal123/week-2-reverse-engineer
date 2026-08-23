"""Fixed deterministic reranker and context packer for the controlled experiment."""

from __future__ import annotations

from collections.abc import Iterable, Mapping


def _tokens(text: str) -> set[str]:
    return set(text.lower().split())


def coverage_score(query_text: str, candidate_text: str) -> float:
    """Return the fraction of query terms covered by the candidate text."""
    query_terms = _tokens(query_text)
    if not query_terms:
        return 0.0
    candidate_terms = _tokens(candidate_text)
    return len(query_terms & candidate_terms) / len(query_terms)


def rerank_candidates(
    query_text: str,
    candidates: Iterable[Mapping],
) -> list[Mapping]:
    """Reorder candidates by query-term coverage without mutating their fields.

    Ordering is descending coverage score, with a stable tie-break by incoming
    rank then chunk ID. Original ``score`` and ``rank`` values are preserved;
    this function may only reorder candidates.
    """
    scored = []
    for position, candidate in enumerate(candidates):
        if "rank" not in candidate or "chunk_id" not in candidate:
            raise ValueError("candidates must carry rank and chunk_id")
        scored.append(
            (
                -coverage_score(query_text, candidate.get("text", "")),
                candidate["rank"],
                candidate["chunk_id"],
                position,
            )
        )

    ordered = sorted(range(len(scored)), key=lambda index: scored[index])
    return [candidates[index] for index in ordered]


def pack_context(
    candidates: Iterable[Mapping],
    budget_tokens: int,
) -> dict:
    """Admit complete chunks until the token approximation budget is reached.

    Chunks are never truncated. Rejected chunks are recorded with a reason.
    Returns ``{"packed": [...], "rejected": [...], "used_tokens": int}``.
    """
    if isinstance(budget_tokens, bool) or not isinstance(budget_tokens, int):
        raise ValueError("budget_tokens must be an integer")
    if budget_tokens < 0:
        raise ValueError("budget_tokens must be non-negative")

    packed: list[Mapping] = []
    rejected: list[dict] = []
    used = 0

    for candidate in candidates:
        text = candidate.get("text", "")
        cost = len(text.split())
        if used + cost <= budget_tokens:
            packed.append(candidate)
            used += cost
        else:
            rejected.append(
                {
                    "chunk_id": candidate.get("chunk_id"),
                    "reason": "budget_exhausted",
                    "chunk_tokens": cost,
                }
            )

    return {"packed": packed, "rejected": rejected, "used_tokens": used}
