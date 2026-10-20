# Design review amendments (binding)

These amendments come from the pre-implementation design review (2026-10-20). They **override** any conflicting text in `docs/PRODUCT_SPEC.md`. IDs refer to review findings.

## Environment and delivery (all products)

- **[C-1] No Docker, no local PostgreSQL.** The dev machine is Windows 11 with `uv` (use Python 3.12: `uv python pin 3.12`), Node 24 and pnpm. Provide a **native dev path that is verified locally** (`uv run ...` backend, `pnpm dev` frontend). Local tests may use SQLite through the same SQLAlchemy models; PostgreSQL-only behavior gets a SQLite-safe fallback or a `@pytest.mark.postgres` marker that runs in CI. Write `compose.yaml` and Dockerfiles, but they are verified **only in CI** by a `compose-smoke` job; the README must say so until that job passes.
- **CI** (GitHub Actions, `ubuntu-latest`): backend Ruff + pytest against a PostgreSQL service container; frontend ESLint + `tsc` + Vitest + build; `compose-smoke` (`docker compose up --build -d`, wait for `/ready`, then `docker compose down -v`).
- **[C-6] Ports:** API `8102`, web `5102`, PostgreSQL host port `5402`.
- **[C-2] Loopback by default.** Uvicorn binds `127.0.0.1`; Compose port mappings use `127.0.0.1:` prefixes. No auth in the MVP, so startup refuses a non-loopback host unless `ALLOW_NETWORK_BIND=true` is set explicitly. `APP_ENV=demo` shows a persistent "Local demo · synthetic data" banner.
- **[C-3] No CPU-heavy work on the event loop.** Import, discovery and KPI computation run via `run_in_threadpool` or a process pool. Long jobs are persisted rows with `status` and `heartbeat_at`; a startup reaper marks stale `RUNNING` jobs `FAILED` with a reason. Add a test proving `/health` stays responsive while a job runs.
- **[C-4] Licensing and git.** Do **not** add a `LICENSE` file; the README states "License: pending owner decision". Do not create remotes or push. Commit locally in small conventional commits (`feat:`, `fix:`, `test:`, `chore:`, `docs:`, `ci:`).
- **Brand:** accent color `#7C3AED` (violet). Light and dark themes.

## Product-specific

- **[HPM-1] PM4Py is AGPL-3.0-or-later.** All core analytics (event validation, canonical ordering, directly-follows graph, variants, funnel, performance, rework) are implemented in pandas/NumPy **without importing pm4py**. PM4Py lives in an optional extra (`[project.optional-dependencies] pm4py = [...]`) behind a lazily imported adapter; features that need it (e.g. token-replay/alignment conformance) are disabled with a clear UI/API message when it is not installed. A simple rule-based conformance check against an allowed-transition model must work without PM4Py. Record the licensing reasoning in `docs/DECISIONS.md`. Core tests must pass in an environment without pm4py.
- **[HPM-2] One ordering contract.** A single `canonical_order()` (UTC timestamp, then original source row number) is the only path into every analytics function. If PM4Py is installed, a parity test asserts identical DFG edge counts between the pandas and PM4Py paths on an equal-timestamp fixture (skip when PM4Py is absent).
- **[HPM-3] DST-safe timestamps.** Store UTC. Ambiguous and nonexistent local times follow a configurable policy (default: flag the record and exclude it from duration metrics), surfaced in the data-quality panel. Fixture: `Europe/Berlin` 2026-10-25 02:30 (ambiguous) and 2026-03-29 02:30 (nonexistent).
