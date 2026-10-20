# Analytical evaluation

How Hiring Process Miner’s KPIs are defined, generated, and audited. Formal field-level
definitions live in [`METRICS.md`](METRICS.md). This page is the evaluation narrative:
what was measured, on which synthetic log, with which denominators, and how to reproduce
the headline figures without treating them as causal claims.

**Observation ≠ causation.** Delays, drop-offs, and fit rates describe the recorded
event log (or a synthetic generator). They are not root causes and not hiring
recommendations.

## What was evaluated

| Question | How it is answered |
| --- | --- |
| Does the seed produce a stable log? | `tests/test_seed.py` — identical CSV for seed 42; interview wait is longest median |
| Are KPI formulas independently correct? | `tests/test_metrics.py` — hand-computed medians, p90, cycle time, funnel, conformance |
| Does import preserve eligibility? | Quality panel + `importer._persist` case_count / eligible_event_count |
| Does the UI journey work? | Playwright `e2e/workflow.spec.ts` (import → map → export) |
| Are screenshots authentic? | Playwright `e2e/screenshots.spec.ts` → `docs/screenshots/*.png` |

Core analytics use **pandas/NumPy**. Token-replay / alignment via optional PM4Py
(**AGPL-3.0-or-later**) is out of the default evaluation path; parity tests skip when
`pm4py` is absent. Enabling that extra may have license implications for a given
distribution or hosting model — review with qualified counsel; this document is not
legal advice. See [`ENGINEERING_DECISIONS.md`](ENGINEERING_DECISIONS.md) HPM-1.

## Synthetic generation

| Parameter | Value |
| --- | --- |
| Module | `hpm.domain.seedgen` |
| Cases requested | 800 (`SYNTHETIC_CASE_MIN`…`MAX` = 500…2000) |
| RNG seed | **42** |
| Timezone for naive stamps | `Europe/Berlin` |
| Startup name | `Synthetic hiring log` |

**Generator construction (not a real employer):**

- Short waits: Uniform(4, 72) hours
- Interview Scheduled → Interview Completed: Uniform(240, 480) hours

Quality-probe rows (duplicate, missing fields, bad / ambiguous / nonexistent timestamps)
are injected for the quality panel and are **excluded** from analytics-eligible events.

## Eligibility and exclusions

A row is analytics-eligible when it has `case_id`, `activity`, one unambiguous UTC
timestamp, and is not a documented duplicate.

`dataset.case_count` = distinct eligible `case_id`. Funnel, variants, and conformance
use the same distinct-case set after filters.

## Canonical ordering

Contract `utc_timestamp_then_source_row`: UTC timestamp ↑, then original `source_row` ↑
(`mergesort`). `build_traces()` always re-orders; analytics never trust a pre-sorted
frame.

## Transition delay

Elapsed UTC seconds between consecutive events after ordering. Single timestamp per
event → **not** labeled processing time. Median = `numpy.median`; p90 =
`numpy.percentile(..., 90, method='linear')`. Negative spans discarded. Insight cards
require ≥ `MIN_OBSERVATIONS` (30) transitions on an edge.

## Completed cycle time

Terminals: `Hired`, `Rejected`, `Withdrawn`. Cycle = first event → earliest terminal.
**Ongoing cases are excluded** from the completed cycle-time distribution (they appear
only in aging with an explicit `as_of`).

## Funnel denominators

Denominator = distinct filtered `case_id`. Stage reach = activity **present** somewhere
in the case (not order-based). Drop-off = set difference vs previous happy-path stage —
not a claim that the candidate “exited” there. Path problems belong to conformance.

## Conformance

Rule-based: a case fits iff every consecutive pair is in the editable allowed-transition
model. **Does not use PM4Py.** Default endpoint fit rate is pandas-only.

## Reproduced seed-42 headline figures

Verified locally against `render_seed_csv(800, 42)` + domain functions (2026-10-20):

| Quantity | Value |
| --- | --- |
| CSV rows | 3825 |
| Eligible events | 3819 |
| Exclusions | 6 (duplicate, missing_case_id, missing_activity, parse_failure, ambiguous, nonexistent — one each) |
| **Eligible cases** | **800** (not 802 — earlier draft text was wrong; probes do not add eligible cases) |
| Completed / ongoing | 736 / 64 |
| Cycle-time sample size | 736 |
| Leading bottleneck edge | Interview Scheduled → Interview Completed |
| Median delay | 1 268 568.8738075001 s ≈ **14.6825 d** → UI **14.7 d** |
| Bottleneck numerator / sample | 592 transitions / 504 cases |
| Top variant | Happy path · 159 cases · share 0.19875 (**19.8%**) |
| Funnel denominator | 800 |
| Conformance fit | 670 / 800 → **0.8375** |

Reproduce:

```powershell
uv run python -c "from hpm.domain.seedgen import render_seed_csv; from hpm.domain.parsing import FieldMapping, parse_csv; from hpm.services.frames import frame_from_parsed; from hpm.domain.metrics import insights; from hpm.domain.quality import quality_report; m=FieldMapping(case_id='case_id',activity='activity',timestamp='timestamp',resource='resource',role='role',channel='channel',outcome='outcome',cost='cost',job_family='job_family'); e=parse_csv(render_seed_csv(800,42),m,'Europe/Berlin'); q=quality_report(e,timezone='Europe/Berlin'); h=insights(frame_from_parsed(e))['cards'][0]; print(q['unique_cases'], round(h['value']/86400,4), h['source_activity'], h['target_activity'])"
```

Expect: `800 14.6825 Interview Scheduled Interview Completed`.

## Test evidence (verified 2026-10-20)

| Suite | Result |
| --- | --- |
| `uv run ruff check src tests` | All checks passed |
| `uv run pytest -q` | **30 passed**, **2 skipped** (PM4Py DFG parity absent) |
| `pnpm test` (Vitest) | **5 passed** (3 files) |

CI: `.github/workflows/ci.yml` — backend Ruff+pytest (Postgres), frontend lint/typecheck/Vitest/build, `compose-smoke`.

## Analyst walkthrough

End-to-end logs → auditable observation: [`DEMO.md`](DEMO.md).

## What this evaluation does **not** claim

- Causal root causes or “days saved” from process changes
- Industry benchmarks or live customer data
- Processing-time vs wait-time splits
- Production SaaS readiness or legal compliance
- That enabling PM4Py is (or is not) AGPL-safe for every deployment — **review required**
