# Design decisions

## HPM-1 — PM4Py stays optional (AGPL)

PM4Py is licensed AGPL-3.0-or-later. Shipping it as a hard dependency would force this application and any hosted service that embeds the analytics path into AGPL obligations.

**Decision:** all core analytics (validation, `canonical_order`, DFG, variants, funnel, performance, rework, rule-based conformance) are implemented with pandas/NumPy and never import `pm4py`. The optional extra is:

```toml
[project.optional-dependencies]
pm4py = ["pm4py>=2.7.15"]
```

Token-replay / alignment-style features live behind `hpm.pm4py_adapter` and are lazily imported. When the extra is absent, the API and UI return a clear message; the rule-based allowed-transition check still runs. Core pytest must pass without pm4py installed.

License for this repository remains **pending owner decision** (see README). Enabling the PM4Py extra may introduce AGPL obligations for that deployment path.

## HPM-2 — One ordering contract

Every analytics function receives rows already ordered by `canonical_order()`: UTC timestamp ascending, then original source row number. No alternate sort paths.

## HPM-3 — DST policy

Timestamps are stored as UTC. Ambiguous and nonexistent local times follow the configured policy (default: flag the record and exclude it from duration metrics). Surfaced in the data-quality panel.
