"""Directly-follows graph, performance, funnel, variants, rework, conformance, insights."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime

import pandas as pd

from hpm.domain.constants import (
    AS_OF_DEFINITION,
    CAUSAL_CAUTION,
    CYCLE_TIME_DEFINITION,
    DEFAULT_ALLOWED_TRANSITIONS,
    DELAY_DEFINITION,
    DROP_OFF_DEFINITION,
    EXIT_ACTIVITIES,
    FUNNEL_DENOMINATOR,
    HAPPY_PATH,
    MIN_OBSERVATIONS,
    ORDERING_CONTRACT,
    P90_METHOD,
    P95_METHOD,
    PROCESSING_TIME_REASON,
)
from hpm.domain.filters import FilterSpec, apply_filters
from hpm.domain.ordering import canonical_order
from hpm.domain.stats import distribution
from hpm.domain.traces import CaseTrace, build_traces, elapsed_seconds


def _iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.strftime("%Y-%m-%dT%H:%M:%SZ")


def transition_records(traces: list[CaseTrace]) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for trace in traces:
        for index in range(len(trace.activities) - 1):
            delay = elapsed_seconds(trace.timestamps[index], trace.timestamps[index + 1])
            if delay is None:
                continue
            records.append(
                {
                    "case_id": trace.case_id,
                    "source": trace.activities[index],
                    "target": trace.activities[index + 1],
                    "delay_seconds": delay,
                }
            )
    return records


def _edge_rows(records: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for record in records:
        grouped[(str(record["source"]), str(record["target"]))].append(record)
    rows: list[dict[str, object]] = []
    for (source, target), items in grouped.items():
        delays = [float(item["delay_seconds"]) for item in items]
        cases = {str(item["case_id"]) for item in items}
        stats = distribution(delays)
        rows.append(
            {
                "source": source,
                "target": target,
                "frequency": int(stats["n"]),
                "case_count": len(cases),
                "mean_delay_seconds": stats["mean"],
                "median_delay_seconds": stats["median"],
                "p90_delay_seconds": stats["p90"],
                "p95_delay_seconds": stats["p95"],
                "delay_sample_size": int(stats["n"]),
            }
        )
    rows.sort(
        key=lambda row: (
            -(
                float(row["median_delay_seconds"])
                if row["median_delay_seconds"] is not None
                else -1
            ),
            -int(row["frequency"]),
            str(row["source"]),
            str(row["target"]),
        )
    )
    return rows


def directly_follows(df: pd.DataFrame | None, *, min_case_ratio: float = 0.0) -> dict[str, object]:
    """Frequency and case-count DFG. ``min_case_ratio`` hides infrequent edges only."""
    ratio = min(1.0, max(0.0, float(min_case_ratio)))
    traces = build_traces(df)
    total_cases = len(traces)
    total_events = sum(len(trace.activities) for trace in traces)
    node_events: dict[str, int] = defaultdict(int)
    node_cases: dict[str, set[str]] = defaultdict(set)
    for trace in traces:
        seen: set[str] = set()
        for activity in trace.activities:
            node_events[activity] += 1
            if activity not in seen:
                node_cases[activity].add(trace.case_id)
                seen.add(activity)
    edges = _edge_rows(transition_records(traces))
    for edge in edges:
        case_count = int(edge["case_count"])
        edge["case_ratio"] = (case_count / total_cases) if total_cases else 0.0
        edge["id"] = f"{edge['source']}→{edge['target']}"
    visible = [edge for edge in edges if float(edge["case_ratio"]) >= ratio - 1e-12]
    nodes = [
        {
            "id": activity,
            "activity": activity,
            "event_count": node_events[activity],
            "case_count": len(node_cases[activity]),
        }
        for activity in sorted(node_events, key=lambda name: (-len(node_cases[name]), name))
    ]
    return {
        "ordering": ORDERING_CONTRACT,
        "delay_definition": DELAY_DEFINITION,
        "total_cases": total_cases,
        "total_events": total_events,
        "min_case_ratio": ratio,
        "edges_before_filter": len(edges),
        "edges_after_filter": len(visible),
        "nodes": nodes,
        "edges": visible,
    }


def _stage_time_to_next(records: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[str, list[float]] = defaultdict(list)
    for record in records:
        grouped[str(record["source"])].append(float(record["delay_seconds"]))
    rows = []
    for activity, delays in grouped.items():
        stats = distribution(delays)
        rows.append(
            {
                "activity": activity,
                "sample_size": int(stats["n"]),
                "mean_seconds": stats["mean"],
                "median_seconds": stats["median"],
                "p90_seconds": stats["p90"],
                "p95_seconds": stats["p95"],
                "method": (
                    "Time from this event until the next event in the same case. "
                    + DELAY_DEFINITION
                ),
            }
        )
    rows.sort(key=lambda row: str(row["activity"]))
    return rows


def performance(
    df: pd.DataFrame | None,
    *,
    as_of: datetime | None = None,
) -> dict[str, object]:
    traces = build_traces(df)
    cycles = [trace.cycle_seconds for trace in traces if trace.completed]
    negative = sum(1 for value in cycles if value is None)
    usable = [float(value) for value in cycles if value is not None]
    cycle_stats = distribution(usable)
    ongoing = [trace for trace in traces if not trace.completed]
    latest = None
    for trace in traces:
        if latest is None or trace.timestamps[-1] > latest:
            latest = trace.timestamps[-1]
    resolved_as_of = as_of or latest
    ages_last: list[float] = []
    ages_start: list[float] = []
    invalid_age = 0
    if resolved_as_of is not None:
        for trace in ongoing:
            since_last = elapsed_seconds(trace.timestamps[-1], resolved_as_of)
            since_start = elapsed_seconds(trace.timestamps[0], resolved_as_of)
            if since_last is None or since_start is None:
                invalid_age += 1
                continue
            ages_last.append(since_last)
            ages_start.append(since_start)
    last_stats = distribution(ages_last)
    start_stats = distribution(ages_start)
    records = transition_records(traces)
    return {
        "ordering": ORDERING_CONTRACT,
        "total_cases": len(traces),
        "completed_cases": sum(1 for trace in traces if trace.completed),
        "ongoing_cases": len(ongoing),
        "excluded_negative_cycle_cases": negative,
        "cycle_time": {
            "sample_size": int(cycle_stats["n"]),
            "sample_definition": (
                "Completed cases with a non-negative span from the first event to the "
                "earliest terminal event. Ongoing cases are excluded."
            ),
            "mean_seconds": cycle_stats["mean"],
            "median_seconds": cycle_stats["median"],
            "p90_seconds": cycle_stats["p90"],
            "p95_seconds": cycle_stats["p95"],
            "method": (
                f"{CYCLE_TIME_DEFINITION} Mean: {cycle_stats['mean_method']}. "
                f"Median: {cycle_stats['median_method']}. P90: {cycle_stats['p90_method']}. "
                f"P95: {cycle_stats['p95_method']}."
            ),
        },
        "transitions": _edge_rows(records),
        "stage_time_to_next": _stage_time_to_next(records),
        "active_aging": {
            "as_of": _iso(resolved_as_of),
            "as_of_definition": AS_OF_DEFINITION,
            "sample_size": int(last_stats["n"]),
            "invalid_age_cases": invalid_age,
            "mean_seconds_since_last_event": last_stats["mean"],
            "median_seconds_since_last_event": last_stats["median"],
            "p90_seconds_since_last_event": last_stats["p90"],
            "p95_seconds_since_last_event": last_stats["p95"],
            "mean_seconds_since_start": start_stats["mean"],
            "median_seconds_since_start": start_stats["median"],
            "p90_seconds_since_start": start_stats["p90"],
            "p95_seconds_since_start": start_stats["p95"],
            "method": (
                "Ongoing cases only. Age is as_of minus the last event, and as_of minus "
                "the first event. Negative ages are excluded and counted."
            ),
        },
        "processing_time": None,
        "processing_time_reason": PROCESSING_TIME_REASON,
    }


def funnel(df: pd.DataFrame | None) -> dict[str, object]:
    traces = build_traces(df)
    denominator = len(traces)
    present = {trace.case_id: set(trace.activities) for trace in traces}
    stages: list[dict[str, object]] = []
    for index, stage in enumerate(HAPPY_PATH):
        reached = {case_id for case_id, activities in present.items() if stage in activities}
        previous = HAPPY_PATH[index - 1] if index else None
        both: set[str] = set()
        previous_reached: set[str] = set()
        if previous is not None:
            previous_reached = {
                case_id for case_id, activities in present.items() if previous in activities
            }
            both = reached & previous_reached
        share = (len(reached) / denominator) if denominator else None
        stages.append(
            {
                "stage": stage,
                "cases_reached": len(reached),
                "share_of_denominator": share,
                "previous_stage": previous,
                "cases_reached_previous": None if previous is None else len(previous_reached),
                "cases_reached_both": None if previous is None else len(both),
                "drop_off_cases": None if previous is None else len(previous_reached - reached),
                "drop_off_definition": None if previous is None else DROP_OFF_DEFINITION,
            }
        )
    exits = []
    for activity in EXIT_ACTIVITIES:
        count = sum(1 for activities in present.values() if activity in activities)
        exits.append({"activity": activity, "cases": count})
    return {
        "ordering": ORDERING_CONTRACT,
        "denominator": denominator,
        "denominator_definition": FUNNEL_DENOMINATOR,
        "counting": (
            "Presence of the activity anywhere in the filtered case. Sequence problems "
            "are reported by conformance, not subtracted inside the funnel."
        ),
        "stages": stages,
        "exits": exits,
    }


def _variant_payload(traces: list[CaseTrace], key: str, rank: int, total: int) -> dict[str, object]:
    activities = key.split(" → ") if key else []
    # Rebuild activities from the first trace so empty keys cannot appear.
    if traces:
        activities = list(traces[0].activities)
        key = " → ".join(activities)
    cycles = [trace.cycle_seconds for trace in traces if trace.completed]
    usable = [float(value) for value in cycles if value is not None]
    stats = distribution(usable)
    outcomes: dict[str, int] = defaultdict(int)
    for trace in traces:
        outcomes[trace.outcome] += 1
    return {
        "rank": rank,
        "key": key,
        "activities": activities,
        "case_count": len(traces),
        "share": (len(traces) / total) if total else None,
        "sample_size": total,
        "sample_definition": "Distinct cases in the filtered log.",
        "completed_cases": sum(1 for trace in traces if trace.completed),
        "mean_cycle_seconds": stats["mean"],
        "median_cycle_seconds": stats["median"],
        "p90_cycle_seconds": stats["p90"],
        "p95_cycle_seconds": stats["p95"],
        "cycle_sample_size": int(stats["n"]),
        "cycle_method": CYCLE_TIME_DEFINITION,
        "outcomes": dict(sorted(outcomes.items())),
        "event_length": len(activities),
    }


def variants(df: pd.DataFrame | None, *, limit: int = 15) -> dict[str, object]:
    traces = build_traces(df)
    grouped: dict[str, list[CaseTrace]] = defaultdict(list)
    for trace in traces:
        grouped[" → ".join(trace.activities)].append(trace)
    ordered = sorted(grouped.items(), key=lambda item: (-len(item[1]), item[0]))
    shown = ordered[: max(0, limit)]
    total = len(traces)
    return {
        "ordering": ORDERING_CONTRACT,
        "total_cases": total,
        "variant_count": len(ordered),
        "shown": len(shown),
        "variants": [
            _variant_payload(items, key, rank, total)
            for rank, (key, items) in enumerate(shown, start=1)
        ],
    }


def compare_variants(df: pd.DataFrame | None, key_a: str, key_b: str) -> dict[str, object]:
    traces = build_traces(df)
    grouped: dict[str, list[CaseTrace]] = defaultdict(list)
    for trace in traces:
        grouped[" → ".join(trace.activities)].append(trace)
    total = len(traces)

    def one(key: str) -> dict[str, object] | None:
        items = grouped.get(key)
        if not items:
            return None
        return _variant_payload(items, key, 0, total)

    left = one(key_a)
    right = one(key_b)
    return {
        "ordering": ORDERING_CONTRACT,
        "a": left,
        "b": right,
        "same_activity_sequence": key_a == key_b,
    }


def rework(df: pd.DataFrame | None) -> dict[str, object]:
    traces = build_traces(df)
    total = len(traces)
    repeats: dict[str, list[str]] = defaultdict(list)
    self_loops: dict[str, int] = defaultdict(int)
    cases_with_repeat: set[str] = set()
    for trace in traces:
        counts: dict[str, int] = defaultdict(int)
        for activity in trace.activities:
            counts[activity] += 1
        for activity, count in counts.items():
            if count >= 2:
                repeats[activity].append(trace.case_id)
                cases_with_repeat.add(trace.case_id)
        for index in range(len(trace.activities) - 1):
            if trace.activities[index] == trace.activities[index + 1]:
                self_loops[trace.activities[index]] += 1
    activities = []
    for activity, case_ids in sorted(repeats.items(), key=lambda item: (-len(item[1]), item[0])):
        activities.append(
            {
                "activity": activity,
                "cases_with_repeat": len(case_ids),
                "numerator": len(case_ids),
                "numerator_definition": "Cases in which this activity occurs at least twice.",
                "sample_size": total,
                "sample_size_definition": "Distinct cases in the filtered log.",
                "self_loop_frequency": int(self_loops.get(activity, 0)),
                "example_case_ids": case_ids[:5],
                "method": (
                    "A repeat is an activity count of at least two after canonical ordering. "
                    "A self-loop is two consecutive events with the same activity. Example "
                    "ids are anonymous case identifiers and are capped at five."
                ),
            }
        )
    return {
        "ordering": ORDERING_CONTRACT,
        "total_cases": total,
        "cases_with_any_repeat": len(cases_with_repeat),
        "activities": activities,
    }


def conformance(
    df: pd.DataFrame | None,
    transitions: tuple[tuple[str, str], ...] | list[tuple[str, str]] | None = None,
) -> dict[str, object]:
    allowed = set(transitions or DEFAULT_ALLOWED_TRANSITIONS)
    traces = build_traces(df)
    fitting = 0
    deviations: dict[tuple[str, str], list[str]] = defaultdict(list)
    deviation_frequency: dict[tuple[str, str], int] = defaultdict(int)
    for trace in traces:
        bad = False
        seen_pairs: set[tuple[str, str]] = set()
        for index in range(len(trace.activities) - 1):
            pair = (trace.activities[index], trace.activities[index + 1])
            if pair not in allowed:
                bad = True
                deviation_frequency[pair] += 1
                if pair not in seen_pairs:
                    deviations[pair].append(trace.case_id)
                    seen_pairs.add(pair)
        if not bad:
            fitting += 1
    rows = []
    for pair, case_ids in deviations.items():
        rows.append(
            {
                "source": pair[0],
                "target": pair[1],
                "frequency": int(deviation_frequency[pair]),
                "case_count": len(case_ids),
                "example_case_ids": case_ids[:5],
            }
        )
    rows.sort(key=lambda row: (-int(row["case_count"]), str(row["source"]), str(row["target"])))
    total = len(traces)
    return {
        "ordering": ORDERING_CONTRACT,
        "method": (
            "A case fits when every consecutive pair after canonical ordering is in the "
            "allowed-transition model. This check does not use PM4Py."
        ),
        "total_cases": total,
        "fitting_cases": fitting,
        "numerator": fitting,
        "numerator_definition": "Cases whose every consecutive transition is allowed.",
        "sample_size": total,
        "sample_size_definition": "Distinct cases in the filtered log.",
        "fit_rate": (fitting / total) if total else None,
        "deviations": rows,
        "allowed_transitions": [
            {"source": source, "target": target} for source, target in sorted(allowed)
        ],
    }


def _delay_card(
    rows: list[dict[str, object]],
    *,
    card_id: str,
    title: str,
    value_key: str,
    adjective: str,
    min_observations: int,
) -> dict[str, object]:
    eligible = [row for row in rows if int(row["frequency"]) >= min_observations]
    if "p95" in value_key:
        percentile_method = P95_METHOD
    elif "p90" in value_key:
        percentile_method = P90_METHOD
    else:
        percentile_method = "numpy.median"
    method = (
        f"{DELAY_DEFINITION} The {adjective} is taken over edges with at least "
        f"{min_observations} observed transitions. {value_key} uses "
        f"{percentile_method}."
    )
    if not eligible:
        return {
            "id": card_id,
            "title": title,
            "statement": (
                f"No transition has at least {min_observations} observations in the "
                "current filter. The threshold was not lowered."
            ),
            "numerator": 0,
            "numerator_definition": "Observed transitions of the selected edge.",
            "sample_size": 0,
            "sample_size_definition": "Distinct cases that contribute at least one such transition.",
            "value": None,
            "unit": "seconds",
            "method": method,
            "caution": CAUSAL_CAUTION,
            "source_activity": None,
            "target_activity": None,
        }
    selected = max(
        eligible,
        key=lambda row: (
            float(row[value_key]) if row[value_key] is not None else -1.0,
            int(row["frequency"]),
            f"{row['source']}→{row['target']}",
        ),
    )
    source = str(selected["source"])
    target = str(selected["target"])
    return {
        "id": card_id,
        "title": title,
        "statement": (
            f"{source} → {target} has the highest {adjective} among steps with at least "
            f"{min_observations} observations."
        ),
        "numerator": int(selected["frequency"]),
        "numerator_definition": "Observed transitions of this edge included in the statistic.",
        "sample_size": int(selected["case_count"]),
        "sample_size_definition": "Distinct cases that contribute at least one such transition.",
        "value": selected[value_key],
        "unit": "seconds",
        "method": method,
        "caution": CAUSAL_CAUTION,
        "source_activity": source,
        "target_activity": target,
    }


def insights(
    df: pd.DataFrame | None,
    *,
    min_observations: int = MIN_OBSERVATIONS,
    as_of: datetime | None = None,
) -> dict[str, object]:
    del as_of  # Aging is reported on the performance payload; delay cards do not use it.
    threshold = max(1, int(min_observations))
    perf = performance(df)
    funnel_payload = funnel(df)
    rework_payload = rework(df)
    transitions = list(perf["transitions"])
    cards = [
        _delay_card(
            transitions,
            card_id="highest_median_transition_delay",
            title="Highest median transition delay",
            value_key="median_delay_seconds",
            adjective="median transition delay",
            min_observations=threshold,
        ),
        _delay_card(
            transitions,
            card_id="highest_p90_transition_delay",
            title="Highest p90 transition delay",
            value_key="p90_delay_seconds",
            adjective="p90 transition delay",
            min_observations=threshold,
        ),
    ]
    stages = [stage for stage in funnel_payload["stages"] if stage["drop_off_cases"] is not None]
    if stages and any(int(stage["drop_off_cases"]) > 0 for stage in stages):
        selected = max(stages, key=lambda stage: int(stage["drop_off_cases"]))
        previous = selected["previous_stage"]
        cards.append(
            {
                "id": "largest_happy_path_drop_off",
                "title": "Largest happy-path drop-off",
                "statement": (
                    f"{selected['drop_off_cases']} cases reached {previous} and did not "
                    f"reach {selected['stage']}."
                ),
                "numerator": int(selected["drop_off_cases"]),
                "numerator_definition": DROP_OFF_DEFINITION,
                "sample_size": int(selected["cases_reached_previous"]),
                "sample_size_definition": f"Cases that reached {previous}.",
                "value": float(selected["drop_off_cases"]),
                "unit": "cases",
                "method": FUNNEL_DENOMINATOR + " " + DROP_OFF_DEFINITION,
                "caution": CAUSAL_CAUTION,
                "source_activity": previous,
                "target_activity": selected["stage"],
            }
        )
    else:
        cards.append(
            {
                "id": "largest_happy_path_drop_off",
                "title": "Largest happy-path drop-off",
                "statement": "No happy-path stage has a positive presence-based drop-off.",
                "numerator": 0,
                "numerator_definition": DROP_OFF_DEFINITION,
                "sample_size": int(funnel_payload["denominator"]),
                "sample_size_definition": FUNNEL_DENOMINATOR,
                "value": 0.0,
                "unit": "cases",
                "method": FUNNEL_DENOMINATOR + " " + DROP_OFF_DEFINITION,
                "caution": CAUSAL_CAUTION,
                "source_activity": None,
                "target_activity": None,
            }
        )
    activities = list(rework_payload["activities"])
    if activities:
        top = activities[0]
        cards.append(
            {
                "id": "most_repeated_activity",
                "title": "Most repeated activity",
                "statement": (
                    f"{top['activity']} occurs at least twice in {top['cases_with_repeat']} cases."
                ),
                "numerator": int(top["cases_with_repeat"]),
                "numerator_definition": "Cases in which this activity occurs at least twice.",
                "sample_size": int(rework_payload["total_cases"]),
                "sample_size_definition": "Distinct cases in the filtered log.",
                "value": float(top["cases_with_repeat"]),
                "unit": "cases",
                "method": str(top["method"]),
                "caution": CAUSAL_CAUTION,
                "source_activity": top["activity"],
                "target_activity": None,
            }
        )
    else:
        cards.append(
            {
                "id": "most_repeated_activity",
                "title": "Most repeated activity",
                "statement": "No activity occurs twice in the same case under the current filter.",
                "numerator": 0,
                "numerator_definition": "Cases in which an activity occurs at least twice.",
                "sample_size": int(rework_payload["total_cases"]),
                "sample_size_definition": "Distinct cases in the filtered log.",
                "value": 0.0,
                "unit": "cases",
                "method": (
                    "A repeat is an activity count of at least two after canonical ordering."
                ),
                "caution": CAUSAL_CAUTION,
                "source_activity": None,
                "target_activity": None,
            }
        )
    return {
        "ordering": ORDERING_CONTRACT,
        "min_observations": threshold,
        "cards": cards,
    }


def filter_options(df: pd.DataFrame | None) -> dict[str, object]:
    frame = canonical_order(df)
    traces = build_traces(frame)
    channels = sorted({value for trace in traces for value in trace.channels if value})
    families = sorted({value for trace in traces for value in trace.job_families if value})
    outcomes = sorted({trace.outcome for trace in traces})
    time_min = None if frame.empty else _iso(pd.Timestamp(frame["timestamp"].min()).to_pydatetime())
    time_max = None if frame.empty else _iso(pd.Timestamp(frame["timestamp"].max()).to_pydatetime())
    return {
        "channels": channels,
        "job_families": families,
        "outcomes": outcomes,
        "time_min": time_min,
        "time_max": time_max,
        "case_status": ["all", "completed", "ongoing"],
        "schema": {
            "time_from": "inclusive naive-UTC or offset ISO-8601, optional",
            "time_to": "inclusive naive-UTC or offset ISO-8601, optional",
            "channels": "repeatable case attribute; a case matches if any event carries it",
            "job_families": "repeatable case attribute; a case matches if any event carries it",
            "outcomes": "case outcome: earliest terminal activity, or ongoing",
            "case_status": "all | completed | ongoing, evaluated after the time filter",
            "as_of": "optional instant for active-case aging; default is the latest filtered event",
            "min_case_ratio": "process map only; hide edges seen in fewer than this share of cases",
        },
    }


def cases_page(
    df: pd.DataFrame | None,
    *,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, object]:
    traces = build_traces(df)
    window = traces[offset : offset + limit]
    rows = []
    for trace in window:
        rows.append(
            {
                "case_id": trace.case_id,
                "variant_key": " → ".join(trace.activities),
                "event_count": len(trace.activities),
                "outcome": trace.outcome,
                "completed": trace.completed,
                "cycle_seconds": trace.cycle_seconds,
                "start": _iso(trace.timestamps[0]),
                "end": _iso(trace.timestamps[-1]),
            }
        )
    return {"total": len(traces), "limit": limit, "offset": offset, "cases": rows}


def case_detail(df: pd.DataFrame | None, case_id: str) -> dict[str, object] | None:
    frame = canonical_order(df)
    if frame.empty:
        return None
    group = frame.loc[frame["case_id"] == case_id]
    if group.empty:
        return None
    trace = build_traces(group)[0]
    events = []
    for _, row in group.iterrows():
        stamp = pd.Timestamp(row["timestamp"]).to_pydatetime().replace(tzinfo=None)
        cost = row["cost"]
        events.append(
            {
                "source_row": int(row["source_row"]),
                "activity": str(row["activity"]),
                "timestamp": _iso(stamp),
                "resource": row["resource"],
                "role": row["role"],
                "channel": row["channel"],
                "outcome": row["outcome"],
                "job_family": row["job_family"],
                "cost": None if pd.isna(cost) else float(cost),
            }
        )
    return {
        "case_id": case_id,
        "outcome": trace.outcome,
        "completed": trace.completed,
        "cycle_seconds": trace.cycle_seconds,
        "events": events,
    }


def prepare(df: pd.DataFrame | None, spec: FilterSpec | None = None) -> pd.DataFrame:
    if spec is None:
        return canonical_order(df)
    return apply_filters(df, spec)
