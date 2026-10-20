"""Turn parsed or stored events into the analytics frame."""

from __future__ import annotations

import pandas as pd

from hpm.domain.ordering import REQUIRED_COLUMNS, empty_frame


def frame_from_parsed(events: list[object]) -> pd.DataFrame:
    records = []
    for event in events:
        if getattr(event, "exclusion_reason", None) is not None:
            continue
        records.append(
            {
                "case_id": event.case_id,
                "activity": event.activity,
                "timestamp": event.timestamp_utc,
                "source_row": event.source_row,
                "resource": event.resource,
                "role": event.role,
                "channel": event.channel,
                "outcome": event.outcome,
                "cost": event.cost,
                "job_family": event.job_family,
            }
        )
    if not records:
        return empty_frame()
    frame = pd.DataFrame.from_records(records)
    for column in REQUIRED_COLUMNS:
        if column not in frame.columns:
            frame[column] = None
    return frame
