# Security boundaries

Hiring Process Miner is a **local demo**, not a multi-tenant SaaS.

## Assumptions

- Default bind is loopback (`127.0.0.1`). Non-loopback requires `ALLOW_NETWORK_BIND=true`.
- No authentication or authorization in the MVP.
- Intended inputs are **anonymized or synthetic** event logs. Do not upload candidate PII (names, emails, resumes, demographics).
- Upload size and row caps are enforced server-side; treat them as abuse limits, not a full WAF.
- CORS is configured for the paired demo UI origins. CORS is not an authentication mechanism.

## Optional PM4Py (AGPL)

The optional `pm4py` extra depends on an **AGPL-3.0-or-later** upstream package. It is not installed by default. Enabling it may change distribution obligations for that deployment path — treat license compatibility as an open item for qualified counsel review. This document is not legal advice.

## What this is not

- Not a production HR platform security posture.
- Not a claim of vulnerability-free dependencies or containers.
- Not suitable for real candidate decisioning systems without a full security redesign (authn/z, tenancy, audit logging, data retention).
