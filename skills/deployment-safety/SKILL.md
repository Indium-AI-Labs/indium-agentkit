---
name: deployment-safety
description: Plan and verify staged deployments with safe rollback.
---

# Deployment Safety

Prepare a production change so it can be released deliberately, observed
continuously, and reversed within a bounded time. The default model is a
**staged rollout** — preflight, canary cohort, observation windows, expansion,
completion — executed against explicit health signals and abort thresholds,
with a rehearsed rollback path.

The default tooling targets **Kubernetes-style platforms** (`kubectl` rollout
state, traffic-weighted canary cohorts) plus generic HTTP health probes
(`curl`) and metrics queries; adapt to the consumer project's actual
deployment platform (serverless, VM images, PaaS, mobile distribution) before
planning. Inspect the project's `AGENTS.md`, deployment platform,
environments, service dependencies, and release policy before making
assumptions.

---

## 1. Required I/O Context Schemas & Natural Language Auto-Inference

The skill supports **two invocation modes**:

1. **Orchestrator / Technical Mode (JSON Manifest)**: Pass the JSON context
   manifest below.
2. **Non-Technical Mode (Plain English Prompts)**: If the user provides a
   natural language prompt (e.g. *"Plan a canary release of checkout-service
   build 9f3a2c1 to production"*), the agent **must automatically infer and
   populate** `release_spec`, `rollout_context`, and `signal_context` from
   the user's text and the repository's deployment configuration.

### JSON Context Manifest Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "DeploymentSafetyContextManifest",
  "type": "object",
  "required": ["release_spec", "rollout_context", "signal_context"],
  "properties": {
    "release_spec": {
      "type": "object",
      "required": ["artifact", "revision", "environment"],
      "properties": {
        "artifact": { "type": "string", "pattern": "^[A-Za-z0-9._/@:-]+$" },
        "revision": { "type": "string", "pattern": "^[0-9a-f]{7,40}$" },
        "environment": { "type": "string", "enum": ["development", "staging", "production"] },
        "change_summary": { "type": "string" },
        "owner": { "type": "string" }
      }
    },
    "rollout_context": {
      "type": "object",
      "required": ["strategy", "authorized"],
      "properties": {
        "strategy": { "type": "string", "enum": ["canary", "blue_green", "rolling", "all_at_once"] },
        "authorized": { "type": "boolean", "default": false },
        "canary_cohorts": {
          "type": "array",
          "items": { "type": "integer", "minimum": 1, "maximum": 100 }
        },
        "observation_window_minutes": { "type": "integer", "minimum": 5, "default": 30 },
        "operator": { "type": "string" },
        "observer": { "type": "string" }
      }
    },
    "signal_context": {
      "type": "object",
      "required": ["health_metrics", "abort_thresholds"],
      "properties": {
        "health_metrics": {
          "type": "array",
          "items": { "type": "string", "enum": ["error_rate", "latency_p95", "latency_p99", "saturation", "business_kpi", "dependency_health", "log_anomalies"] },
          "minItems": 1
        },
        "abort_thresholds": {
          "type": "object",
          "properties": {
            "error_rate_max": { "type": "number", "minimum": 0, "maximum": 1, "default": 0.01 },
            "latency_p95_max_ms": { "type": "integer", "minimum": 1, "default": 500 },
            "latency_p99_max_ms": { "type": "integer", "minimum": 1, "default": 1500 },
            "business_kpi_drop_max": { "type": "number", "minimum": 0, "maximum": 1, "default": 0.05 }
          }
        },
        "rollback_time_objective_minutes": { "type": "integer", "minimum": 1, "default": 15 }
      }
    }
  }
}
```

### Automatic Natural Language Inference & Path Traversal Validation Rules

If no raw JSON payload is provided, apply these defaults and safety checks:

- **`artifact`**: Detected from the project's build output configuration
  (container image reference, package version). Every artifact must be
  traceable to `revision`; an untraceable artifact blocks the plan.
- **`revision`**: The current commit SHA from version control. Never plan a
  production deploy of an untracked working tree.
- **`environment`**: Inferred from prompt keywords; defaults to `staging`.
  Any inference of `production` must be explicitly confirmed by the user.
- **`strategy`**: Inferred from platform capability and change risk:
  `canary` for user-facing production services, `rolling` for stateless
  workers, `blue_green` where paired environments exist.
- **`authorized`**: Always `false` unless the user explicitly authorizes
  production execution. Natural language never implies authorization.
- **`health_metrics`**: Defaults to
  `["error_rate", "latency_p95", "dependency_health"]` when the repository
  declares no observability conventions.
- **`abort_thresholds`**: Derived from existing SLO documents or alert rules
  if present; otherwise the schema defaults apply.
- **Path Traversal Protection**: Any file path referenced in the rollout plan
  (manifests, runbooks, handoffs) MUST NOT contain traversal segments (`.` or
  `..`). Normalize paths and **ABORT execution immediately** if a traversal
  attempt is detected.

---

## 2. Deterministic State Machine Execution Flow

Follow this exact sequential protocol. Do not skip steps or alter execution
ordering.

### Step 1: Change Definition & Blast Radius

1. Define the change, owner, target environment, blast radius, and explicit
   success and abort criteria.
2. Record affected services, downstream consumers, and shared resources
   (databases, queues, caches) that a failure could touch.
3. Write success criteria as measurable signal statements, not adjectives:
   "error rate stays below 1% for 30 minutes", never "looks healthy".

### Step 2: Artifact & Preconditions Verification

1. Verify the artifact is reproducible and traceable to a commit: the build
   digest matches CI output for `revision`.
2. Confirm tests pass at `revision`, migrations are reviewed, configuration
   diffs are enumerated, feature flags exist for risky behavior, and all
   required approvals are recorded.

### Step 3: Environment Parity & Capacity Check

1. Check environment parity, runtime versions, dependency availability,
   secrets references (by name only), permissions, capacity headroom, and
   maintenance windows.
2. Diff configuration between source and target environments; unexplained
   deltas block the rollout until resolved or documented.

### Step 4: Staged Rollout Plan Authorship

1. Write a staged rollout: preflight, canary or small cohort, observation
   window, expansion, and completion.
2. Assign an operator (executes) and an observer (watches signals). One
   person should not hold both roles for production without explicit
   acknowledgment in the plan.

### Step 5: Health Signal Selection

1. Choose health signals before rollout: error rate, latency, saturation,
   business outcome, logs, traces, and dependency health.
2. Bind each signal to a concrete query or command the observer can execute
   verbatim at every stage gate.

### Step 6: Abort Thresholds & Halt Authority

1. Define exact abort thresholds, who can stop the rollout, and how to halt
   it without destroying evidence.
2. The halt procedure must preserve logs, metrics snapshots, and deployment
   state for post-incident analysis.

### Step 7: Rollback & Forward-Fix Rehearsal

1. Define and rehearse rollback or forward-fix steps, including database and
   queue compatibility.
2. Never assume a schema rollback is automatically safe: verify
   expand-and-contract compatibility or document the forward-fix path.
3. Execute the rollback drill in staging (Section 4) and record the measured
   time-to-baseline against the RTO before requesting production
   authorization.

### Step 8: Authorized Execution & Evidence Capture

1. Execute only the authorized scope, record timestamps and evidence at every
   gate, and update the deployment handoff with results, limitations, and
   follow-up actions.
2. If any gate fails, halt per Step 6, capture the evidence bundle, and roll
   back per Step 7. Do not improvise new actions mid-incident.

---

## 3. Reference Implementation: Staged Rollout Plan Document

```yaml
# rollout-plan.yaml — canary release of checkout-service
release:
  artifact: registry.example.com/checkout-service
  revision: 9f3a2c1d4e5f60718293a4b5c6d7e8f901234567
  digest: sha256:<immutable-build-digest>
  environment: production
  owner: <release-owner-handle>
  change_summary: "Add idempotent payment retry with exponential backoff"
  blast_radius: "checkout-service pods; shared payments Postgres (read-only)"

approvals:
  code_review: "PR-4821 approved"
  migration_review: "not required (no schema change)"
  security_review: "not required (no new data flows)"

preflight:
  - verify digest matches CI build output for revision
  - confirm tests green at revision: unit, integration, contract
  - diff staging vs production configuration; expect zero unexplained deltas
  - confirm feature flag payment_retry_v2 exists and defaults to disabled
  - confirm capacity headroom >= 30% on CPU and connection pool
  - confirm on-call operator and observer assignments

rollout:
  strategy: canary
  operator: <operator-handle>
  observer: <observer-handle>
  stages:
    - name: canary-5
      traffic_percent: 5
      observation_window_minutes: 30
      gates: [error_rate, latency_p95, dependency_health]
    - name: canary-25
      traffic_percent: 25
      observation_window_minutes: 30
      gates: [error_rate, latency_p95, business_kpi]
    - name: canary-50
      traffic_percent: 50
      observation_window_minutes: 20
      gates: [error_rate, latency_p95]
    - name: full
      traffic_percent: 100
      observation_window_minutes: 60
      gates: [error_rate, latency_p95, latency_p99, saturation, business_kpi, dependency_health]

signals:
  error_rate: 'sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))'
  latency_p95: 'histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))'
  dependency_health: 'up{job="payments-gateway"} == 1'
  business_kpi: 'rate(checkout_completed_total[10m]) >= 0.95 * baseline'

abort_thresholds:
  error_rate_max: 0.01
  latency_p95_max_ms: 500
  latency_p99_max_ms: 1500
  business_kpi_drop_max: 0.05

halt_authority: [<operator-handle>, <observer-handle>, <on-call-commander>]
halt_procedure:
  - freeze traffic weight at the current value; do not continue expansion
  - snapshot metrics, logs, and pod state before any restart
  - page the halt authority list with the evidence bundle

rollback:
  type: revert_deployment
  rto_minutes: 15
  steps:
    - kubectl rollout undo deployment/checkout-service
    - kubectl rollout status deployment/checkout-service --timeout=600s
    - disable feature flag payment_retry_v2
    - verify error_rate and latency_p95 return to baseline within 10 minutes
  forward_fix_fallback: "if rollback breaks queue consumers, roll forward with branch hotfix/payment-retry-compat"
  data_compatibility: "no schema change; new code tolerates old rows and old code tolerates new events"
```

---

## 4. Health-Check Verification Pattern & Rollback Drill

The observer executes this command set verbatim at every stage gate. Any gate
failure triggers the halt procedure, then the rollback steps.

```bash
NAMESPACE="production"; DEPLOY="checkout-service"

# 1. Rollout progress and pod health
kubectl -n "$NAMESPACE" rollout status "deployment/$DEPLOY" --timeout=300s
kubectl -n "$NAMESPACE" get pods -l app="$DEPLOY" -o wide

# 2. HTTP health probe through the public seam
curl -fsS -o /dev/null -w 'status=%{http_code} latency=%{time_total}s\n' \
  https://api.example.com/healthz

# 3. Error-rate gate: exits non-zero when the abort threshold is exceeded
ERROR_RATE=$(curl -fsS '<metrics-endpoint>/api/v1/query' \
  --data-urlencode 'query=sum(rate(http_requests_total{status=~"5.."}[5m]))/sum(rate(http_requests_total[5m]))' \
  | jq -r '.data.result[0].value[1]')
if awk -v r="$ERROR_RATE" 'BEGIN { exit !(r < 0.01) }'; then
  echo "GATE PASS: error_rate=$ERROR_RATE"
else
  echo "GATE FAIL: error_rate=$ERROR_RATE >= 0.01 — halt and roll back"
fi
```

### Rollback Drill Checklist (staging, before production authorization)

- [ ] Roll forward to the candidate revision, execute `kubectl rollout undo`,
      and measure time-to-baseline.
- [ ] Confirm measured rollback time is within the RTO (default 15 minutes);
      record the actual value.
- [ ] Verify the old revision serves new-format data correctly (backward
      compatibility proof).
- [ ] Verify the feature-flag disable path works without a redeploy.
- [ ] Confirm the halt procedure preserves logs and metrics snapshots.
- [ ] Record drill evidence (timestamps, command output) in the deployment
      handoff.

---

## 5. Abort Threshold, Cohort Sizing & RTO Mathematics

$$\text{Abort} = \left( \frac{\#\{r : \text{status}(r) \ge 500\}}{\#\{r\}} > \tau_{\text{err}} \right) \;\lor\; \left( P95(t_{\text{req}}) > \tau_{p95} \right) \;\lor\; \left( \text{KPI} < (1 - \tau_{\text{kpi}}) \times \text{baseline} \right)$$

$$\text{cohorts} = [c_1, c_2, \dots, c_n] = [5\%, 25\%, 50\%, 100\%], \qquad \text{promote}(c_i \to c_{i+1}) \Rightarrow \bigwedge_{s \in \text{gates}(c_i)} \text{pass}(s) \;\wedge\; t_{\text{observe}}(c_i) \ge t_{\min}$$

$$\text{RTO} = t_{\text{rollback\_complete}} - t_{\text{abort\_decision}} \;\le\; 15\,\text{min}$$

$$\forall\, \text{stage } s: \quad \text{execute}(s) \Rightarrow \text{evidence}(s) \;\wedge\; \text{timestamp}(s) \;\wedge\; \text{operator}(s) \text{ recorded}$$

---

## 6. Guardrails

### Operational Restrictions

- **Explicit Authorization**: Do **NOT** deploy to production, rotate
  credentials, or run destructive commands without explicit authorization.
  Execute only the authorized scope; expanding beyond it requires new
  authorization recorded in the plan.
- **Backward-Compatible Change Shape**: Prefer backward-compatible
  expand-and-contract changes when old and new versions overlap in
  production.
- **No Assumed Schema Safety**: Never assume a schema rollback is
  automatically safe; rehearse it or document the forward-fix path.
- **Single-Agent Executable**: Optional release-engineer delegation can
  accelerate preparation; one agent can complete this workflow independently.

### Security Invariants

- **Secret-Free Artifacts**: Keep secrets out of plans, logs, screenshots,
  and chat transcripts. Reference secrets by environment variable or vault
  path name only — never by value.
- **Sanitized Evidence**: Evidence bundles must be sanitized before sharing:
  redact tokens, session identifiers, and customer payloads.
- **Authenticated Tooling Only**: Deployment credentials are used only
  through the platform's authenticated tooling. Never echo kubeconfig
  contents or cloud tokens into plan documents or terminal logs shared in
  the handoff.

---

## 7. Atomic Failure Recovery & Rollback Handler

Two rollback layers exist and must not be conflated: **repository rollback**
(files created or modified while authoring the plan) and **deployment
rollback** (platform state changed during authorized execution). Before
creating or modifying files, capture a baseline list of modified and
untracked files. If any verification command in Section 8 fails and cannot be
resolved within 2 iterations, execute targeted repository rollback restricted
ONLY to files created or modified during this run:

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

For deployment rollback, execute the plan's `rollback.steps` exactly as
written and verify time-to-baseline against the RTO. Never roll back a
deployment that was not part of the authorized scope, and never improvise
platform actions outside the plan. After either rollback, output the exact
error trace and state failure causes.

---

## 8. Verification Plan & Deployment Toolchain Commands

Execute the following commands using project-local runners; adapt to the
project's declared deployment platform:

```bash
# 1. Confirm artifact traceability: digest matches CI build for the revision
kubectl get deployment checkout-service -o jsonpath='{.spec.template.spec.containers[0].image}'

# 2. Confirm tests pass at the release revision
npm run test

# 3. Rehearse rollback in staging and measure time-to-baseline
kubectl rollout undo deployment/checkout-service --namespace=staging
kubectl rollout status deployment/checkout-service --namespace=staging --timeout=600s

# 4. Execute the stage-gate health checks (Section 4) at the current cohort
curl -fsS -o /dev/null -w 'status=%{http_code} latency=%{time_total}s\n' https://api.example.com/healthz

# 5. Confirm the plan document contains no secret values before sharing
grep -nEi '(password|token|secret|api[_-]?key): *[^< ]' rollout-plan.yaml \
  && echo "REDACT BEFORE SHARE" || echo "CLEAN"
```

---

## 9. Completion Report

Report the artifact and revision with digest, environments touched, preflight
checks with evidence, rollout gates and observed signal values at each
cohort, abort threshold evaluations, rollback readiness with drill evidence
(including measured time-to-baseline against the RTO), exact commands
executed with timestamps, operator and observer identities, and anything left
unverified.
