---
name: database-design
description: Design safe PostgreSQL schemas and staged migrations.
---

# Database design

Design data models and compatible migrations before implementation. PostgreSQL
is the default target, but respect the project's current database, ORM, and
operational constraints.

## Workflow

1. Read `AGENTS.md`, the feature brief, API contract, existing schema, and
   query paths. State uncertainties about cardinality, retention, ownership,
   privacy, and expected access patterns.
2. Model entities, keys, constraints, relationships, lifecycle fields, and
   ownership boundaries. Prefer database-enforced invariants for critical data
   integrity.
3. Choose indexes from real query predicates, ordering, join paths, and expected
   volume. Explain each index and avoid speculative indexes.
4. Produce a staged migration plan: preflight, expand, backfill, dual-read or
   dual-write if needed, cutover, contract, verification, and rollback.
5. Assess lock duration, transaction size, backfill batching, replication lag,
   and deploy ordering. Use the `safe-migration` skill when it provides deeper
   guidance.
6. Define data validation and reconciliation queries, including counts and
   invariant checks, before any production action.
7. Keep the API contract and feature brief aligned with nullability, defaults,
   uniqueness, deletion, and error behavior.
8. Capture the proposal in `templates/handoffs/data-migration-plan.md` or the
   project's equivalent, including assumptions and exact verification evidence.

## Guardrails

- This skill designs and verifies migrations; never run a production migration
  or destructive data operation without explicit authorization.
- Preserve backward compatibility through staged changes when multiple versions
  of an application may run concurrently.
- A migration-planner subagent may independently inspect the design, but it is
  optional and this workflow remains usable by one agent.

## Completion report

Report the proposed schema, invariants, access-path rationale, rollout and
rollback plan, validation queries, dependencies, and open risks.
