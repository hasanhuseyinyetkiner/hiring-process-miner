# Architecture

Hiring Process Miner is a single-user local demo: React + Vite on port **5102**, FastAPI
on port **8102**, SQLite by default (PostgreSQL via Compose/CI on host **5402**).

## Runtime topology

```mermaid
%%{init: {
  "theme": "base",
  "themeVariables": {
    "primaryColor": "#7C3AED",
    "primaryTextColor": "#ffffff",
    "primaryBorderColor": "#5B21B6",
    "lineColor": "#7C3AED",
    "secondaryColor": "#EDE9FE",
    "tertiaryColor": "#F5F3FF",
    "fontFamily": "ui-sans-serif, system-ui, sans-serif"
  }
}}%%
flowchart TB
  subgraph client ["Web · 127.0.0.1:5102"]
    UI[React + Vite + TypeScript]
    RF[React Flow process map]
    RQ[TanStack Query]
  end

  subgraph api ["API · 127.0.0.1:8102"]
    FA[FastAPI routes]
    TP[Thread pool jobs]
    DOM[Domain: ordering · metrics · quality]
    AD[Optional pm4py_adapter]
  end

  subgraph data ["Persistence"]
    SQ[(SQLite local)]
    PG[(Postgres Compose/CI)]
  end

  UI --> RQ
  RQ --> FA
  RF --> UI
  FA --> TP
  TP --> DOM
  DOM --> SQ
  DOM --> PG
  AD -.->|lazy import if installed| DOM
```

## Layering

| Layer | Location | Responsibility |
| --- | --- | --- |
| HTTP | `src/hpm/api/routes.py` | DTOs, filters, thread-pool handoff, exports |
| Services | `src/hpm/services/` | Import pipeline, query assembly, HTML report |
| Domain | `src/hpm/domain/` | Ordering, traces, DFG, funnel, variants, conformance, seed |
| Adapter | `src/hpm/pm4py_adapter.py` | Optional PM4Py path (AGPL dependency); not on the default import graph |
| UI | `frontend/src/` | Routes, map, insight cards, methodology copy |

Domain algorithms do not import FastAPI or React. Tests call domain functions with
hand-built frames (`tests/helpers.py`) so KPI expectations are independent of the API.

## Data flow (CSV → insight)

```mermaid
%%{init: {
  "theme": "base",
  "themeVariables": {
    "primaryColor": "#7C3AED",
    "primaryTextColor": "#ffffff",
    "primaryBorderColor": "#5B21B6",
    "lineColor": "#7C3AED",
    "secondaryColor": "#EDE9FE",
    "tertiaryColor": "#F5F3FF"
  }
}}%%
flowchart LR
  CSV[Event log CSV] --> Map[Column mapper]
  Map --> Qual[Quality panel]
  Qual --> Store[(Eligible events)]
  Store --> Ord[canonical_order]
  Ord --> Trace[Case traces]
  Trace --> DFG[Directly-follows graph]
  Trace --> KPI[Variants · funnel · performance · rework]
  Trace --> Conf[Rule-based conformance]
  DFG --> UI[React Flow]
  KPI --> Cards[Insight cards]
  Conf --> Model[Editable allowed transitions]
```

1. Upload or synthetic seed → draft → mapped columns → validated events.
2. Timestamps converted to UTC; ambiguous/nonexistent local times flagged and excluded
   from duration metrics under the default policy.
3. Every analytics call builds traces only after `canonical_order()`.
4. UI filters (`status`, `channel`, `job_family`, `outcome`) share one `FilterSpec`.
5. Exports (CSV summary, HTML report, SVG/PNG map) include assumptions from
   `hpm.domain.constants`.

## Technology rationale

| Choice | Why |
| --- | --- |
| pandas/NumPy core | Deterministic, testable KPIs without importing `pm4py` on the default path |
| Optional PM4Py | Token-replay/alignment behind lazy adapter; dependency is AGPL-3.0-or-later — license review advised |
| FastAPI + Pydantic v2 | Typed request/response contracts; OpenAPI at `/docs` |
| SQLAlchemy 2 + Alembic | Same models for SQLite and Postgres |
| React Flow | Interactive DFG with node/edge drawers and client-side export |
| Loopback bind | No auth in MVP; reduce accidental LAN exposure |

## Health and jobs

- `GET /health` — process up.
- `GET /ready` — migrations applied / DB reachable (Compose smoke waits on this).
- Import and discovery jobs store `status` and `heartbeat_at`; startup reaper fails
  stale `RUNNING` rows.

## Ports

| Service | Port |
| --- | --- |
| Web | 5102 |
| API | 8102 |
| Postgres (Compose host) | 5402 |

## See also

- [`ENGINEERING_DECISIONS.md`](ENGINEERING_DECISIONS.md) — licensing and correctness contracts
- [`METRICS.md`](METRICS.md) — formal definitions and seed-42 reproduction
- [`EVALUATION.md`](EVALUATION.md) — analytical evaluation summary
- [`DEMO.md`](DEMO.md) — analyst case study with screenshots
- [`RELEASE_READINESS.md`](RELEASE_READINESS.md) — pre-release checklist
- [`GITHUB_METADATA.md`](GITHUB_METADATA.md) — About box and topics
