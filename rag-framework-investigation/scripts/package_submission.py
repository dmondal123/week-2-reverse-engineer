#!/usr/bin/env python3
"""Package the investigation into submission/rag-framework-investigation.zip.

Safety model:

- EXPLICIT ALLOWLIST: only the exact files/directories listed below are ever
  considered; nothing is discovered by walking the tree unfiltered.
- DENYLIST: any candidate whose path contains prohibited fragments (env dirs,
  caches, credentials, vendor clones, build outputs) is rejected, and any
  single file above ARTIFACT_SIZE_LIMIT_BYTES is rejected.
- The archive is verified mechanically after writing (testzip, required-file
  list, exclusion scan, extraction to a temp dir, JSON/CSV parse of every data
  member) and the ZIP SHA-256 plus verification output are saved beside it.
"""

from __future__ import annotations

import csv
import hashlib
import json
import sys
import tempfile
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ZIP_PATH = PROJECT_ROOT / "submission" / "rag-framework-investigation.zip"
VERIFICATION_PATH = PROJECT_ROOT / "submission" / "verification.json"

ARTIFACT_SIZE_LIMIT_BYTES = 2 * 1024 * 1024  # 2 MiB per file

# Explicit allowlist: exact files and directories (recursed) relative to the
# project root. Everything not listed here never enters the archive.
ALLOWED_FILES = [
    "README.md",
    "pyproject.toml",
    "requirements.txt",
    "config/experiment.json",
    "config/environment-manifest.json",
    "config/repository-manifest.json",
    "eval/cases.json",
    "evidence/hypotheses.md",
    "evidence/ledger.csv",
    "evidence/provenance-matrix.csv",
    "evidence/source-references.md",
    "paper/insights-paper.md",
    "paper/decision.adr.md",
    "paper/architecture.mmd",
    "paper/hypothesis-evidence.md",
    "paper/experiment-results.md",
    "paper/risk-control.md",
    "artifacts/results/controlled-results.csv",
    "artifacts/results/controlled-summary.json",
    "artifacts/results/failure-injection.json",
    "artifacts/raw/environment-freeze.txt",
    "artifacts/raw/environment-freeze-post-task5.txt",
    "artifacts/raw/pip-freeze.txt",
    "artifacts/raw/failure-injection-trace.jsonl",
    "artifacts/raw/failure-injection-post-recovery-trace.jsonl",
    "scripts/freeze_environment.sh",
]

ALLOWED_DIRS = [
    "src/rag_compare",           # package source (recursed)
    "tests",                     # test suites
    "corpus/v1",                 # corpus + manifests
    "corpus/v2",
    "corpus/v1/manifest.json",
    "corpus/v2/manifest.json",
    "artifacts/results",         # sanitized result summaries
    # canonical controlled run (paper-cited)
    "artifacts/raw/task6-20260823T202231",
    # clean-shell reproduction run (Task 9 verification)
    "artifacts/raw/task6-20260823T203946",
    # preserved superseded evidence
    "artifacts/raw/archive-pre-remediation-20260824",
]

REQUIRED_MEMBERS = [
    "README.md",
    "config/experiment.json",
    "config/repository-manifest.json",
    "eval/cases.json",
    "evidence/ledger.csv",
    "paper/insights-paper.md",
    "paper/decision.adr.md",
    "paper/architecture.mmd",
    "src/rag_compare/release.py",
    "src/rag_compare/adapters/haystack_adapter.py",
    "src/rag_compare/adapters/llamaindex_adapter.py",
    "tests/test_failure_injection.py",
    "corpus/v1/manifest.json",
    "corpus/v2/manifest.json",
    "artifacts/results/controlled-summary.json",
    "artifacts/results/failure-injection.json",
]

# Prohibited path fragments — hard reject.
DENYLIST_FRAGMENTS = (
    ".env",
    ".venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    "credential",
    "secret",
    "token.txt",
    "vendor/",
    "dist/",
    "build/",
    ".egg-info",
    ".git",
)

DATA_SUFFIXES = {".json", ".csv"}


def iter_allowlist() -> list[Path]:
    """Resolve the allowlist into a sorted list of existing files."""
    candidates: set[Path] = set()
    for entry in ALLOWED_FILES + ALLOWED_DIRS:
        path = PROJECT_ROOT / entry
        if not path.exists():
            raise FileNotFoundError(f"allowlisted path does not exist: {entry}")
        if path.is_file():
            candidates.add(path)
        else:
            candidates.update(p for p in path.rglob("*") if p.is_file())
    return sorted(candidates)


def check_allowed(path: Path) -> str | None:
    """Return a rejection reason for ``path``, or None if it may be archived."""
    rel = path.relative_to(PROJECT_ROOT).as_posix()
    for fragment in DENYLIST_FRAGMENTS:
        if fragment in f"{rel}/":
            return f"prohibited fragment {fragment!r}"
    if path.stat().st_size > ARTIFACT_SIZE_LIMIT_BYTES:
        return (
            f"file exceeds size limit ({path.stat().st_size} > "
            f"{ARTIFACT_SIZE_LIMIT_BYTES} bytes)"
        )
    return None


def build_zip() -> dict:
    ZIP_PATH.parent.mkdir(parents=True, exist_ok=True)
    rejected: list[dict] = []
    included: list[str] = []

    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in iter_allowlist():
            reason = check_allowed(path)
            if reason:
                rejected.append(
                    {
                        "path": path.relative_to(PROJECT_ROOT).as_posix(),
                        "reason": reason,
                    }
                )
                continue
            arcname = path.relative_to(PROJECT_ROOT).as_posix()
            zf.write(path, arcname)
            included.append(arcname)

        # Disclosure lives one level up from the project root.
        disclosure = PROJECT_ROOT.parent / "AI_COLLABORATION.md"
        if disclosure.is_file():
            zf.write(disclosure, "AI_COLLABORATION.md")
            included.append("AI_COLLABORATION.md")

    return {"included": included, "rejected": rejected}


def verify_zip() -> dict:
    """Mechanical verification: integrity, allowlist conformance, parseability."""
    failures: list[str] = []
    with zipfile.ZipFile(ZIP_PATH) as zf:
        names = zf.namelist()

        if zf.testzip() is not None:
            failures.append("testzip() reported a corrupt member")

        missing = [name for name in REQUIRED_MEMBERS if name not in names]
        if missing:
            failures.append(f"required members missing: {missing}")

        prohibited = [
            name
            for name in names
            for fragment in DENYLIST_FRAGMENTS
            if fragment in f"{name}/"
        ]
        if prohibited:
            failures.append(f"prohibited members present: {prohibited}")

        with tempfile.TemporaryDirectory() as tmp:
            zf.extractall(tmp)
            extract_root = Path(tmp)
            for name in names:
                target = (extract_root / name).resolve()
                if not target.is_relative_to(extract_root.resolve()):
                    failures.append(
                        f"unsafe member path escapes extraction dir: {name}"
                    )
                    continue
                if target.suffix.lower() in DATA_SUFFIXES:
                    try:
                        if target.suffix == ".json":
                            json.loads(target.read_text(encoding="utf-8"))
                        else:
                            with target.open(newline="", encoding="utf-8") as handle:
                                next(csv.reader(handle))
                    except Exception as error:  # noqa: BLE001 - report and continue
                        failures.append(f"unparseable data member {name}: {error}")

    sha256 = hashlib.sha256(ZIP_PATH.read_bytes()).hexdigest()
    report = {
        "zip_path": str(ZIP_PATH.relative_to(PROJECT_ROOT)),
        "zip_sha256": sha256,
        "member_count": len(names),
        "checks": {
            "testzip": (
                "passed"
                if "testzip() reported a corrupt member" not in failures
                else "failed"
            ),
            "required_members": (
                "passed"
                if not any(f.startswith("required") for f in failures)
                else "failed"
            ),
            "exclusion_scan": (
                "passed"
                if not any(f.startswith("prohibited") for f in failures)
                else "failed"
            ),
            "extraction_and_parse": (
                "passed"
                if not any(f.startswith(("unparseable", "unsafe")) for f in failures)
                else "failed"
            ),
        },
        "failures": failures,
        "status": "passed" if not failures else "failed",
    }
    VERIFICATION_PATH.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return report


def main() -> int:
    result = build_zip()
    print(f"[package] wrote {len(result['included'])} members to {ZIP_PATH}")
    for item in result["rejected"]:
        print(f"[package] REJECTED {item['path']}: {item['reason']}", file=sys.stderr)

    report = verify_zip()
    print(f"[package] verification status={report['status']} "
          f"members={report['member_count']} sha256={report['zip_sha256']}")
    print(f"[package] verification report -> {VERIFICATION_PATH}")
    for failure in report["failures"]:
        print(f"[package] FAILURE: {failure}", file=sys.stderr)
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
