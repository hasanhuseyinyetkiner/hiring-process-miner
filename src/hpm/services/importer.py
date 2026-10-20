"""Import drafts, background jobs, and the startup reaper."""

from __future__ import annotations

import csv
import io
import json
import logging
from datetime import timedelta
from pathlib import Path
from uuid import uuid4

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from hpm.config import get_settings
from hpm.db import session_scope, utc_now
from hpm.domain.constants import PRIVACY_NOTICE, SYNTHETIC_TIMEZONE
from hpm.domain.parsing import (
    FieldMapping,
    detect_delimiter,
    parse_csv,
    suggest_mapping,
)
from hpm.domain.quality import quality_report
from hpm.domain.seedgen import render_seed_csv
from hpm.errors import ImportRejected
from hpm.models import Dataset, Draft, Event, Job

logger = logging.getLogger("hpm")

SYNTHETIC_NOTE = "Synthetic demo data generated inside this app. Not real candidates or employers."
ALLOWED_CONTENT_TYPES = {
    "",
    "text/csv",
    "application/csv",
    "application/vnd.ms-excel",
    "text/plain",
    "application/octet-stream",
}


def clean_filename(name: str | None) -> str:
    base = Path(name or "upload.csv").name.replace("\x00", "")
    if not base or base in {".", ".."}:
        return "upload.csv"
    return base[:255]


def decode_csv(raw: bytes) -> str:
    settings = get_settings()
    if len(raw) > settings.max_upload_bytes:
        raise ImportRejected(
            f"File exceeds the {settings.max_upload_bytes} byte upload cap.",
            "file_too_large",
            413,
        )
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ImportRejected("CSV must be UTF-8.", "encoding") from exc


def _headers_and_count(text: str) -> tuple[list[str], int]:
    delimiter = detect_delimiter(text)
    reader = csv.reader(io.StringIO(text), delimiter=delimiter)
    try:
        header = next(reader)
    except StopIteration as exc:
        raise ImportRejected("The CSV has no header row.", "missing_header") from exc
    if not header or any(not cell.strip() for cell in header):
        raise ImportRejected("The CSV header has an empty column name.", "bad_header")
    count = sum(1 for _ in reader)
    if count > get_settings().max_rows:
        raise ImportRejected(
            f"The CSV has more than {get_settings().max_rows} data rows.",
            "too_many_rows",
            413,
        )
    return header, count


def _raw_sample(text: str, limit: int = 8) -> list[dict[str, str | None]]:
    delimiter = detect_delimiter(text)
    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
    rows: list[dict[str, str | None]] = []
    for index, row in enumerate(reader):
        if index >= limit:
            break
        rows.append(dict(row))
    return rows


def store_draft(
    *,
    filename: str,
    csv_text: str,
    synthetic: bool,
    timezone_suggestion: str,
    generator_seed: int | None = None,
    generator_cases: int | None = None,
) -> Draft:
    _headers, row_count = _headers_and_count(csv_text)
    draft = Draft(
        id=str(uuid4()),
        created_at=utc_now(),
        filename=clean_filename(filename),
        csv_text=csv_text,
        synthetic=synthetic,
        timezone_suggestion=timezone_suggestion,
        generator_seed=generator_seed,
        generator_cases=generator_cases,
        row_count=row_count,
    )
    with session_scope() as session:
        session.add(draft)
        session.flush()
        session.refresh(draft)
        session.expunge(draft)
    return draft


def create_upload_draft(filename: str, raw: bytes, content_type: str | None) -> Draft:
    normalized = (content_type or "").split(";")[0].strip().lower()
    if normalized not in ALLOWED_CONTENT_TYPES:
        raise ImportRejected("Upload a CSV file.", "unsupported_type", 415)
    if not clean_filename(filename).lower().endswith(".csv"):
        raise ImportRejected("The file extension must be .csv.", "unsupported_type", 415)
    return store_draft(
        filename=filename,
        csv_text=decode_csv(raw),
        synthetic=False,
        timezone_suggestion="UTC",
    )


def create_synthetic_draft(cases: int, seed: int) -> Draft:
    csv_text = render_seed_csv(cases, seed)
    return store_draft(
        filename="synthetic-hiring-log.csv",
        csv_text=csv_text,
        synthetic=True,
        timezone_suggestion=SYNTHETIC_TIMEZONE,
        generator_seed=seed,
        generator_cases=cases,
    )


def _mapping_from_payload(payload: dict[str, str | None]) -> FieldMapping:
    required = ("case_id", "activity", "timestamp")
    for field in required:
        if not payload.get(field):
            raise ImportRejected(f"Map the {field} column before importing.", "incomplete_mapping")
    return FieldMapping(
        case_id=str(payload["case_id"]),
        activity=str(payload["activity"]),
        timestamp=str(payload["timestamp"]),
        resource=payload.get("resource") or None,
        role=payload.get("role") or None,
        channel=payload.get("channel") or None,
        outcome=payload.get("outcome") or None,
        cost=payload.get("cost") or None,
        job_family=payload.get("job_family") or None,
    )


def build_preview(draft_id: str, mapping_payload: dict[str, str | None], timezone: str) -> dict:
    with session_scope() as session:
        draft = session.get(Draft, draft_id)
        if draft is None:
            raise ImportRejected("Draft not found. Upload the file again.", "draft_not_found", 404)
        text = draft.csv_text
        filename = draft.filename
        suggestion = draft.timezone_suggestion
        synthetic = draft.synthetic
        row_count = draft.row_count
    headers, _count = _headers_and_count(text)
    suggested = suggest_mapping(headers)
    applied = dict(suggested)
    for key, value in mapping_payload.items():
        if value:
            applied[key] = value
    quality = None
    parsed_sample: list[dict[str, object]] = []
    if applied.get("case_id") and applied.get("activity") and applied.get("timestamp"):
        events = parse_csv(
            text, _mapping_from_payload(applied), timezone, max_rows=get_settings().max_rows
        )
        quality = quality_report(events, timezone=timezone)
        for event in events[:20]:
            parsed_sample.append(
                {
                    "source_row": event.source_row,
                    "case_id": event.case_id,
                    "activity": event.activity,
                    "raw_timestamp": event.raw_timestamp,
                    "timestamp_utc": (
                        None
                        if event.timestamp_utc is None
                        else event.timestamp_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
                    ),
                    "exclusion_reason": event.exclusion_reason,
                    "warning": event.warning,
                }
            )
    return {
        "draft_id": draft_id,
        "filename": filename,
        "headers": headers,
        "raw_sample": _raw_sample(text),
        "suggested_mapping": suggested,
        "applied_mapping": applied,
        "timezone_suggestion": suggestion,
        "timezone": timezone,
        "synthetic": synthetic,
        "row_count": row_count,
        "parsed_sample": parsed_sample,
        "quality": quality,
        "privacy_notice": PRIVACY_NOTICE,
    }


def enqueue_import(
    draft_id: str, mapping_payload: dict[str, str | None], timezone: str, name: str
) -> Job:
    from hpm.domain.timestamps import timezone_exists

    mapping = _mapping_from_payload(mapping_payload)
    if not timezone_exists(timezone):
        raise ImportRejected(
            f"Unknown timezone {timezone!r}. Use an IANA name such as Europe/Berlin or UTC.",
            "unknown_timezone",
        )
    with session_scope() as session:
        draft = session.get(Draft, draft_id)
        if draft is None:
            raise ImportRejected("Draft not found. Upload the file again.", "draft_not_found", 404)
        headers, _count = _headers_and_count(draft.csv_text)
        missing = [
            column for column in mapping.columns().values() if column and column not in headers
        ]
        if missing:
            raise ImportRejected(
                f"Mapped column(s) not in the CSV header: {', '.join(missing)}.",
                "missing_mapped_column",
            )
        job = Job(
            id=str(uuid4()),
            dataset_id=None,
            kind="import",
            status="PENDING",
            created_at=utc_now(),
            payload_json=json.dumps(
                {
                    "draft_id": draft_id,
                    "mapping": mapping_payload,
                    "timezone": timezone,
                    "name": name.strip()[:200] or "Imported event log",
                }
            ),
        )
        session.add(job)
        session.flush()
        session.refresh(job)
        session.expunge(job)
    return job


def _persist(session: Session, events: list, info: dict) -> Dataset:
    dataset = Dataset(
        id=str(uuid4()),
        name=info["name"],
        created_at=utc_now(),
        source="synthetic" if info["synthetic"] else "upload",
        timezone=info["timezone"],
        synthetic=bool(info["synthetic"]),
        notes=SYNTHETIC_NOTE if info["synthetic"] else None,
        generator_seed=info["seed"],
        generator_cases=info["cases"],
        row_count=0,
        eligible_event_count=0,
        case_count=0,
    )
    session.add(dataset)
    session.flush()
    batch: list[Event] = []
    for event in events:
        batch.append(
            Event(
                dataset_id=dataset.id,
                source_row=event.source_row,
                case_id=event.case_id,
                activity=event.activity,
                timestamp_utc=event.timestamp_utc,
                raw_timestamp=event.raw_timestamp,
                resource=event.resource,
                role=event.role,
                channel=event.channel,
                outcome=event.outcome,
                cost=event.cost,
                job_family=event.job_family,
                exclusion_reason=event.exclusion_reason,
                warning=event.warning,
            )
        )
        if len(batch) >= 2000:
            session.add_all(batch)
            session.flush()
            batch = []
            job = session.get(Job, info["job_id"])
            if job is not None and job.status == "RUNNING":
                job.heartbeat_at = utc_now()
    if batch:
        session.add_all(batch)
    eligible = [event for event in events if event.exclusion_reason is None and event.case_id]
    dataset.row_count = len(events)
    dataset.eligible_event_count = sum(1 for event in events if event.exclusion_reason is None)
    dataset.case_count = len({event.case_id for event in eligible})
    return dataset


def execute_import(job_id: str) -> None:
    """Run one import off the request thread. Owns its own database sessions."""
    try:
        with session_scope() as session:
            job = session.get(Job, job_id)
            if job is None or not job.payload_json:
                return
            payload = json.loads(job.payload_json)
            draft = session.get(Draft, payload["draft_id"])
            if draft is None:
                job.status = "FAILED"
                job.error = "Draft expired or was already imported."
                job.finished_at = utc_now()
                return
            job.status = "RUNNING"
            job.started_at = utc_now()
            job.heartbeat_at = job.started_at
            info = {
                "csv_text": draft.csv_text,
                "mapping": payload["mapping"],
                "timezone": payload["timezone"],
                "name": payload["name"],
                "synthetic": draft.synthetic,
                "seed": draft.generator_seed,
                "cases": draft.generator_cases,
                "draft_id": draft.id,
                "job_id": job_id,
            }
        events = parse_csv(
            info["csv_text"],
            _mapping_from_payload(info["mapping"]),
            info["timezone"],
            max_rows=get_settings().max_rows,
        )
        with session_scope() as session:
            dataset = _persist(session, events, info)
            draft = session.get(Draft, info["draft_id"])
            if draft is not None:
                session.delete(draft)
            job = session.get(Job, job_id)
            if job is not None:
                job.status = "SUCCEEDED"
                job.dataset_id = dataset.id
                job.heartbeat_at = utc_now()
                job.finished_at = utc_now()
                job.error = None
    except ImportRejected as exc:
        logger.info("import rejected job=%s code=%s", job_id, exc.code)
        _fail_job(job_id, exc.message)
    except Exception:
        logger.exception("import failed job=%s", job_id)
        _fail_job(job_id, "Import failed before the dataset was saved.")


def _fail_job(job_id: str, message: str) -> None:
    with session_scope() as session:
        job = session.get(Job, job_id)
        if job is None or job.status == "SUCCEEDED":
            return
        job.status = "FAILED"
        job.error = message
        job.finished_at = utc_now()


def seed_if_empty() -> None:
    with session_scope() as session:
        existing = session.scalar(select(Dataset.id).limit(1))
        if existing:
            return
    draft = create_synthetic_draft(800, 42)
    mapping = {
        "case_id": "case_id",
        "activity": "activity",
        "timestamp": "timestamp",
        "resource": "resource",
        "role": "role",
        "channel": "channel",
        "outcome": "outcome",
        "cost": "cost",
        "job_family": "job_family",
    }
    job = enqueue_import(draft.id, mapping, SYNTHETIC_TIMEZONE, "Synthetic hiring log")
    execute_import(job.id)


def reap_stale_jobs(session: Session, *, now, stale_seconds: int) -> int:
    """Mark abandoned RUNNING and ancient PENDING jobs failed. Returns the count."""
    cutoff = now - timedelta(seconds=stale_seconds)
    jobs = session.scalars(select(Job).where(Job.status.in_(("RUNNING", "PENDING")))).all()
    changed = 0
    for job in jobs:
        if job.status == "RUNNING":
            heartbeat = job.heartbeat_at or job.started_at
            stale = heartbeat is None or heartbeat < cutoff
            reason = "stale heartbeat; marked failed by startup reaper"
        else:
            stale = job.created_at < cutoff
            reason = "pending job never started; marked failed by startup reaper"
        if not stale:
            continue
        job.status = "FAILED"
        job.error = reason
        job.finished_at = now
        changed += 1
    session.flush()
    return changed


def delete_old_drafts(session: Session, *, now, max_age_seconds: int = 86_400) -> None:
    cutoff = now - timedelta(seconds=max_age_seconds)
    session.execute(delete(Draft).where(Draft.created_at < cutoff))
