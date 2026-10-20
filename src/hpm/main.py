"""Application factory. Bind checks and migrations run before the app serves traffic."""

from __future__ import annotations

import logging
import sys
from collections.abc import AsyncIterator
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from hpm import __version__
from hpm.api.routes import router
from hpm.config import assert_bind_allowed, get_settings, host_from_argv
from hpm.db import maybe_reset_sqlite, reset_engine, run_migrations, session_scope, utc_now
from hpm.services.importer import delete_old_drafts, reap_stale_jobs, seed_if_empty

logger = logging.getLogger("hpm")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    assert_bind_allowed(settings.host, settings.allow_network_bind)
    argv_host = host_from_argv(sys.argv)
    if argv_host is not None:
        assert_bind_allowed(argv_host, settings.allow_network_bind)
    maybe_reset_sqlite()
    reset_engine()
    run_migrations()
    app.state.executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="hpm-job")
    with session_scope() as session:
        reaped = reap_stale_jobs(
            session,
            now=utc_now(),
            stale_seconds=settings.stale_job_seconds,
        )
        delete_old_drafts(session, now=utc_now())
    if reaped:
        logger.info("startup reaper marked %s job(s) failed", reaped)
    if settings.seed_on_startup:
        seed_if_empty()
    yield
    app.state.executor.shutdown(wait=False, cancel_futures=True)
    reset_engine()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Hiring Process Miner",
        version=__version__,
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router, prefix="/api")

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/ready")
    def ready() -> dict[str, str]:
        from sqlalchemy import text

        from hpm.db import get_engine

        with get_engine().connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"status": "ready"}

    return app


app = create_app()
