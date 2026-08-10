---
name: data-pipeline-design
description: "Design safe ETL/ELT pipelines, data warehouse schemas, partition strategies, idempotency controls, and data quality assertions before implementation."
---

# Data pipeline design

Design scalable data transformation pipelines and warehouse data models. PostgreSQL,
BigQuery, Snowflake, and DuckDB are supported patterns; follow the consumer project's
established data warehouse stack, orchestrator, and transformation framework.

## Workflow

1. Read `AGENTS.md`, feature brief, source schema, target warehouse model, and query
   patterns. State constraints regarding data volume, latency SLA, privacy, and retention.
2. Model target tables using appropriate dimensional schemas (Star schema, Snowflake
   schema, or One Big Table). Define primary keys, foreign keys, partition keys,
   clustering fields, and data types.
3. Design extraction and transformation logic (dbt, SQL, Spark, or Python). Enforce
   idempotency so pipeline re-runs produce identical results without duplicate rows.
4. Define incremental loading strategies (watermark columns, change data capture, append-only
   with deduplication window) to minimize compute cost and warehouse lock times.
5. Establish data quality assertions (non-null, uniqueness, referential integrity,
   accepted values, custom threshold checks) to run before and after transformation.
6. Design PII handling, masking, column-level access controls, and data deletion
   compliance hooks in accordance with data governance policies.
7. Plan pipeline monitoring: record counts, execution duration, byte scan volume, schema
   drift detection, and failure alert notifications.
8. Record pipeline specification, schema design, data quality checks, and operational
   risks in the agreed architecture handoff.

## Guardrails

- Design for idempotency: every transformation run must be safely re-runnable.
- Do not execute destructive table drops or unpartitioned full table scans in production
  without explicit authorization.
- An optional data-engineer subagent can inspect schemas in parallel, but one agent can
  complete this workflow independently.

## Completion report

Report target schema design, partitioning strategy, transformation logic, idempotency
mechanism, quality assertions defined, governance controls, and performance risks.
