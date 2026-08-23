"""Durable append-only JSONL trace output."""

import json
import os
from pathlib import Path

from rag_compare.contracts import StageEvent


class JsonlTrace:
    """Append validated stage events to a JSONL file durably."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def append(self, event: StageEvent) -> None:
        serialized = (
            json.dumps(event.to_dict(), sort_keys=True, separators=(",", ":")) + "\n"
        )
        with self.path.open("a", encoding="utf-8") as trace_file:
            trace_file.write(serialized)
            trace_file.flush()
            os.fsync(trace_file.fileno())
