"""Event-log integrity: exclusions, ordering, QX probes, incomplete traces.

The CSV schema has no separate event_id column. Duplicate detection uses the
documented composite key (case_id, activity, UTC timestamp, attributes).
"""

from __future__ import annotations

from tests.helpers import at, frame

from hpm.domain.metrics import directly_follows, funnel, performance
from hpm.domain.parsing import FieldMapping, parse_csv
from hpm.domain.quality import quality_report
from hpm.domain.seedgen import generate_cases, render_csv, render_seed_csv
from hpm.services.frames import frame_from_parsed

MAPPING = FieldMapping(
    case_id="case_id",
    activity="activity",
    timestamp="timestamp",
    resource="resource",
    role="role",
    channel="channel",
    outcome="outcome",
    cost="cost",
    job_family="job_family",
)


def test_composite_duplicate_excludes_later_row_not_the_case() -> None:
    csv_text = "\n".join(
        [
            "case_id,activity,timestamp,resource,role,channel,outcome,cost,job_family",
            "A,Applied,2026-01-01T00:00:00Z,r1,coord,careers,,0,engineering",
            "A,Applied,2026-01-01T00:00:00Z,r1,coord,careers,,0,engineering",
            "A,Hired,2026-01-02T00:00:00Z,r1,hm,careers,Hired,0,engineering",
        ]
    )
    events = parse_csv(csv_text, MAPPING, "UTC")
    assert [event.exclusion_reason for event in events] == [None, "duplicate", None]
    report = quality_report(events, timezone="UTC")
    assert report["duplicate_count"] == 1
    assert report["unique_cases"] == 1
    assert report["eligible_event_count"] == 2
    data = frame_from_parsed(events)
    assert directly_follows(data)["total_cases"] == 1
    assert performance(data)["completed_cases"] == 1


def test_missing_case_id_never_enters_unique_cases_or_dfg() -> None:
    csv_text = "\n".join(
        [
            "case_id,activity,timestamp",
            ",Applied,2026-01-01T00:00:00Z",
            "KEEP,Applied,2026-01-01T00:00:00Z",
            "KEEP,Screened,2026-01-02T00:00:00Z",
        ]
    )
    mapping = FieldMapping(case_id="case_id", activity="activity", timestamp="timestamp")
    events = parse_csv(csv_text, mapping, "UTC")
    assert events[0].exclusion_reason == "missing_case_id"
    report = quality_report(events, timezone="UTC")
    assert report["missing_case_id"] == 1
    assert report["unique_cases"] == 1
    data = frame_from_parsed(events)
    assert directly_follows(data)["total_cases"] == 1
    assert funnel(data)["denominator"] == 1


def test_identical_timestamps_order_by_source_row_and_zero_delay() -> None:
    data = frame(
        [
            {
                "case_id": "T",
                "activity": "Interview Scheduled",
                "timestamp": at("2026-03-01T12:00:00Z"),
                "source_row": 20,
            },
            {
                "case_id": "T",
                "activity": "Screened",
                "timestamp": at("2026-03-01T12:00:00Z"),
                "source_row": 10,
            },
            {
                "case_id": "T",
                "activity": "Applied",
                "timestamp": at("2026-03-01T11:00:00Z"),
                "source_row": 5,
            },
        ]
    )
    graph = directly_follows(data)
    edges = {(edge["source"], edge["target"]): edge for edge in graph["edges"]}
    assert ("Screened", "Interview Scheduled") in edges
    assert edges[("Screened", "Interview Scheduled")]["mean_delay_seconds"] == 0
    assert edges[("Screened", "Interview Scheduled")]["median_delay_seconds"] == 0
    assert edges[("Screened", "Interview Scheduled")]["p90_delay_seconds"] == 0


def test_incomplete_trace_is_ongoing_and_excluded_from_cycle_time() -> None:
    data = frame(
        [
            {
                "case_id": "OPEN",
                "activity": "Applied",
                "timestamp": at("2026-04-01T00:00:00Z"),
                "source_row": 1,
            },
            {
                "case_id": "OPEN",
                "activity": "Screened",
                "timestamp": at("2026-04-02T00:00:00Z"),
                "source_row": 2,
            },
            {
                "case_id": "DONE",
                "activity": "Applied",
                "timestamp": at("2026-04-01T00:00:00Z"),
                "source_row": 3,
            },
            {
                "case_id": "DONE",
                "activity": "Rejected",
                "timestamp": at("2026-04-03T00:00:00Z"),
                "source_row": 4,
            },
        ]
    )
    perf = performance(data)
    assert perf["total_cases"] == 2
    assert perf["ongoing_cases"] == 1
    assert perf["completed_cases"] == 1
    assert perf["cycle_time"]["sample_size"] == 1
    assert perf["cycle_time"]["mean_seconds"] == 2 * 86_400
    assert perf["cycle_time"]["median_seconds"] == 2 * 86_400
    assert funnel(data)["denominator"] == 2


def test_unknown_activity_is_retained_not_silently_dropped() -> None:
    csv_text = "\n".join(
        [
            "case_id,activity,timestamp",
            "U,Applied,2026-05-01T00:00:00Z",
            "U,Background Check,2026-05-02T00:00:00Z",
            "U,Hired,2026-05-03T00:00:00Z",
        ]
    )
    mapping = FieldMapping(case_id="case_id", activity="activity", timestamp="timestamp")
    events = parse_csv(csv_text, mapping, "UTC")
    assert all(event.exclusion_reason is None for event in events)
    data = frame_from_parsed(events)
    graph = directly_follows(data)
    pairs = {(edge["source"], edge["target"]) for edge in graph["edges"]}
    assert ("Applied", "Background Check") in pairs
    assert ("Background Check", "Hired") in pairs


def test_generate_cases_800_has_no_qx_and_seed_csv_keeps_eligible_at_800() -> None:
    cases = generate_cases(800, 42)
    assert len(cases) == 800
    case_ids = {row["case_id"] for case in cases for row in case}
    assert len(case_ids) == 800
    assert not any(case_id.startswith("QX") for case_id in case_ids)

    clean = parse_csv(render_csv(cases, inject_quality_rows=False), MAPPING, "Europe/Berlin")
    assert quality_report(clean, timezone="Europe/Berlin")["unique_cases"] == 800

    seeded = parse_csv(render_seed_csv(800, 42), MAPPING, "Europe/Berlin")
    report = quality_report(seeded, timezone="Europe/Berlin")
    assert report["unique_cases"] == 800
    qx_rows = [event for event in seeded if event.case_id and str(event.case_id).startswith("QX")]
    assert qx_rows
    assert all(event.exclusion_reason for event in qx_rows)
    data = frame_from_parsed(seeded)
    assert directly_follows(data)["total_cases"] == 800
    assert funnel(data)["denominator"] == 800
