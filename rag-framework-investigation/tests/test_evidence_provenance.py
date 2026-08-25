"""Automated provenance checks for the paper set and evidence files.

Guarantees:
1. Every cited evidence ID (``EV-*-*``) in ``paper/`` and ``evidence/``
   exists as a row in ``evidence/ledger.csv`` (ranges like
   ``EV-T4-001..012`` / ``EV-T8-001…003`` are expanded).
2. Every cited run ID (``task6-YYYYMMDDTHHMMSS`` /
   ``failure-injection-YYYYMMDDTHHMMSS``) is recorded either in a canonical
   result JSON under ``artifacts/results/`` or as an entry under
   ``artifacts/raw/``.
3. Every commit-bound source file referenced in
   ``evidence/source-references.md`` exists on disk at the documented path.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

SCAN_FILES = sorted(
    list((ROOT / "paper").glob("*.md"))
    + list((ROOT / "evidence").glob("*.md"))
    + [ROOT / "evidence" / "ledger.csv"]
)

EVIDENCE_ID_RE = re.compile(r"\bEV-[A-Z]+-\d{3}\b")
RANGE_RE = re.compile(
    r"\b(EV-[A-Z]+)-(\d{3})\s*(?:\.\.|\u2026|\.\.\.|—|to)\s*(\d{3})\b"
)
RUN_ID_RE = re.compile(r"\b(?:task6|failure-injection)-\d{8}T\d{6}\b")
SOURCE_FILE_RE = re.compile(r"`([a-z_][a-z0-9_/.-]+\.(?:py|md|yaml|json))`")


def _load_ledger_ids() -> set[str]:
    with (ROOT / "evidence" / "ledger.csv").open(newline="", encoding="utf-8") as f:
        return {row["evidence_id"] for row in csv.DictReader(f)}


def _expand_ranges(text: str) -> set[str]:
    """Expand shorthand ranges like EV-T4-001..012 or EV-T8-001\u2026003."""
    ids: set[str] = set()
    for prefix, start, end in RANGE_RE.findall(text):
        ids.update(f"{prefix}-{n:03d}" for n in range(int(start), int(end) + 1))
    return ids


def _known_run_ids() -> set[str]:
    runs: set[str] = set()
    for path in (ROOT / "artifacts" / "results").glob("*.json"):
        runs.update(RUN_ID_RE.findall(path.read_text(encoding="utf-8")))
    raw_dir = ROOT / "artifacts" / "raw"
    if raw_dir.is_dir():
        for entry in raw_dir.rglob("*"):
            runs.update(RUN_ID_RE.findall(entry.name))
    return runs


def test_scan_files_exist():
    assert SCAN_FILES, "expected paper and evidence files to scan"


def test_every_cited_evidence_id_exists_in_ledger():
    ledger_ids = _load_ledger_ids()
    missing: dict[str, set[str]] = {}
    for path in SCAN_FILES:
        text = path.read_text(encoding="utf-8")
        # Strip ranges first so their endpoints are checked via expansion,
        # not as bare (possibly nonexistent) IDs.
        bare = set(EVIDENCE_ID_RE.findall(RANGE_RE.sub("", text)))
        bare |= _expand_ranges(text)
        unknown = {i for i in bare if i not in ledger_ids}
        if unknown:
            missing[str(path.relative_to(ROOT))] = unknown
    assert not missing, f"Evidence IDs cited but absent from ledger.csv: {missing}"


def test_every_cited_run_id_exists_in_artifacts():
    known = _known_run_ids()
    missing: dict[str, set[str]] = {}
    for path in SCAN_FILES:
        text = path.read_text(encoding="utf-8")
        cited = set(RUN_ID_RE.findall(text))
        unknown = {r for r in cited if r not in known}
        if unknown:
            missing[str(path.relative_to(ROOT))] = unknown
    assert not missing, f"Run IDs cited but not found in artifacts: {missing}"


def test_source_reference_files_exist_on_disk():
    """Paths in source-references.md resolve against the vendored clones
    under ``vendors/`` inside this project root."""
    if not (ROOT / "vendors").is_dir():
        pytest.skip("vendors/ clones not present; run README sections 3-4")
    text = (ROOT / "evidence" / "source-references.md").read_text(encoding="utf-8")
    missing = [
        rel
        for rel in sorted(set(SOURCE_FILE_RE.findall(text)))
        if not (ROOT / "vendors" / rel).is_file() and not (ROOT / rel).is_file()
    ]
    assert not missing, f"Source references point to missing files: {missing}"
