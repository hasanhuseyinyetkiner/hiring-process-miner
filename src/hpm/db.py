"""Engine, sessions, and migrations. SQLite is the native path; Postgres is the CI path."""

from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from hpm.config import get_settings
from hpm.paths import ALEMBIC_INI

_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


def utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def sqlite_path(url: str) -> Path | None:
    if not url.startswith("sqlite:///"):
        return None
    raw = url.removeprefix("sqlite:///")
    if raw in {":memory:", ""}:
        return None
    return Path(raw)


def ensure_sqlite_parent(url: str) -> None:
    path = sqlite_path(url)
    if path is not None and path.parent and str(path.parent) not in {"", "."}:
        path.parent.mkdir(parents=True, exist_ok=True)


def maybe_reset_sqlite() -> None:
    """Delete the configured SQLite file when HPM_RESET_DB=1. Never touches Postgres."""
    if os.environ.get("HPM_RESET_DB") != "1":
        return
    path = sqlite_path(get_settings().database_url)
    if path is not None:
        path.unlink(missing_ok=True)


def reset_engine() -> None:
    global _engine, _session_factory
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _session_factory = None


def get_engine() -> Engine:
    global _engine, _session_factory
    if _engine is None:
        url = get_settings().database_url
        ensure_sqlite_parent(url)
        connect_args: dict[str, object] = {}
        if url.startswith("sqlite"):
            connect_args = {"check_same_thread": False, "timeout": 30}
        _engine = create_engine(url, pool_pre_ping=True, connect_args=connect_args)
        if _engine.dialect.name == "sqlite":

            @event.listens_for(_engine, "connect")
            def _enable_foreign_keys(dbapi_connection, _record) -> None:
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()

        _session_factory = sessionmaker(bind=_engine, expire_on_commit=False)
    return _engine


def get_sessionmaker() -> sessionmaker[Session]:
    get_engine()
    assert _session_factory is not None
    return _session_factory


@contextmanager
def session_scope() -> Iterator[Session]:
    session = get_sessionmaker()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def run_migrations() -> None:
    url = get_settings().database_url
    ensure_sqlite_parent(url)
    config = Config(str(ALEMBIC_INI))
    # ConfigParser treats % as interpolation. Escape it for the ini value.
    config.set_main_option("sqlalchemy.url", url.replace("%", "%%"))
    command.upgrade(config, "head")
