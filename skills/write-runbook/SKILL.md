---
name: write-runbook
description: "Create or update an operational runbook for a service, feature, or failure mode with detection, diagnosis, mitigation, recovery, and escalation procedures."
---

# Write Runbook

Produce a forward-looking operational playbook that helps operators detect,
diagnose, mitigate, and recover from a specific failure or operational
scenario, and that tells them exactly when and how to escalate. The default
approach is **extract, never invent**: every procedure is drawn from code,
configuration, infrastructure definitions, and observed behavior — a step
that has not been tested is marked untested, not presented as fact.

The skill is stack-agnostic but evidence-bound. Before writing anything,
inspect the local repository to inherit its service layout, monitoring
conventions, alert definitions, and documentation style, and adapt every
command and path below to the project's real tooling.

---

## 1. Required I/O Context Schemas & Natural Language Auto-Inference

The skill supports **two invocation modes**:

1. **Orchestrator / Technical Mode (JSON Manifest)**: Pass the JSON context
   manifest below.
2. **Non-Technical Mode (Plain English Prompts)**: If the user provides a
   natural language request (e.g. *"Write the runbook for when the orders
   API runs out of database connections"*), the agent **must automatically
   infer and populate** `runbook_spec`, `signal_context`, and
   `authority_context` from the user's text and the repository's service
   catalog, alert rules, and ownership files.

### JSON Context Manifest Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "WriteRunbookContextManifest",
  "type": "object",
  "required": ["runbook_spec"],
  "properties": {
    "runbook_spec": {
      "type": "object",
      "required": ["service", "failure_mode", "owning_team"],
      "properties": {
        "service": { "type": "string", "pattern": "^[a-z0-9-]+$" },
        "failure_mode": { "type": "string", "pattern": "^[a-z0-9-]+$" },
        "owning_team": { "type": "string", "pattern": "^[a-z0-9-]+$" },
        "runbook_status": { "type": "string", "enum": ["draft", "tested"], "default": "draft" }
      }
    },
    "signal_context": {
      "type": "object",
      "required": ["alerts"],
      "properties": {
        "alerts": { "type": "array", "items": { "type": "string" }, "minItems": 1 },
        "dashboards": { "type": "array", "items": { "type": "string" } },
        "log_sources": { "type": "array", "items": { "type": "string" } },
        "health_endpoints": { "type": "array", "items": { "type": "string" } }
      }
    },
    "authority_context": {
      "type": "object",
      "required": ["default_executor"],
      "properties": {
        "default_executor": { "type": "string", "enum": ["on_call", "team_lead", "dba", "sre", "incident_commander"] },
        "elevated_steps_require": {
          "type": "array",
          "items": { "type": "string", "enum": ["on_call", "team_lead", "dba", "sre", "incident_commander"] }
        },
        "escalation_targets": { "type": "array", "items": { "type": "string" } }
      }
    }
  }
}
```

### Automatic Natural Language Inference & Safety Rules

If no raw JSON payload is provided, apply these defaults and safety checks:

- **`service`**: Extracted from the prompt noun and confirmed against the
  repository's service registry (`docker-compose.yml`, Kubernetes namespaces,
  `package.json` name, Terraform workspaces). If two services match, ask.
- **`failure_mode`**: Converted to kebab-case from the prompt ("pool
  exhaustion" becomes `pool-exhaustion`). One runbook covers one failure
  mode; a second failure mode is a second runbook.
- **`owning_team`**: Detected from `CODEOWNERS`, a service catalog file, or
  deployment annotations. If ownership is undiscoverable, record it as
  `unknown` and flag the gap in the completion report — never invent a team.
- **`signal_context.alerts`**: Harvested from Alertmanager or Prometheus rule
  files, Grafana provisioning directories, or PagerDuty service definitions.
  If no alerts exist for this failure mode, say so in the Detection section
  and recommend one as a follow-up; do not fabricate an alert name.
- **`authority_context.default_executor`**: Defaults to `on_call`. Any step
  that destroys data, restarts stateful infrastructure, or changes network
  policy defaults into `elevated_steps_require` with at least `team_lead`.
- **Execution Safety**: The skill documents procedures; it never runs them.
  No production command is executed while authoring — commands are validated
  for syntax only, never for effect.

---

## 2. Deterministic State Machine Execution Flow

Follow this exact sequential protocol. Do not skip steps or alter execution
ordering. A runbook section that cannot be grounded in repository evidence is
written as a marked gap, not as plausible-sounding prose.

### Step 1: Evidence Ingestion & Failure-Mode Scoping

1. Read `AGENTS.md`, service architecture documents, monitoring
   configuration, alert definitions, deployment procedures, and every
   existing runbook in the repository.
2. Identify the single failure mode or operational scenario to document, and
   confirm it is distinct from failure modes already covered elsewhere.
3. List the evidence sources that ground each future section: which file or
   system proves each command, threshold, and ownership claim.

### Step 2: Scope, Ownership & Signal Linkage

1. Define the runbook's scope, owning team, service, and audience (primary
   on-call, not the system designer).
2. Record the related alerts and dashboards discovered in Step 1, using
   backticked code spans for names and paths so they survive rendering.
3. If the failure mode has no alert coverage, record the gap and propose the
   minimum alert that would cover it as a follow-up recommendation.

### Step 3: Detection — Signals That Indicate This Problem

1. Document what signals indicate the problem: exact alert names, metric
   expressions, dashboard panels, and log patterns.
2. Document where to look first, in the order an operator should look.
3. Document how to distinguish this issue from its lookalikes — name each
   similar failure mode, give the discriminating observation, and point to
   the sibling runbook that owns it.

### Step 4: Diagnosis — Confirm the Root Cause Class

1. Document specific commands, log queries, metric checks, and health
   endpoints that confirm the root cause class, ordered cheapest-first.
2. Include each exact command with its expected output in both the confirmed
   and healthy cases, so the operator can pattern-match without
   interpretation.
3. Annotate each diagnostic step with the authority required to run it.

### Step 5: Mitigation — Reduce User Impact First

1. Document step-by-step actions to reduce user impact, ordered from least
   to most invasive.
2. For every mitigation step, record three mandatory fields: the **expected
   effect** (what improves and how fast), the **abort condition** (the
   observation that means stop and roll back the step), and the **authority
   requirement** (who is allowed to execute it).
3. Mark every untested step `UNTESTED` inline; a runbook containing any
   untested mitigation step is labeled `Status: DRAFT` in its header.

### Step 6: Recovery — Restore Full Functionality

1. Document the steps that restore full functionality after mitigation,
   including how to reverse each mitigation action taken.
2. Include verification checks with exact commands and expected outputs that
   prove the service is healthy, not merely quiet.
3. Define the watch period and the closing criterion for the incident.

### Step 7: Escalation — When, to Whom, With What

1. Document when to escalate: the time box or failed-step count that makes
   escalation mandatory, not optional.
2. Document to whom, through which channel, in which order — an escalation
   matrix, not a single name.
3. Document what information to provide: the exact snapshot set (metrics,
   command outputs, timeline) that lets the next responder skip re-diagnosis.

### Step 8: Hygiene, Labeling & Secret Discipline

1. Keep credentials, tokens, and sensitive configuration values out of the
   runbook content; reference the secret-management system by role or path
   (e.g. `vault:<path>` or `<from secret manager>`) instead.
2. Apply the untested-steps labeling rule from Section 5 and set the
   runbook's `Status` header accordingly.
3. Record the last-tested date and drill cadence in the header; a runbook
   without a drill schedule decays silently.

---

## 3. Reference Implementation: Complete Failure-Mode Runbook

Complete example for one failure mode. Note the mandatory per-step fields,
the exact expected outputs, and the explicit authority annotations.

```markdown
# RUNBOOK: PostgreSQL Connection Pool Exhaustion — orders-api

- Service: `orders-api` | Owning team: `team-payments` | Status: TESTED
- Failure mode: `pool-exhaustion` | Last drill: 2026-07-20 | Cadence: quarterly
- Review trigger: after any incident touching this failure mode.

## 1. Detection
Page-worthy signals (any one):
- Alert `orders_api_pool_saturation`: pool utilization
  `active / max > 0.9` for 5 minutes (rule file: `alerts/orders-api.yaml`).
- Alert `orders_api_5xx_spike`: 5xx rate > 1% for 3 minutes.
- Dashboard `grafana/d/orders-api-db`, panels "Pool utilization" and
  "Checkout wait time".

Distinguish from lookalikes:
- Slow queries, not exhaustion: active connections < 50% but query p99 > 2s.
  Use runbook `orders-api-slow-queries`.
- Database down, not exhaustion: `pg_isready -h <db-host>` exits non-zero.
  Use runbook `postgres-failover`.

## 2. Diagnosis (run in order; stop when one confirms)
1. `psql "<admin-dsn-from-vault:orders/admin>" -c "SHOW POOLS;"` (pgbouncer console)
   - CONFIRMED: `cl_waiting > 0` and growing; `sv_active` at pool maximum.
   - HEALTHY: `cl_waiting = 0`.
2. `psql "<admin-dsn-from-vault:orders/admin>" -c "SELECT state, count(*) FROM pg_stat_activity WHERE datname='orders' GROUP BY state;"`
   - CONFIRMED: `active` near `max_connections`; many `idle in transaction`.
   - HEALTHY: mostly `idle`, `active` well below the limit.
3. Log query `{app="orders-api"} |= "pool checkout"` in Loki.
   - CONFIRMED: checkout-wait entries above 500ms correlating with 500s.

## 3. Mitigation (steps 1-2: on-call; steps 3+: team-payments lead approval)
Step 1 — Terminate idle-in-transaction sessions older than 5 minutes.
- Command: `psql "<admin-dsn-from-vault:orders/admin>" -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state='idle in transaction' AND now() - xact_start > interval '5 minutes';"`
- Expected effect: pool utilization drops below 70% within 2 minutes; 5xx stops.
- Abort condition: any terminated pid owned by role `deployer` — stop and
  escalate immediately (half-applied migration risk).

Step 2 — Shed load: enable read-only mode via flag `ORDERS_READ_ONLY=1`.
- Command: `kubectl -n orders set env deploy/orders-api ORDERS_READ_ONLY=1`
- Expected effect: write endpoints return 503 with `Retry-After`; pool
  pressure roughly halves within one deploy cycle.
- Abort condition: 5xx rate rises above 5% after enabling — revert with
  `ORDERS_READ_ONLY=0`.

Step 3 — (lead approval) Restart the connection pooler to drop poisoned
server connections. Status: UNTESTED.
- Command: `kubectl -n orders rollout restart deploy/pgbouncer`
- Expected effect: all server connections re-established; utilization resets.
- Abort condition: rollout not complete within 5 minutes — escalate to DBA.

## 4. Recovery
1. Confirm pool utilization < 60% for 10 consecutive minutes on the dashboard.
2. Disable read-only mode: `kubectl -n orders set env deploy/orders-api ORDERS_READ_ONLY=0`.
3. Verify writes with the synthetic probe:
   `curl -sS -X POST "https://<internal-host>/api/orders/synthetic" -H "Authorization: Bearer <synthetic-token-from-vault:orders/synthetic>" -d '{"sku":"PROBE-1","qty":1}'`
   - Expected: `HTTP/1.1 201` and a row visible in `orders.synthetic_probes`.
4. Watch the error-budget panel for 30 minutes; close when burn rate < 1.

## 5. Escalation
| Condition                              | Escalate to         | Channel   | Provide                                  |
|----------------------------------------|---------------------|-----------|------------------------------------------|
| Steps 1-2 ineffective after 15 minutes | team-payments lead  | pager     | pg_stat_activity snapshot, pool graph    |
| Any abort condition hit                | DBA on-call         | pager     | terminated pid list, migration status    |
| Suspected data corruption              | incident commander  | bridge    | timeline, affected order ids, probe log  |
Every escalation includes: current 5xx rate, pool utilization, steps already
run with their outputs, and minutes since first detection.
```

---

## 4. Runbook Validation Checklist & Drill Record Pattern

A runbook is only as trustworthy as its test evidence. Track every command's
verification state, and run scheduled drills that produce a written record.

```markdown
# Validation Checklist — RUNBOOK orders-api pool-exhaustion
| # | Step / Command                              | Tested | Last tested | By        | Environment |
|---|---------------------------------------------|--------|-------------|-----------|-------------|
| 1 | Diagnosis 1: SHOW POOLS                     | yes    | 2026-07-20  | on-call A | staging     |
| 2 | Diagnosis 2: pg_stat_activity query         | yes    | 2026-07-20  | on-call A | staging     |
| 3 | Mitigation 1: terminate idle-in-transaction | yes    | 2026-07-20  | on-call B | staging     |
| 4 | Mitigation 2: read-only flag                | yes    | 2026-07-20  | on-call B | staging     |
| 5 | Mitigation 3: pgbouncer restart             | NO     | -           | -         | -           |
| 6 | Recovery 3: synthetic order probe           | yes    | 2026-07-20  | on-call A | production  |

Rules:
- A step is TESTED only after end-to-end execution in staging, a drill, or
  an observed incident. Reading the command aloud does not count.
- Any UNTESTED row forces `Status: DRAFT` in the runbook header.
- Drill cadence: quarterly, plus after every incident in this failure mode.

# Tabletop / Drill Record — 2026-07-20 (quarterly)
- Scenario: staged exhaustion via `pgbench -c 120 -j 8` against the staging
  pooler while running the order generator.
- Participants: on-call primary, shadow, facilitator (team-payments lead).
- Timeline: detected 4m (alert fired), diagnosed 6m, mitigated 9m,
  recovered 7m. Total 26m against a 30m target.
- What broke: Diagnosis 1 command hung without the console `-h` flag —
  fixed in place. Dashboard panel link returned 404 — link corrected.
- Newly discovered untested step: Mitigation 3 (pooler restart) — marked
  UNTESTED and scheduled for next game day.
- Action items: automate the synthetic probe check (owner: on-call A, due
  2026-09-01); add alert for `idle in transaction` count > 20.
```

---

## 5. Runbook Quality Invariants & MTTR Mathematics

**Mitigation completeness**: every mitigation step carries a non-empty
expected effect, abort condition, and authority requirement:

$$\forall s \in \text{MitigationSteps}:\; \text{effect}(s) \neq \varnothing \;\wedge\; \text{abort}(s) \neq \varnothing \;\wedge\; \text{authority}(s) \neq \varnothing$$

**Untested-steps labeling rule**: the runbook's declared status is a pure
function of its verification evidence:

$$\text{Status}(R) = \begin{cases} \text{DRAFT} & \text{if } \exists\, s \in R:\; \text{tested}(s) = \text{false} \\ \text{TESTED} & \text{otherwise} \end{cases}$$

**Detection-signal specificity**: each detection signal should fire for this
failure mode and almost nothing else, and each alert maps to exactly one
runbook:

$$\text{Specificity}(\sigma) = \frac{\lvert \text{firings}(\sigma) \cap \text{incidents}(F) \rvert}{\lvert \text{firings}(\sigma) \rvert} \ge 0.8, \qquad \forall \sigma:\; \lvert \text{runbooks}(\sigma) \rvert = 1$$

**MTTR contribution estimate**: a tested runbook compresses diagnosis and
mitigation, which dominate time-to-restore:

$$MTTR = t_{\text{detect}} + t_{\text{diagnose}} + t_{\text{mitigate}} + t_{\text{recover}}, \qquad \Delta MTTR_{\text{runbook}} \approx -(0.4 \ldots 0.6)\,(t_{\text{diagnose}} + t_{\text{mitigate}})$$

---

## 6. Guardrails

### Operational Restrictions

- **Document, Never Execute**: Runbooks document procedures; they do not
  execute them. Do not run production commands, apply configuration, or
  modify infrastructure as part of writing a runbook. Commands are
  syntax-checked at most, never run for effect.
- **Extract, Never Invent**: Every command, threshold, path, and ownership
  claim must trace to code, configuration, infrastructure definitions, or
  observed drill evidence. If evidence is missing, write a marked gap.
- **Untested Means Labeled**: Mark untested procedures explicitly and inline.
  A runbook containing any untested step is labeled `Status: DRAFT` in its
  header — no exceptions, no footnotes instead of labels.
- **One Failure Mode Per Runbook**: Do not merge distinct failure modes to
  save pages; ambiguity at 3 a.m. is the enemy this document exists to kill.
- **Single-Agent Executable**: An optional explorer subagent can map
  infrastructure or inventory alert rules in parallel, but one agent must be
  able to complete this workflow end to end.

### Security Invariants

- **Zero Credential Content**: No credentials, tokens, connection strings
  with passwords, private keys, or sensitive configuration values in runbook
  content. Reference the secret-management system by role or path
  (e.g. `<admin-dsn-from-vault:orders/admin>`) instead.
- **Least-Authority Annotations**: Every step names the minimum role allowed
  to execute it. Destructive or stateful-infrastructure steps require
  elevated authority and say so.
- **No Reachable Attack Recipes**: Sanitize internal hostnames, unauthenticated
  debug endpoints, and bypass flags to `<placeholder>` form when the runbook
  could leave the trust boundary (public repo, vendor ticket, chat export).
- **Command Safety Review**: Flag every command that can destroy data or drop
  traffic with an explicit risk note and a pre-execution verification query.

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

Rollback restores repository state, not operational state — since this skill
never executes procedures, there is no infrastructure to roll back. After
rollback, output the exact verification failure, the list of evidence sources
already gathered, and which runbook sections were complete, so the next
attempt resumes from evidence rather than from scratch.

---

## 8. Verification Plan & Documentation Toolchain Commands

Execute the following commands against the runbook artifact; adapt paths to
the project's documentation layout:

```bash
# 1. Lint markdown structure (when the project configures a linter)
npx --no-install markdownlint-cli2 "docs/runbooks/**/*.md"

# 2. Scan for credential-shaped strings with the project's scanner
gitleaks detect --source docs/runbooks --no-git --verbose

# 3. Verify every mitigation step declares its mandatory fields
grep -c "Expected effect" docs/runbooks/<runbook-file>.md
grep -c "Abort condition" docs/runbooks/<runbook-file>.md
grep -c "Authority" docs/runbooks/<runbook-file>.md

# 4. Syntax-check embedded shell commands locally (never execute them)
awk '/```(bash|sh)/{f=1;next}/```/{f=0}f' docs/runbooks/<runbook-file>.md > /tmp/runbook-cmds.sh
bash -n /tmp/runbook-cmds.sh && echo "COMMAND SYNTAX OK"

# 5. Verify referenced backticked repository paths actually exist
grep -oE '`[a-zA-Z0-9_./-]+/[a-zA-Z0-9_./-]+`' docs/runbooks/<runbook-file>.md | tr -d '`' | sort -u | while read -r p; do
  [ -e "$p" ] || echo "MISSING PATH: $p"
done

# 6. Enforce the untested-steps labeling rule
if grep -q "UNTESTED" docs/runbooks/<runbook-file>.md; then
  grep -q "Status: DRAFT" docs/runbooks/<runbook-file>.md || echo "LABELING VIOLATION: untested steps without DRAFT status"
fi

# 7. Confirm header freshness fields are present
grep -E "Last (tested|drill):" docs/runbooks/<runbook-file>.md
grep -E "Cadence:" docs/runbooks/<runbook-file>.md
```

---

## 9. Completion Report

Report the following, in order:

1. **Runbook produced**: path, service, failure mode, owning team, and the
   declared `Status` (`DRAFT` or `TESTED`) with the reason.
2. **Failure modes covered**: the single documented mode plus the lookalike
   modes it explicitly discriminates against.
3. **Procedures documented**: counts of detection signals, diagnostic steps,
   mitigation steps (each with effect, abort condition, and authority), and
   recovery steps.
4. **Commands verified**: which commands were syntax-checked, which were
   confirmed against live or drill evidence, and the evidence source for
   each.
5. **Untested steps**: the explicit list, why each remains untested, and the
   scheduled drill or game day that will test them.
6. **Maintenance recommendations**: alert gaps discovered, drill cadence set,
   review triggers, and suggested automation (synthetic probes, checklist
   CI).
