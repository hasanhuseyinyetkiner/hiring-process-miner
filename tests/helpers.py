from datetime import datetime

import pandas as pd

from hpm.domain.ordering import REQUIRED_COLUMNS


def frame(rows: list[dict]) -> pd.DataFrame:
    records = []
    for index, row in enumerate(rows, start=1):
        record = {column: None for column in REQUIRED_COLUMNS}
        record.update(row)
        record.setdefault("source_row", index)
        records.append(record)
    return pd.DataFrame.from_records(records)


def at(text: str) -> datetime:
    return datetime.fromisoformat(text.replace("Z", "+00:00")).replace(tzinfo=None)
