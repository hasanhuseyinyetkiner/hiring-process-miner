# Hiring Process Miner — frontend

React + Vite + TypeScript UI for the local Hiring Process Miner demo. Talks to the
FastAPI backend on **http://127.0.0.1:8102** and serves the web app on
**http://127.0.0.1:5102**.

This is not the generic Vite template README. Product architecture and KPI contracts:
[`../docs/ARCHITECTURE.md`](../docs/ARCHITECTURE.md), [`../docs/EVALUATION.md`](../docs/EVALUATION.md).

## Stack

| Piece | Choice |
| --- | --- |
| Framework | React 19 + React Router |
| Build | Vite 8 |
| Language | TypeScript |
| Styling | Tailwind CSS 4 |
| Data | TanStack Query |
| Process map | React Flow (`@xyflow/react`) |
| Charts | Recharts |
| Tests | Vitest + Testing Library; Playwright e2e |

Accent color: `#7C3AED`. Light and dark themes via `hpm.theme` in localStorage.

## Routes

| Path | Page |
| --- | --- |
| `/` | Overview KPIs, operational telemetry, data hygiene |
| `/import` | CSV upload / synthetic generate + quality panel |
| `/map` | Directly-follows process map + drawer + export |
| `/bottlenecks` | Insight cards + transition latency table |
| `/variants` | Path ranking + side-by-side compare |
| `/cases` | Case explorer |
| `/methodology` | API-served methodology copy (matches backend constants) |

## Scripts

From this directory (`frontend/`):

```powershell
pnpm install
pnpm dev          # http://127.0.0.1:5102 (strictPort)
pnpm lint
pnpm typecheck
pnpm test         # Vitest
pnpm build
pnpm e2e          # Playwright workflow (API 8102 + web 5102 required)
pnpm screenshots  # Writes ../docs/screenshots/*.png
```

Proxy / API base: see `src/api/client.ts` (default loopback API).

## Verification (2026-10-20)

| Command | Result |
| --- | --- |
| `pnpm test` | 5 passed (3 files) |

Backend must be running for e2e and screenshots. Core analytics live in Python
(pandas/NumPy); this UI does not embed PM4Py.
