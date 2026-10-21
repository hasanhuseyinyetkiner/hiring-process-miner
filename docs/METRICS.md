# Metrics and evaluation

Formal definitions used by the API, UI methodology page, insight cards, and pytest
golden fixtures. Verified seed-42 numbers below were reproduced against the code on
2026-10-20 — not invented marketing figures. Narrative evaluation summary:
[`EVALUATION.md`](EVALUATION.md). Analyst walkthrough: [`DEMO.md`](DEMO.md).

| Source of truth | Location |
| --- | --- |
| Strings / terminals / happy path | `src/hpm/domain/constants.py` |
| Ordering | `src/hpm/domain/ordering.py` |
| Traces | `src/hpm/domain/traces.py` |
| KPIs / DFG / conformance / insights | `src/hpm/domain/metrics.py` |
| Distributions | `src/hpm/domain/stats.py` |
| Synthetic generator | `src/hpm/domain/seedgen.py` |
| Eligibility / quality | `src/hpm/domain/quality.py`, `parsing.py` |
| Optional PM4Py adapter | `src/hpm/pm4py_adapter.py` (not on default path) |

**Observation ≠ causation.** Every insight card carries `CAUSAL_CAUTION`: recorded delays
and drop-offs describe the event log only. They are not causal root causes and are not
hiring recommendations.

## Synthetic generation

| Item | Value |
| --- | --- |
| Generator | `hpm.domain.seedgen.render_seed_csv` / `generate_cases` |
| Default `generator_cases` | 800 (bounds 500–2000) |
| Seed | **42** (`numpy.random.default_rng(42)`) |
| Timezone of naive stamps | `Europe/Berlin` |
| Startup dataset name | `Synthetic hiring log` (`seed_if_empty`) |
| Label | Synthetic — never real candidates |

**By construction (generator, not a real employer):** short waits draw from
Uniform(4, 72) hours; **Interview Scheduled → Interview Completed** draws from
Uniform(240, 480) hours. That separation is intentional so the demo bottleneck is
auditable. It is not evidence about any live hiring org.

Quality-probe rows (duplicate, missing fields, bad/ambiguous/nonexistent timestamps)
are appended when `inject_quality_rows=True` so the quality panel has deterministic
fixtures. Those rows are **excluded** from analytics-eligible events under the default
DST / parse policy.

## Eligibility

A row is analytics-eligible when it has a `case_id`, an `activity`, and one unambiguous
UTC timestamp, and it is not a documented duplicate (`eligible_definition` in
`quality_report`).

`dataset.case_count` = distinct `case_id` among eligible events
(`importer._persist`). Funnel / variants / conformance denominators use the same
distinct-case set after filters (`build_traces`).

### Seed 42, `generator_cases=800` (reproduced)

| Quantity | Value |
| --- | --- |
| CSV rows | 3825 |
| Eligible events | 3819 |
| Exclusions | 6 — duplicate 1, missing_case_id 1, missing_activity 1, timestamp_parse_failure 1, ambiguous_local_time 1, nonexistent_local_time 1 |
| **Eligible cases (`case_count`)** | **800** |
| Completed / ongoing | 736 / 64 |
| Cycle-time sample size | 736 (ongoing excluded) |

> **Correction note.** Earlier README draft text said “802 eligible cases.” Re-running
> `parse_csv(render_seed_csv(800, 42), …)` + `quality_report` / `directly_follows`
> yields **800**. Probe case ids `QX1`–`QX4` are all excluded. Docs and UI copy must
> use 800.

## Canonical ordering

| Field | Value |
| --- | --- |
| Contract id | `utc_timestamp_then_source_row` |
| Sort | UTC timestamp ascending, then `source_row` ascending |
| Stability | `mergesort` via `canonical_order()` |
| Entry point | `build_traces()` always re-orders; callers are not trusted |

Equal timestamps are ordered by the original CSV row index. This is the only path into
DFG, variants, funnel, performance, rework, and conformance.

## Transition delay

Elapsed UTC seconds between two **consecutive** events in a case after canonical
ordering. Each event has one timestamp, so delay is **not** labeled processing time or
active work (`DELAY_DEFINITION`).

- Mean: `numpy.mean` (arithmetic mean of the sample).
- Median: `numpy.median` (average of the two central values when *n* is even).
- p90: `numpy.percentile(values, 90, method='linear')`.
- p95: `numpy.percentile(values, 95, method='linear')` (tail companion to p90).
- API payloads and the Bottlenecks latency table expose **mean / median / p90 / p95** so
  skewed tails are visible without implying causation.
- Negative spans are discarded (not clamped) and counted separately where applicable.
- Insight delay cards require `MIN_OBSERVATIONS = 30` transitions on the edge.

## Filtering impact

When cohort filters are applied, process and performance API payloads include
`filter_impact`: cases/events before vs after the `FilterSpec`, with retention ratios and
`CAUSAL_CAUTION`. This is a retention diagnostic on the filtered log — not a claim that
the filter “caused” KPI changes.

## Timestamp outlier policy

Source of truth: `TIMESTAMP_OUTLIER_POLICY` in `src/hpm/domain/constants.py`.

| Situation | Behavior |
| --- | --- |
| Ambiguous DST fall-back local time | Excluded (`ambiguous_local_time`) |
| Nonexistent spring-forward local time | Excluded (`nonexistent_local_time`) |
| Unparseable timestamp | Excluded (`timestamp_parse_failure`) |
| Aware offset timestamps | Converted to UTC directly |
| Extreme but parseable instants | **Retained** (no far-past / far-future drop) |
| Negative elapsed spans | Discarded and counted — **never clamped** to zero |

Tests: `tests/test_timestamps.py`, `tests/test_timestamp_outliers.py`.

### Seed 42 leading bottleneck (reproduced)

| Field | Value |
| --- | --- |
| Edge | Interview Scheduled → Interview Completed |
| Median delay | **1 268 568.8738075001 s** ≈ **14.6825 d** |
| UI display | `formatDuration` → **14.7 d** (one decimal day) |
| Numerator (transitions) | 592 |
| Sample size (distinct cases) | 504 |
| Method | Highest median among edges with ≥ 30 observations |

This is an **observation** on the synthetic log (and matches the generator’s long-wait
construction). It is not a causal claim that interview scheduling “causes” delay in a
real organization.

## Cycle time (completed vs ongoing)

| Term | Definition |
| --- | --- |
| Terminal activities | `Hired`, `Rejected`, `Withdrawn` |
| Completed case | Has at least one terminal activity |
| Ongoing case | No terminal activity |
| Cycle time | First event → earliest terminal event (UTC elapsed seconds) |
| Distribution sample | Completed cases with a non-negative span only |

Ongoing cases contribute to **active-case aging** (`as_of` = explicit instant or latest
event in the filtered log) and are **excluded** from the completed cycle-time
distribution. Tests: `test_cycle_time_excludes_ongoing_cases`,
`test_import_matches_hand_computed_cycle_time_and_edge`.

## Funnel denominators

| Term | Definition |
| --- | --- |
| Denominator | Distinct `case_id` among analytics-eligible events after filters |
| Stage reach | Presence of the activity anywhere in the case (not order-based) |
| Drop-off | Cases that reached the previous happy-path stage but not this stage (set difference of case ids) |

Happy path: `Applied → Screened → Interview Scheduled → Interview Completed → Offer → Hired`.

On seed 42, funnel `denominator` = **800**. Sequence / skip problems are reported by
**conformance**, not subtracted inside the funnel. Test: `test_funnel_denominator_and_drop_off`.

## Variants

Exact activity sequences after ordering, ranked by case count. Median cycle per variant
uses the same completed-only rule. Share denominator = distinct cases in the filtered
log.

### Seed 42 top variant (reproduced)

| Field | Value |
| --- | --- |
| Sequence | Applied → Screened → Interview Scheduled → Interview Completed → Offer → Hired |
| Case count | 159 |
| Share | 0.19875 → **19.8%** in UI |

## Rework

- **Repeat:** activity occurs ≥ 2 times in a case after ordering.
- **Self-loop:** two consecutive events with the same activity.
- Example case ids are anonymous and capped at five in API payloads.

## Conformance (rule-based; pandas core)

A case **fits** when every consecutive pair after ordering is in the allowed-transition
model (editable per dataset; default happy-path-oriented edges in
`DEFAULT_ALLOWED_TRANSITIONS`). **Does not import or call PM4Py.**

| Field | Meaning |
| --- | --- |
| `fitting_cases` / `numerator` | Cases with zero disallowed transitions |
| `sample_size` | Distinct cases in the filtered log |
| `fit_rate` | numerator / sample_size |

Seed 42 (default model): **670 / 800** fitting → fit_rate **0.8375**.

Token-replay and alignments need the optional `pm4py` extra (**AGPL-3.0-or-later**) and
are **not** invoked by the default conformance endpoint. See
[`ENGINEERING_DECISIONS.md`](ENGINEERING_DECISIONS.md) HPM-1. Enabling that extra may
have licensing implications for a given distribution or hosting model — have qualified
counsel review. This document does not give legal advice or categorical compliance
conclusions.

## Insight cards

Cards such as “highest median transition delay” always expose:

1. **Numerator** — observations included in the statistic (e.g. transition count).
2. **Sample size** — distinct cases contributing.
3. **Method** — definition string from constants.
4. **Causal caution** — observation ≠ causation; not a hiring recommendation.

## Core stack vs optional PM4Py

| Path | Libraries | License note |
| --- | --- | --- |
| Default discovery & KPIs | **pandas / NumPy** | Repository MIT; optional pm4py is AGPL upstream |
| Optional token-replay / alignment | `pm4py` via `uv sync --extra pm4py` | Dependency is **AGPL-3.0-or-later**; review before enabling |

Core pytest must pass without `pm4py` installed (parity tests skip).

## Reproducibility checklist

```powershell
uv run python -c "from hpm.domain.seedgen import render_seed_csv; from hpm.domain.parsing import FieldMapping, parse_csv; from hpm.services.frames import frame_from_parsed; from hpm.domain.metrics import insights, directly_follows; from hpm.domain.quality import quality_report; m=FieldMapping(case_id='case_id',activity='activity',timestamp='timestamp',resource='resource',role='role',channel='channel',outcome='outcome',cost='cost',job_family='job_family'); e=parse_csv(render_seed_csv(800,42),m,'Europe/Berlin'); q=quality_report(e,timezone='Europe/Berlin'); d=frame_from_parsed(e); h=insights(d)['cards'][0]; print(q['unique_cases'], h['value'], h['source_activity'], h['target_activity'])"
```

Expect: `800`, median ≈ `1268568.87`, edge `Interview Scheduled` → `Interview Completed`.

Also:

1. Compare edge median/p90 and cycle time to `tests/test_metrics.py` hand calculations.
2. Confirm ongoing cases never enter `performance.cycle_time.sample_size`.
3. Confirm funnel `denominator` equals filtered distinct case count.
4. Confirm conformance `method` string states PM4Py is not used.
5. `tests/test_seed.py` asserts deterministic CSV and that interview wait is the longest median on the synthetic funnel.

## What is not measured

- Causal root causes or “days saved” from process changes.
- Live customer benchmarks or industry percentiles.
- Coverage percentages beyond counting pytest/Vitest outcomes that were actually run.
- Processing-time vs wait-time splits (single timestamp per event).
