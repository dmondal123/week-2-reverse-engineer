import pytest

from rag_compare.rerank import coverage_score, pack_context, rerank_candidates


def make_candidate(chunk_id, text, score, rank):
    return {
        "chunk_id": chunk_id,
        "text": text,
        "score": score,
        "rank": rank,
        "release_id": "v1",
    }


def test_coverage_score_is_lowercase_token_fraction():
    assert coverage_score("Hotel Wi-Fi LIMIT", "the hotel limit for wi-fi") == 1.0
    assert coverage_score("hotel limit", "hotel only") == 0.5
    assert coverage_score("hotel", "nothing matches") == 0.0
    assert coverage_score("", "text") == 0.0


def test_reranker_orders_by_coverage_then_incoming_rank_then_chunk_id():
    query = "hotel wifi reimbursement limit"
    candidates = [
        make_candidate("c-low", "office snacks policy", 0.9, 1),
        make_candidate("c-tie-b", "hotel wifi", 0.4, 3),
        make_candidate("c-tie-a", "wifi hotel", 0.8, 2),
        make_candidate("c-full", "hotel wifi reimbursement limit applies", 0.1, 4),
    ]

    ordered = rerank_candidates(query, candidates)

    assert [candidate["chunk_id"] for candidate in ordered] == [
        "c-full",
        "c-tie-a",
        "c-tie-b",
        "c-low",
    ]


def test_ties_break_by_chunk_id_when_ranks_are_equal():
    query = "wifi"
    candidates = [
        make_candidate("z-chunk", "wifi rules", 0.5, 2),
        make_candidate("a-chunk", "wifi rules", 0.9, 2),
    ]

    ordered = rerank_candidates(query, candidates)

    assert [candidate["chunk_id"] for candidate in ordered] == ["a-chunk", "z-chunk"]


def test_reranker_preserves_original_score_and_rank_and_does_not_mutate_input():
    query = "hotel"
    original = [
        {"chunk_id": "b", "text": "hotel", "score": 0.2, "rank": 7},
        {"chunk_id": "a", "text": "hotel info", "score": 0.6, "rank": 8},
    ]
    snapshot = [dict(candidate) for candidate in original]

    ordered = rerank_candidates(query, original)

    # Equal coverage: stable tie-break by incoming rank keeps rank 7 first.
    assert [(c["score"], c["rank"]) for c in ordered] == [(0.2, 7), (0.6, 8)]
    assert original == snapshot


def test_reranker_requires_rank_and_chunk_id():
    with pytest.raises(ValueError):
        rerank_candidates("query", [{"text": "no identity"}])


def test_packer_admits_complete_chunks_within_budget():
    candidates = [
        {"chunk_id": "small", "text": "one two three"},
        {"chunk_id": "fits", "text": "four five"},
        {"chunk_id": "too-big", "text": "six seven eight nine ten"},
    ]

    result = pack_context(candidates, budget_tokens=5)

    assert [chunk["chunk_id"] for chunk in result["packed"]] == ["small", "fits"]
    assert result["used_tokens"] == 5
    assert result["rejected"] == [
        {"chunk_id": "too-big", "reason": "budget_exhausted", "chunk_tokens": 5}
    ]


def test_packer_never_truncates_a_chunk():
    text = "ten tokens " * 10
    candidates = [{"chunk_id": "whole-only", "text": text}]

    result = pack_context(candidates, budget_tokens=3)

    assert result["packed"] == []
    assert result["rejected"] == [
        {"chunk_id": "whole-only", "reason": "budget_exhausted", "chunk_tokens": 20}
    ]
    # The source candidate is untouched - no truncation was applied anywhere.
    assert candidates[0]["text"] == text


@pytest.mark.parametrize("budget", (-1, True, 1.5, "10"))
def test_packer_rejects_invalid_budgets(budget):
    with pytest.raises(ValueError):
        pack_context([], budget_tokens=budget)
