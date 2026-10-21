# Evaluation and reproduction

## Seed-42 synthetic log

| Parameter | Value |
| --- | --- |
| Generator cases | 800 |
| Eligible case count | 800 |
| Seed | 42 |
| QX probes | Excluded from aggregate KPIs |

Bottleneck median for the leading transition (verified in golden tests): see `tests/test_metrics.py` and [`METRICS.md`](METRICS.md).

## Commands

```powershell
uv run ruff check src tests
uv run pytest -q
cd frontend
pnpm test
pnpm build
pnpm e2e
```

Record exit codes and skip reasons when reporting results. Do not treat skipped optional PM4Py tests as failures of the pandas core.

## What evaluation is not

- Not a production hiring-process benchmark.
- Not evidence of causation between process steps and outcomes.
- Not a substitute for domain expert review of real event logs.
