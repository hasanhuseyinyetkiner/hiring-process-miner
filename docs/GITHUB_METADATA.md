# GitHub repository metadata

Use these values when configuring the public GitHub repository About box and topics.
Do not invent stars, download counts, coverage percentages, or live demo URLs.

## About description

GitHub About has a short character limit. Prefer:

```
Process mining for hiring funnels — DFG, bottlenecks, variants, conformance. pandas core; optional AGPL PM4Py.
```

## Topics

```
process-mining
pm4py
data-analytics
fastapi
react
hr-tech
event-logs
python
pandas
typescript
```

`pm4py` is listed because the optional adapter exists; **core analytics do not require
PM4Py** (see [`ENGINEERING_DECISIONS.md`](ENGINEERING_DECISIONS.md) HPM-1). Enabling the
optional extra may have AGPL implications depending on how you distribute or host the
software — have qualified counsel review; metadata here is not legal advice.

## Homepage

Leave empty until a stable public demo URL exists.

## Suggested pin rationale (portfolio)

> Hiring Process Miner — process-mining case study: explainable KPIs,
> observation≠causation discipline, AGPL-aware optional PM4Py, interactive DFG.

## Release notes checklist

When cutting a tagged release (owner-driven; no push from agents without approval):

1. Confirm README test table matches a fresh local or CI run.
2. Confirm screenshots in `docs/screenshots/` match ports 5102/8102 and violet `#7C3AED`.
3. Confirm seed copy: **800** eligible cases (seed 42), bottleneck ≈ **14.68 d** with
   numerator/sample/method — see [`EVALUATION.md`](EVALUATION.md).
4. State whether the release includes the `pm4py` optional extra or not; note license
   review for that path.
5. Reaffirm: MIT for this repo; synthetic data only; not a hiring decision engine.

## Notes

- README commands must match `pyproject.toml`, `frontend/package.json`, and
  `.github/workflows/ci.yml`.
- Prefer evidence from `uv run pytest`, `pnpm test`, Playwright, and Actions — never
  aspirational numbers.
