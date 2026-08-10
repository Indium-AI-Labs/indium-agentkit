# Data migration plan

## Current and target state

Describe current schema and data, target schema, invariants, and ownership.

## Preflight

List backups, volume estimates, lock assessment, feature flags, and required
application versions before rollout.

## Rollout

Describe the staged expand, backfill, compatibility, cutover, and contract
steps. Include batching and deployment ordering where relevant.

## Rollback

Describe the safe stop point, reversal steps, and data recovery limitations.

## Verification

List reconciliation queries, row counts, invariants, query-plan checks, and
application behavior to verify.

## Handoff

**Changed contract:** State nullability, defaults, uniqueness, or API effects.

**Files / systems affected:** List schemas, migrations, services, and jobs.

**Evidence and tests:** List dry runs and validation evidence.

**Risks / rollback:** State locks, data loss risks, and recovery path.

**What the next agent needs:** List approvals, sequencing, and open questions.
