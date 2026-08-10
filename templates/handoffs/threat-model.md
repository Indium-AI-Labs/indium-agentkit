# Threat model

## Scope and system overview

Describe the system component, architecture scope, data flow boundaries, and primary assets.

## Trust boundaries and assets

| Trust boundary | Source | Destination | Asset transferred | Protection mechanism |
| --- | --- | --- | --- | --- |
| `boundary name` | component | component | asset | TLS / Auth / Encryption |

## STRIDE threat inventory

| ID | STRIDE category | Threat description | Affected component | Risk level | Proposed mitigation |
| --- | --- | --- | --- | --- | --- |
| T-01 | Spoofing | Impersonation risk | Auth API | High | WebAuthn / mTLS |
| T-02 | Tampering | Parameter manipulation | Checkout endpoint | Medium | HMAC signatures |
| T-03 | Repudiation | Unlogged admin action | User Management | Medium | Immutable audit log |
| T-04 | Info Disclosure | PII leak in error trace | Logging middleware | High | Structured redaction |
| T-05 | DoS | Unbounded payload query | GraphQL resolver | High | Query depth limits |
| T-06 | Elevation | Missing RBAC check | Settings controller | Critical | Role-check guard |

## Residual risk assessment

Document any threats that cannot be fully mitigated in current scope, with operational workarounds.

## Handoff

**Changed contract:** Describe any security contract changes or state `none`.

**Files / systems affected:** List architecture boundaries, handlers, and security middleware.

**Evidence and tests:** List static analysis checks, threat validation cases, and verification.

**Risks / rollback:** State risks of security mitigation deployment.

**What the next agent needs:** Actionable engineering tasks to implement mitigations.
