# Design decisions

Canonical long-form record: [`ENGINEERING_DECISIONS.md`](ENGINEERING_DECISIONS.md).
Short summaries below keep older links stable.

## HPM-1 — PM4Py stays optional

The `pm4py` dependency is licensed **AGPL-3.0-or-later**. To keep the default demo path
on pandas/NumPy only, PM4Py is an optional extra behind a lazy adapter — an engineering
isolation choice, **not** a legal determination of your obligations. Review AGPL terms
with counsel before enabling the extra in a distributed or hosted product.

**Decision:** all core analytics (validation, `canonical_order`, DFG, variants, funnel,
performance, rework, rule-based conformance) are implemented with pandas/NumPy and never
import `pm4py`. The optional extra is:

```toml
[project.optional-dependencies]
pm4py = ["pm4py>=2.7.15"]
```

Token-replay / alignment-style features live behind `hpm.pm4py_adapter` and are lazily
imported. When the extra is absent, the API and UI return a clear message; the rule-based
allowed-transition check still runs. Core pytest must pass without pm4py installed.

License for this repository remains **pending owner decision** (see README).

## HPM-2 — One ordering contract

Every analytics function receives rows already ordered by `canonical_order()`: UTC
timestamp ascending, then original source row number. No alternate sort paths.

## HPM-3 — DST policy

Timestamps are stored as UTC. Ambiguous and nonexistent local times follow the configured
policy (default: flag the record and exclude it from duration metrics). Surfaced in the
data-quality panel.
