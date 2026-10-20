# Limitations

Honest boundaries of this MVP. Nothing here is a production hiring platform claim.

## Product

- **Not a decision engine.** No automatic reject/advance of candidates.
- **Observation ≠ causation.** Delays and drop-offs describe the event log only.
- **Single timestamp per event.** Transition delay is elapsed time, not processing time.
- **CSV only.** XES import is not shipped.
- **No multi-user auth.** Loopback demo; unsuitable for shared production without auth,
  tenancy, and a license decision.
- **Synthetic demo data.** Seeded log is generated; never real candidate PII.

## Analytics

- Funnel stage reach is **presence-based**, not path-order-based.
- Completed cycle time excludes ongoing cases; mixing them would bias medians.
- Rule-based conformance uses an editable allowed-transition model; token-replay needs
  optional PM4Py (AGPL) and is not on the default path.
- Edge-frequency filters hide rare edges in the map; they do not delete cases from KPIs
  unless filters exclude them.

## Operations

- Upload size and row caps apply (`MAX_UPLOAD_BYTES`, `MAX_ROWS` in settings / `.env`).
- Heavy jobs run in a small thread pool; pathological logs can still be slow.
- Docker Compose is verified in CI `compose-smoke`; the documented native path is
  `uv` + `pnpm` on Windows/Linux.

## Licensing

- Repository license: **pending owner decision** (no `LICENSE` file in this MVP).
- Optional `pm4py` extra depends on a package licensed **AGPL-3.0-or-later** — see
  [`ENGINEERING_DECISIONS.md`](ENGINEERING_DECISIONS.md). Review with counsel before
  enabling in a deployment you distribute or host; docs here are not legal advice.
