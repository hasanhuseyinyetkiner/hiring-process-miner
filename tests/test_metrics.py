"""Hand-computed expectations for a three-case log.

Day = 86400 seconds.

Case A (completed, Hired), cycle 24 days = 2073600 seconds
    Applied 2026-01-01, Screened +2d, Interview Scheduled +1d,
    Interview Completed +16d, Offer +2d, Hired +3d
Case B (completed, Rejected), cycle 2 days = 172800 seconds
    Applied 2026-01-01, Screened +1d, Rejected +1d
Case C (ongoing), same timestamp on Screened and Interview Scheduled.
    Source row orders Screened before Interview Scheduled. Delay is 0.
    Cycle time is excluded.

Applied → Screened delays: 2d, 1d, 1d = 172800, 86400, 86400
    mean = (172800 + 86400 + 86400) / 3 = 115200
    sorted 86400, 86400, 172800
    median = 86400
    p90 linear index = 0.9 * (3 - 1) = 1.8
    value = 86400 + 0.8 * (172800 - 86400) = 155520
    p95 linear index = 0.95 * (3 - 1) = 1.9
    value = 86400 + 0.9 * (172800 - 86400) = 164160

Screened → Interview Scheduled delays: 1d and 0
    mean = 43200
    median = 43200
    p90 linear index = 0.9 * (2 - 1) = 0.9
    value = 0 + 0.9 * 86400 = 77760
    p95 linear index = 0.95
    value = 0 + 0.95 * 86400 = 82080

Completed cycle times: 2073600 and 172800
    mean = (2073600 + 172800) / 2 = 1123200
    median = (2073600 + 172800) / 2 = 1123200
    p90 index = 0.9
    value = 172800 + 0.9 * (2073600 - 172800) = 1883520
    p95 index = 0.95
    value = 172800 + 0.95 * (2073600 - 172800) = 1978560
"""

from datetime import datetime

from tests.helpers import at, frame

from hpm.domain.filters import FilterSpec, filter_impact
from hpm.domain.metrics import (
    conformance,
    directly_follows,
    funnel,
    performance,
    rework,
    variants,
)
from hpm.domain.ordering import canonical_order
from hpm.domain.traces import elapsed_seconds

DAY = 86400


def golden():
    return frame(
        [
            {
                "case_id": "A",
                "activity": "Applied",
                "timestamp": at("2026-01-01T00:00:00Z"),
                "source_row": 1,
                "channel": "referral",
                "job_family": "engineering",
            },
            {
                "case_id": "A",
                "activity": "Screened",
                "timestamp": at("2026-01-03T00:00:00Z"),
                "source_row": 2,
                "channel": "referral",
                "job_family": "engineering",
            },
            {
                "case_id": "A",
                "activity": "Interview Scheduled",
                "timestamp": at("2026-01-04T00:00:00Z"),
                "source_row": 3,
                "channel": "referral",
                "job_family": "engineering",
            },
            {
                "case_id": "A",
                "activity": "Interview Completed",
                "timestamp": at("2026-01-20T00:00:00Z"),
                "source_row": 4,
                "channel": "referral",
                "job_family": "engineering",
            },
            {
                "case_id": "A",
                "activity": "Offer",
                "timestamp": at("2026-01-22T00:00:00Z"),
                "source_row": 5,
                "channel": "referral",
                "job_family": "engineering",
            },
            {
                "case_id": "A",
                "activity": "Hired",
                "timestamp": at("2026-01-25T00:00:00Z"),
                "source_row": 6,
                "channel": "referral",
                "job_family": "engineering",
                "outcome": "Hired",
            },
            {
                "case_id": "B",
                "activity": "Applied",
                "timestamp": at("2026-01-01T00:00:00Z"),
                "source_row": 7,
                "channel": "agency",
                "job_family": "design",
            },
            {
                "case_id": "B",
                "activity": "Screened",
                "timestamp": at("2026-01-02T00:00:00Z"),
                "source_row": 8,
                "channel": "agency",
                "job_family": "design",
            },
            {
                "case_id": "B",
                "activity": "Rejected",
                "timestamp": at("2026-01-03T00:00:00Z"),
                "source_row": 9,
                "channel": "agency",
                "job_family": "design",
                "outcome": "Rejected",
            },
            {
                "case_id": "C",
                "activity": "Applied",
                "timestamp": at("2026-01-05T00:00:00Z"),
                "source_row": 10,
                "channel": "referral",
                "job_family": "engineering",
            },
            {
                "case_id": "C",
                "activity": "Interview Scheduled",
                "timestamp": at("2026-01-06T00:00:00Z"),
                "source_row": 12,
                "channel": "referral",
                "job_family": "engineering",
            },
            {
                "case_id": "C",
                "activity": "Screened",
                "timestamp": at("2026-01-06T00:00:00Z"),
                "source_row": 11,
                "channel": "referral",
                "job_family": "engineering",
            },
        ]
    )


def test_equal_timestamps_break_ties_by_source_row() -> None:
    ordered = canonical_order(golden())
    case_c = ordered.loc[ordered["case_id"] == "C", "activity"].tolist()
    assert case_c == ["Applied", "Screened", "Interview Scheduled"]


def test_negative_duration_is_discarded_not_clamped() -> None:
    assert elapsed_seconds(datetime(2026, 1, 2), datetime(2026, 1, 1)) is None
    assert elapsed_seconds(datetime(2026, 1, 1), datetime(2026, 1, 1)) == 0


def test_graph_edge_counts_and_delays_match_hand_calculation() -> None:
    graph = directly_follows(golden(), min_case_ratio=0)
    edges = {(edge["source"], edge["target"]): edge for edge in graph["edges"]}
    assert graph["total_cases"] == 3
    applied = edges[("Applied", "Screened")]
    assert applied["frequency"] == 3
    assert applied["case_count"] == 3
    assert applied["mean_delay_seconds"] == 115200
    assert applied["median_delay_seconds"] == DAY
    assert applied["p90_delay_seconds"] == 155520
    assert applied["p95_delay_seconds"] == 164160
    scheduled = edges[("Screened", "Interview Scheduled")]
    assert scheduled["frequency"] == 2
    assert scheduled["case_count"] == 2
    assert scheduled["mean_delay_seconds"] == DAY / 2
    assert scheduled["median_delay_seconds"] == DAY / 2
    assert scheduled["p90_delay_seconds"] == 77760
    assert scheduled["p95_delay_seconds"] == 82080
    bottleneck = edges[("Interview Scheduled", "Interview Completed")]
    assert bottleneck["frequency"] == 1
    assert bottleneck["median_delay_seconds"] == 16 * DAY
    assert ("Screened", "Rejected") in edges
    hidden = directly_follows(golden(), min_case_ratio=0.9)
    hidden_pairs = {(edge["source"], edge["target"]) for edge in hidden["edges"]}
    assert ("Applied", "Screened") in hidden_pairs
    assert ("Interview Scheduled", "Interview Completed") not in hidden_pairs
    assert hidden["edges_before_filter"] > hidden["edges_after_filter"]


def test_cycle_time_excludes_ongoing_cases() -> None:
    perf = performance(golden())
    assert perf["completed_cases"] == 2
    assert perf["ongoing_cases"] == 1
    assert perf["cycle_time"]["sample_size"] == 2
    assert perf["cycle_time"]["mean_seconds"] == 1123200
    assert perf["cycle_time"]["median_seconds"] == 1123200
    assert perf["cycle_time"]["p90_seconds"] == 1883520
    assert perf["cycle_time"]["p95_seconds"] == 1978560
    assert perf["processing_time"] is None
    assert "not labeled as processing time" in str(perf["processing_time_reason"])
    assert perf["excluded_negative_cycle_cases"] == 0
    assert all(row["median_delay_seconds"] >= 0 for row in perf["transitions"])


def test_out_of_order_rows_follow_timestamp_then_source_row() -> None:
    scrambled = frame(
        [
            {
                "case_id": "Z",
                "activity": "Screened",
                "timestamp": at("2026-04-01T00:00:00Z"),
                "source_row": 5,
            },
            {
                "case_id": "Z",
                "activity": "Applied",
                "timestamp": at("2026-04-01T00:00:00Z"),
                "source_row": 4,
            },
            {
                "case_id": "Z",
                "activity": "Hired",
                "timestamp": at("2026-04-03T00:00:00Z"),
                "source_row": 2,
            },
        ]
    )
    ordered = canonical_order(scrambled)
    assert ordered["activity"].tolist() == ["Applied", "Screened", "Hired"]
    perf = performance(scrambled)
    assert perf["cycle_time"]["sample_size"] == 1
    assert perf["cycle_time"]["median_seconds"] == 2 * DAY


def test_funnel_denominator_and_drop_off() -> None:
    payload = funnel(golden())
    assert payload["denominator"] == 3
    by_stage = {stage["stage"]: stage for stage in payload["stages"]}
    assert by_stage["Applied"]["cases_reached"] == 3
    assert by_stage["Applied"]["share_of_denominator"] == 1
    assert by_stage["Interview Scheduled"]["cases_reached"] == 2
    assert by_stage["Hired"]["cases_reached"] == 1
    assert by_stage["Screened"]["drop_off_cases"] == 0
    assert by_stage["Interview Scheduled"]["drop_off_cases"] == 1
    assert by_stage["Interview Completed"]["drop_off_cases"] == 1
    exits = {item["activity"]: item["cases"] for item in payload["exits"]}
    assert exits["Rejected"] == 1
    assert exits["Withdrawn"] == 0


def test_variants_group_exact_sequences() -> None:
    payload = variants(golden(), limit=10)
    assert payload["variant_count"] == 3
    keys = [item["key"] for item in payload["variants"]]
    assert "Applied → Screened → Rejected" in keys
    hired = next(item for item in payload["variants"] if item["outcomes"].get("Hired") == 1)
    assert hired["cycle_sample_size"] == 1
    assert hired["median_cycle_seconds"] == 24 * DAY
    ongoing = next(item for item in payload["variants"] if "ongoing" in item["outcomes"])
    assert ongoing["median_cycle_seconds"] is None


def test_rework_counts_repeats_and_self_loops() -> None:
    data = frame(
        [
            {
                "case_id": "R",
                "activity": "Screened",
                "timestamp": at("2026-05-01T00:00:00Z"),
                "source_row": 1,
            },
            {
                "case_id": "R",
                "activity": "Screened",
                "timestamp": at("2026-05-02T00:00:00Z"),
                "source_row": 2,
            },
            {
                "case_id": "R",
                "activity": "Rejected",
                "timestamp": at("2026-05-03T00:00:00Z"),
                "source_row": 3,
            },
            {
                "case_id": "S",
                "activity": "Interview Scheduled",
                "timestamp": at("2026-05-01T00:00:00Z"),
                "source_row": 4,
            },
            {
                "case_id": "S",
                "activity": "Interview Completed",
                "timestamp": at("2026-05-02T00:00:00Z"),
                "source_row": 5,
            },
            {
                "case_id": "S",
                "activity": "Interview Scheduled",
                "timestamp": at("2026-05-03T00:00:00Z"),
                "source_row": 6,
            },
        ]
    )
    payload = rework(data)
    assert payload["cases_with_any_repeat"] == 2
    screened = next(item for item in payload["activities"] if item["activity"] == "Screened")
    assert screened["cases_with_repeat"] == 1
    assert screened["self_loop_frequency"] == 1
    assert screened["example_case_ids"] == ["R"]
    scheduled = next(
        item for item in payload["activities"] if item["activity"] == "Interview Scheduled"
    )
    assert scheduled["self_loop_frequency"] == 0
    assert scheduled["example_case_ids"] == ["S"]


def test_conformance_known_cases() -> None:
    fit = conformance(golden())
    assert fit["total_cases"] == 3
    assert fit["fitting_cases"] == 3
    deviant = frame(
        [
            {
                "case_id": "D",
                "activity": "Applied",
                "timestamp": at("2026-07-01T00:00:00Z"),
                "source_row": 1,
            },
            {
                "case_id": "D",
                "activity": "Hired",
                "timestamp": at("2026-07-02T00:00:00Z"),
                "source_row": 2,
            },
        ]
    )
    result = conformance(deviant)
    assert result["fitting_cases"] == 0
    assert result["numerator"] == 0
    assert result["sample_size"] == 1
    assert result["deviations"][0]["source"] == "Applied"
    assert result["deviations"][0]["target"] == "Hired"
    assert "PM4Py" in str(result["method"])


def test_filters_change_graph_and_performance_together() -> None:
    spec = FilterSpec(channels=frozenset({"referral"}))
    graph = directly_follows(golden())
    from hpm.domain.filters import apply_filters

    filtered = apply_filters(golden(), spec)
    graph_filtered = directly_follows(filtered)
    perf_filtered = performance(filtered)
    funnel_all = funnel(golden())
    funnel_filtered = funnel(filtered)
    impact = filter_impact(golden(), filtered)
    assert graph["total_cases"] == 3
    assert graph_filtered["total_cases"] == 2
    assert graph_filtered["total_cases"] == perf_filtered["total_cases"]
    assert funnel_filtered["denominator"] == 2
    assert funnel_filtered["denominator"] < funnel_all["denominator"]
    assert impact["cases_before"] == 3
    assert impact["cases_after"] == 2
    assert impact["cases_retained_ratio"] == 2 / 3
    assert impact["events_after"] < impact["events_before"]
    assert "not a causal" in str(impact["caution"]).lower()
    ongoing = apply_filters(golden(), FilterSpec(case_status="ongoing"))
    assert directly_follows(ongoing)["total_cases"] == 1
    assert performance(ongoing)["completed_cases"] == 0
    assert performance(ongoing)["cycle_time"]["sample_size"] == 0
    assert funnel(ongoing)["denominator"] == 1


def test_empty_and_single_event_logs() -> None:
    empty = frame([])
    assert directly_follows(empty)["total_cases"] == 0
    assert funnel(empty)["denominator"] == 0
    assert performance(empty)["cycle_time"]["median_seconds"] is None
    one = frame(
        [
            {
                "case_id": "ONLY",
                "activity": "Applied",
                "timestamp": at("2026-08-01T00:00:00Z"),
                "source_row": 1,
            }
        ]
    )
    assert directly_follows(one)["edges"] == []
    assert performance(one)["ongoing_cases"] == 1
    assert performance(one)["cycle_time"]["sample_size"] == 0
    aging = performance(one)
    assert aging["active_aging"]["sample_size"] == 1
    assert aging["active_aging"]["median_seconds_since_last_event"] == 0
