---
name: database-design
description: Design safe PostgreSQL schemas and staged migrations.
---

# Database Design

Design data models, database-enforced invariants, and compatible staged
migrations before implementation. **PostgreSQL** is the default target engine;
inspect the repository and respect the project's current database, ORM,
migration tool, and operational constraints (connection limits, replication
topology, deploy cadence) before proposing anything.

The skill is **design and verification focused**: it produces a reviewed schema
proposal and a staged migration plan captured in
`templates/handoffs/data-migration-plan.md` (or the project's equivalent), plus
the validation queries that prove correctness. It never executes production
migrations.

---

## 1. Required I/O Context Schemas & Natural Language Auto-Inference

The skill supports **two invocation modes**:

1. **Orchestrator / Technical Mode (JSON Manifest)**: Pass the JSON context
   manifest below.
2. **Non-Technical Mode (Plain English Prompts)**: If the user provides a
   natural language prompt (e.g. *"Design the tables for per-team API keys
   with usage tracking and a safe rollout from the existing tokens table"*),
   the agent **must automatically infer and populate** `entity_spec`,
   `access_pattern_context`, and `migration_context` from the user's text and
   the existing repository schema.

### JSON Context Manifest Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "DatabaseDesignContextManifest",
  "type": "object",
  "required": ["entity_spec", "migration_context"],
  "properties": {
    "entity_spec": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "required": ["entity_name", "primary_key"],
        "properties": {
          "entity_name": { "type": "string", "pattern": "^[a-z][a-z0-9_]*$" },
          "primary_key": { "type": "string" },
          "ownership_scope": { "type": "string", "enum": ["user", "team", "tenant", "global"] },
          "estimated_rows": { "type": "integer", "minimum": 0 },
          "contains_pii": { "type": "boolean", "default": false },
          "retention_policy": { "type": "string" },
          "relationships": {
            "type": "array",
            "items": {
              "type": "object",
              "required": ["target_entity", "cardinality"],
              "properties": {
                "target_entity": { "type": "string" },
                "cardinality": { "type": "string", "enum": ["one_to_one", "one_to_many", "many_to_many"] },
                "on_delete": { "type": "string", "enum": ["restrict", "cascade", "set_null", "no_action"], "default": "restrict" }
              }
            }
          }
        }
      }
    },
    "access_pattern_context": {
      "type": "object",
      "required": ["query_patterns"],
      "properties": {
        "query_patterns": {
          "type": "array",
          "minItems": 1,
          "items": {
            "type": "object",
            "required": ["description", "frequency"],
            "properties": {
              "description": { "type": "string" },
              "frequency": { "type": "string", "enum": ["per_request", "periodic", "rare"] },
              "predicates": { "type": "array", "items": { "type": "string" } },
              "ordering": { "type": "string" },
              "expected_selectivity": { "type": "string", "enum": ["high", "medium", "low"] }
            }
          }
        },
        "read_write_ratio": { "type": "string", "pattern": "^[0-9]+:[0-9]+$" }
      }
    },
    "migration_context": {
      "type": "object",
      "required": ["migration_kind", "stages"],
      "properties": {
        "migration_kind": { "type": "string", "enum": ["greenfield", "expand_contract", "backfill_only", "index_only"] },
        "stages": {
          "type": "array",
          "items": { "type": "string", "enum": ["preflight", "expand", "backfill", "dual_write", "dual_read", "cutover", "contract", "verify", "rollback"] },
          "minItems": 2
        },
        "backfill_batch_size": { "type": "integer", "minimum": 100, "maximum": 100000, "default": 5000 },
        "lock_timeout_budget_ms": { "type": "integer", "minimum": 100, "maximum": 60000, "default": 3000 },
        "zero_downtime_required": { "type": "boolean", "default": true }
      }
    }
  }
}
```

### Automatic Natural Language Inference Rules

If no raw JSON payload is provided, apply these defaults and safety checks:

- **`entity_spec`**: Extract entities from the prompt nouns and the existing
  schema (inspect the migrations directory and ORM models). Table names follow
  the project's existing snake_case pluralization convention.
- **`access_pattern_context.query_patterns`**: Derived from the API contract's
  operations and existing query call sites. Every listed operation that reads
  data must map to at least one query pattern; unknown selectivity defaults to
  `medium` and is flagged as an assumption.
- **`migration_context.migration_kind`**: `greenfield` when no overlapping
  table exists; `expand_contract` when an existing table or column changes
  while old application versions may still run.
- **`migration_context.stages`**: Defaults to the full
  `["preflight", "expand", "backfill", "dual_write", "cutover", "contract",
  "verify", "rollback"]` chain for `expand_contract`; the dual stages are
  omitted only for purely additive greenfield work.
- **Safety validation**: If the prompt requests a destructive operation (drop,
  truncate, or a column rewrite on a large table) without staged rollout
  language, default `zero_downtime_required` to `true` and surface the
  conflict as an explicit open risk instead of complying silently.

---

## 2. Deterministic State Machine Execution Flow

Follow this exact sequential protocol. Do not skip steps or alter execution
ordering.

### Step 1: Context Ingestion & Uncertainty Declaration

1. Read `AGENTS.md`, the feature brief, the API contract, the existing
   schema, and the query paths that will touch the new or changed tables.
2. Inspect the migration history and ORM models to learn the naming, type,
   and index conventions already in use.
3. State uncertainties about cardinality, retention, ownership, privacy, and
   expected access patterns before designing; record each as an assumption or
   open question in the plan.

### Step 2: Entity & Invariant Modeling

1. Model entities, keys, constraints, relationships, lifecycle fields
   (`created_at`, `updated_at`, soft-delete markers), and ownership
   boundaries.
2. Prefer database-enforced invariants for critical integrity: primary keys,
   foreign keys with deliberate `ON DELETE` behavior, `NOT NULL`, `CHECK`
   constraints, and uniqueness constraints over application-only enforcement.
3. Mark every PII-bearing column explicitly and tie it to a retention and
   deletion policy in the plan.

### Step 3: Index Selection from Real Access Paths

1. Choose indexes from real query predicates, ordering requirements, join
   paths, and expected volume — never speculatively.
2. Explain each index in the plan: which query pattern it serves, its column
   order rationale, and its estimated write-amplification cost.
3. Prefer partial or covering indexes where they shrink index size; reject
   redundant indexes already implied by existing constraints.

### Step 4: Staged Migration Plan Construction

1. Produce the staged plan: preflight, expand, backfill, dual-read or
   dual-write if needed, cutover, contract, verification, and rollback.
2. The **expand** stage adds new structures compatibly: nullable columns or
   columns with safe defaults, new tables, and `CREATE INDEX CONCURRENTLY`.
3. The **backfill** stage copies or derives data in bounded batches keyed by
   primary key ranges, never in one monolithic transaction.
4. The **cutover** stage flips reads and writes to the new structure only
   after reconciliation passes; the **contract** stage removes legacy
   structures only after the old application version is fully retired.
5. Use the `safe-migration` skill when it provides deeper guidance for the
   rollout mechanics.

### Step 5: Operational Risk Assessment

1. Assess lock duration per statement against the lock-timeout budget,
   transaction size, backfill batching, replication lag, and deploy ordering
   relative to application releases.
2. Classify every statement by lock mode and confirm no `ACCESS EXCLUSIVE`
   statement holds longer than the budget on a hot table.
3. Verify every stage is independently reversible and that the rollback path
   is written down before any stage executes.

### Step 6: Validation & Reconciliation Query Definition

1. Define data validation and reconciliation queries — counts, checksums,
   null-fraction checks, orphan detection, and invariant checks — **before**
   any production action.
2. Pair every backfill with a reconciliation query whose acceptance threshold
   is stated numerically (exact match or an explicitly bounded delta).

### Step 7: Contract & Brief Alignment

1. Keep the API contract and feature brief aligned with nullability,
   defaults, uniqueness, deletion behavior, and error behavior implied by the
   schema.
2. Flag any schema decision that forces a contract change (e.g. a newly
   required field) back to the `api-design` output before proceeding.

### Step 8: Plan Handoff Assembly

1. Capture the proposal in `templates/handoffs/data-migration-plan.md` or the
   project's equivalent, including assumptions, stage ordering, exact
   verification evidence requirements, and rollback instructions.
2. Cross-check that every entity, index, and stage traces to a stated
   requirement or access pattern.

---

## 3. Reference Implementation: PostgreSQL DDL & Staged Migration Sketch

The following demonstrates the expected depth: core DDL with per-decision
rationale comments, followed by a staged expand/backfill sketch with bounded
batches and lock-timeout discipline.

```sql
-- ============================================================
-- Stage: EXPAND — additive, zero-downtime compatible.
-- Rationale comments explain each decision for reviewers.
-- ============================================================

-- api_keys: one row per issued key. Ownership is team-scoped so that
-- authorization queries filter on team_id without an extra join.
CREATE TABLE api_keys (
    id              uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id         uuid        NOT NULL REFERENCES teams(id) ON DELETE RESTRICT,
    -- ON DELETE RESTRICT: deleting a team with live keys must fail loudly,
    -- not silently orphan or cascade-revoke credentials.
    name            text        NOT NULL CHECK (char_length(name) BETWEEN 1 AND 120),
    key_prefix      text        NOT NULL CHECK (char_length(key_prefix) = 8),
    -- Store only prefix + hash; the raw secret is never persisted.
    key_hash        bytea       NOT NULL,
    status          text        NOT NULL DEFAULT 'active'
                    CHECK (status IN ('active', 'revoked', 'expired')),
    created_at      timestamptz NOT NULL DEFAULT now(),
    revoked_at      timestamptz,
    -- Lifecycle CHECK pairs the status with its timestamp.
    CHECK ((status = 'revoked') = (revoked_at IS NOT NULL)),
    -- Uniqueness on prefix supports fast lookup at authentication time.
    CONSTRAINT api_keys_prefix_unique UNIQUE (key_prefix)
);

-- Serves query pattern "list active keys for a team" (per_request,
-- high selectivity on team_id). Column order matches equality-then-sort.
CREATE INDEX CONCURRENTLY api_keys_team_active_idx
    ON api_keys (team_id, created_at DESC)
    WHERE status = 'active';

-- api_key_usage: append-only usage events, partitioned by month so that
-- retention drops whole partitions instead of running mass DELETEs.
CREATE TABLE api_key_usage (
    api_key_id    uuid        NOT NULL REFERENCES api_keys(id) ON DELETE CASCADE,
    recorded_at   timestamptz NOT NULL,
    request_count integer     NOT NULL CHECK (request_count >= 0),
    PRIMARY KEY (api_key_id, recorded_at)
) PARTITION BY RANGE (recorded_at);

CREATE TABLE api_key_usage_2026_08 PARTITION OF api_key_usage
    FOR VALUES FROM ('2026-08-01') TO ('2026-09-01');

-- ============================================================
-- Stage: BACKFILL — bounded batches, lock-timeout discipline.
-- legacy_tokens -> api_keys, advanced by primary-key ranges only.
-- ============================================================
SET lock_timeout = '3s';
SET statement_timeout = '30s';

WITH batch AS (
    SELECT id, team_id, left(key_material, 8) AS key_prefix,
           digest(key_material, 'sha256') AS key_hash
    FROM legacy_tokens
    WHERE id > $1               -- last processed key from the prior batch
    ORDER BY id
    LIMIT 5000                  -- bounded batch: fits lock and lag budgets
)
INSERT INTO api_keys (id, team_id, key_prefix, key_hash, status, created_at)
SELECT id, team_id, key_prefix, key_hash, 'active', now()
FROM batch
ON CONFLICT (id) DO NOTHING;    -- idempotent: safe to re-run the same batch

-- Stage: CONTRACT (only after cutover verifies and old app versions retire)
-- DROP TABLE legacy_tokens;  -- requires explicit operator authorization
```

---

## 4. Validation & Reconciliation Query Pattern

Every backfill and cutover ships with executable reconciliation queries whose
acceptance thresholds are numeric and stated in the plan.

```sql
-- 1. Row-count reconciliation: source vs target must match exactly.
SELECT
    (SELECT count(*) FROM legacy_tokens WHERE status = 'active') AS source_rows,
    (SELECT count(*) FROM api_keys)                              AS target_rows;
-- Acceptance: source_rows = target_rows

-- 2. Invariant check: no active key may lack a hash or violate prefix length.
SELECT count(*) AS invariant_violations
FROM api_keys
WHERE status = 'active'
  AND (key_hash IS NULL OR char_length(key_prefix) <> 8);
-- Acceptance: invariant_violations = 0

-- 3. Orphan detection: every usage row must reference a live key row.
SELECT count(*) AS orphan_usage_rows
FROM api_key_usage u
LEFT JOIN api_keys k ON k.id = u.api_key_id
WHERE k.id IS NULL;
-- Acceptance: orphan_usage_rows = 0

-- 4. Sampled value equivalence: a 1% random sample must hash-match source.
SELECT count(*) AS mismatches
FROM (
    SELECT t.id, t.key_material
    FROM legacy_tokens t TABLESAMPLE SYSTEM (1)
) s
JOIN api_keys k ON k.id = s.id
WHERE k.key_hash <> digest(s.key_material, 'sha256');
-- Acceptance: mismatches = 0

-- 5. Replication lag guard before cutover (run on the primary).
SELECT client_addr,
       pg_wal_lsn_diff(pg_current_wal_lsn(), replay_lsn) AS lag_bytes
FROM pg_stat_replication;
-- Acceptance: lag_bytes < 16 MiB for every replica before cutover proceeds
```

---

## 5. Lock, Backfill & Compatibility Invariants

$$t_{\text{lock}}(s) \le B_{\text{lock}} = 3000\text{ms} \quad \forall\, \text{statement } s \in \text{migration}$$

$$|B_{\text{batch}}| \le \min\!\left(5000\ \text{rows},\ \frac{B_{\text{txn}}}{w_{\text{row}}}\right), \qquad t_{\text{batch}} \le 30\text{s}$$

$$\text{lag}_{\text{replica}} = \mathrm{pg\_wal\_lsn\_diff}(\text{primary}_{lsn}, \text{replay}_{lsn}) < 16\ \text{MiB at cutover}$$

$$\forall\, t \in [\text{expand}, \text{contract}): \quad \text{AppVersion}_{old}(\text{schema}_t)\ \text{remains operable (backward compatible)}$$

$$\text{reconciled} \iff \bigl|\,\text{count}(\text{source}) - \text{count}(\text{target})\,\bigr| = 0 \ \wedge\ \text{invariantViolations} = 0$$

---

## 6. Guardrails

### Operational Restrictions

- **Design and Verify Only**: This skill designs and verifies migrations; it
  **never runs a production migration or destructive data operation** without
  explicit authorization from the operator.
- **Staged Backward Compatibility**: Preserve backward compatibility through
  staged changes whenever multiple versions of an application may run
  concurrently against the same database; never expand and contract in the
  same release.
- **No Speculative Indexes**: Every index must trace to a real, stated query
  pattern; speculative "just in case" indexes are rejected.
- **Single-Agent Executable**: A migration-planner subagent may independently
  inspect the design, but it is optional and this workflow remains usable by
  one agent end to end.

### Security Invariants

- **No Secret Material at Rest**: Never design storage for raw credentials;
  store hashes, prefixes, or references into the project's secret manager
  instead.
- **PII Explicitness**: Every PII column must be marked in the plan with a
  retention and deletion policy; undocumented PII storage is a design defect.
- **Least-Privilege Migration Role**: Migration statements assume a role with
  DDL rights only on the target schema, never superuser-by-default.
- **Destructive Operation Gate**: `DROP`, `TRUNCATE`, and column rewrites on
  populated tables appear in the plan only behind an explicit authorization
  checkpoint with a rehearsed rollback path.

---

## 7. Atomic Failure Recovery & Rollback Handler

Before creating or modifying files, capture a baseline list of modified and
untracked files. If any verification command in Section 8 fails and cannot be
resolved within 2 iterations, execute targeted rollback restricted ONLY to
files created or modified during this run:

```bash
# Revert ONLY modified files tracked during this execution run
if [ -n "${MODIFIED_FILES:-}" ]; then
  git checkout -- ${MODIFIED_FILES} 2>/dev/null
fi

# Remove ONLY newly created untracked files from this execution run
if [ -n "${CREATED_FILES:-}" ]; then
  rm -rf ${CREATED_FILES} 2>/dev/null
fi
```

After executing targeted rollback, output the exact error trace and state
failure causes. Never roll back migration files that were not created by this
run, and never execute database-level rollback SQL without explicit
authorization.

---

## 8. Verification Plan & PostgreSQL Toolchain Commands

Execute the following commands using project-local runners; adapt to the
project's declared migration and database tooling:

```bash
# 1. Lint/validate migration files with the project's migration tool
npx --no-install drizzle-kit check        # or: alembic check / atlas lint

# 2. Dry-run each stage against a scratch database, failing on any error
psql "$SCRATCH_DATABASE_URL" -v ON_ERROR_STOP=1 -f migrations/<stage>.sql

# 3. Execute reconciliation queries and assert zero-delta acceptance
psql "$SCRATCH_DATABASE_URL" -v ON_ERROR_STOP=1 -f checks/reconcile.sql

# 4. Run the project's test suite (schema-dependent integration tests)
npm run test
```

---

## 9. Completion Report

The final report must contain: the proposed schema with per-table and
per-index rationale, the database-enforced invariants, the access-path
analysis tying each index to a query pattern, the full staged rollout and
rollback plan with lock and batch budgets, the validation and reconciliation
queries with their numeric acceptance thresholds, dependencies on application
deploys or contract changes, and every open risk and uncertainty that the
operator must resolve before authorizing execution.
