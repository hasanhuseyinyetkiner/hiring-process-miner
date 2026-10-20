"""The single ordering contract used by every analytics function."""

from __future__ import annotations

import math

import pandas as pd

REQUIRED_COLUMNS = (
    "case_id",
    "activity",
    "timestamp",
    "source_row",
    "resource",
    "role",
    "channel",
    "outcome",
    "cost",
    "job_family",
)


def empty_frame() -> pd.DataFrame:
    frame = pd.DataFrame(columns=list(REQUIRED_COLUMNS))
    frame["timestamp"] = pd.to_datetime(frame["timestamp"])
    return frame


def _blank(value: object) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    return False


def _optional_text(value: object) -> str | None:
    if _blank(value):
        return None
    text = str(value).strip()
    return text or None


def ensure_frame(df: pd.DataFrame | None) -> pd.DataFrame:
    """Return a frame of analytics-eligible events with stable dtypes.

    Rows missing case_id, activity, or timestamp are dropped. Optional attributes
    stay as text or None so later filters do not treat NaN as a real channel.
    """
    if df is None or len(df.index) == 0:
        return empty_frame()
    missing = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing:
        raise ValueError(f"event frame missing columns: {', '.join(missing)}")
    out = df.loc[:, list(REQUIRED_COLUMNS)].copy()
    out["case_id"] = out["case_id"].map(lambda value: None if _blank(value) else str(value).strip())
    out["activity"] = out["activity"].map(
        lambda value: None if _blank(value) else str(value).strip()
    )
    out["timestamp"] = pd.to_datetime(out["timestamp"], utc=False)
    out["source_row"] = pd.to_numeric(out["source_row"], errors="coerce")
    for column in ("resource", "role", "channel", "outcome", "job_family"):
        out[column] = out[column].map(_optional_text)
    out["cost"] = pd.to_numeric(out["cost"], errors="coerce")
    out = out.dropna(subset=["case_id", "activity", "timestamp", "source_row"])
    out["source_row"] = out["source_row"].astype(int)
    out["case_id"] = out["case_id"].astype(str)
    out["activity"] = out["activity"].astype(str)
    return out.reset_index(drop=True)


def canonical_order(df: pd.DataFrame | None) -> pd.DataFrame:
    """Sort by UTC timestamp, then original source row. This is the only ordering."""
    frame = ensure_frame(df)
    if frame.empty:
        return frame
    return frame.sort_values(
        ["timestamp", "source_row"],
        ascending=[True, True],
        kind="mergesort",
    ).reset_index(drop=True)
