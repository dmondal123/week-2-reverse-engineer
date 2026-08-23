import json

import pytest

from rag_compare.contracts import StageEvent
from rag_compare.trace import JsonlTrace

STAGES = (
    "parse",
    "chunk",
    "embed",
    "index",
    "retrieve",
    "rerank",
    "pack",
    "generate",
)

FIELDS = (
    "run_id",
    "framework",
    "framework_commit",
    "path",
    "stage",
    "component",
    "source_reference",
    "started_at",
    "duration_ms",
    "resolved_config",
    "input_ids",
    "output_ids",
    "metadata_delta",
    "score_rank_delta",
    "release_id",
    "artifact_path",
    "status",
    "error",
)


def make_event(**overrides):
    values = {
        "run_id": "run-1",
        "framework": "haystack",
        "framework_commit": "abc123",
        "path": "baseline",
        "stage": "parse",
        "component": "parser",
        "source_reference": "corpus/policy.txt",
        "started_at": "2025-06-22T12:00:00Z",
        "duration_ms": 12.5,
        "resolved_config": {"chunk_size": 200},
        "input_ids": ["source-1"],
        "output_ids": ["document-1"],
        "metadata_delta": {"language": "en"},
        "score_rank_delta": {"document-1": {"rank": 1, "score": 0.9}},
        "release_id": "release-1",
        "artifact_path": "artifacts/run-1.jsonl",
        "status": "ok",
        "error": None,
    }
    values.update(overrides)
    return StageEvent(**values)


@pytest.mark.parametrize("stage", STAGES)
def test_stage_event_supports_each_pipeline_stage_and_has_the_contract_fields(stage):
    event = make_event(stage=stage)

    assert tuple(event.to_dict()) == FIELDS
    assert event.to_dict()["stage"] == stage


def test_trace_rejects_negative_duration(tmp_path):
    with pytest.raises(ValueError, match="duration_ms"):
        make_event(duration_ms=-0.1)


@pytest.mark.parametrize("field", ("input_ids", "output_ids"))
def test_stage_event_requires_identifier_collections_to_be_lists(field):
    with pytest.raises(ValueError, match=field):
        make_event(**{field: ("id-1",)})


def test_trace_rejects_non_json_serializable_resolved_config(tmp_path):
    with pytest.raises(ValueError, match="resolved_config"):
        make_event(resolved_config={"unsupported": {"value"}})


def test_trace_requires_a_nonempty_release_id(tmp_path):
    with pytest.raises(ValueError, match="release_id"):
        make_event(release_id="")


@pytest.mark.parametrize("field", ("input_ids", "output_ids"))
@pytest.mark.parametrize(
    "mutation",
    (
        lambda values: values.append("id-2"),
        lambda values: values.extend(["id-2"]),
        lambda values: values.insert(0, "id-0"),
        lambda values: values.remove("source-1"),
        lambda values: values.pop(),
        lambda values: values.clear(),
        lambda values: values.reverse(),
        lambda values: values.sort(),
        lambda values: values.__setitem__(0, "id-2"),
        lambda values: values.__setitem__(slice(0, 1), ["id-2"]),
        lambda values: values.__delitem__(0),
        lambda values: values.__delitem__(slice(0, 1)),
        lambda values: values.__iadd__(["id-2"]),
        lambda values: values.__imul__(2),
    ),
)
def test_stage_event_identifier_lists_are_immutable(field, mutation):
    input_ids = ["source-1"]
    output_ids = ["document-1"]
    event = make_event(input_ids=input_ids, output_ids=output_ids)

    assert isinstance(event.input_ids, list)
    assert isinstance(event.output_ids, list)

    input_ids.append("later")
    output_ids.append("later")

    assert event.input_ids == ["source-1"]
    assert event.output_ids == ["document-1"]

    with pytest.raises(TypeError, match="immutable"):
        mutation(getattr(event, field))


def test_trace_appends_sorted_json_and_fsyncs_each_event(tmp_path, monkeypatch):
    event = make_event()

    trace_path = tmp_path / "events.jsonl"

    fsync_calls = []
    monkeypatch.setattr("rag_compare.trace.os.fsync", fsync_calls.append)

    JsonlTrace(trace_path).append(event)

    assert fsync_calls and len(fsync_calls) == 1
    assert trace_path.read_text(encoding="utf-8") == (
        json.dumps(event.to_dict(), sort_keys=True, separators=(",", ":")) + "\n"
    )
