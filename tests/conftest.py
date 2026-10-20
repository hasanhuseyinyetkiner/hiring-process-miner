import os
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from hpm.config import get_settings
from hpm.db import reset_engine, session_scope
from hpm.main import create_app
from hpm.models import Dataset, Draft, Event, Job


@pytest.fixture
def client(tmp_path, monkeypatch) -> Iterator[TestClient]:
    current = os.environ.get("DATABASE_URL", "")
    if current.startswith("postgresql"):
        monkeypatch.setenv("DATABASE_URL", current)
    else:
        database = tmp_path / "test.sqlite"
        monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database.as_posix()}")
    monkeypatch.setenv("SEED_ON_STARTUP", "false")
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("ALLOW_NETWORK_BIND", "false")
    monkeypatch.setenv("HOST", "127.0.0.1")
    get_settings.cache_clear()
    reset_engine()
    app = create_app()
    with TestClient(app) as test_client:
        with session_scope() as session:
            session.execute(delete(Event))
            session.execute(delete(Job))
            session.execute(delete(Draft))
            session.execute(delete(Dataset))
        yield test_client
    reset_engine()
    get_settings.cache_clear()
