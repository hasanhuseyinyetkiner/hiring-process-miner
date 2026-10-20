"""Optional PM4Py adapter. Importing this module does not import pm4py."""

from __future__ import annotations

import importlib.util
from datetime import datetime, timedelta

import pandas as pd

from hpm.domain.constants import PM4PY_NOT_USED, PM4PY_UNAVAILABLE
from hpm.domain.traces import build_traces


def pm4py_installed() -> bool:
    try:
        return importlib.util.find_spec("pm4py") is not None
    except (ImportError, ValueError):
        return False


def pm4py_conformance_status() -> dict[str, object]:
    if not pm4py_installed():
        return {
            "available": False,
            "used": False,
            "feature": "token_replay_and_alignments",
            "message": PM4PY_UNAVAILABLE,
        }
    return {
        "available": True,
        "used": False,
        "feature": "token_replay_and_alignments",
        "message": PM4PY_NOT_USED,
    }


def dfg_frequency(df: pd.DataFrame) -> dict[tuple[str, str], int]:
    """DFG edge frequencies via PM4Py, ordered by the canonical contract.

    PM4Py sorts by timestamp and does not know source-row ties. The frame passed
    in is therefore rebuilt with strictly increasing synthetic timestamps that
    follow canonical order. Durations are not taken from this call.
    """
    import pm4py

    rows: list[dict[str, object]] = []
    for trace in build_traces(df):
        for index, activity in enumerate(trace.activities):
            rows.append(
                {
                    "case:concept:name": trace.case_id,
                    "concept:name": activity,
                    "time:timestamp": datetime(2020, 1, 1) + timedelta(seconds=index),
                }
            )
    if not rows:
        return {}
    log = pd.DataFrame(rows)
    log["time:timestamp"] = pd.to_datetime(log["time:timestamp"], utc=True)
    discovered, _start, _end = pm4py.discover_dfg(
        log,
        case_id_key="case:concept:name",
        activity_key="concept:name",
        timestamp_key="time:timestamp",
    )
    return {
        (str(source), str(target)): int(count) for (source, target), count in discovered.items()
    }
