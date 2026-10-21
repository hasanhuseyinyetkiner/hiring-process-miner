import os
import threading
import time
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient

from hpm.config import assert_bind_allowed, get_settings
from hpm.db import reset_engine, session_scope, utc_now
from hpm.errors import BindRefused
from hpm.main import create_app
from hpm.models import Job

GOLDEN_CSV = """case_id,activity,timestamp,channel,job_family
A,Applied,2026-01-01T00:00:00Z,referral,engineering
A,Screened,2026-01-03T00:00:00Z,referral,engineering
A,Interview Scheduled,2026-01-04T00:00:00Z,referral,engineering
A,Interview Completed,2026-01-20T00:00:00Z,referral,engineering
A,Offer,2026-01-22T00:00:00Z,referral,engineering
A,Hired,2026-01-25T00:00:00Z,referral,engineering
B,Applied,2026-01-01T00:00:00Z,agency,design
B,Screened,2026-01-02T00:00:00Z,agency,design
B,Rejected,2026-01-03T00:00:00Z,agency,design
C,Applied,2026-01-05T00:00:00Z,referral,engineering
C,Screened,2026-01-06T00:00:00Z,referral,engineering
C,Interview Scheduled,2026-01-06T00:00:00Z,referral,engineering
"""

MAPPING = {
    "case_id": "case_id",
    "activity": "activity",
    "timestamp": "timestamp",
    "channel": "channel",
    "job_family": "job_family",
}


def _wait_job(client: TestClient, job_id: str) -> dict:
    for _ in range(100):
        response = client.get(f"/api/jobs/{job_id}")
        assert response.status_code == 200
        body = response.json()
        if body["status"] in {"SUCCEEDED", "FAILED"}:
            return body
        time.sleep(0.05)
    raise AssertionError("job did not finish")


def _import_csv(
    client: TestClient,
    text: str,
    timezone: str = "UTC",
    name: str = "Golden",
    mapping: dict | None = None,
) -> str:
    draft = client.post(
        "/api/drafts",
        files={"file": ("events.csv", text.encode(), "text/csv")},
    )
    assert draft.status_code == 201, draft.text
    imported = client.post(
        "/api/datasets/import",
        json={
            "draft_id": draft.json()["draft_id"],
            "timezone": timezone,
            "name": name,
            "mapping": mapping or MAPPING,
        },
    )
    assert imported.status_code == 202, imported.text
    job = _wait_job(client, imported.json()["id"])
    assert job["status"] == "SUCCEEDED", job
    return str(job["dataset_id"])


def test_health_ready_and_meta(client: TestClient) -> None:
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/ready").json() == {"status": "ready"}
    meta = client.get("/api/meta").json()
    assert meta["ordering_contract"] == "utc_timestamp_then_source_row"
    assert meta["pm4py_available"] is False
    assert (
        "AGPL" in meta["pm4py_message"]
        or "not installed" in meta["pm4py_message"].lower()
        or "pm4py" in meta["pm4py_message"].lower()
    )
    assert meta["demo_banner"] is False
    assert "anonymized" in meta["privacy_notice"].lower()
    sections = client.get("/api/methodology").json()["sections"]
    assert any("processing" in section["body"].lower() for section in sections)


def test_import_matches_hand_computed_cycle_time_and_edge(client: TestClient) -> None:
    dataset_id = _import_csv(client, GOLDEN_CSV)
    performance = client.get(f"/api/datasets/{dataset_id}/performance").json()
    assert performance["completed_cases"] == 2
    assert performance["ongoing_cases"] == 1
    assert performance["cycle_time"]["sample_size"] == 2
    assert performance["cycle_time"]["mean_seconds"] == 1_123_200
    assert performance["cycle_time"]["median_seconds"] == 1_123_200
    assert performance["cycle_time"]["p90_seconds"] == 1_883_520
    assert performance["cycle_time"]["p95_seconds"] == 1_978_560
    assert performance["processing_time"] is None
    assert performance["filter_impact"]["cases_before"] == 3
    assert performance["filter_impact"]["cases_after"] == 3
    graph = client.get(f"/api/datasets/{dataset_id}/process").json()
    edges = {(edge["source"], edge["target"]): edge for edge in graph["edges"]}
    assert edges[("Applied", "Screened")]["frequency"] == 3
    assert edges[("Applied", "Screened")]["mean_delay_seconds"] == 115_200
    assert edges[("Applied", "Screened")]["median_delay_seconds"] == 86_400
    assert edges[("Applied", "Screened")]["p90_delay_seconds"] == 155_520
    assert edges[("Applied", "Screened")]["p95_delay_seconds"] == 164_160
    case_c = client.get(f"/api/datasets/{dataset_id}/cases/C").json()
    assert [event["activity"] for event in case_c["events"]] == [
        "Applied",
        "Screened",
        "Interview Scheduled",
    ]
    filtered = client.get(
        f"/api/datasets/{dataset_id}/performance",
        params={"channels": "referral"},
    ).json()
    assert filtered["total_cases"] == 2
    assert filtered["filter_impact"]["cases_after"] == 2
    assert filtered["filter_impact"]["cases_before"] == 3
    hidden = client.get(
        f"/api/datasets/{dataset_id}/process",
        params={"min_case_ratio": 0.9},
    ).json()
    assert hidden["edges_after_filter"] < hidden["edges_before_filter"]
    assert "filter_impact" in hidden
    quality = client.get(f"/api/datasets/{dataset_id}/quality").json()
    assert quality["unique_cases"] == 3
    assert quality["eligible_event_count"] == 12
    report = client.get(f"/api/datasets/{dataset_id}/export/report.html")
    assert report.status_code == 200
    assert "1123200" in report.text
    summary = client.get(f"/api/datasets/{dataset_id}/export/summary.csv")
    assert summary.status_code == 200
    assert "cycle_time" in summary.text


def test_dst_rows_surface_in_the_quality_panel(client: TestClient) -> None:
    csv_text = "\n".join(
        [
            "case_id,activity,timestamp",
            "A,Applied,2026-06-15 12:00",
            "B,Applied,2026-10-25 02:30",
            "C,Applied,2026-03-29 02:30",
        ]
    )
    dataset_id = _import_csv(
        client,
        csv_text,
        timezone="Europe/Berlin",
        name="DST",
        mapping={"case_id": "case_id", "activity": "activity", "timestamp": "timestamp"},
    )
    quality = client.get(f"/api/datasets/{dataset_id}/quality").json()
    assert quality["ambiguous_timestamps"] == 1
    assert quality["nonexistent_timestamps"] == 1
    assert quality["unique_cases"] == 1
    assert quality["timezone_warnings"]


def test_delete_dataset_removes_events(client: TestClient) -> None:
    dataset_id = _import_csv(client, GOLDEN_CSV, name="Disposable")
    assert client.delete(f"/api/datasets/{dataset_id}").status_code == 204
    assert client.get(f"/api/datasets/{dataset_id}").status_code == 404
    assert client.get(f"/api/datasets/{dataset_id}/process").status_code == 404


def test_conformance_flags_a_skip(client: TestClient) -> None:
    csv_text = (
        "case_id,activity,timestamp\nD,Applied,2026-07-01T00:00:00Z\nD,Hired,2026-07-02T00:00:00Z\n"
    )
    dataset_id = _import_csv(
        client,
        csv_text,
        name="Skip",
        mapping={"case_id": "case_id", "activity": "activity", "timestamp": "timestamp"},
    )
    body = client.get(f"/api/datasets/{dataset_id}/conformance").json()
    assert body["fitting_cases"] == 0
    assert body["sample_size"] == 1
    assert body["pm4py"]["used"] is False
    assert body["deviations"][0]["source"] == "Applied"
    assert body["deviations"][0]["target"] == "Hired"
    updated = client.put(
        f"/api/datasets/{dataset_id}/conformance",
        json={"transitions": [{"source": "Applied", "target": "Hired"}]},
    )
    assert updated.status_code == 200
    assert updated.json()["fitting_cases"] == 1


def test_rejects_non_csv_and_unknown_dataset(client: TestClient) -> None:
    rejected = client.post(
        "/api/drafts",
        files={"file": ("notes.txt", b"hello", "text/plain")},
    )
    assert rejected.status_code == 415
    missing = client.get("/api/datasets/missing/quality")
    assert missing.status_code == 404


def test_health_stays_responsive_while_a_job_runs(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    started = threading.Event()
    release = threading.Event()

    def slow(_job_id: str) -> None:
        started.set()
        release.wait(5)

    monkeypatch.setattr("hpm.services.importer.execute_import", slow)
    assert client.get("/health").status_code == 200
    draft = client.post(
        "/api/drafts",
        files={
            "file": (
                "events.csv",
                b"case_id,activity,timestamp\nA,Applied,2026-01-01T00:00:00Z\n",
                "text/csv",
            )
        },
    )
    assert draft.status_code == 201
    try:
        started_at = time.perf_counter()
        response = client.post(
            "/api/datasets/import",
            json={
                "draft_id": draft.json()["draft_id"],
                "timezone": "UTC",
                "name": "blocked",
                "mapping": {
                    "case_id": "case_id",
                    "activity": "activity",
                    "timestamp": "timestamp",
                },
            },
        )
        assert time.perf_counter() - started_at < 2
        assert response.status_code == 202
        assert started.wait(3)
        health_started = time.perf_counter()
        health = client.get("/health")
        assert health.status_code == 200
        assert time.perf_counter() - health_started < 1
    finally:
        release.set()


def test_startup_reaper_marks_stale_jobs(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    database = tmp_path / "reaper.sqlite"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database.as_posix()}")
    monkeypatch.setenv("SEED_ON_STARTUP", "false")
    monkeypatch.setenv("HOST", "127.0.0.1")
    monkeypatch.setenv("ALLOW_NETWORK_BIND", "false")
    get_settings.cache_clear()
    reset_engine()
    with TestClient(create_app()):
        old = utc_now() - timedelta(hours=2)
        with session_scope() as session:
            session.add(
                Job(
                    id="stale-running",
                    kind="import",
                    status="RUNNING",
                    created_at=old,
                    started_at=old,
                    heartbeat_at=old,
                )
            )
            session.add(
                Job(
                    id="fresh-running",
                    kind="import",
                    status="RUNNING",
                    created_at=utc_now(),
                    started_at=utc_now(),
                    heartbeat_at=utc_now(),
                )
            )
            session.add(
                Job(
                    id="stale-pending",
                    kind="import",
                    status="PENDING",
                    created_at=old,
                )
            )
    get_settings.cache_clear()
    reset_engine()
    with TestClient(create_app()) as restarted:
        stale = restarted.get("/api/jobs/stale-running").json()
        pending = restarted.get("/api/jobs/stale-pending").json()
        fresh = restarted.get("/api/jobs/fresh-running").json()
    assert stale["status"] == "FAILED"
    assert "stale heartbeat" in stale["error"]
    assert pending["status"] == "FAILED"
    assert "never started" in pending["error"]
    assert fresh["status"] == "RUNNING"


def test_public_bind_requires_an_explicit_opt_in(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(BindRefused):
        assert_bind_allowed("0.0.0.0", False)
    assert_bind_allowed("127.0.0.1", False)
    assert_bind_allowed("0.0.0.0", True)
    database = tmp_path / "bind.sqlite"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database.as_posix()}")
    monkeypatch.setenv("HOST", "0.0.0.0")
    monkeypatch.setenv("ALLOW_NETWORK_BIND", "false")
    monkeypatch.setenv("SEED_ON_STARTUP", "false")
    get_settings.cache_clear()
    reset_engine()
    with pytest.raises(BindRefused):
        with TestClient(create_app()):
            pass
    monkeypatch.setenv("ALLOW_NETWORK_BIND", "true")
    get_settings.cache_clear()
    reset_engine()
    with TestClient(create_app()) as allowed:
        assert allowed.get("/health").status_code == 200


@pytest.mark.postgres
@pytest.mark.skipif(
    not os.environ.get("DATABASE_URL", "").startswith("postgresql"),
    reason="PostgreSQL-only check; runs in CI",
)
def test_postgres_is_reachable(client: TestClient) -> None:
    from sqlalchemy import text

    from hpm.db import get_engine

    with get_engine().connect() as connection:
        version = connection.execute(text("SELECT version()")).scalar()
    assert "PostgreSQL" in str(version)
    assert client.get("/ready").status_code == 200
