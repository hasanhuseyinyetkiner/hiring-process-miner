# Security and privacy

## Intended use

Local analysis of **already anonymized** hiring event logs, or the built-in **synthetic**
seed. Do not upload candidate names, emails, phones, resumes, or demographics.

## Controls in this MVP

| Control | Behavior |
| --- | --- |
| Bind address | Default `127.0.0.1`; non-loopback requires `ALLOW_NETWORK_BIND=true` |
| Auth | None — treat as a single-operator demo |
| Uploads | Size and row caps; CSV expected; drafts cleaned on a schedule |
| CORS | Explicit origin list (default ports 5102) |
| Secrets | No hardcoded credentials; use `.env` locally and never commit it |
| Jobs | Stale `RUNNING` jobs reaped on startup |

## Privacy defaults

- Case identifiers should already be anonymized before import.
- UI and API carry a privacy notice (`PRIVACY_NOTICE` in domain constants).
- Dataset delete removes stored events for that dataset id.

## Out of scope until hardened

- Multi-tenant isolation, SSO, audit logs for regulated HR systems.
- Network exposure without authentication.
- Guarantees about customer data retention beyond local disk.

Report security concerns privately to the repository owner. Do not file public issues
that include real candidate data.
