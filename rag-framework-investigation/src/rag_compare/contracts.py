"""Shared, framework-independent contracts for investigation artifacts."""

import json
from dataclasses import asdict, dataclass


class ImmutableList(list):
    """A list-shaped value that rejects all normal in-place mutation APIs."""

    def __init__(self, values: list) -> None:
        super().__init__(values)

    def _immutable(self, *args, **kwargs):
        raise TypeError("identifier lists are immutable")

    append = _immutable
    clear = _immutable
    extend = _immutable
    insert = _immutable
    pop = _immutable
    remove = _immutable
    reverse = _immutable
    sort = _immutable

    __setitem__ = _immutable
    __delitem__ = _immutable
    __iadd__ = _immutable
    __imul__ = _immutable


@dataclass(frozen=True)
class StageEvent:
    run_id: str
    framework: str
    framework_commit: str
    path: str
    stage: str
    component: str
    source_reference: str
    started_at: str
    duration_ms: float
    resolved_config: object
    input_ids: list
    output_ids: list
    metadata_delta: object
    score_rank_delta: object
    release_id: str
    artifact_path: str
    status: str
    error: object

    def __post_init__(self) -> None:
        try:
            if self.duration_ms < 0:
                raise ValueError("duration_ms must be non-negative")
        except TypeError as error:
            raise ValueError("duration_ms must be a non-negative number") from error

        if not isinstance(self.input_ids, list):
            raise ValueError("input_ids must be a list")
        if not isinstance(self.output_ids, list):
            raise ValueError("output_ids must be a list")
        if not isinstance(self.release_id, str) or not self.release_id:
            raise ValueError("release_id must be nonempty")

        try:
            json.dumps(self.resolved_config, sort_keys=True)
        except (TypeError, ValueError) as error:
            raise ValueError("resolved_config must be JSON serializable") from error

        object.__setattr__(self, "input_ids", ImmutableList(self.input_ids))
        object.__setattr__(self, "output_ids", ImmutableList(self.output_ids))

    def to_dict(self) -> dict:
        """Return the event in its stable field declaration order."""
        return asdict(self)
