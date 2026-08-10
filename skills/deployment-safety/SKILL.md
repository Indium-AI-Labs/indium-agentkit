---
name: deployment-safety
description: Plan and verify staged deployments with safe rollback.
---

# Deployment safety

Prepare a production change so it can be released deliberately, observed, and
reversed. Inspect the project's `AGENTS.md`, deployment platform, environments,
service dependencies, and release policy before making assumptions.

## Workflow

1. Define the change, owner, target environment, blast radius, and explicit
   success and abort criteria.
2. Verify the artifact is reproducible and traceable to a commit. Confirm tests,
   migrations, configuration, feature flags, and required approvals.
3. Check environment parity, runtime versions, dependency availability, secrets
   references, permissions, capacity, and maintenance windows.
4. Write a staged rollout: preflight, canary or small cohort, observation
   window, expansion, and completion. Assign an operator and observer.
5. Choose health signals before rollout: error rate, latency, saturation,
   business outcome, logs, traces, and dependency health.
6. Define exact abort thresholds, who can stop the rollout, and how to halt it
   without destroying evidence.
7. Define and rehearse rollback or forward-fix steps, including database and
   queue compatibility. Never assume a schema rollback is automatically safe.
8. Execute only the authorized scope, record timestamps and evidence, and update
   the deployment handoff with results, limitations, and follow-up actions.

## Guardrails

- Do not deploy to production, rotate credentials, or run destructive commands
  without explicit authorization.
- Prefer backward-compatible expand-and-contract changes when versions overlap.
- Keep secrets out of plans, logs, screenshots, and chat transcripts.
- Optional release-engineer delegation can accelerate preparation; one agent can
  complete this workflow independently.

## Completion report

Report artifact and revision, environments, checks, rollout gates, observed
signals, rollback readiness, exact commands, and anything unverified.
