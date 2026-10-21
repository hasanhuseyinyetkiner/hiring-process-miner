# Limitations

Honest constraints for reviewers and operators.

## Analytics

- Bottlenecks are **observations**, not causal claims.
- Incomplete / censored cases and quality-probe (QX) rows are excluded from aggregates; they appear in hygiene views instead of silently inflating KPIs.
- Identical timestamps use deterministic canonical ordering; wall-clock truth may still be ambiguous in source systems.
- Optional PM4Py paths are not required for core DFG/KPI computation.

## Product scope

- Single-user local demo; no auth, no multi-tenancy.
- Synthetic seed (`generator_cases=800`, seed 42) is for reproducibility, not a real hiring funnel.
- Cross-timezone imports depend on correct source timestamps; the demo does not invent missing TZ metadata.

## Evaluation

- Golden fixtures cover known seed-42 contracts. They are not a substitute for production data QA.
- PM4Py parity tests may be skipped when the optional extra is absent.
