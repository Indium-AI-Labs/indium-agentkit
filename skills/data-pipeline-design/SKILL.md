---
name: data-pipeline-design
description: "Design safe ETL/ELT pipelines, data warehouse schemas, partition strategies, idempotency controls, and data quality assertions before implementation."
---

# Data Pipeline Design

Design scalable, idempotent data transformation pipelines and warehouse data
models before implementation. PostgreSQL, BigQuery, Snowflake, and DuckDB are
the supported warehouse patterns, with dbt, SQL, Spark, or Python as the
transformation layer; inspect the repository and follow the consumer project's
established data warehouse stack, orchestrator, and transformation framework
before designing anything.

The skill is **design-first**: the output is a pipeline specification covering
target schemas, partitioning, transformation logic, idempotency controls,
quality assertions, and governance controls, captured in the project's agreed
architecture handoff. It does not execute production pipelines.

---

## 1. Required I/O Context Schemas & Natural Language Auto-Inference

The skill supports **two invocation modes**:

1. **Orchestrator / Technical Mode (JSON Manifest)**: Pass the JSON context
   manifest below.
2. **Non-Technical Mode (Plain English Prompts)**: If the user provides a
   natural language prompt (e.g. *"Design a daily pipeline that loads payment
   charges into a finance fact table with dedup and freshness checks"*), the
   agent **must automatically infer and populate** `source_spec`,
   `target_model_context`, `orchestration_context`, and `quality_context`
   from the user's text and the existing repository conventions.

### JSON Context Manifest Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "DataPipelineDesignContextManifest",
  "type": "object",
  "required": ["source_spec", "target_model_context", "quality_context"],
  "properties": {
    "source_spec": {
      "type": "object",
      "required": ["source_system", "ingest_mode"],
      "properties": {
        "source_system": { "type": "string" },
        "ingest_mode": { "type": "string", "enum": ["full_refresh", "incremental_watermark", "cdc", "append_only"] },
        "watermark_column": { "type": "string" },
        "estimated_daily_rows": { "type": "integer", "minimum": 0 },
        "contains_pii": { "type": "boolean", "default": false },
        "source_latency_sla_minutes": { "type": "integer", "minimum": 1 }
      }
    },
    "target_model_context": {
      "type": "object",
      "required": ["modeling_style", "warehouse_engine"],
      "properties": {
        "modeling_style": { "type": "string", "enum": ["star", "snowflake", "one_big_table"] },
        "warehouse_engine": { "type": "string", "enum": ["postgresql", "bigquery", "snowflake", "duckdb"] },
        "partition_key": { "type": "string" },
        "clustering_fields": { "type": "array", "items": { "type": "string" }, "maxItems": 4 },
        "grain": { "type": "string" }
      }
    },
    "orchestration_context": {
      "type": "object",
      "required": ["orchestrator", "schedule"],
      "properties": {
        "orchestrator": { "type": "string", "enum": ["airflow", "dagster", "dbt_cloud", "cron", "other"] },
        "schedule": { "type": "string" },
        "freshness_sla_minutes": { "type": "integer", "minimum": 1 },
        "max_bytes_scanned_per_run": { "type": "integer", "minimum": 0 }
      }
    },
    "quality_context": {
      "type": "object",
      "required": ["assertions"],
      "properties": {
        "assertions": {
          "type": "array",
          "minItems": 1,
          "items": { "type": "string", "enum": ["not_null", "unique", "referential_integrity", "accepted_values", "row_count_threshold", "freshness", "custom_sql"] }
        },
        "failure_policy": { "type": "string", "enum": ["block_publish", "warn_and_publish"], "default": "block_publish" },
        "min_coverage_ratio": { "type": "number", "minimum": 0, "maximum": 1, "default": 0.8 }
      }
    }
  }
}
```

### Automatic Natural Language Inference Rules

If no raw JSON payload is provided, apply these defaults and safety checks:

- **`source_spec`**: The source system is extracted from the prompt (e.g.
  "payment charges"). `ingest_mode` defaults to `incremental_watermark` when a
  monotonic timestamp exists in the source, otherwise `append_only` with a
  deduplication window.
- **`target_model_context`**: `modeling_style` defaults to `star` for
  analytics workloads with clear fact/dimension separation, and to
  `one_big_table` for single-entity reporting. `warehouse_engine`, partition
  key, and clustering fields are detected from existing dbt project files and
  warehouse DDL in the repository.
- **`orchestration_context`**: Detected from existing orchestrator config
  (`airflow/`, `dagster.yaml`, `dbt_project.yml`). `freshness_sla_minutes`
  defaults to 1.5x the schedule interval when not stated explicitly.
- **`quality_context.assertions`**: Defaults to `not_null` and `unique` on the
  declared grain, plus `freshness` on the partition key; PII sources add
  masking-verification checks.
- **Safety validation**: If the prompt implies PII movement without governance
  language, default `contains_pii` to `true` and require explicit masking
  decisions in the design; surface the conflict as an open risk rather than
  omitting governance silently.

---

## 2. Deterministic State Machine Execution Flow

Follow this exact sequential protocol. Do not skip steps or alter execution
ordering.

### Step 1: Context Ingestion & Constraint Declaration

1. Read `AGENTS.md`, the feature brief, the source schema, the target
   warehouse model, and the downstream query patterns.
2. State constraints regarding data volume, latency SLA, privacy, and
   retention before designing; record unknowns as assumptions or open
   questions in the handoff.

### Step 2: Target Schema Modeling

1. Model target tables using the appropriate dimensional schema (star,
   snowflake, or One Big Table) for the stated query patterns.
2. Define primary keys, foreign keys, partition keys, clustering fields, and
   data types; declare the grain of every fact table in one sentence.
3. Choose the partition key from actual filter predicates (usually the event
   date), and clustering fields from the highest-selectivity join or filter
   columns.

### Step 3: Extraction & Transformation Logic Design

1. Design extraction and transformation logic in the project's established
   framework (dbt, SQL, Spark, or Python).
2. Enforce idempotency so that pipeline re-runs produce identical results
   without duplicate rows: `MERGE` on stable keys, partition replacement, or
   delete-and-insert bounded to the reprocessed window.
3. Keep transformations deterministic: no unkeyed `INSERT ... SELECT` into
   shared targets, and no dependence on row arrival order.

### Step 4: Incremental Loading Strategy

1. Define the incremental loading strategy: watermark columns, change data
   capture, or append-only with a deduplication window.
2. Size the lookback/dedup window to cover late-arriving data without
   rescanning history; the goal is minimal compute cost and warehouse lock
   time per run.
3. Specify exactly how the watermark advances after success and how it is
   recovered after a failed run.

### Step 5: Data Quality Assertion Design

1. Establish data quality assertions — non-null, uniqueness, referential
   integrity, accepted values, and custom threshold checks — to run before
   and after transformation.
2. Wire assertions to a failure policy: `block_publish` assertions gate the
   load; `warn_and_publish` assertions page for review without stopping data.
3. Set a coverage target: every fact table's grain carries at least
   `not_null` and `unique` assertions, and every PII column carries a masking
   verification.

### Step 6: PII Governance & Access Control Design

1. Design PII handling: classification of every source column, masking or
   hashing at ingestion, column-level access controls in the warehouse, and
   data-deletion compliance hooks (subject-erasure propagation) in accordance
   with the project's data governance policies.
2. Ensure raw PII never lands in the curated layer unmasked; document the
   masking function and its key management story in the handoff.

### Step 7: Monitoring & Cost Observability Design

1. Plan pipeline monitoring: record counts, execution duration, byte scan
   volume, schema drift detection, and failure alert notifications.
2. Define the bytes-scanned budget per run and the alert threshold; tie cost
   observability to the orchestrator's metadata or the warehouse's query
   history.

### Step 8: Pipeline Specification Handoff

1. Record the pipeline specification, schema design, data quality checks,
   idempotency mechanism, governance controls, and operational risks in the
   agreed architecture handoff.
2. Cross-check that every target column traces to a source field or a
   documented derivation, and that every assertion traces to a stated quality
   or compliance requirement.

---

## 3. Reference Implementation: Idempotent dbt Model with Partition DDL

The following demonstrates the expected depth: an incremental dbt-style model
with watermark logic and an idempotent merge, plus the warehouse DDL for
partitioning and clustering.

```sql
-- models/facts/fct_charges.sql
-- Grain: one row per charge_id. Idempotent via MERGE on charge_id within
-- the reprocessed watermark window.
{{
  config(
    materialized = 'incremental',
    unique_key = 'charge_id',
    incremental_strategy = 'merge',
    partition_by = {'field': 'charge_date', 'data_type': 'date'},
    cluster_by = ['customer_id', 'status']
  )
}}

with source as (
    select
        charge_id,
        customer_id,
        cast(created_at as date)          as charge_date,
        amount_cents,
        currency,
        status,
        -- PII: email is hashed at ingestion; raw email never enters the
        -- curated layer. Key management lives in the secret manager.
        sha256(lower(trim(email)))        as customer_email_hash,
        created_at,
        updated_at
    from {{ source('payments', 'charges') }}
    {% if is_incremental() %}
    -- Watermark window: reprocess the last 3 days to absorb late updates
    -- without rescanning full history.
    where updated_at >= (
        select date_sub(max(charge_date), interval 3 day)
        from {{ this }}
    )
    {% endif %}
),

deduped as (
    -- Defensive dedup inside the window: keep the newest version per key.
    select *
    from source
    qualify row_number() over (
        partition by charge_id
        order by updated_at desc
    ) = 1
)

select
    charge_id,
    customer_id,
    charge_date,
    amount_cents,
    currency,
    status,
    customer_email_hash,
    created_at,
    updated_at
from deduped
```

```sql
-- ddl/fct_charges.sql — target table DDL (BigQuery dialect shown; adapt to
-- the project's engine). Partitioning bounds scan cost; clustering
-- accelerates the dominant per-customer and per-status query patterns.
CREATE TABLE IF NOT EXISTS analytics.fct_charges (
    charge_id           STRING      NOT NULL,
    customer_id         STRING      NOT NULL,
    charge_date         DATE        NOT NULL,
    amount_cents        INT64       NOT NULL,
    currency            STRING      NOT NULL,
    status              STRING      NOT NULL,
    customer_email_hash BYTES,
    created_at          TIMESTAMP   NOT NULL,
    updated_at          TIMESTAMP   NOT NULL
)
PARTITION BY charge_date
CLUSTER BY customer_id, status
OPTIONS (
    partition_expiration_days = 2555,   -- 7-year finance retention policy
    require_partition_filter  = true     -- blocks unpartitioned full scans
);

-- dim_customers (star-schema dimension) follows the same discipline:
-- clustered on customer_id, with PII columns masked by a dynamic data
-- policy so only the governance-approved role sees raw values.
```

---

## 4. Data Quality Assertion Pattern (dbt Tests / GE-Style YAML)

Assertions run before publish; `block_publish` failures gate the load.

```yaml
# models/facts/schema.yml
version: 2

models:
  - name: fct_charges
    description: One row per charge; grain is charge_id.
    tests:
      # Row-count threshold: a run landing under 50% of the trailing 7-day
      # median volume indicates an upstream extract failure.
      - dbt_utils.expression_is_true:
          expression: >
            count(*) >= 0.5 * (
              select percentile_cont(0.5) within group (order by daily_rows)
              from analytics_metrics.fct_charges_daily_volume
            )
          config:
            severity: error
    columns:
      - name: charge_id
        tests:
          - not_null
          - unique
      - name: customer_id
        tests:
          - not_null
          - relationships:
              to: ref('dim_customers')
              field: customer_id
      - name: status
        tests:
          - accepted_values:
              values: ['succeeded', 'pending', 'failed', 'refunded']
      - name: amount_cents
        tests:
          - dbt_utils.expression_is_true:
              expression: "amount_cents >= 0"
      - name: customer_email_hash
        description: PII governance: only the hashed form may appear here.
        tests:
          - dbt_utils.expression_is_true:
              expression: "octet_length(customer_email_hash) = 32"

# Freshness assertion on the source, evaluated by the orchestrator:
sources:
  - name: payments
    tables:
      - name: charges
        freshness:
          warn_after: { count: 12, period: hour }
          error_after: { count: 24, period: hour }
        loaded_at_field: updated_at
```

---

## 5. Idempotency, Freshness & Cost Invariants

$$\text{Idempotency: } \forall\, w: \quad \text{state}(T \circ T(w)) = \text{state}(T(w)) \;\Rightarrow\; \text{no duplicates, no drift on re-run}$$

$$\text{Freshness: } t_{\text{now}} - \max(\text{loaded\_at}) \le \text{SLA}_{\text{freshness}} = 1.5 \times \text{scheduleInterval}$$

$$\text{QualityCoverage} = \frac{\#\{\text{grain columns carrying not\_null} \wedge \text{unique assertions}\}}{\#\{\text{grain columns}\}} \ge 0.8$$

$$\text{CostBudget: } \sum_{\text{run}} \text{bytesScanned} \le B_{\text{scan}}, \qquad \text{alert when } > 1.2 \times \text{P95}_{30d}$$

$$\text{DuplicateGuard: } \forall\, k \in \text{grain keys}: \quad \text{count}(k) = 1 \text{ after every completed run}$$

---

## 6. Guardrails

### Operational Restrictions

- **Idempotency by Construction**: Design for idempotency — every
  transformation run must be safely re-runnable and produce identical target
  state; reject any design that tolerates duplicate-producing re-runs.
- **No Unauthorized Destructive Operations**: Do not execute destructive
  table drops, mass deletes, or unpartitioned full table scans in production
  without explicit authorization; partition-filter guards are the default,
  not an option.
- **Framework Conformance**: Use the project's established orchestrator and
  transformation framework; never introduce a second orchestration system in
  a single design.
- **Single-Agent Executable**: An optional data-engineer subagent can inspect
  schemas in parallel, but one agent can complete this workflow independently
  end to end.

### Security Invariants

- **PII Governance First**: Every PII column is classified, masked or hashed
  at ingestion, covered by column-level access controls, and wired to
  deletion-compliance hooks in accordance with data governance policies; raw
  PII never lands in the curated layer unmasked.
- **No Secrets in Code or Logs**: Connection strings, API tokens, and
  warehouse credentials live in the project's secret manager; designs
  reference them by name (e.g. `<secret-ref>`) and never inline values.
- **Least-Privilege Warehouse Roles**: Pipeline roles receive write access
  only to their target schemas and read access only to declared sources.
- **Auditability**: Every published table records load metadata (run id,
  watermark window, row counts) sufficient to reconstruct what data moved and
  when.

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
failure causes. Never drop warehouse tables or re-run destructive
transformations as part of rollback without explicit authorization.

---

## 8. Verification Plan & Data Toolchain Commands

Execute the following commands using project-local runners; adapt to the
project's declared data tooling:

```bash
# 1. Compile the transformation project (syntax and ref resolution)
npx --no-install dbt compile              # or: dbt parse / sqlmesh plan

# 2. Build the changed models against a scratch target
npx --no-install dbt build --select state:modified+ --target scratch

# 3. Run data quality assertions (tests gate publish)
npx --no-install dbt test --select state:modified+

# 4. Verify idempotency: run the incremental build twice, diff row counts
npx --no-install dbt run --select <model> --target scratch && \
npx --no-install dbt run --select <model> --target scratch && \
psql "$SCRATCH_WAREHOUSE_URL" -f checks/idempotency_count.sql

# 5. Run the project's lint and unit test suite
npm run lint && npm run test
```

---

## 9. Completion Report

The final report must contain: the target schema design with grain,
partitioning, and clustering rationale; the transformation logic and its
idempotency mechanism (watermark window, merge keys, dedup strategy); the
incremental loading strategy with cost analysis; the complete set of quality
assertions with their failure policies and coverage ratio; the PII governance
controls (classification, masking, access, deletion hooks); the monitoring and
alerting plan including the bytes-scanned budget; and every operational risk
and open question that must be resolved before the pipeline is built or
scheduled.
