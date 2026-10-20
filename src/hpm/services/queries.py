"""Read-side analytics. Each call opens its own session so it can run in a worker thread."""

from __future__ import annotations

import json

from sqlalchemy import select

from hpm.db import session_scope
from hpm.domain.constants import DEFAULT_ALLOWED_TRANSITIONS
from hpm.domain.filters import FilterSpec
from hpm.domain.metrics import (
    case_detail,
    cases_page,
    compare_variants,
    conformance,
    directly_follows,
    filter_options,
    funnel,
    insights,
    performance,
    prepare,
    rework,
    variants,
)
from hpm.domain.quality import quality_report
from hpm.errors import DatasetNotFound
from hpm.models import Dataset, Event
from hpm.services.frames import frame_from_parsed
from hpm.services.report import render_html, render_summary_csv


def _load(dataset_id: str) -> tuple[Dataset, list[Event]]:
    with session_scope() as session:
        dataset = session.get(Dataset, dataset_id)
        if dataset is None:
            raise DatasetNotFound(dataset_id)
        events = list(
            session.scalars(
                select(Event).where(Event.dataset_id == dataset_id).order_by(Event.source_row)
            )
        )
        session.expunge(dataset)
        for event in events:
            session.expunge(event)
        return dataset, events


def _transitions(dataset: Dataset) -> list[tuple[str, str]]:
    if not dataset.conformance_json:
        return list(DEFAULT_ALLOWED_TRANSITIONS)
    payload = json.loads(dataset.conformance_json)
    return [(item["source"], item["target"]) for item in payload]


def dataset_frame(dataset_id: str, spec: FilterSpec | None = None):
    _dataset, events = _load(dataset_id)
    return prepare(frame_from_parsed(events), spec)


def quality_for(dataset_id: str) -> dict:
    dataset, events = _load(dataset_id)
    report = quality_report(events, timezone=dataset.timezone)
    report["dataset_id"] = dataset.id
    report["name"] = dataset.name
    report["synthetic"] = dataset.synthetic
    return report


def process_for(dataset_id: str, spec: FilterSpec, min_case_ratio: float) -> dict:
    return directly_follows(dataset_frame(dataset_id, spec), min_case_ratio=min_case_ratio)


def performance_for(dataset_id: str, spec: FilterSpec, as_of):
    return performance(dataset_frame(dataset_id, spec), as_of=as_of)


def funnel_for(dataset_id: str, spec: FilterSpec) -> dict:
    return funnel(dataset_frame(dataset_id, spec))


def variants_for(dataset_id: str, spec: FilterSpec, limit: int) -> dict:
    return variants(dataset_frame(dataset_id, spec), limit=limit)


def compare_for(dataset_id: str, spec: FilterSpec, key_a: str, key_b: str) -> dict:
    return compare_variants(dataset_frame(dataset_id, spec), key_a, key_b)


def rework_for(dataset_id: str, spec: FilterSpec) -> dict:
    return rework(dataset_frame(dataset_id, spec))


def insights_for(dataset_id: str, spec: FilterSpec, min_observations: int, as_of) -> dict:
    return insights(
        dataset_frame(dataset_id, spec),
        min_observations=min_observations,
        as_of=as_of,
    )


def conformance_for(dataset_id: str, spec: FilterSpec) -> dict:
    dataset, events = _load(dataset_id)
    result = conformance(prepare(frame_from_parsed(events), spec), _transitions(dataset))
    from hpm.pm4py_adapter import pm4py_conformance_status

    result["pm4py"] = pm4py_conformance_status()
    return result


def options_for(dataset_id: str) -> dict:
    return filter_options(dataset_frame(dataset_id))


def cases_for(dataset_id: str, spec: FilterSpec, limit: int, offset: int) -> dict:
    return cases_page(dataset_frame(dataset_id, spec), limit=limit, offset=offset)


def case_for(dataset_id: str, case_id: str) -> dict:
    from hpm.errors import CaseNotFound

    detail = case_detail(dataset_frame(dataset_id), case_id)
    if detail is None:
        raise CaseNotFound(case_id)
    return detail


def save_conformance(dataset_id: str, transitions: list[tuple[str, str]]) -> dict:
    payload = [{"source": source, "target": target} for source, target in transitions]
    with session_scope() as session:
        dataset = session.get(Dataset, dataset_id)
        if dataset is None:
            raise DatasetNotFound(dataset_id)
        dataset.conformance_json = json.dumps(payload)
    return conformance_for(dataset_id, FilterSpec())


def summary_csv(dataset_id: str, spec: FilterSpec) -> str:
    dataset, events = _load(dataset_id)
    frame = prepare(frame_from_parsed(events), spec)
    return render_summary_csv(
        dataset,
        performance(frame),
        funnel(frame),
    )


def html_report(dataset_id: str, spec: FilterSpec) -> str:
    dataset, events = _load(dataset_id)
    frame = prepare(frame_from_parsed(events), spec)
    return render_html(
        dataset,
        quality_report(events, timezone=dataset.timezone),
        performance(frame),
        funnel(frame),
        insights(frame),
    )
