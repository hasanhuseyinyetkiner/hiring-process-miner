# Engineering decisions

Short ADRs for the process-mining core. Full KPI contracts live in [`METRICS.md`](METRICS.md).

## Canonical event ordering

**Decision:** Sort by timestamp, then by a stable secondary key so identical timestamps remain deterministic.

**Why:** Hiring logs often collide on wall-clock precision. Non-deterministic order would make DFG edges and bottleneck medians flake across runs.

## Completed vs ongoing cases

**Decision:** Funnel and duration KPIs distinguish completed cases from open traces; censored/open cases do not silently enter “time-to-hire” denominators.

**Why:** Mixing open and closed cases biases latency downward and invents false throughput.

## Quality probes (QX)

**Decision:** Synthetic quality-probe rows are visible in hygiene tooling and excluded from aggregate KPIs.

**Why:** Probe injection validates import hygiene without inflating `generate_cases(800)` eligible counts.

## Pandas core; optional PM4Py

**Decision:** Discovery, DFG, variants, and bottlenecks run on pandas/NumPy. PM4Py is an optional AGPL adapter, never a hard dependency of the default install.

**Why:** Keeps the MIT core usable offline and makes AGPL adoption an explicit operator choice.

## Import jobs off the event loop

**Decision:** CSV import and heavy analytics run in a thread pool; startup reaper fails stale `RUNNING` jobs.

**Why:** Large logs must not block `/health` and `/ready`.

## Timestamp outliers

**Decision:** Exclude ambiguous/nonexistent local times and parse failures; keep extreme but valid UTC instants; discard (do not clamp) negative durations. See `TIMESTAMP_OUTLIER_POLICY`.

**Why:** DST gaps have no single UTC instant. Clamping invents false throughput; dropping far-future stamps without a documented window would silently bias cohorts.

## Filter impact diagnostics

**Decision:** Analytics responses that accept `FilterSpec` expose `filter_impact` (cases/events retained) with the same causal caution as insight cards.

**Why:** Analysts need to see how aggressive a cohort filter is without reading retention as causation.
