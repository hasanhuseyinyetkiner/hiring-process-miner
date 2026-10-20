# Hiring Process Miner

Understand how hiring actually happens — from event logs to explainable insights.

Process discovery, variants, bottlenecks and conformance on **synthetic** hiring event logs. Core analytics are pandas/NumPy (PM4Py is an optional AGPL extra).

## Verified local run (Windows)

```powershell
# Terminal 1 — API (127.0.0.1:8102)
uv sync
uv run python -m hpm

# Terminal 2 — Web (127.0.0.1:5102)
cd frontend
pnpm install
pnpm dev
```

| Service | URL |
| --- | --- |
| Web | http://127.0.0.1:5102 |
| API docs | http://127.0.0.1:8102/docs |

Startup seeds a synthetic dataset when the DB is empty (`seed_on_startup=true`). Or import via UI / `POST /api/drafts/synthetic`.

```powershell
uv run pytest -q
```

## Status

Backend + frontend MVP runnable. License pending owner decision (PM4Py optional → AGPL only if you install the `pm4py` extra).
