"""Tests for byte-verified citation spans and claim-support grading."""

from __future__ import annotations

from rag_compare.metrics import (
    citation_span_correctness,
    citation_support,
)


def _candidate(chunk_id, text, span, source_id="doc-a"):
    return {
        "chunk_id": chunk_id,
        "source_id": source_id,
        "text": text,
        "span": list(span),
    }


def _citation(candidate):
    return {
        "chunk_id": candidate["chunk_id"],
        "source_id": candidate["source_id"],
        "span": list(candidate["span"]),
    }


SOURCE_TEXTS = {"doc-a": "HEADER policy text $50 threshold applies daily."}


def test_span_verifies_against_immutable_source_bytes():
    candidate = _candidate("c1", "policy text", (7, 18))
    citations = [_citation(candidate)]
    score = citation_span_correctness([candidate], citations, SOURCE_TEXTS)
    assert score == 1.0


def test_tampered_candidate_text_fails_source_verification():
    # The citation copies its span from the packed candidate, so a
    # self-confirming comparison would pass; the immutable source bytes
    # expose the mismatch instead.
    tampered = _candidate("c1", "TAMPERED text", (7, 18))
    citations = [_citation(tampered)]
    score = citation_span_correctness([tampered], citations, SOURCE_TEXTS)
    assert score == 0.0


def test_degraded_mode_is_self_confirming_and_documented():
    candidate = _candidate("c1", "TAMPERED text", (7, 18))
    score = citation_span_correctness([candidate], [_citation(candidate)], None)
    assert score == 1.0  # without source bytes the check proves nothing


def test_citation_support_grades_cited_spans_only():
    cited = _candidate("c1", "policy text $50", (7, 22))
    sources = dict(SOURCE_TEXTS, **{"doc-b": "free wifi included everywhere."})
    support = citation_support(["$50", "wifi"], [_citation(cited)], sources)
    assert support == 0.5  # only the cited span's facts count
