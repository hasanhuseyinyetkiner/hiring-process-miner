# Engineering decisions

Staff-level product and licensing choices for Hiring Process Miner. Short IDs match
`docs/DECISIONS.md`.

## HPM-1 — Core analytics are pandas; PM4Py is an optional extra

**Context.** The `pm4py` package is published under **AGPL-3.0-or-later**. Shipping it as
a hard dependency would couple the default demo path to that dependency’s license. This
document records an **engineering** choice (keep AGPL code off the default import graph).
It is **not legal advice** and does not conclude whether a particular deployment is
compliant — have qualified counsel review AGPL terms before enabling PM4Py in a product
you distribute or host.

**Decision.** Every shipped discovery and KPI path is implemented with **pandas/NumPy**
and never imports `pm4py`:

| Capability | Implementation |
| --- | --- |
| Validation, DST policy, duplicates | `hpm.domain.parsing`, `timestamps`, `quality` |
| Ordering | `canonical_order()` in `hpm.domain.ordering` |
| DFG, variants, funnel, performance, rework | `hpm.domain.metrics` |
| Rule-based conformance | Allowed-transition model in `metrics.conformance` |
| Token-replay / alignment | Optional `hpm.pm4py_adapter` only |

Optional install:

```toml
[project.optional-dependencies]
pm4py = ["pm4py>=2.7.15"]
```

```powershell
uv sync --extra pm4py
```

When the extra is absent, the API reports `available: false` with a clear message; the
rule-based conformance endpoint still returns a fit rate. Core pytest must pass without
`pm4py` installed (parity tests are skipped).

**License status.** This repository is **MIT** (see root `LICENSE`). The default demo
path does not install `pm4py`. Enabling `uv sync --extra pm4py` pulls an upstream
package licensed **AGPL-3.0-or-later** and may have licensing implications for that
deployment path. Have qualified counsel review AGPL implications before hosting a
product that links PM4Py. This document states dependency facts and does **not** give
categorical legal conclusions about compliance.

## HPM-2 — One ordering contract

**Decision.** `canonical_order()` sorts by UTC timestamp ascending, then original
`source_row` ascending (`mergesort`). `build_traces()` always calls it; analytics
functions never trust a pre-sorted frame. Equal-timestamp fixtures prove the tie-break.

## HPM-3 — DST-safe timestamps

**Decision.** Store UTC. Ambiguous and nonexistent local times (default policy) are
flagged in the quality panel and excluded from duration metrics. Fixtures use
`Europe/Berlin` fall-back and spring-forward edges.

## HPM-4 — Observation is not causation

**Decision.** Insight cards always expose **numerator**, **sample size**, and
**method**. Copy states that transition delay is elapsed time between events, not
processing time, and is not a causal root cause or a hiring recommendation. No
automatic reject/advance decisions exist in the product.

## HPM-5 — Completed vs ongoing cycle time

**Decision.** A case is **completed** when it has a terminal activity
(`Hired`, `Rejected`, `Withdrawn`). Cycle time is first event → earliest terminal
event. Ongoing cases appear in aging metrics only and are excluded from the
completed cycle-time distribution. Negative spans are discarded and counted, not clamped.

## HPM-6 — Funnel denominators are explicit

**Decision.** Funnel denominator = distinct `case_id` values among analytics-eligible
events after filters. Stage reach is **presence-based** (activity appears somewhere in
the case), not order-based. Drop-off is a set difference of case ids between consecutive
happy-path stages — not a claim that the case exited at that step. Sequence problems
belong to conformance.

## HPM-7 — Loopback demo, no auth in MVP

**Decision.** Bind `127.0.0.1` by default. Non-loopback hosts require
`ALLOW_NETWORK_BIND=true`. Compose maps `127.0.0.1:8102`, `127.0.0.1:5102`,
`127.0.0.1:5402`. Suitable for synthetic / already anonymized logs only.

## HPM-8 — Heavy work off the event loop

**Decision.** Import, discovery, and KPI computation use a thread pool /
`run_in_threadpool`. Jobs persist `status` + `heartbeat_at`; a startup reaper marks
stale `RUNNING` jobs `FAILED`. `/health` stays responsive under load (covered by test).

## Related files

| File | Role |
| --- | --- |
| [`DECISIONS.md`](DECISIONS.md) | Short HPM-1…3 record |
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | Runtime topology and module map |
| [`METRICS.md`](METRICS.md) | Formal metric definitions |
| [`EVALUATION.md`](EVALUATION.md) | Evaluation narrative + reproduced seed figures |
