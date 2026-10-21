# Analyst case study — synthetic hiring log

A concise end-to-end path from event log to an **auditable observation**. All numbers
below were reproduced against `render_seed_csv(800, 42)` (see
[`EVALUATION.md`](EVALUATION.md)). Screenshots in `docs/screenshots/` were captured from
the live UI (API **8102**, web **5102**) via Playwright.

## Setup

1. Start the stack (`uv run python -m hpm` and `pnpm dev` in `frontend/`).
2. With `SEED_ON_STARTUP=true` (default), an empty database seeds **Synthetic hiring log**
   (`generator_cases=800`, seed **42**, **800** eligible cases).
3. Open http://127.0.0.1:5102 — select the synthetic dataset (Synthetic badge).

Tiny cold-import alternative: [`samples/tiny-hiring-log.csv`](../samples/tiny-hiring-log.csv).

## Step 1 — Process map (directly-follows)

Open **Process map**. The graph is a directly-follows map after canonical ordering
(UTC timestamp, then `source_row`). Click **Interview Scheduled** to open the drawer
(case and event counts for that stage).

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="screenshots/process-map-dark.png">
    <img alt="Process map of Synthetic hiring log (800 eligible cases) with Interview Scheduled selected in the details drawer" src="screenshots/process-map-light.png" width="100%">
  </picture>
</p>

*Caption: Seeded synthetic DFG; Interview Scheduled selected. Edge thickness reflects
case frequency after the map’s min-ratio filter. Observation of structure only — not a
claim that this is an optimal hiring design.*

## Step 2 — Bottleneck insight card

Open **Bottlenecks**. The leading card ranks edges by median transition delay among
edges with ≥ 30 observations.

| Field | Seed-42 value |
| --- | --- |
| Edge | Interview Scheduled → Interview Completed |
| Median | ≈ **14.68 d** (exact ≈ 1 268 568.87 s ≈ 14.6825 d; UI often rounds to 14.7 d) |
| Numerator | 592 transitions |
| Sample size | 504 distinct cases |
| Caution | Not a causal root cause; not a hiring recommendation |

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="screenshots/bottlenecks-dark.png">
    <img alt="Bottlenecks page: highest median transition delay for Interview Scheduled to Interview Completed on the seeded synthetic log" src="screenshots/bottlenecks-light.png" width="100%">
  </picture>
</p>

*Caption: Transparent insight card (numerator, sample size, method). The long wait is
also **by construction** in the synthetic generator (Uniform 240–480 h on this edge);
treat it as a demo of the KPI contract, not as industry evidence.*

## Step 3 — Variants

Open **Variants**. Top path on seed 42:

| Field | Value |
| --- | --- |
| Sequence | Applied → Screened → Interview Scheduled → Interview Completed → Offer → Hired |
| Cases | 159 |
| Share | 19.8% of 800 |

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="screenshots/variants-dark.png">
    <img alt="Variants page ranking distinct activity sequences for 800 synthetic eligible cases" src="screenshots/variants-light.png" width="100%">
  </picture>
</p>

*Caption: Exact activity sequences after canonical ordering, ranked by case volume.
Share denominator = distinct cases in the filtered log.*

## Step 4 — Export an auditable artifact

From the map toolbar, export **CSV summary** or **HTML report**. Both include dataset
assumptions (ordering contract, delay definition, causal caution). That export is the
handoff artifact for an ops review — numbers with method, not a root-cause memo.

## What to write in a review note

> On the synthetic seed (800 cases, seed 42), Interview Scheduled → Interview Completed
> has the highest median transition delay among edges with ≥ 30 observations
> (≈ 14.68 d; n = 592 transitions from 504 cases). This is an observation on the log
> (and matches the generator’s long-wait construction). It does not establish why
> interviews wait in a real organization, and it is not a recommendation to change
> staffing or reject candidates.

## Recapture screenshots

```powershell
# API on 8102 and web on 5102 must be running
cd frontend
pnpm screenshots
```
