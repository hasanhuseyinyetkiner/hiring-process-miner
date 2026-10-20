# CURSOR AGENT PROMPT — HIRING PROCESS MINER

You are a senior process-mining researcher, data engineer, Python backend engineer and product-minded frontend developer. Build **Hiring Process Miner**, a complete open-source HR event-log analytics application in this repository. Write working code and test it; don't stop at design documents. Read `.cursor/rules/*.mdc` where present. Favor complete vertical slices and real demo examples.

## Product concept

A hiring operations team uploads an **anonymized event log** and receives a discovery graph of their actual process, its most common paths, median/p90 wait times, rework loops, delayed stages and process-conformance findings. Turn messy event data into decision-support analytics. Distinguish observation from causation and completed cases from active cases.

**Portfolio differentiator:** mathematically traceable process insights and a compelling interactive process map, not a generic KPI chart dashboard.

## Technology

- Python 3.12+, FastAPI, PM4Py, pandas, NumPy, Pydantic v2, SQLAlchemy 2 + Alembic, PostgreSQL, pytest, Ruff.
- React + Vite + TypeScript + Tailwind, React Flow or Cytoscape.js for process maps, Recharts/Plotly for charts, TanStack Query, React Router, Lucide.
- Docker Compose; GitHub Actions; Vitest + Playwright.
- Use a library-supported PM4Py release and documented API calls; don't fabricate process-mining package methods.

## Inputs and data contracts

- Accept CSV with mapped columns `case_id`, `activity`, `timestamp`; optional `resource`, `role`, `channel`, `outcome`, `cost`.
- Explicit field mapper and preview of first records, timestamp timezone selection, invalid-record/error report, duplicate detection and privacy warning.
- Optional XES import only as a second phase, if supported reliably.
- Preserve anonymized case IDs. Do not require candidate names, emails, resumes or demographic data.
- Generate 500–2,000 **synthetic hiring cases** with varied stages (`Applied`, `Screened`, `Interview Scheduled`, `Interview Completed`, `Offer`, `Hired`, `Rejected`, `Withdrawn`) and deterministic bottlenecks at interview scheduling. Include incomplete cases, skipped stages, repeated interviews and out-of-order/invalid records in a separate validation fixture.

## Core features

1. Upload/import + data quality panel: record count, unique cases, missing fields, parse failures, duplicates, timezone warnings.
2. Process discovery: direct-follows graph weighted by case count or transition frequency; filter out infrequent edges with a slider. Tooltips show counts and transition delay distributions.
3. Process variants: top flows, distribution, compare two variants, their case outcomes and lengths.
4. Performance: case cycle time, per-stage dwell time, median/p90, active-case aging, wait vs processing time where timestamps permit distinction.
5. Funnel: drop-off by stage, distinct-case counting, explicit definition of denominator.
6. Rework: repeat loops, revisits and repeated steps; show examples using anonymous IDs.
7. Conformance: compare discovered traces against an editable allowed-flow model or a preconfigured reference process, using PM4Py mechanisms that really exist.
8. Filters: time range, source channel, job family, outcome, completed/ongoing; recompute graph and KPIs consistently.
9. Export: PNG/SVG for graph (where implemented), CSV summary and HTML report with dataset assumptions.
10. Insight cards: transparent rules such as "Interview Scheduled → Interview Completed has the highest median wait among steps with >= N observations"; always show numerator, sample size and methodology. Never assert a causal root cause from event logs alone.

## UX

- Dashboard with KPI summary + attractive full-width interactive flow.
- Import wizard and validation table.
- Process Explorer with selectable node/edge details drawer.
- Bottlenecks, Variants, Case Explorer and Methodology tabs.
- Responsive design with accessible controls, loading indicators, empty states and safe error messages.
- Real demo screenshots from browser automation, not invented mockups.

## Backend/API

Suggested endpoints: `POST /api/datasets/import`, `GET /api/datasets`, `GET /api/datasets/{id}/quality`, `GET /api/datasets/{id}/process`, `GET /api/datasets/{id}/variants`, `GET /api/datasets/{id}/performance`, `GET /api/datasets/{id}/cases`, `GET /api/datasets/{id}/conformance`, `GET /health`. Filter options must have one documented shared schema. Use clear units and ISO 8601 timestamps.

Separate event validation, case aggregation, graph construction, analytics, PM4Py adapters, and API endpoints into testable modules. Cap upload size and row count for demo server; guard expensive queries from pathological user input.

## Correctness requirements

- Event ordering must use an explicit stable tie-breaker for equal timestamps.
- Deduplicate only by a documented rule and never silently drop valid repeated activities.
- Don't count unfinished cases in a completed-cycle-time distribution.
- If both start/complete timestamps are not available, don't label transition time as active processing duration.
- Handle missing end events, negative durations, empty logs, one-case logs, changed filters and high-frequency graphs.
- KPIs must be independently reproducible with pandas tests separate from PM4Py visualization.

## Tests

Unit tests for invalid schemas/timestamps, duplicate semantics, stage durations, ongoing case treatment, graph edge counts, funnel denominators, variant grouping, filter consistency and conformance known-case fixtures. Integration tests for import -> metrics -> report and Playwright upload -> explore -> export. Show realistic data quality warnings.

## GitHub README requirements

An outstanding English README with headline "Understand how hiring actually happens — from event logs to explainable insights." Include actual product screenshot, clear problem statement, example small anonymized CSV table, dashboard tour, Mermaid import-to-graph pipeline, exact Quick Start commands, real CLI/API examples, detailed metric definitions and data limitations, evaluation/test examples, security/privacy, supported input formats, architecture, contribution guide and selected license. **No made-up cycle-time improvements, client stories, deployment URLs, stars or coverage.** Include `docs/GITHUB_METADATA.md` with About description `Open-source process mining for hiring funnels, bottlenecks, variants and conformance analysis.` and topics `process-mining`, `pm4py`, `data-analytics`, `fastapi`, `react`, `hr-tech`, `event-logs`, `python`.

## Phases and acceptance

Phase 1: working app shell, CSV import/validation, SQL storage and deterministic seed.
Phase 2: PM4Py process discovery + independently verified KPIs + graph UI.
Phase 3: filters, variants, rework, conformance, export, comprehensive tests.
Phase 4: UX polish, real screenshots, architecture/evaluation docs, CI, clean Docker install and professional README.

At completion a stranger can upload the sample event log, see the correct process map, inspect a bottleneck, and reproduce the numbers from documented data. Actually run builds, linters, tests and smoke tests. Report failures; don't pretend. Do not push or deploy without owner approval.
