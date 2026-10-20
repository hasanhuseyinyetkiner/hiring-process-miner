"""HTTP API. Heavy work is handed to a thread pool or the import executor."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, File, Query, Request, UploadFile
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel, Field
from sqlalchemy import delete, select
from starlette.concurrency import run_in_threadpool

from hpm import __version__
from hpm.config import get_settings
from hpm.db import session_scope
from hpm.domain.constants import (
    AS_OF_DEFINITION,
    CAUSAL_CAUTION,
    CYCLE_TIME_DEFINITION,
    DELAY_DEFINITION,
    DEMO_BANNER_TEXT,
    DROP_OFF_DEFINITION,
    DUPLICATE_RULE,
    FUNNEL_DENOMINATOR,
    ORDERING_CONTRACT,
    ORDERING_DESCRIPTION,
    PRIVACY_NOTICE,
    PROCESSING_TIME_REASON,
    SYNTHETIC_CASE_MAX,
    SYNTHETIC_CASE_MIN,
)
from hpm.domain.filters import FilterSpec
from hpm.errors import CaseNotFound, DatasetNotFound, ImportRejected
from hpm.models import Dataset, Job
from hpm.pm4py_adapter import pm4py_conformance_status, pm4py_installed
from hpm.services import importer, queries

router = APIRouter()


class MappingIn(BaseModel):
    case_id: str | None = None
    activity: str | None = None
    timestamp: str | None = None
    resource: str | None = None
    role: str | None = None
    channel: str | None = None
    outcome: str | None = None
    cost: str | None = None
    job_family: str | None = None


class PreviewIn(BaseModel):
    mapping: MappingIn
    timezone: str = "UTC"


class ImportIn(BaseModel):
    draft_id: str
    mapping: MappingIn
    timezone: str
    name: str = Field(default="Imported event log", max_length=200)


class SyntheticIn(BaseModel):
    cases: int = Field(default=800, ge=SYNTHETIC_CASE_MIN, le=SYNTHETIC_CASE_MAX)
    seed: int = 42


class TransitionIn(BaseModel):
    source: str = Field(min_length=1, max_length=200)
    target: str = Field(min_length=1, max_length=200)


class ConformanceIn(BaseModel):
    transitions: list[TransitionIn] = Field(min_length=1, max_length=200)


def _mapping(mapping: MappingIn) -> dict[str, str | None]:
    return {key: (value or None) for key, value in mapping.model_dump().items()}


def _naive(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value
    return value.astimezone(UTC).replace(tzinfo=None)


def _set(values: list[str] | None) -> frozenset[str] | None:
    if not values:
        return None
    cleaned = frozenset(value for value in values if value)
    return cleaned or None


def analytics_filter(
    time_from: Annotated[datetime | None, Query()] = None,
    time_to: Annotated[datetime | None, Query()] = None,
    channels: Annotated[list[str] | None, Query()] = None,
    job_families: Annotated[list[str] | None, Query()] = None,
    outcomes: Annotated[list[str] | None, Query()] = None,
    case_status: Literal["all", "completed", "ongoing"] = "all",
) -> FilterSpec:
    return FilterSpec(
        time_from=_naive(time_from),
        time_to=_naive(time_to),
        channels=_set(channels),
        job_families=_set(job_families),
        outcomes=_set(outcomes),
        case_status=case_status,
    )


def _iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.strftime("%Y-%m-%dT%H:%M:%SZ")


def _dataset_dict(dataset: Dataset) -> dict[str, object]:
    return {
        "id": dataset.id,
        "name": dataset.name,
        "created_at": _iso(dataset.created_at),
        "source": dataset.source,
        "timezone": dataset.timezone,
        "synthetic": dataset.synthetic,
        "notes": dataset.notes,
        "generator_seed": dataset.generator_seed,
        "generator_cases": dataset.generator_cases,
        "row_count": dataset.row_count,
        "eligible_event_count": dataset.eligible_event_count,
        "case_count": dataset.case_count,
    }


def _job_dict(job: Job) -> dict[str, object]:
    return {
        "id": job.id,
        "dataset_id": job.dataset_id,
        "kind": job.kind,
        "status": job.status,
        "error": job.error,
        "created_at": _iso(job.created_at),
        "started_at": _iso(job.started_at),
        "heartbeat_at": _iso(job.heartbeat_at),
        "finished_at": _iso(job.finished_at),
    }


async def _call(func, *args):
    try:
        return await run_in_threadpool(func, *args)
    except ImportRejected as exc:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=exc.status_code,
            detail={"detail": exc.message, "code": exc.code},
        ) from exc
    except DatasetNotFound as exc:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=404,
            detail={"detail": "Dataset not found.", "code": "not_found"},
        ) from exc
    except CaseNotFound as exc:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=404,
            detail={"detail": "Case not found in this dataset.", "code": "case_not_found"},
        ) from exc


@router.get("/meta")
def meta() -> dict[str, object]:
    settings = get_settings()
    pm4py = pm4py_conformance_status()
    return {
        "name": "Hiring Process Miner",
        "version": __version__,
        "environment": settings.app_env,
        "demo_banner": settings.demo_banner,
        "demo_banner_text": DEMO_BANNER_TEXT,
        "pm4py_available": pm4py_installed(),
        "pm4py_message": pm4py["message"],
        "privacy_notice": PRIVACY_NOTICE,
        "ordering_contract": ORDERING_CONTRACT,
        "max_upload_bytes": settings.max_upload_bytes,
        "max_rows": settings.max_rows,
        "synthetic_case_min": SYNTHETIC_CASE_MIN,
        "synthetic_case_max": SYNTHETIC_CASE_MAX,
    }


@router.get("/methodology")
def methodology() -> dict[str, object]:
    return {
        "ordering_contract": ORDERING_CONTRACT,
        "sections": [
            {"id": "ordering", "title": "Event ordering", "body": ORDERING_DESCRIPTION},
            {"id": "duplicates", "title": "Duplicates", "body": DUPLICATE_RULE},
            {"id": "delays", "title": "Transition delay", "body": DELAY_DEFINITION},
            {"id": "cycle", "title": "Case cycle time", "body": CYCLE_TIME_DEFINITION},
            {"id": "processing", "title": "Processing time", "body": PROCESSING_TIME_REASON},
            {"id": "funnel", "title": "Funnel denominator", "body": FUNNEL_DENOMINATOR},
            {"id": "dropoff", "title": "Drop-off", "body": DROP_OFF_DEFINITION},
            {"id": "aging", "title": "Active-case aging", "body": AS_OF_DEFINITION},
            {"id": "caution", "title": "What this is not", "body": CAUSAL_CAUTION},
            {"id": "privacy", "title": "Privacy", "body": PRIVACY_NOTICE},
        ],
    }


@router.post("/drafts", status_code=201)
async def create_draft(file: Annotated[UploadFile, File()]) -> dict[str, object]:
    raw = await file.read()
    draft = await _call(
        importer.create_upload_draft, file.filename or "upload.csv", raw, file.content_type
    )
    return {"draft_id": draft.id, "filename": draft.filename, "row_count": draft.row_count}


@router.post("/drafts/synthetic", status_code=201)
async def create_synthetic(body: SyntheticIn) -> dict[str, object]:
    draft = await _call(importer.create_synthetic_draft, body.cases, body.seed)
    return {
        "draft_id": draft.id,
        "filename": draft.filename,
        "row_count": draft.row_count,
        "timezone_suggestion": draft.timezone_suggestion,
        "synthetic": True,
    }


@router.post("/drafts/{draft_id}/preview")
async def preview(draft_id: str, body: PreviewIn) -> dict[str, object]:
    return await _call(importer.build_preview, draft_id, _mapping(body.mapping), body.timezone)


@router.post("/datasets/import", status_code=202)
async def start_import(body: ImportIn, request: Request) -> dict[str, object]:
    job = await _call(
        importer.enqueue_import,
        body.draft_id,
        _mapping(body.mapping),
        body.timezone,
        body.name,
    )
    request.app.state.executor.submit(importer.execute_import, job.id)
    return _job_dict(job)


@router.get("/jobs/{job_id}")
def get_job(job_id: str) -> dict[str, object]:
    with session_scope() as session:
        job = session.get(Job, job_id)
        if job is None:
            from fastapi import HTTPException

            raise HTTPException(
                status_code=404,
                detail={"detail": "Job not found.", "code": "not_found"},
            )
        return _job_dict(job)


@router.get("/datasets")
def list_datasets() -> dict[str, object]:
    with session_scope() as session:
        rows = session.scalars(select(Dataset).order_by(Dataset.created_at.desc())).all()
        return {"datasets": [_dataset_dict(row) for row in rows]}


@router.get("/datasets/{dataset_id}")
def get_dataset(dataset_id: str) -> dict[str, object]:
    with session_scope() as session:
        dataset = session.get(Dataset, dataset_id)
        if dataset is None:
            from fastapi import HTTPException

            raise HTTPException(
                status_code=404,
                detail={"detail": "Dataset not found.", "code": "not_found"},
            )
        return _dataset_dict(dataset)


@router.delete("/datasets/{dataset_id}", status_code=204)
def remove_dataset(dataset_id: str) -> Response:
    from hpm.models import Event

    with session_scope() as session:
        dataset = session.get(Dataset, dataset_id)
        if dataset is None:
            from fastapi import HTTPException

            raise HTTPException(
                status_code=404,
                detail={"detail": "Dataset not found.", "code": "not_found"},
            )
        session.execute(delete(Event).where(Event.dataset_id == dataset_id))
        session.execute(delete(Job).where(Job.dataset_id == dataset_id))
        session.delete(dataset)
    return Response(status_code=204)


@router.get("/datasets/{dataset_id}/quality")
async def quality(dataset_id: str) -> dict[str, object]:
    return await _call(queries.quality_for, dataset_id)


@router.get("/datasets/{dataset_id}/process")
async def process(
    dataset_id: str,
    spec: Annotated[FilterSpec, Depends(analytics_filter)],
    min_case_ratio: Annotated[float, Query(ge=0.0, le=1.0)] = 0.0,
) -> dict[str, object]:
    return await _call(queries.process_for, dataset_id, spec, min_case_ratio)


@router.get("/datasets/{dataset_id}/performance")
async def performance(
    dataset_id: str,
    spec: Annotated[FilterSpec, Depends(analytics_filter)],
    as_of: datetime | None = None,
) -> dict[str, object]:
    return await _call(queries.performance_for, dataset_id, spec, _naive(as_of))


@router.get("/datasets/{dataset_id}/funnel")
async def funnel(
    dataset_id: str,
    spec: Annotated[FilterSpec, Depends(analytics_filter)],
) -> dict[str, object]:
    return await _call(queries.funnel_for, dataset_id, spec)


@router.get("/datasets/{dataset_id}/variants")
async def variant_list(
    dataset_id: str,
    spec: Annotated[FilterSpec, Depends(analytics_filter)],
    limit: Annotated[int, Query(ge=1, le=100)] = 15,
) -> dict[str, object]:
    return await _call(queries.variants_for, dataset_id, spec, limit)


@router.get("/datasets/{dataset_id}/variants/compare")
async def variant_compare(
    dataset_id: str,
    spec: Annotated[FilterSpec, Depends(analytics_filter)],
    a: str,
    b: str,
) -> dict[str, object]:
    return await _call(queries.compare_for, dataset_id, spec, a, b)


@router.get("/datasets/{dataset_id}/rework")
async def rework(
    dataset_id: str,
    spec: Annotated[FilterSpec, Depends(analytics_filter)],
) -> dict[str, object]:
    return await _call(queries.rework_for, dataset_id, spec)


@router.get("/datasets/{dataset_id}/insights")
async def insight_cards(
    dataset_id: str,
    spec: Annotated[FilterSpec, Depends(analytics_filter)],
    min_observations: Annotated[int, Query(ge=1, le=100_000)] = 30,
    as_of: datetime | None = None,
) -> dict[str, object]:
    return await _call(queries.insights_for, dataset_id, spec, min_observations, _naive(as_of))


@router.get("/datasets/{dataset_id}/conformance")
async def conformance_view(
    dataset_id: str,
    spec: Annotated[FilterSpec, Depends(analytics_filter)],
) -> dict[str, object]:
    return await _call(queries.conformance_for, dataset_id, spec)


@router.put("/datasets/{dataset_id}/conformance")
async def conformance_update(dataset_id: str, body: ConformanceIn) -> dict[str, object]:
    transitions = [(item.source, item.target) for item in body.transitions]
    return await _call(queries.save_conformance, dataset_id, transitions)


@router.get("/datasets/{dataset_id}/filters")
async def filters(dataset_id: str) -> dict[str, object]:
    return await _call(queries.options_for, dataset_id)


@router.get("/datasets/{dataset_id}/cases")
async def case_list(
    dataset_id: str,
    spec: Annotated[FilterSpec, Depends(analytics_filter)],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> dict[str, object]:
    return await _call(queries.cases_for, dataset_id, spec, limit, offset)


@router.get("/datasets/{dataset_id}/cases/{case_id}")
async def one_case(dataset_id: str, case_id: str) -> dict[str, object]:
    return await _call(queries.case_for, dataset_id, case_id)


@router.get("/datasets/{dataset_id}/export/summary.csv")
async def export_csv(
    dataset_id: str,
    spec: Annotated[FilterSpec, Depends(analytics_filter)],
) -> Response:
    text = await _call(queries.summary_csv, dataset_id, spec)
    return Response(
        content=text,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="hiring-summary.csv"'},
    )


@router.get("/datasets/{dataset_id}/export/report.html")
async def export_html(
    dataset_id: str,
    spec: Annotated[FilterSpec, Depends(analytics_filter)],
) -> HTMLResponse:
    text = await _call(queries.html_report, dataset_id, spec)
    return HTMLResponse(text)
