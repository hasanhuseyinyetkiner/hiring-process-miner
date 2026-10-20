# Release readiness checklist

Owner-driven checklist before tagging a public release. Agents must **not** push,
create remotes, or publish without explicit owner approval. No `LICENSE` file until the
owner chooses a license.

## Product honesty

- [ ] README status remains **local MVP / demo** (not multi-user production SaaS).
- [ ] Synthetic data labeled synthetic everywhere; no implication of real candidates.
- [ ] Observation ≠ causation language present on bottleneck / insight surfaces.
- [ ] Seed case count in README matches code: **800** eligible cases for
      `generator_cases=800`, seed 42 (not 802).
- [ ] Bottleneck figure cited with method: ≈ **14.7 d** UI display for Interview
      Scheduled → Interview Completed; exact seconds reproducible via
      [`EVALUATION.md`](EVALUATION.md).

## Technology and licensing

- [ ] Default path: **pandas/NumPy** only; PM4Py not required.
- [ ] Docs state optional `uv sync --extra pm4py` pulls **AGPL-3.0-or-later** and advise
      **license review** — no categorical legal conclusions in README or marketing.
- [ ] Repository license still **pending** unless the owner has decided and added
      `LICENSE` themselves.
- [ ] Release notes state whether the tagged build includes the `pm4py` extra.

## Evidence

- [ ] Fresh `uv run ruff check src tests` and `uv run pytest -q` recorded in README table.
- [ ] Fresh `pnpm lint`, `pnpm typecheck`, `pnpm test`, `pnpm build`.
- [ ] Screenshots in `docs/screenshots/` still match ports 5102/8102 and accent `#7C3AED`
      (or recapture with `pnpm screenshots`).
- [ ] Relative links and image paths in README / `docs/*` resolve.
- [ ] CI green on the commit to tag (`.github/workflows/ci.yml`).

## Security / privacy

- [ ] Loopback bind defaults unchanged; no secrets committed.
- [ ] Privacy notice and upload caps documented ([`SECURITY.md`](SECURITY.md)).
- [ ] [`LIMITATIONS.md`](LIMITATIONS.md) still accurate.

## Docs set for a stranger

| Doc | Purpose |
| --- | --- |
| Root `README.md` | Run, demo, evidence |
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | Topology |
| [`EVALUATION.md`](EVALUATION.md) / [`METRICS.md`](METRICS.md) | KPI audit |
| [`DEMO.md`](DEMO.md) | Analyst case study |
| [`ENGINEERING_DECISIONS.md`](ENGINEERING_DECISIONS.md) | Staff decisions |
| [`GITHUB_METADATA.md`](GITHUB_METADATA.md) | About box / topics |
| [`PRODUCT_SPEC.md`](PRODUCT_SPEC.md) | **Historical** brief only |

## Explicit non-goals for this checklist

- Do not invent coverage %, stars, live-demo URLs, or client case studies.
- Do not rewrite git history or force-push.
- Do not claim “production ready,” “compliant,” or “bias free.”
