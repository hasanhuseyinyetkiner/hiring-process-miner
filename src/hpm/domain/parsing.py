"""CSV parsing, field mapping, duplicate detection, and timestamp policy."""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from datetime import datetime

from hpm.domain.timestamps import aware_to_utc_naive, local_naive_to_utc, timezone_exists
from hpm.errors import ImportRejected

MAX_FIELD_LENGTH = 200

ALIASES: dict[str, set[str]] = {
    "case_id": {"case_id", "caseid", "case", "case_identifier"},
    "activity": {"activity", "event", "stage", "activity_name", "event_name"},
    "timestamp": {"timestamp", "time", "datetime", "event_time", "date", "event_timestamp"},
    "resource": {"resource", "user", "actor", "employee"},
    "role": {"role"},
    "channel": {"channel", "source", "source_channel"},
    "outcome": {"outcome", "status", "result"},
    "cost": {"cost"},
    "job_family": {"job_family", "family", "job", "department"},
}


@dataclass
class FieldMapping:
    case_id: str
    activity: str
    timestamp: str
    resource: str | None = None
    role: str | None = None
    channel: str | None = None
    outcome: str | None = None
    cost: str | None = None
    job_family: str | None = None

    def columns(self) -> dict[str, str | None]:
        return {
            "case_id": self.case_id,
            "activity": self.activity,
            "timestamp": self.timestamp,
            "resource": self.resource,
            "role": self.role,
            "channel": self.channel,
            "outcome": self.outcome,
            "cost": self.cost,
            "job_family": self.job_family,
        }


@dataclass
class ParsedEvent:
    source_row: int
    case_id: str | None
    activity: str | None
    timestamp_utc: datetime | None
    raw_timestamp: str | None
    resource: str | None
    role: str | None
    channel: str | None
    outcome: str | None
    cost: float | None
    job_family: str | None
    exclusion_reason: str | None
    warning: str | None


def _norm_header(value: str) -> str:
    return value.strip().lower().replace("-", "_").replace(" ", "_")


def detect_delimiter(text: str) -> str:
    header = ""
    for line in text.splitlines():
        if line.strip():
            header = line
            break
    if header.count(";") > header.count(","):
        return ";"
    return ","


def suggest_mapping(headers: list[str]) -> dict[str, str | None]:
    normalized = {_norm_header(header): header for header in headers}
    suggestion: dict[str, str | None] = {}
    for field, aliases in ALIASES.items():
        match = next((normalized[alias] for alias in aliases if alias in normalized), None)
        suggestion[field] = match
    return suggestion


def _clean_filename_cell(
    value: str | None, limit: int = MAX_FIELD_LENGTH
) -> tuple[str | None, bool]:
    if value is None:
        return None, False
    text = value.strip()
    if not text:
        return None, False
    if len(text) > limit:
        return text[:limit], True
    return text, False


def _parse_cost(raw: str | None) -> tuple[float | None, str | None]:
    if raw is None:
        return None, None
    try:
        return float(raw), None
    except ValueError:
        return None, "invalid_cost"


def _duplicate_key(event: ParsedEvent) -> tuple[object, ...]:
    cost = None if event.cost is None else round(event.cost, 6)
    return (
        event.case_id,
        event.activity,
        event.timestamp_utc,
        event.resource,
        event.role,
        event.channel,
        event.outcome,
        cost,
        event.job_family,
    )


def parse_timestamp(raw: str, timezone_name: str) -> tuple[datetime | None, str | None]:
    """Return ``(naive_utc, exclusion_reason)`` for one timestamp cell."""
    text = raw.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None, "timestamp_parse_failure"
    if parsed.tzinfo is not None:
        return aware_to_utc_naive(parsed), None
    return local_naive_to_utc(parsed, timezone_name)


def parse_csv(
    text: str,
    mapping: FieldMapping,
    timezone_name: str,
    *,
    max_rows: int | None = None,
) -> list[ParsedEvent]:
    if not timezone_exists(timezone_name):
        raise ImportRejected(
            f"Unknown timezone {timezone_name!r}. Use an IANA name such as Europe/Berlin or UTC.",
            "unknown_timezone",
        )
    if "\x00" in text[:1024]:
        raise ImportRejected("The file does not look like a CSV text file.", "not_csv")
    delimiter = detect_delimiter(text)
    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
    if not reader.fieldnames:
        raise ImportRejected("The CSV has no header row.", "missing_header")
    headers = list(reader.fieldnames)
    if any(header is None or header.strip() == "" for header in headers):
        raise ImportRejected("The CSV header has an empty column name.", "bad_header")
    if len(headers) != len(set(headers)):
        raise ImportRejected("The CSV header contains duplicate column names.", "duplicate_header")
    mapped = [column for column in mapping.columns().values() if column]
    missing = [column for column in mapped if column not in headers]
    if missing:
        joined = ", ".join(missing)
        raise ImportRejected(
            f"Mapped column(s) not in the CSV header: {joined}.",
            "missing_mapped_column",
        )

    events: list[ParsedEvent] = []
    for source_row, row in enumerate(reader, start=1):
        if max_rows is not None and source_row > max_rows:
            raise ImportRejected(
                f"The CSV has more than {max_rows} data rows.",
                "too_many_rows",
                413,
            )
        cells: dict[str, str | None] = {}
        too_long = False
        for field, column in mapping.columns().items():
            raw = None if column is None else row.get(column)
            cleaned, truncated = _clean_filename_cell(raw)
            cells[field] = cleaned
            too_long = too_long or truncated
        cost, cost_warning = _parse_cost(cells["cost"])
        event = ParsedEvent(
            source_row=source_row,
            case_id=cells["case_id"],
            activity=cells["activity"],
            timestamp_utc=None,
            raw_timestamp=cells["timestamp"],
            resource=cells["resource"],
            role=cells["role"],
            channel=cells["channel"],
            outcome=cells["outcome"],
            cost=cost,
            job_family=cells["job_family"],
            exclusion_reason=None,
            warning=cost_warning,
        )
        if too_long:
            event.exclusion_reason = "field_too_long"
        elif event.case_id is None:
            event.exclusion_reason = "missing_case_id"
        elif event.activity is None:
            event.exclusion_reason = "missing_activity"
        elif event.raw_timestamp is None:
            event.exclusion_reason = "missing_timestamp"
        else:
            instant, reason = parse_timestamp(event.raw_timestamp, timezone_name)
            event.timestamp_utc = instant
            event.exclusion_reason = reason
        events.append(event)

    seen: dict[tuple[object, ...], int] = {}
    for event in events:
        if event.exclusion_reason is not None:
            continue
        key = _duplicate_key(event)
        if key in seen:
            event.exclusion_reason = "duplicate"
            event.timestamp_utc = event.timestamp_utc
        else:
            seen[key] = event.source_row
    return events
