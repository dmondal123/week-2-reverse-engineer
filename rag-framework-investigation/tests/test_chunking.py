"""Tests for the shared cl100k_base token-window splitter (declared chunking)."""

from __future__ import annotations

import pytest

from rag_compare.adapters.base import (
    AdapterError,
    parse_markdown_file,
    token_window_structures,
)


def _write_doc(tmp_path, words: int):
    body = " ".join(f"word{i}" for i in range(words))
    raw = f"---\nsource_id: long-doc\npolicy_version: v1\ntitle: T\n---\n{body}\n"
    path = tmp_path / "long-doc.md"
    path.write_text(raw, encoding="utf-8")
    return parse_markdown_file(path), raw


def test_long_body_is_split_into_multiple_token_windows(tmp_path):
    parsed, raw = _write_doc(tmp_path, words=800)
    structures = token_window_structures(
        parsed, "v1", "policy_version", size_tokens=64, overlap_tokens=16
    )
    assert len(structures) > 1
    # Windows advance by size-overlap and cover the whole body exactly once
    # at the boundaries: first starts at body start, last ends at body end.
    assert structures[0]["span"][0] == parsed.body_start
    assert structures[-1]["span"][1] == parsed.body_end
    for structure in structures:
        start, end = structure["span"]
        assert raw[start:end] == structure["text"]
        assert structure["content_sha256"] == parsed.content_sha256


def test_short_body_yields_one_window_identical_to_whole_document(tmp_path):
    parsed, _raw = _write_doc(tmp_path, words=20)
    structures = token_window_structures(
        parsed, "v1", "policy_version", size_tokens=200, overlap_tokens=40
    )
    assert len(structures) == 1
    assert structures[0]["span"] == [parsed.body_start, parsed.body_end]


def test_invalid_window_configuration_is_rejected(tmp_path):
    parsed, _ = _write_doc(tmp_path, words=10)
    with pytest.raises(AdapterError):
        token_window_structures(
            parsed, "v1", "policy_version", size_tokens=40, overlap_tokens=40
        )
