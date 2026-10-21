"""Fault injection around CSV import and draft lifecycle."""

from __future__ import annotations

import time

from fastapi.testclient import TestClient

from hpm.domain.parsing import FieldMapping, parse_csv
from hpm.errors import ImportRejected

MAPPING = FieldMapping(
    case_id="case_id",
    activity="activity",
    timestamp="timestamp",
)


def _wait_job(client: TestClient, job_id: str) -> dict:
    for _ in range(100):
        response = client.get(f"/api/jobs/{job_id}")
        assert response.status_code == 200
        body = response.json()
        if body["status"] in {"SUCCEEDED", "FAILED"}:
            return body
        time.sleep(0.05)
    raise AssertionError("job did not finish")


def test_corrupt_csv_rows_are_excluded_not_crash() -> None:
    csv_text = "\n".join(
        [
            "case_id,activity,timestamp",
            "A,Applied,2026-01-01T00:00:00Z",
            "B,Screened,not-a-timestamp",
            ",Applied,2026-01-02T00:00:00Z",
            "C,,2026-01-03T00:00:00Z",
            'D,Offer,"2026-01-04T00:00:00Z",extra,columns,should,not,crash',
            "E,Hired,2026-01-05T00:00:00Z",
        ]
    )
    events = parse_csv(csv_text, MAPPING, "UTC")
    reasons = [event.exclusion_reason for event in events]
    assert None in reasons
    assert "timestamp_parse_failure" in reasons
    assert "missing_case_id" in reasons
    assert "missing_activity" in reasons
    eligible = [event for event in events if event.exclusion_reason is None]
    assert {event.case_id for event in eligible} >= {"A", "E"}


def test_missing_required_columns_rejected() -> None:
    try:
        parse_csv("alpha,beta\n1,2\n", MAPPING, "UTC")
    except ImportRejected as exc:
        assert exc.code == "missing_mapped_column"
    else:
        raise AssertionError("expected missing mapped column")


def test_import_is_idempotent_on_draft_consumption(client: TestClient) -> None:
    text = "case_id,activity,timestamp\nA,Applied,2026-01-01T00:00:00Z\n"
    draft = client.post(
        "/api/drafts",
        files={"file": ("events.csv", text.encode(), "text/csv")},
    )
    assert draft.status_code == 201, draft.text
    draft_id = draft.json()["draft_id"]
    payload = {
        "draft_id": draft_id,
        "timezone": "UTC",
        "name": "Fault injection",
        "mapping": {
            "case_id": "case_id",
            "activity": "activity",
            "timestamp": "timestamp",
        },
    }
    first = client.post("/api/datasets/import", json=payload)
    assert first.status_code == 202, first.text
    job = _wait_job(client, first.json()["id"])
    assert job["status"] == "SUCCEEDED"
    assert job["dataset_id"]

    # Successful import deletes the draft; a replay cannot re-import the same draft_id.
    second = client.post("/api/datasets/import", json=payload)
    assert second.status_code == 404
    assert second.json()["detail"]["code"] == "draft_not_found"


def test_empty_header_and_missing_mapped_column_rejected(client: TestClient) -> None:
    empty = client.post(
        "/api/drafts",
        files={"file": ("bad.csv", b"\n", "text/csv")},
    )
    assert empty.status_code == 400
    assert empty.json()["detail"]["code"] in {"missing_header", "bad_header"}
    draft = client.post(
        "/api/drafts",
        files={
            "file": (
                "ok.csv",
                b"case_id,activity,timestamp\nA,Applied,2026-01-01T00:00:00Z\n",
                "text/csv",
            )
        },
    )
    assert draft.status_code == 201
    missing_col = client.post(
        "/api/datasets/import",
        json={
            "draft_id": draft.json()["draft_id"],
            "timezone": "UTC",
            "name": "missing map",
            "mapping": {
                "case_id": "case_id",
                "activity": "activity",
                "timestamp": "not_in_file",
            },
        },
    )
    assert missing_col.status_code == 400
    assert missing_col.json()["detail"]["code"] == "missing_mapped_column"
