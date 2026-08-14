---
name: safe-migration
description: "Plan and implement safe schema, API, configuration, storage, or file-format migrations with compatibility analysis, staged rollout, rollback, and evidence-based verification."
---

# Safe Migration

Plan and execute migrations of database schemas, API contracts, configuration,
storage engines, or file formats without downtime, data loss, or broken
consumers. The default approach is **expand-migrate-contract**: introduce
backward-compatible readers and writers first, move data or traffic through
verifiable stages, and remove legacy behavior only after the new path is
proven under production-like conditions.

The skill is **evidence-based**: every stage terminates in measurable checks
with recorded output, and a tested rollback path exists before any destructive
or irreversible step is attempted. Adapt stage mechanics, tooling, and command
syntax to the repository's migration framework, deployment pipeline, and
datastore before writing or running any change.

---

## 1. Required I/O Context Schemas & Natural Language Auto-Inference

The skill supports **two invocation modes**:

1. **Orchestrator / Technical Mode (JSON Manifest)**: Pass the JSON context
   manifest below.
2. **Non-Technical Mode (Plain English Prompts)**: If the user provides a
   natural language prompt (e.g. *"Split the users.full_name column into
   first_name and last_name without downtime"*), the agent **must
   automatically infer and populate** `migration_spec`,
   `compatibility_context`, and `rollout_context` from the user's text and
   from repository evidence.

### JSON Context Manifest Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "SafeMigrationContextManifest",
  "type": "object",
  "required": ["migration_spec", "compatibility_context", "rollout_context"],
  "properties": {
    "migration_spec": {
      "type": "object",
      "required": ["kind", "source_state", "target_state"],
      "properties": {
        "kind": { "type": "string", "enum": ["schema", "api", "config", "storage", "file_format"] },
        "source_state": { "type": "string", "minLength": 1 },
        "target_state": { "type": "string", "minLength": 1 },
        "affected_artifacts": { "type": "array", "items": { "type": "string" } },
        "data_at_risk": { "type": "boolean", "default": true }
      }
    },
    "compatibility_context": {
      "type": "object",
      "required": ["producers", "consumers", "version_overlap"],
      "properties": {
        "producers": { "type": "array", "items": { "type": "string" }, "minItems": 1 },
        "consumers": { "type": "array", "items": { "type": "string" }, "minItems": 1 },
        "version_overlap": { "type": "string", "enum": ["none", "rolling_deploy", "long_lived_clients"] },
        "breaking_change": { "type": "boolean", "default": false }
      }
    },
    "rollout_context": {
      "type": "object",
      "required": ["stages", "cutover_criterion", "rollback_path"],
      "properties": {
        "stages": {
          "type": "array",
          "items": { "type": "string", "enum": ["preflight", "expand", "dual_write", "backfill", "dual_read", "cutover", "contract", "cleanup"] },
          "minItems": 1
        },
        "cutover_criterion": { "type": "string", "minLength": 1 },
        "rollback_path": { "type": "string", "minLength": 1 },
        "irreversible_operations": { "type": "array", "items": { "type": "string" }, "default": [] }
      }
    }
  }
}
```

### Automatic Natural Language Inference & Safety Rules

If no raw JSON payload is provided, apply these defaults and safety checks:

- **`migration_spec.kind`**: Inferred from prompt keywords: column/table
  changes map to `schema`; endpoint or payload versioning maps to `api`;
  environment or flag changes map to `config`; engine or bucket moves map to
  `storage`; serialization or schema-file changes map to `file_format`.
- **`source_state` / `target_state`**: Extracted verbatim from the prompt
  (e.g. `users.full_name` to `users.first_name + users.last_name`). If either
  state is ambiguous, stop and ask before planning.
- **`producers` / `consumers`**: Discovered from the repository by searching
  for references to the affected artifact (table, endpoint, key, or format
  module). Never assume an empty consumer list; record the search evidence.
- **`version_overlap`**: Defaults to `rolling_deploy` when the project deploys
  services independently; use `long_lived_clients` when mobile or external
  clients pin old versions; `none` only for single-artifact atomic deploys.
- **`rollout_context.stages`**: Defaults to the full expand-migrate-contract
  chain: `preflight`, `expand`, `dual_write`, `backfill`, `dual_read`,
  `cutover`, `contract`, `cleanup`.
- **`cutover_criterion`**: Defaults to zero reconciliation mismatches over a
  defined observation window. The criterion must be measurable; reject vague
  criteria such as "looks fine".
- **`rollback_path`**: Must be derivable for every stage. If no rollback path
  can be constructed for a stage, mark it irreversible and stop for approval.
- **Irreversibility detection**: Treat `DROP`, `DELETE`, destructive rewrites,
  format overwrites without backups, and API removals without deprecation as
  irreversible. **Never execute irreversible operations without explicit
  user approval recorded in the plan.**

---

## 2. Deterministic State Machine Execution Flow

Follow this exact sequential protocol. Do not skip steps or alter execution
ordering.

### Step 1: Context Ingestion & Compatibility Inventory

1. Read `AGENTS.md`, the feature brief, existing migration tooling, and any
   prior plan in `templates/handoffs/data-migration-plan.md` format.
2. Inventory producers, consumers, data stores, configuration keys, deployment
   order, and version boundaries for the affected artifact.
3. Classify every consumer by update latency: deploys with the server,
  rolls independently, or is long-lived and pinned (mobile, external API
   clients, partner integrations).
4. Record the inventory as evidence; a migration planned against an assumed
   (unverified) consumer list is not safe.

### Step 2: Target State & Cutover Criterion Definition

1. Write down the source state and the target state precisely enough that a
   reviewer can diff them (schema DDL, endpoint contract, config key set, or
   format specification).
2. Define the compatibility contract that must hold during overlap: which
   versions read which representation, and which writes are dual-emitted.
3. Define preflight checks (environment, permissions, disk, replication lag,
   backup presence) and a **measurable cutover criterion** (e.g. mismatch
   rate below threshold for a sustained window, consumer error rate flat).

### Step 3: Stage Decomposition (Expand-Migrate-Contract)

1. Prefer staged expand-migrate-contract changes over big-bang rewrites:
   - **Expand**: add the new column, field, key, or format reader alongside
     the old one; nothing is removed.
   - **Migrate**: dual-write new writes, backfill existing rows or traffic,
     and dual-read with comparison where feasible.
   - **Contract**: remove legacy behavior only after the criterion in Step 2
     is met and recorded.
2. If a change cannot be decomposed (rare), document why, shrink its blast
   radius, and treat the whole change as one gated irreversible stage.

### Step 4: Rollback Path Design & Irreversibility Gates

1. Define a tested rollback path **before** destructive or irreversible
   steps: restore procedure, reverse migration, flag flip, or traffic shift.
2. Rehearse rollback on a copy or staging environment; an untested rollback
   plan is a hypothesis, not a control.
3. **Stop and request approval for irreversible operations.** Present the
   operation, the blast radius, the backup evidence, and the restore drill
   result before proceeding.

### Step 5: Smallest Verifiable Stage Implementation

1. Implement the smallest stage that can be verified safely on its own.
2. Protect existing data: never rewrite in place what can be copied, never
   drop what can be renamed, and never couple data movement to unrelated
   refactors.
3. Avoid mixing unrelated changes into the migration; each stage diff should
   be reviewable in isolation.

### Step 6: Preflight Checks & Stage Execution

1. Run the preflight checklist from Step 2 and record results before
   touching data or traffic.
2. Execute exactly one stage per rollout window; observe health signals
   (error rate, latency, lag, consumer complaints) before advancing.
3. If any signal regresses beyond its threshold, halt the rollout and follow
   the rollback path for the current stage.

### Step 7: Reconciliation, Evidence Capture & Cutover Decision

1. Run reconciliation queries and invariant checks comparing old and new
   representations (row counts, sampled field comparisons, checksums).
2. Run consumer smoke checks against the new path for every consumer class
   inventoried in Step 1.
3. Evaluate the cutover criterion with the recorded evidence. Advance only
   when the criterion is met; otherwise extend observation or roll back.

### Step 8: Contract, Cleanup & Rollout Report

1. After cutover stabilizes, schedule the contract stage (drop legacy
   column, remove old endpoint, delete fallback reader) as its own gated
   change with its own rollback note.
2. Report rollout state, checks, metrics or evidence, rollback readiness,
   and remaining cleanup work in the data-migration-plan handoff.

---

## 3. Reference Implementation: Expand-Migrate-Contract Plan Document

```yaml
# Data migration plan: split users.full_name into first_name / last_name.
# Artifact format follows templates/handoffs/data-migration-plan.md.
migration:
  id: MIG-2026-014-split-users-full-name
  kind: schema
  source_state: users.full_name TEXT NOT NULL (single column, all writers)
  target_state: users.first_name TEXT NOT NULL, users.last_name TEXT NOT NULL
  data_at_risk: true
  owner: <migration-owner>

compatibility:
  producers: [api-server (POST /users, PATCH /users/:id), admin-import-job]
  consumers: [api-server (GET /users/:id), billing-sync-worker, email-service]
  version_overlap: rolling_deploy        # old and new app versions coexist
  breaking_change: false                 # expand-migrate-contract keeps compat
  overlap_contract: |
    During overlap, writers dual-write full_name and (first_name, last_name).
    Readers keep reading full_name until cutover; after backfill verifies,
    a flag switches reads to the split columns. Old app versions remain
    functional at every stage.

preflight_checks:
  - id: PF-1
    check: Verified backup of the users table younger than 1 hour exists.
  - id: PF-2
    check: Replication lag < 5s on all read replicas.
  - id: PF-3
    check: Deploy pipeline can roll back api-server within 10 minutes.
  - id: PF-4
    check: No open schema-change locks on users (pg_stat_activity clean).

stages:
  - name: expand
    change: ALTER TABLE users ADD COLUMN first_name TEXT, ADD COLUMN last_name TEXT;
    rollback: ALTER TABLE users DROP COLUMN first_name, DROP COLUMN last_name;
    verify: Columns exist, nullable, zero writes broken (deploy canary passes).

  - name: dual_write
    change: Deploy writers emitting full_name plus split columns (derived by
            the same normalization function used by the backfill).
    rollback: Flag off dual-write; full_name remains authoritative.
    verify: 100% of new writes populate split columns; write error rate flat.

  - name: backfill
    change: Batched backfill of historical rows (500 rows/batch, throttled,
            resumable by primary-key cursor, idempotent on re-run).
    rollback: Stop backfill job; already-written values are additive only.
    verify: Reconciliation (Section 4) shows zero mismatches on full scan.

  - name: dual_read
    change: Readers compare full_name vs concat(first_name, last_name) and
            log mismatches; reads still served from full_name.
    rollback: Disable comparison logging.
    verify: mismatch_rate == 0 over a 7-day observation window.

  - name: cutover
    change: Flag readers to serve from first_name/last_name.
    criterion: mismatch_rate == 0 for 7 days AND consumer smoke checks pass
               for api-server, billing-sync-worker, and email-service.
    rollback: Flag back to full_name reads (instant, no data movement).

  - name: contract
    change: Stop writing full_name; rename to full_name_deprecated.
    rollback: Re-enable full_name writes from split columns (reverse sync).
    approval: REQUIRED - first step that can strand long-lived readers.

  - name: cleanup
    change: DROP COLUMN full_name_deprecated after 30-day quiet period.
    rollback: Restore from backup drill (PF-1); rehearsed on staging copy.
    approval: REQUIRED - irreversible.

rollback_runbook:
  trigger: error rate +0.5% for 5 min, mismatch_rate > 0, or consumer alert.
  steps:
    - Halt rollout; freeze further deploys touching users.
    - Execute the rollback listed for the current stage (flag first).
    - Verify rollback: reconciliation queries return to baseline.
    - Record timeline, evidence, and decision in the handoff artifact.
```

---

## 4. Reconciliation & Evidence Verification Pattern

```bash
# Reconciliation queries for the users name-split migration.
# Run after backfill, during dual_read, and before cutover. Log all output.

# 1. Row-count parity: total rows vs rows with split columns populated.
psql "$DATABASE_URL" -c "
  SELECT
    COUNT(*) AS total_rows,
    COUNT(first_name) AS rows_with_first,
    COUNT(*) - COUNT(first_name) AS missing_split
  FROM users;"

# 2. Invariant check: split columns must reconstruct full_name exactly.
#    Any row returned here is a mismatch that blocks cutover.
psql "$DATABASE_URL" -c "
  SELECT id, full_name, first_name, last_name
  FROM users
  WHERE full_name IS DISTINCT FROM
        NULLIF(TRIM(BOTH ' ' FROM concat_ws(' ', first_name, last_name)), '')
  LIMIT 100;"

# 3. Mismatch rate over a sampled window (run hourly during dual_read).
psql "$DATABASE_URL" -c "
  SELECT
    COUNT(*) FILTER (
      WHERE full_name IS DISTINCT FROM
        NULLIF(TRIM(BOTH ' ' FROM concat_ws(' ', first_name, last_name)), '')
    )::float / NULLIF(COUNT(*), 0) AS mismatch_rate
  FROM users TABLESAMPLE SYSTEM (1);"

# 4. Consumer smoke checks: one representative call per consumer class.
curl -fsS -H "Authorization: Bearer <service-token>" \
  "https://api.example.internal/users/<known-user-id>" | jq '.firstName, .lastName'

# 5. Evidence log entry (append one JSON line per check execution).
printf '%s\n' '{"migration":"MIG-2026-014","stage":"backfill","check":"row_count_parity","total":184203,"missing_split":0,"result":"pass","at":"2026-08-14T09:30:00Z"}' \
  >> migration-evidence.log
```

Each evidence line records the migration id, stage, check name, measured
values, pass/fail result, and timestamp so the cutover decision in Step 7 is
auditable without rerunning queries.

---

## 5. Zero-Downtime, Data-Loss & Cutover Invariants

For zero downtime, every deployed writer version must emit data readable by
every deployed reader version at all times during the overlap window:

$$\forall t \in [t_{\text{expand}}, t_{\text{contract}}]: \quad \text{writes}(V(t)) \subseteq \bigcap_{r \in \text{readers}(t)} \text{readableBy}(r)$$

Data-loss tolerance is zero; every irreversible stage $s$ requires a tested
rollback and an approved backup before execution:

$$P(\text{unrecoverable data loss}) = 0 \;\Rightarrow\; \forall s \in S_{\text{irreversible}}: \; \text{testedRollback}(s) \wedge \text{verifiedBackup}(s) \wedge \text{approved}(s)$$

The cutover criterion requires the mismatch rate to stay below tolerance
$\epsilon$ (default $0$) for the full observation window $W$:

$$\text{mismatchRate}(t) = \frac{\#\{r : \text{oldRepr}(r) \neq \text{newRepr}(r)\}}{\#\{r\}} < \epsilon \quad \forall t \in W, \; |W| \ge W_{\min}$$

Rollback must complete within the recovery time objective, measured from
trigger detection to restored baseline:

$$T_{\text{rollback}} = t_{\text{baseline-restored}} - t_{\text{trigger}} \le T_{\text{RTO}}$$

---

## 6. Guardrails

### Operational Restrictions

- **Smallest Verifiable Stage**: Implement the smallest stage that can be
  verified safely; never bundle multiple rollout stages into one deploy.
- **No Mixed Concerns**: Avoid mixing unrelated changes into the migration;
  refactors, feature work, and dependency upgrades ship separately.
- **Tested Rollback Before Irreversible Steps**: Define and rehearse the
  rollback path before any destructive or irreversible operation; an
  untested rollback does not satisfy the gate.
- **Approval Gate for Irreversible Operations**: Stop and request explicit
  user approval for `DROP`, destructive deletes, format overwrites without
  backups, and API removals without a deprecation period.
- **Protect Existing Data**: Prefer additive changes (new columns, new keys,
  new format versions) over in-place rewrites; rename before dropping.
- **Single-Agent Executable**: An optional migration-reviewer subagent can
  double-check the plan, but one agent must be able to perform this workflow
  end to end.

### Security Invariants

- **Credential Hygiene**: Never place real credentials, connection strings,
  or tokens in plans, evidence logs, or handoff artifacts; use
  `<placeholder>` references to the project's secret store.
- **Access Scoping**: Run migration stages with the least-privileged
  database role that can perform the stage; never use a superuser role for
  routine backfills.
- **Data Exposure**: Reconciliation output and evidence logs must not dump
  sensitive column values at scale; sample and redact where the migrated
  data is regulated (PII, payment, health).
- **Audit Trail**: Every stage execution, approval, and rollback is recorded
  with actor, timestamp, and evidence reference.

---

## 7. Atomic Failure Recovery & Rollback Handler

Before creating or modifying files, capture a baseline list of modified and
untracked files. If a stage verification fails and cannot be resolved within
2 iterations, halt the rollout and execute targeted rollback restricted ONLY
to files created or modified during this run, then apply the stage rollback
defined in the plan:

```bash
# 1. Execute the plan-defined data/traffic rollback for the current stage
#    (flag flips first; never skip ahead to destructive restores).
case "${CURRENT_STAGE:-}" in
  dual_write|dual_read|cutover) ./scripts/set-flag reads_from=legacy ;;
  expand)                       psql "$DATABASE_URL" -f rollback/expand_down.sql ;;
  *)                            echo "manual rollback required for ${CURRENT_STAGE}" ;;
esac

# 2. Revert ONLY modified files tracked during this execution run
if [ -n "${MODIFIED_FILES:-}" ]; then
  git checkout -- ${MODIFIED_FILES} 2>/dev/null
fi

# 3. Remove ONLY newly created untracked files from this execution run
if [ -n "${CREATED_FILES:-}" ]; then
  rm -rf ${CREATED_FILES} 2>/dev/null
fi

# 4. Re-run reconciliation to confirm baseline is restored, then record
#    the failure, the evidence, and the rollback outcome in the handoff.
```

After executing targeted rollback, output the exact error trace, the stage
that failed, the reconciliation result after rollback, and the failure cause.
Never roll back migration stages that were not executed by this run.

---

## 8. Verification Plan & Migration Toolchain Commands

Execute the following commands using project-local runners; adapt to the
project's declared migration and deployment tooling:

```bash
# 1. Validate the migration plan and pending migrations
python scripts/validate_handoff.py templates/handoffs/data-migration-plan.md
npx --no-install knex migrate:list        # or: alembic history, flyway info

# 2. Dry-run pending migrations against a staging copy (never prod first)
psql "$STAGING_DATABASE_URL" -f migrations/2026_014_expand_users_name.sql

# 3. Run the project's type check, lint, and test suite
npm run lint && npm run test

# 4. Run reconciliation checks and capture evidence (Section 4)
./scripts/reconcile.sh MIG-2026-014 backfill >> migration-evidence.log

# 5. Confirm rollback readiness: flag path and restore drill timestamp
./scripts/set-flag --dry-run reads_from=legacy
psql "$STAGING_DATABASE_URL" -c "SELECT now() - MAX(completed_at) < interval '24 hours' AS restore_drill_recent FROM restore_drills;"
```

---

## 9. Completion Report

Report the migration id and kind; the inventoried producers and consumers
with discovery evidence; the stage decomposition actually executed; preflight
check results; reconciliation outputs (row counts, mismatch rates, sampled
comparisons); the measured cutover decision against its criterion; rollback
readiness (flag path, backup age, restore drill date); approvals obtained for
irreversible operations; remaining contract/cleanup work with scheduled
dates; and any unverified risks or follow-up work handed to the team.
