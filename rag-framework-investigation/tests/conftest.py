"""Skip framework-dependent suites gracefully when the vendored pinned clones
are not installed (e.g. a fresh checkout of the submission zip before running
the README §3–4 setup steps).

Bare ``pytest`` on an unconfigured tree then reports skips instead of failing
with ModuleNotFoundError collection errors.
"""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _importable(name: str) -> bool:
    try:
        __import__(name)
    except ModuleNotFoundError:
        return False
    return True


# Suites that require haystack + llama_index editable installs.
# Paths are relative to this conftest's directory (tests/).
_FRAMEWORK_SUITES = [
    "test_adapters.py",
    "test_failure_injection.py",
    "test_identity.py",
]

# On-disk source-reference check is additionally guarded per-test via
# pytest.mark.skipif (see test_evidence_provenance.py) since only one of its
# tests needs vendors/.
HAS_FRAMEWORKS = _importable("haystack") and _importable("llama_index")
HAS_VENDORS = (PROJECT_ROOT / "vendors").is_dir()

collect_ignore = []
if not HAS_FRAMEWORKS:
    collect_ignore.extend(_FRAMEWORK_SUITES)
