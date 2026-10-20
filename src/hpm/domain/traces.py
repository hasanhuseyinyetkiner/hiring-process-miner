"""Case traces built only after canonical ordering."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import pandas as pd

from hpm.domain.constants import TERMINAL_ACTIVITIES
from hpm.domain.ordering import canonical_order


def elapsed_seconds(start: datetime, end: datetime) -> float | None:
    """Return a non-negative duration in seconds, or None when the span is negative."""
    delta = pd.Timestamp(end) - pd.Timestamp(start)
    seconds = float(delta.total_seconds())
    if seconds < 0:
        return None
    return seconds


def _py_datetime(value: object) -> datetime:
    stamp = pd.Timestamp(value)
    if stamp.tzinfo is not None:
        stamp = stamp.tz_convert("UTC").tz_localize(None)
    return stamp.to_pydatetime().replace(tzinfo=None)


@dataclass
class CaseTrace:
    case_id: str
    activities: list[str]
    timestamps: list[datetime]
    source_rows: list[int]
    channels: list[str | None]
    job_families: list[str | None]

    @property
    def terminal_index(self) -> int | None:
        for index, activity in enumerate(self.activities):
            if activity in TERMINAL_ACTIVITIES:
                return index
        return None

    @property
    def completed(self) -> bool:
        return self.terminal_index is not None

    @property
    def outcome(self) -> str:
        index = self.terminal_index
        if index is None:
            return "ongoing"
        return self.activities[index]

    @property
    def cycle_seconds(self) -> float | None:
        index = self.terminal_index
        if index is None:
            return None
        return elapsed_seconds(self.timestamps[0], self.timestamps[index])

    def attribute_values(self, kind: str) -> set[str]:
        source = self.channels if kind == "channel" else self.job_families
        return {value for value in source if value}


def build_traces(df: pd.DataFrame | None) -> list[CaseTrace]:
    frame = canonical_order(df)
    traces: list[CaseTrace] = []
    if frame.empty:
        return traces
    for case_id, group in frame.groupby("case_id", sort=False):
        traces.append(
            CaseTrace(
                case_id=str(case_id),
                activities=group["activity"].astype(str).tolist(),
                timestamps=[_py_datetime(value) for value in group["timestamp"].tolist()],
                source_rows=[int(value) for value in group["source_row"].tolist()],
                channels=list(group["channel"].tolist()),
                job_families=list(group["job_family"].tolist()),
            )
        )
    return traces
