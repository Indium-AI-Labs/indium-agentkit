---
name: incident-triage
description: Triage incidents with evidence, mitigation, and follow-up.
---

# Incident Triage

Turn an active or suspected production problem into a bounded, evidence-led
response. The default model is **incident command**: a named incident owner, a
recorded timeline, facts separated from hypotheses, the lowest-risk reversible
mitigation applied first, and blameless follow-up with owned corrective
actions.

The default tooling is whatever the project already exposes — metrics
dashboards and query endpoints, log aggregation, distributed tracing, alert
history, deploy history, feature-flag systems, and status-page or chat
channels. Inspect the project's `AGENTS.md`, observability stack, on-call
model, and communication conventions before assuming a toolchain. Keep a
timeline, distinguish facts from hypotheses, and optimize first for user
safety and service stability — never for speed of explanation.

---

## 1. Required I/O Context Schemas & Natural Language Auto-Inference

The skill supports **two invocation modes**:

1. **Orchestrator / Technical Mode (JSON Manifest)**: Pass the JSON context
   manifest below.
2. **Non-Technical Mode (Plain English Prompts)**: If the user provides a
   natural language prompt (e.g. *"Checkout error rate spiked twenty minutes
   ago, help me triage"*), the agent **must automatically infer and populate**
   `incident_spec`, `response_context`, and `signal_context` from the user's
   text and the repository's observability and incident conventions.

### JSON Context Manifest Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "IncidentTriageContextManifest",
  "type": "object",
  "required": ["incident_spec", "response_context"],
  "properties": {
    "incident_spec": {
      "type": "object",
      "required": ["severity", "impact", "started_at"],
      "properties": {
        "incident_id": { "type": "string", "pattern": "^INC-[0-9]{4,}$" },
        "severity": { "type": "string", "enum": ["SEV1", "SEV2", "SEV3", "SEV4"] },
        "impact": { "type": "string", "minLength": 1 },
        "started_at": { "type": "string", "format": "date-time" },
        "affected_scope": { "type": "string" },
        "detected_via": { "type": "string", "enum": ["alert", "user_report", "observation", "dependency"], "default": "alert" }
      }
    },
    "response_context": {
      "type": "object",
      "required": ["incident_owner", "channel", "authority"],
      "properties": {
        "incident_owner": { "type": "string", "minLength": 1 },
        "channel": { "type": "string", "minLength": 1 },
        "authority": { "type": "string", "enum": ["read_only_observe", "mitigate_with_approval", "full_mitigation"], "default": "read_only_observe" },
        "roles": {
          "type": "array",
          "items": { "type": "string", "enum": ["incident_commander", "operations_lead", "communications_lead", "scribe", "subject_matter_expert"] }
        },
        "update_cadence_minutes": { "type": "integer", "minimum": 5, "default": 30 }
      }
    },
    "signal_context": {
      "type": "object",
      "properties": {
        "metrics_sources": { "type": "array", "items": { "type": "string" } },
        "log_sources": { "type": "array", "items": { "type": "string" } },
        "trace_sources": { "type": "array", "items": { "type": "string" } },
        "alert_sources": { "type": "array", "items": { "type": "string" } },
        "deploy_history_source": { "type": "string" },
        "feature_flag_source": { "type": "string" }
      }
    }
  }
}
```

### Automatic Natural Language Inference & Safety Rules

If no raw JSON payload is provided, apply these defaults and safety checks:

- **`incident_id`**: Generated as `INC-<YYYYMMDD>-<sequence>` when the project
  has no id convention; otherwise reuse the project's existing scheme. Every
  timeline entry, status update, and report references this id.
- **`severity`**: Inferred from impact language: full outage, data loss, or
  security exposure maps to SEV1; a major feature degraded for many users maps
  to SEV2; minor degradation or a single-tenant impact maps to SEV3; cosmetic
  or internal-only issues map to SEV4. When ambiguous, assume the higher
  severity and de-escalate only with evidence.
- **`started_at`**: The best available evidence — first alert, first anomalous
  metric point, or first user report — recorded together with its source.
  Never guess a start time silently; mark uncertainty explicitly.
- **`incident_owner`**: The responding agent unless a human owner is named.
  Any handoff to a human commander is recorded in the timeline.
- **`channel`**: The project's declared incident channel convention. If none
  exists, propose one (a dedicated chat channel or bridge) and record the
  choice in the timeline.
- **`authority`**: Defaults to `read_only_observe`. Natural language never
  upgrades authority; production changes require an explicit grant plus a
  recorded rollback or stop plan before any action.
- **`signal_context`**: Discovered from the repository's observability
  configuration: dashboards-as-code, alert rule definitions, logging and
  tracing setup, and deployment tooling.
- **Path Safety**: Any file path referenced in evidence capture or reports
  MUST NOT contain traversal segments (`.` or `..`). Normalize paths and
  **ABORT execution immediately** if a traversal attempt is detected.

---

## 2. Deterministic State Machine Execution Flow

Follow this exact sequential protocol. Do not skip steps or alter execution
ordering. Steps 1-5 run during the active incident; Steps 6-8 run after
stabilization.

### Step 1: Incident Framing & Role Assignment

1. Establish incident start time, current impact, affected users or regions,
   severity, incident owner, communications channel, and decision authority.
2. Announce the incident, severity, owner, and channel in a single message;
   every subsequent action and update references the incident id.
3. Assign roles as needed (operations lead, communications lead, scribe); for
   a single-agent response, the agent holds all roles and says so.
4. Open the timeline document (Section 3) immediately; the first entry is the
   declaration itself.

### Step 2: Evidence Preservation

1. Preserve evidence before anything changes: deploy history, metrics, logs,
   traces, alerts, request examples, and configuration changes.
2. Record exact timestamps and verbatim queries for every observation so
   another operator can reproduce it.
3. Snapshot state before any restart, failover, flag flip, or configuration
   change. Evidence-before-restart is mandatory, not optional.
4. Correlate the incident window against recent deploys, flag changes, and
   infrastructure events; record each correlation with its source.

### Step 3: Hypothesis Register

1. Form a small set of testable hypotheses ranked by expected impact and
   available evidence; three to five entries is typical.
2. For each hypothesis, record the evidence for, the evidence against, and a
   concrete test with an expected observable outcome.
3. Avoid speculative changes that destroy the ability to compare signals:
   change one variable at a time, with before-and-after capture.

### Step 4: Lowest-Risk Mitigation Selection

1. Choose the lowest-risk mitigation: disable a feature, stop a rollout, shed
   load, fail over, or revert a compatible artifact.
2. State the expected effect and the abort condition before acting, and
   record both in the timeline.
3. Prefer reversible mitigations (flags, traffic weights, rollbacks) over
   irreversible ones (data deletion, resource teardown); confirm the required
   authority level before executing anything.

### Step 5: Mitigation Verification & Communication

1. Verify each mitigation against user-impact and dependency-health signals
   using the checklist in Section 4.
2. Continue the timeline through stabilization; never leave gaps longer than
   the severity's update cadence.
3. Communicate status, uncertainty, and the next update time on cadence,
   using the status-update format in Section 4.

### Step 6: Root Cause Analysis

1. After stabilization, identify root cause separately from contributing
   factors; the trigger (a deploy) is rarely the root cause (a missing guard).
2. Reproduce safely — in staging, by replay, or by log analysis — never by
   re-breaking production.
3. Preserve a regression test or detection rule that would have caught the
   condition, and link it from the report.

### Step 7: Corrective Action Definition

1. Define corrective actions with owners and due dates across all applicable
   categories: code, infrastructure, monitoring, runbooks, permissions, and
   process.
2. Rank actions by risk reduction per unit effort; quick detection and
   rollback improvements usually outrank deep refactors.

### Step 8: Incident Report & Blameless Review

1. Complete an incident report without credentials or sensitive payloads,
   covering impact, timeline, hypotheses, mitigations, root cause status, and
   follow-ups.
2. Review the report for blameless, evidence-backed language: describe system
   and process conditions, not personal fault. Every claim must trace to a
   timeline entry or evidence artifact.

---

## 3. Reference Implementation: Incident Timeline & Hypothesis Register

The timeline is the single source of truth during the response. Keep it
append-only: corrections are new entries, never edits to history.

```markdown
# INC-2026-0142 — Checkout 5xx spike

severity: SEV2 | owner: <incident-owner-handle> | channel: #incident-2026-0142
authority: mitigate_with_approval | started_at: 2026-08-14T09:41:00Z
detected_via: alert | update_cadence: 30 minutes

## Impact

- ~12% of checkout attempts returning 502 since 09:41 UTC
- All regions affected; payment capture unaffected (async path healthy)
- Estimated 400 failed checkouts as of 10:05 UTC

## Timeline (UTC; every entry evidence-backed and append-only)

| Time  | Event                                                          | Source                    |
|-------|----------------------------------------------------------------|---------------------------|
| 09:38 | deploy checkout-service rev 9f3a2c1 completed                  | CI deploy log #4821       |
| 09:41 | first 5xx alert fires (checkout-5xx-rate)                      | alertmanager alert a-7781 |
| 09:44 | incident declared SEV2; owner assigned; channel opened         | channel message 09:44     |
| 09:47 | snapshot: error rate 12.4%, p95 latency 1.9s                   | metrics query q-0091      |
| 09:52 | hypothesis register opened with 3 hypotheses                   | this document             |
| 10:02 | mitigation: feature flag payment_retry_v2 disabled             | flag audit log f-331      |
| 10:08 | error rate 0.3%, p95 480ms — mitigation holding                | metrics query q-0094      |
| 10:12 | approval granted for rollback of rev 9f3a2c1                   | approval note a-102       |
| 10:30 | rollback of rev 9f3a2c1 completed                              | rollout history entry     |
| 10:41 | error rate at baseline 0.1% for 10 min — monitoring window     | metrics query q-0099      |
| 11:15 | incident stabilized; moved to root-cause analysis              | owner note 11:15          |

## Hypothesis Register

| ID | Hypothesis                                        | Evidence For                                              | Evidence Against                              | Test                                    | Status                 |
|----|---------------------------------------------------|-----------------------------------------------------------|-----------------------------------------------|-----------------------------------------|------------------------|
| H1 | payment_retry_v2 retry storm saturating gateway   | spike began 3 min after flag-enabled deploy; 429s in traces | 5xx persisted briefly after flag off        | disable flag; watch error rate 10 min   | CONFIRMED contributing |
| H2 | database connection pool exhaustion               | pool saturation metric elevated                           | saturation began after 5xx, not before        | inspect pool metrics pre-incident       | REJECTED (effect)      |
| H3 | upstream payments gateway outage                  | gateway 429s observed                                     | gateway health endpoint green throughout      | query dependency health series          | REJECTED               |

## Mitigation Record

- Action: disable feature flag payment_retry_v2 (reversible, no redeploy)
- Expected effect: error rate below 1% within 10 minutes
- Abort condition: error rate still above 5% after 10 min -> proceed to rollback
- Stop plan: re-enable flag restores prior behavior in under 1 minute
- Result: effect observed at 10:08; rollback executed as defense in depth

## Evidence Index

- q-0091, q-0094, q-0099: metrics queries stored in evidence/metrics/
- f-331: feature-flag audit log export
- a-7781: alertmanager alert payload
- logs: evidence/logs/checkout-service-0938-1041.log (captured pre-restart)
```

---

## 4. Mitigation Verification Checklist & Status Update Pattern

Verify every mitigation against this checklist before declaring progress, and
communicate on cadence using the status-update format.

```markdown
### Mitigation Verification Checklist

- [ ] User-impact signal (error rate, success ratio) trending toward baseline
- [ ] Dependency-health signals green or fully explained
- [ ] No new alert classes firing since the mitigation
- [ ] Mitigation effect sustained for the full monitoring window
- [ ] Evidence snapshots (queries, timestamps, outputs) stored in the timeline
- [ ] Stop plan still valid if the condition regresses
- [ ] Status update posted with a committed next update time

### Status Update Message Format

[INC-2026-0142][SEV2] 10:15 UTC — STATUS UPDATE
Summary: Checkout 5xx spike mitigated; error rate 0.3% and falling.
Impact: ~12% of checkout attempts failing 09:41-10:08 UTC; no payment capture loss.
Current state: Feature flag payment_retry_v2 disabled; rollback of rev 9f3a2c1 in progress.
Actions taken: Flag disabled 10:02 (effect confirmed 10:08); rollback approved 10:12, started 10:14.
Uncertainty: Root cause not yet confirmed; retry-storm hypothesis leading.
Next update: 10:45 UTC or immediately on regression.
```

### Verification Command Sketch

```bash
# Confirm the user-impact signal is trending toward baseline
curl -fsS '<metrics-endpoint>/api/v1/query' \
  --data-urlencode 'query=sum(rate(http_requests_total{status=~"5.."}[5m]))/sum(rate(http_requests_total[5m]))' \
  | jq -r '.data.result[0].value[1]'

# Confirm dependency health
curl -fsS -o /dev/null -w 'status=%{http_code}\n' https://api.example.com/healthz
```

---

## 5. Response SLA & Severity Classification Mathematics

$$\text{MTTA} = \frac{1}{N} \sum_{i=1}^{N} \left( t_{\text{ack}}^{(i)} - t_{\text{alert}}^{(i)} \right) \;\le\; 5\,\text{min} \quad (\text{SEV1/SEV2})$$

$$\text{MTTR} = \frac{1}{N} \sum_{i=1}^{N} \left( t_{\text{mitigated}}^{(i)} - t_{\text{detected}}^{(i)} \right) \;\le\; 60\,\text{min} \quad (\text{SEV2 target})$$

$$\Delta t_{\text{update}}(\text{SEV}) = \begin{cases} 15\,\text{min} & \text{SEV1} \\ 30\,\text{min} & \text{SEV2} \\ 60\,\text{min} & \text{SEV3} \\ 120\,\text{min} & \text{SEV4} \end{cases}, \qquad t_{\text{next\_update}} \;\le\; t_{\text{last\_update}} + \Delta t_{\text{update}}(\text{SEV})$$

$$\text{SEV1} \Leftrightarrow \text{outage} \;\lor\; \text{data loss} \;\lor\; \text{security breach}, \qquad \text{severity} = \max\big(\text{user\_impact},\; \text{data\_risk},\; \text{security\_risk}\big)$$

$$\forall\, a \in \{\text{restart}, \text{delete}, \text{failover}\}: \quad \text{permit}(a) \;\Rightarrow\; \text{evidence-snapshotted}(a) \;\wedge\; \text{stop-plan-recorded}(a) \;\wedge\; \text{authority-granted}(a)$$

$$\text{choose}(m^{*}) = \arg\min_{m \in M} \; \text{risk}(m) \quad \text{subject to} \quad \text{expected-effect}(m) \ge \text{required effect}, \quad \text{reversible}(m) \text{ preferred}$$

---

## 6. Guardrails

### Operational Restrictions

- **Authority Before Action**: Do **NOT** perform production changes,
  credential operations, or destructive recovery without explicit authority
  and a recorded rollback or stop plan. The authority level
  (`read_only_observe`, `mitigate_with_approval`, `full_mitigation`) gates
  every action and is recorded in the timeline.
- **Reversible Mitigations First**: Prefer reversible mitigations — feature
  flags, traffic weights, artifact rollbacks — over irreversible ones. Change
  one variable at a time so before-and-after signals remain comparable.
- **Evidence Before Restart**: Preserve logs before restarting or deleting
  resources. Snapshot state before every action; an action without a prior
  snapshot is a guardrail violation.
- **Single-Agent Executable**: An incident-commander subagent can coordinate
  notes and hypotheses, but one agent must be able to run this workflow end
  to end, including timeline keeping and status communication.

### Security Invariants

- **Redact Secrets Everywhere**: Redact secrets, tokens, session identifiers,
  and customer payloads from timelines, status updates, evidence bundles, and
  reports. Reference credentials by name only.
- **No Credentials in Reports**: Incident channels and reports contain no
  credentials or sensitive payloads; run the redaction sweep (Section 8)
  before sharing any artifact.
- **Blameless Language**: Reports describe system and process conditions, not
  personal fault. Blameless reporting is a security property of the process:
  it keeps future incident data truthful and complete.
- **Scoped Authority**: Elevated incident authority expires with the
  incident; standing access is never created as a side effect of the
  response.

---

## 7. Atomic Failure Recovery & Rollback Handler

Two recovery layers exist and must not be conflated: **repository rollback**
(files created while documenting the response) and **mitigation reversal**
(operational actions taken during the response). Before creating or modifying
files, capture a baseline list of modified and untracked files. If any
verification command in Section 8 fails and cannot be resolved within 2
iterations, execute targeted repository rollback restricted ONLY to files
created or modified during this run:

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

For mitigation reversal, every mitigation entry in the timeline must carry
its own stop plan (re-enable the flag, restore the traffic weight, roll the
deployment forward or back). Execute the stop plan exactly as recorded;
never improvise a reversal that was not written down. After either rollback,
output the exact error trace and state failure causes, and append the
recovery event to the incident timeline.

---

## 8. Verification Plan & Evidence Capture Commands

Execute the following commands to verify response completeness and preserve a
reproducible evidence bundle; adapt endpoints to the project's observability
stack:

```bash
# 1. Freeze the incident window bounds for reproducible queries
START="2026-08-14T09:41:00Z"; END="2026-08-14T11:00:00Z"

# 2. Export deploy and change history for the window
kubectl get events --sort-by=.lastTimestamp > evidence/deploy-events.txt

# 3. Snapshot the error-rate series across the window
curl -fsS '<metrics-endpoint>/api/v1/query_range' \
  --data-urlencode 'query=sum(rate(http_requests_total{status=~"5.."}[5m]))' \
  --data-urlencode "start=$START" --data-urlencode "end=$END" \
  --data-urlencode 'step=60' > evidence/error-rate-series.json

# 4. Snapshot logs BEFORE any restart or teardown
kubectl logs deploy/checkout-service --since-time="$START" > evidence/service-logs.txt

# 5. Verify timeline completeness: every mitigation has a verification entry
grep -c "Mitigation Record" incident-timeline.md

# 6. Redaction sweep on the report before sharing
grep -nEi '(token|secret|password|api[_-]?key|authorization:)' incident-report.md \
  && echo "REDACT BEFORE SHARE" || echo "CLEAN"
```

---

## 9. Completion Report

Report impact (users, scope, duration, and business effect), the full
append-only timeline with its evidence index, hypotheses with dispositions
and test results, mitigations with verification results and stop plans, root
cause status (confirmed, suspected, or unknown) separated from contributing
factors, residual risk, detection gaps and the regression test or detection
rule preserved, and owned follow-up actions with due dates across code,
infrastructure, monitoring, runbooks, permissions, and process. State clearly
what remains unverified, and confirm the report passed the redaction sweep
and blameless-language review before distribution.
