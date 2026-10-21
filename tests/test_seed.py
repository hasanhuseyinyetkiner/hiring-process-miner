from hpm.domain.metrics import directly_follows, insights, performance
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


def test_seed_is_deterministic_and_within_bounds() -> None:
    first = render_seed_csv(500, 42)
    second = render_seed_csv(500, 42)
    assert first == second
    assert render_seed_csv(500, 7) != first
    cases = generate_cases(500, 42)
    assert len(cases) == 500


def test_seed_interview_wait_is_the_longest_median() -> None:
    events = parse_csv(
        render_csv(generate_cases(800, 42), inject_quality_rows=False), MAPPING, "Europe/Berlin"
    )
    assert all(event.exclusion_reason is None for event in events)
    data = frame_from_parsed(events)
    graph = directly_follows(data)
    assert graph["total_cases"] == 800
    hero = insights(data)["cards"][0]
    assert hero["source_activity"] == "Interview Scheduled"
    assert hero["target_activity"] == "Interview Completed"
    assert hero["numerator"] >= 30
    assert hero["sample_size"] >= 30
    assert hero["value"] > 200 * 3600
    assert "not a causal root cause" in hero["caution"]
    transitions = performance(data)["transitions"]
    others = [
        row
        for row in transitions
        if (row["source"], row["target"]) != ("Interview Scheduled", "Interview Completed")
        and row["frequency"] >= 30
    ]
    assert others
    assert max(row["median_delay_seconds"] for row in others) < 80 * 3600


def test_seed_csv_quality_counts_are_exact() -> None:
    events = parse_csv(render_seed_csv(500, 42), MAPPING, "Europe/Berlin")
    report = quality_report(events, timezone="Europe/Berlin")
    assert report["unique_cases"] == 500
    assert report["duplicate_count"] == 1
    assert report["missing_case_id"] == 1
    assert report["missing_activity"] == 1
    assert report["parse_failures"] == 1
    assert report["ambiguous_timestamps"] == 1
    assert report["nonexistent_timestamps"] == 1
    assert report["invalid_cost_warnings"] == 1
    assert report["privacy_notice"]


def test_seed_800_eligible_excludes_qx_probes_and_matches_bottleneck() -> None:
    events = parse_csv(render_seed_csv(800, 42), MAPPING, "Europe/Berlin")
    report = quality_report(events, timezone="Europe/Berlin")
    assert report["unique_cases"] == 800
    assert report["excluded_event_count"] >= 5
    qx_eligible = [
        event
        for event in events
        if event.case_id and str(event.case_id).startswith("QX") and event.exclusion_reason is None
    ]
    assert qx_eligible == []
    qx_excluded = {
        str(event.case_id)
        for event in events
        if event.case_id and str(event.case_id).startswith("QX") and event.exclusion_reason
    }
    assert qx_excluded == {"QX1", "QX2", "QX3", "QX4"}
    data = frame_from_parsed(events)
    hero = insights(data)["cards"][0]
    assert hero["source_activity"] == "Interview Scheduled"
    assert hero["target_activity"] == "Interview Completed"
    assert hero["value"] is not None
    days = float(hero["value"]) / 86_400
    assert 14.6 < days < 14.8
    assert abs(days - 14.6825) < 0.01
    assert hero["numerator"] == 592
    assert hero["sample_size"] == 504
