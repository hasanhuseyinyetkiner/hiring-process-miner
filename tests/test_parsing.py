from hpm.domain.constants import DUPLICATE_RULE
from hpm.domain.parsing import FieldMapping, parse_csv
from hpm.domain.quality import quality_report

MAPPING = FieldMapping(
    case_id="case_id",
    activity="activity",
    timestamp="timestamp",
    resource="resource",
    cost="cost",
)


def test_duplicate_keeps_first_source_row_and_retains_repeats() -> None:
    csv_text = "\n".join(
        [
            "case_id,activity,timestamp,resource,cost",
            "A,Interview Completed,2026-01-02T00:00:00Z,interviewer-1,10",
            "A,Interview Completed,2026-01-02T00:00:00Z,interviewer-1,10",
            "A,Interview Completed,2026-01-09T00:00:00Z,interviewer-1,10",
        ]
    )
    events = parse_csv(csv_text, MAPPING, "UTC")
    assert events[0].exclusion_reason is None
    assert events[1].exclusion_reason == "duplicate"
    assert events[2].exclusion_reason is None
    report = quality_report(events, timezone="UTC")
    assert report["duplicate_count"] == 1
    assert report["eligible_event_count"] == 2
    assert DUPLICATE_RULE in str(report["duplicate_rule"])


def test_dst_rows_are_excluded_and_repeated_activity_is_not_a_duplicate() -> None:
    csv_text = "\n".join(
        [
            "case_id,activity,timestamp,resource,cost",
            "A,Applied,2026-06-15 12:00,recruiter-1,",
            "B,Applied,2026-10-25 02:30,recruiter-1,",
            "C,Applied,2026-03-29 02:30,recruiter-1,",
            "D,Applied,not-a-date,recruiter-1,",
            ",Applied,2026-06-15 12:00,recruiter-1,",
            "E,,2026-06-15 12:00,recruiter-1,",
            "F,Applied,,recruiter-1,",
            "G,Applied,2026-06-15 12:00,recruiter-1,nope",
        ]
    )
    events = parse_csv(csv_text, MAPPING, "Europe/Berlin")
    reasons = [event.exclusion_reason for event in events]
    assert reasons == [
        None,
        "ambiguous_local_time",
        "nonexistent_local_time",
        "timestamp_parse_failure",
        "missing_case_id",
        "missing_activity",
        "missing_timestamp",
        None,
    ]
    assert events[0].timestamp_utc is not None
    assert events[0].timestamp_utc.hour == 10
    assert events[-1].warning == "invalid_cost"
    assert events[-1].cost is None
    report = quality_report(events, timezone="Europe/Berlin")
    assert report["ambiguous_timestamps"] == 1
    assert report["nonexistent_timestamps"] == 1
    assert report["parse_failures"] == 1
    assert report["unique_cases"] == 2
    assert report["timezone_warnings"]


def test_unknown_timezone_and_missing_column_are_rejected() -> None:
    from hpm.errors import ImportRejected

    try:
        parse_csv(
            "case_id,activity,timestamp\nA,Applied,2026-01-01T00:00:00Z\n", MAPPING, "Mars/Base"
        )
    except ImportRejected as exc:
        assert exc.code == "unknown_timezone"
    else:
        raise AssertionError("expected unknown timezone")
    try:
        parse_csv("a,b\n1,2\n", MAPPING, "UTC")
    except ImportRejected as exc:
        assert exc.code == "missing_mapped_column"
    else:
        raise AssertionError("expected missing column")
