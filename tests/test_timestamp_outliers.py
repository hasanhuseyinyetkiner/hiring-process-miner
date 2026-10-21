"""Timestamp outlier policy: exclude DST/parse failures; retain extreme valid instants."""

from datetime import datetime

from hpm.domain.constants import TIMESTAMP_OUTLIER_POLICY
from hpm.domain.parsing import FieldMapping, parse_csv
from hpm.domain.quality import quality_report
from hpm.domain.timestamps import local_naive_to_utc
from hpm.domain.traces import elapsed_seconds

MAPPING = FieldMapping(case_id="case_id", activity="activity", timestamp="timestamp")


def test_policy_string_documents_no_clamping() -> None:
    assert "not by clamping" in TIMESTAMP_OUTLIER_POLICY
    assert "Ambiguous" in TIMESTAMP_OUTLIER_POLICY
    assert "Negative elapsed" in TIMESTAMP_OUTLIER_POLICY


def test_dst_and_parse_failures_excluded_extreme_valid_retained() -> None:
    csv_text = "\n".join(
        [
            "case_id,activity,timestamp",
            "FAR,Applied,1900-01-01T00:00:00Z",
            "FUTURE,Applied,2099-12-31T23:59:59Z",
            "AMB,Applied,2026-10-25 02:30",
            "GAP,Applied,2026-03-29 02:30",
            "BAD,Applied,not-a-date",
            "OK,Applied,2026-06-15 12:00",
        ]
    )
    events = parse_csv(csv_text, MAPPING, "Europe/Berlin")
    by_case = {event.case_id: event for event in events}
    assert by_case["FAR"].exclusion_reason is None
    assert by_case["FUTURE"].exclusion_reason is None
    assert by_case["AMB"].exclusion_reason == "ambiguous_local_time"
    assert by_case["GAP"].exclusion_reason == "nonexistent_local_time"
    assert by_case["BAD"].exclusion_reason == "timestamp_parse_failure"
    assert by_case["OK"].exclusion_reason is None
    report = quality_report(events, timezone="Europe/Berlin")
    assert report["ambiguous_timestamps"] == 1
    assert report["nonexistent_timestamps"] == 1
    assert report["parse_failures"] == 1
    assert report["unique_cases"] == 3


def test_negative_span_discarded_not_clamped() -> None:
    assert elapsed_seconds(datetime(2099, 1, 2), datetime(1900, 1, 1)) is None
    instant, reason = local_naive_to_utc(datetime(2026, 10, 25, 2, 30), "Europe/Berlin")
    assert instant is None
    assert reason == "ambiguous_local_time"
