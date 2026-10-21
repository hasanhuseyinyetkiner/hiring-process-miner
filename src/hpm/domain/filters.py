"""Shared analytics filter. Time bounds are applied before case attributes."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import pandas as pd

from hpm.domain.constants import CAUSAL_CAUTION
from hpm.domain.ordering import canonical_order
from hpm.domain.traces import CaseTrace, build_traces


@dataclass(frozen=True)
class FilterSpec:
    """One filter schema for the graph, variants, funnel, and performance.

    ``time_from`` and ``time_to`` are inclusive naive UTC instants. Attribute
    filters then keep or drop whole remaining cases. Case status is the status of
    the visible trace: a time filter that removes the terminal event makes the
    case ongoing.
    """

    time_from: datetime | None = None
    time_to: datetime | None = None
    channels: frozenset[str] | None = None
    job_families: frozenset[str] | None = None
    outcomes: frozenset[str] | None = None
    case_status: str = "all"


def _matches(trace: CaseTrace, spec: FilterSpec) -> bool:
    if spec.case_status == "completed" and not trace.completed:
        return False
    if spec.case_status == "ongoing" and trace.completed:
        return False
    if spec.channels is not None and trace.attribute_values("channel").isdisjoint(spec.channels):
        return False
    if spec.job_families is not None and trace.attribute_values("job_family").isdisjoint(
        spec.job_families
    ):
        return False
    if spec.outcomes is not None and trace.outcome not in spec.outcomes:
        return False
    return True


def apply_filters(df: pd.DataFrame | None, spec: FilterSpec) -> pd.DataFrame:
    frame = canonical_order(df)
    if spec.time_from is not None:
        frame = frame.loc[frame["timestamp"] >= pd.Timestamp(spec.time_from)]
    if spec.time_to is not None:
        frame = frame.loc[frame["timestamp"] <= pd.Timestamp(spec.time_to)]
    frame = frame.reset_index(drop=True)
    if frame.empty:
        return frame
    if (
        spec.case_status == "all"
        and spec.channels is None
        and spec.job_families is None
        and spec.outcomes is None
    ):
        return frame
    keep = {trace.case_id for trace in build_traces(frame) if _matches(trace, spec)}
    if not keep:
        return frame.iloc[0:0].copy()
    return frame.loc[frame["case_id"].isin(keep)].reset_index(drop=True)


def filter_impact(
    before: pd.DataFrame | None,
    after: pd.DataFrame | None,
) -> dict[str, object]:
    """Retention diagnostics for an applied filter. Observation only — not causation."""
    before_frame = canonical_order(before)
    after_frame = canonical_order(after)
    cases_before = len(build_traces(before_frame))
    cases_after = len(build_traces(after_frame))
    events_before = int(len(before_frame))
    events_after = int(len(after_frame))
    return {
        "cases_before": cases_before,
        "cases_after": cases_after,
        "cases_retained_ratio": (cases_after / cases_before) if cases_before else None,
        "events_before": events_before,
        "events_after": events_after,
        "events_retained_ratio": (events_after / events_before) if events_before else None,
        "definition": (
            "Counts of distinct cases and event rows before versus after the active "
            "FilterSpec. Retention ratios describe the filtered log only."
        ),
        "caution": CAUSAL_CAUTION,
    }
