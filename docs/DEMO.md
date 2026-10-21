# Demo walkthrough

Prerequisites: API on `http://127.0.0.1:8102`, web on `http://127.0.0.1:5102` (see root README quick start).

1. Open the web UI — confirm the **Synthetic** badge and **800** eligible cases (seed 42).
2. **Process map** — select an activity (for example Interview Scheduled); the drawer shows case/event counts from the live API.
3. **Bottlenecks** — inspect the leading transition latency card and the distribution table (mean / median / percentiles as exposed).
4. **Overview → Data Hygiene** — confirm QX probe rows are listed and excluded from analytics.
5. Apply a cohort filter — KPIs recalculate via the API (not a static screenshot snapshot).
6. Export CSV or HTML from the map toolbar.

Tiny CSV sample: [`../samples/tiny-hiring-log.csv`](../samples/tiny-hiring-log.csv).

```powershell
curl http://127.0.0.1:8102/api/datasets
curl "http://127.0.0.1:8102/api/datasets/<id>/process?min_case_ratio=0.05"
```
