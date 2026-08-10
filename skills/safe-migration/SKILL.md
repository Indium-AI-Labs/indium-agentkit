---
name: safe-migration
description: "Plan and implement safe schema, API, configuration, storage, or file-format migrations with compatibility analysis, staged rollout, rollback, and evidence-based verification."
---

# Safe migration

1. Inventory producers, consumers, data stores, configuration, deployment order, and version boundaries.
2. Define the target state, compatibility contract, preflight checks, and a measurable cutover criterion.
3. Prefer staged expand-migrate-contract changes: introduce compatible readers and writers, migrate data or traffic, verify, then remove legacy behavior.
4. Define a tested rollback path before destructive or irreversible steps. Stop and request approval for irreversible operations.
5. Implement the smallest stage that can be verified safely. Protect existing data and avoid mixing unrelated changes into the migration.
6. Report rollout state, checks, metrics or evidence, rollback readiness, and remaining cleanup work.
