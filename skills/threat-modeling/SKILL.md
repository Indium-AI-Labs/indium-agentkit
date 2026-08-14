---
name: threat-modeling
description: "Perform structured threat modeling (STRIDE/PASTA) on architecture diagrams, system interfaces, and data flow graphs before implementation."
---

# Threat Modeling

Identify security threats, attack vectors, trust boundaries, and mitigation
controls **before** feature development or architectural overhaul. The
baseline taxonomy is STRIDE (Spoofing, Tampering, Repudiation, Information
Disclosure, Denial of Service, Elevation of Privilege); PASTA-style attacker
and impact staging may supplement it when the project requires risk-centric
scoring.

The skill is **pre-implementation and evidence-backed**: threats are derived
from architecture diagrams, data flow graphs, API specifications, and auth
models that actually exist in the repository, never from speculative
scenarios. Every enumerated threat receives a likelihood/impact rating, a
concrete mitigation, and a verification test. Adapt the documentation format
to the project's architecture artifacts and record results in
`templates/handoffs/threat-model.md`.

---

## 1. Required I/O Context Schemas & Natural Language Auto-Inference

The skill supports **two invocation modes**:

1. **Orchestrator / Technical Mode (JSON Manifest)**: Pass the JSON context
   manifest below.
2. **Non-Technical Mode (Plain English Prompts)**: If the user provides a
   natural language prompt (e.g. *"Threat-model the new checkout flow from
   browser through our API to the payments provider"*), the agent **must
   automatically infer and populate** `system_spec`, `boundary_context`, and
   `methodology_context` from the user's text and from repository evidence.

### JSON Context Manifest Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "ThreatModelingContextManifest",
  "type": "object",
  "required": ["system_spec", "boundary_context", "methodology_context"],
  "properties": {
    "system_spec": {
      "type": "object",
      "required": ["components", "data_stores"],
      "properties": {
        "components": { "type": "array", "items": { "type": "string" }, "minItems": 1 },
        "data_stores": { "type": "array", "items": { "type": "string" }, "minItems": 1 },
        "externals": { "type": "array", "items": { "type": "string" }, "default": [] },
        "assets": { "type": "array", "items": { "type": "string" }, "minItems": 1 }
      }
    },
    "boundary_context": {
      "type": "object",
      "required": ["trust_boundaries"],
      "properties": {
        "trust_boundaries": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["from", "to"],
            "properties": {
              "from": { "type": "string", "minLength": 1 },
              "to": { "type": "string", "minLength": 1 },
              "channel": { "type": "string", "enum": ["public_internet", "internal_network", "process_local", "third_party_api"] },
              "data_classes": { "type": "array", "items": { "type": "string", "enum": ["pii", "payment", "health", "credentials", "public"] } }
            }
          },
          "minItems": 1
        }
      }
    },
    "methodology_context": {
      "type": "object",
      "required": ["taxonomy", "scoring"],
      "properties": {
        "taxonomy": { "type": "string", "enum": ["stride", "pasta", "stride_with_pasta_scoring"], "default": "stride" },
        "scoring": { "type": "string", "enum": ["dread", "cvss", "project_defined"], "default": "dread" },
        "risk_threshold": { "type": "number", "minimum": 0, "default": 3.0 }
      }
    }
  }
}
```

### Automatic Natural Language Inference & Safety Rules

If no raw JSON payload is provided, apply these defaults and safety checks:

- **`system_spec.components`**: Extracted from the prompt nouns and confirmed
  against the repository (routes, services, workers, frontends). Components
  that cannot be confirmed from code or docs are marked assumed, not
  silently invented.
- **`data_stores`**: Detected from ORM configuration, connection modules,
  cache clients, and bucket references in the scoped code paths.
- **`externals`**: Detected from outbound HTTP clients, SDK imports, and
  webhook registrations in scope (payment providers, email services,
  identity providers).
- **`assets`**: Derived from the data classes the scoped components handle:
  account records, credentials, payment instruments, session tokens.
- **`trust_boundaries`**: Enumerated from actual crossings: browser to API,
  API to database, API to third-party, job runner to queue. Every component
  pair that exchanges data across a trust level must appear; an empty
  boundary list is invalid.
- **`methodology_context`**: Defaults to `stride` taxonomy with `dread`
  scoring. Reuse a project-defined scoring model when the repository or
  security policy declares one; never invent a new scale mid-review.
- **Evidence rule**: If no architecture documentation exists, build the data
  flow graph from code and say so explicitly; do not present inferred
  structure as documented fact.

---

## 2. Deterministic State Machine Execution Flow

Follow this exact sequential protocol. Do not skip steps or alter execution
ordering.

### Step 1: Context Ingestion & Architecture Recon

1. Read `AGENTS.md`, system architecture documentation, data flow diagrams,
   API specs, and auth models present in the repository.
2. Map key assets, data stores, external dependencies, and deployment
  topology for the scoped system.
3. Where documentation is stale or missing, reconstruct the data flow graph
   from code (routes, clients, queries) and flag each reconstructed edge as
   code-derived evidence.

### Step 2: Asset & Data Classification

1. List the assets worth attacking: data records, credentials, sessions,
   money movement, admin capabilities, availability of the service itself.
2. Classify data crossing each edge: `pii`, `payment`, `health`,
   `credentials`, or `public`, using the project's data classification
   policy where one exists.
3. Rank assets by business impact so scoring in Step 5 reflects real
   consequences rather than abstract severity.

### Step 3: Trust Boundary Enumeration

1. Identify trust boundaries: every point where data passes between
   different levels of trust (e.g. browser to web server, web server to
   database, internal service to third-party API, job runner to queue).
2. For each boundary, record the channel (`public_internet`,
   `internal_network`, `process_local`, `third_party_api`), the
   authentication mechanism on the crossing, and the data classes carried.
3. Verify completeness: every component pair in the data flow graph that
   crosses a trust level must be represented as a boundary. The coverage
   invariant in Section 5 makes this checkable.

### Step 4: STRIDE Threat Enumeration per Boundary

Enumerate threats across each trust boundary using STRIDE:

- **Spoofing**: Can an attacker impersonate a user, service, or the
  third-party endpoint on this crossing?
- **Tampering**: Can data in transit or at rest be modified without
  authorization (payload edits, row updates, queue message flips)?
- **Repudiation**: Can an actor perform an action without audit trail proof
  tying the action to their identity?
- **Information Disclosure**: Can sensitive data be leaked through
  responses, errors, logs, caches, or side channels on this crossing?
- **Denial of Service**: Can resources be exhausted or rendered unavailable
  (unbounded payloads, expensive queries, retry storms, quota abuse)?
- **Elevation of Privilege**: Can an unprivileged actor gain privileged
  control across this boundary (role confusion, missing object-level checks,
  confused deputies)?

Record only threats backed by architectural evidence: a real crossing, a
real data class, and a plausible attacker. Speculative or irrelevant
vulnerability scenarios are excluded.

### Step 5: Risk Scoring & Prioritization

1. Rate each threat's likelihood and impact using the declared scoring model
   (DREAD average or CVSS base score) per the formulas in Section 5.
2. Sort threats by composite risk; anything at or above `risk_threshold`
   requires a mitigation before implementation proceeds.
3. Reuse the project's existing risk scale when one is defined; document the
   scale used so scores are comparable across models.

### Step 6: Mitigation Control Design

1. Formulate concrete mitigation controls for each threat at or above the
   threshold: mTLS, request signing, rate limiting, role-based access
   control, input sanitization, audit logging, token expiry, schema
   validation.
2. Every mitigation must be implementable in this repository and must map to
   a specific component and boundary; "add more security" is not a control.
3. Prefer controls that fail closed and that are verifiable by an automated
   test (Section 4).

### Step 7: Residual Risk & Verification Follow-up

1. Document residual risk for each threat after mitigation: what remains,
   why it is accepted, and who accepts it.
2. Define the follow-up verification tests that will prove each mitigation
   works (penetration-style unit tests, integration checks, config audits).
3. Record open questions that need security-team or stakeholder decisions
   before implementation begins.

### Step 8: Record Findings in the Threat-Model Handoff

1. Record the completed model in `templates/handoffs/threat-model.md` or the
   equivalent project artifact, following that template's sections.
2. Ensure the artifact is self-contained: a reader can reconstruct the
   boundaries, threats, scores, mitigations, and residual risks without
   rerunning the analysis.
3. Link (by path reference in backticks, not hyperlink) the handoff from the
   feature brief or implementation plan it gates.

---

## 3. Reference Implementation: Completed Threat Model Document

```yaml
# Threat model: checkout flow (browser -> API -> DB -> payments provider).
# Artifact format follows templates/handoffs/threat-model.md.
threat_model:
  id: TM-2026-007-checkout-flow
  date: 2026-08-14
  methodology: stride_with_pasta_scoring
  scoring: dread
  risk_threshold: 3.0
  author: threat-modeling skill (single agent)

system:
  components: [web-browser-spa, checkout-api, order-db, payments-provider]
  data_stores: [order-db (postgres), session-cache (redis)]
  externals: [payments-provider]
  assets: [payment-instruments, order-records, session-tokens, admin-console]

trust_boundaries:
  - id: TB-1
    from: web-browser-spa
    to: checkout-api
    channel: public_internet
    data_classes: [payment, pii, credentials]
    auth: bearer session token (httpOnly cookie)
  - id: TB-2
    from: checkout-api
    to: order-db
    channel: internal_network
    data_classes: [payment, pii]
    auth: database role checkout_rw (least privilege)
  - id: TB-3
    from: checkout-api
    to: payments-provider
    channel: third_party_api
    data_classes: [payment]
    auth: API key in secret store, TLS 1.3, signed webhooks inbound

threats:
  - id: T-1
    boundary: TB-1
    stride: Spoofing
    threat: Attacker replays or forges a session token to place orders as
            another user.
    evidence: Login issues 24h tokens; checkout-api accepts any unexpired
              token without binding to device or rotation.
    dread: { damage: 4, reproducibility: 3, exploitability: 3, affected: 4, discoverability: 2 }
    risk: 3.2
    mitigations:
      - control: Rotate session tokens on checkout start; bind to cart id.
        component: checkout-api
        verify: Integration test rejects pre-rotation token at /checkout/confirm.
    residual: Token theft via XSS remains; accepted pending CSP hardening
              ticket SEC-118.

  - id: T-2
    boundary: TB-2
    stride: Tampering
    threat: SQL injection in order notes mutates other tenants' rows.
    evidence: orders.notes concatenated into a raw UPDATE in
              src/repos/orders.ts (code-derived edge).
    dread: { damage: 5, reproducibility: 4, exploitability: 3, affected: 5, discoverability: 3 }
    risk: 4.0
    mitigations:
      - control: Parameterize the update through the query builder; add
                 tenant predicate to every order mutation.
        component: checkout-api
        verify: Security unit test with metacharacter payload mutates zero
                rows; pg audit shows parameterized statements only.
    residual: None identified after parameterization.

  - id: T-3
    boundary: TB-3
    stride: Repudiation
    threat: Disputed charge cannot be tied to a user action.
    evidence: No audit event links checkout confirmation to provider
              charge id.
    dread: { damage: 3, reproducibility: 4, exploitability: 2, affected: 3, discoverability: 4 }
    risk: 3.2
    mitigations:
      - control: Write immutable audit row (actor, cart, charge id, hash
                 chain) before calling the provider.
        component: checkout-api
        verify: Test asserts audit row exists for every successful charge.
    residual: Provider-side logs remain the system of record for disputes.

  - id: T-4
    boundary: TB-1
    stride: DenialOfService
    threat: Unbounded checkout attempts exhaust payments-provider quota.
    evidence: No rate limit on POST /checkout/confirm.
    dread: { damage: 3, reproducibility: 5, exploitability: 4, affected: 4, discoverability: 4 }
    risk: 4.0
    mitigations:
      - control: Per-user and per-IP rate limit (10/min) with 429 envelope;
                 circuit breaker on provider 5xx.
        component: checkout-api
        verify: Load test at 100 rps sustains quota; breaker opens in test.
    residual: Distributed abuse above limits needs WAF rule (ops follow-up).
```

---

## 4. Mitigation-to-Test Mapping & Residual-Risk Sign-Off Pattern

Every mitigation declared in the model must map to a concrete verification
test, and every residual risk must carry an explicit sign-off. Unmapped
mitigations block the model from closing.

```bash
# Mitigation-to-test mapping ledger (one line per mitigation).
cat > threat-model-verification.tsv <<'EOF'
threat_id	mitigation	test_artifact	test_type	status
T-1	rotate session tokens at checkout start	tests/security/session-rotation.test.ts	integration	pending
T-2	parameterize order mutations + tenant predicate	tests/security/order-injection.test.ts	unit	pending
T-3	immutable audit row before provider call	tests/security/charge-audit.test.ts	integration	pending
T-4	rate limit + provider circuit breaker	load/checkout-confirm.k6.js	load	pending
EOF

# Residual-risk sign-off record (appended to the threat-model handoff).
cat >> threat-model-signoff.md <<'EOF'
## Residual risk sign-off
- T-1 residual: session theft via XSS. Accepted by: <security-owner>.
  Compensating follow-up: SEC-118 CSP hardening, due next release.
- T-3 residual: provider-side dispute logs. Accepted by: <product-owner>.
- T-4 residual: distributed abuse above app limits. Accepted by: <ops-owner>.
  Compensating follow-up: WAF rule request NET-204.

Sign-off rule: every residual risk names an accountable owner and either an
acceptance rationale or a tracked follow-up item. Blank sign-offs are
treated as unmitigated threats at their original score.
EOF

# Coverage check: every trust boundary enumerated has at least one threat,
# and every threat at/above threshold has at least one mapped test.
python - <<'PY'
import csv, sys
rows = list(csv.DictReader(open("threat-model-verification.tsv"), delimiter="\t"))
assert all(r["test_artifact"] for r in rows), "unmapped mitigation found"
print(f"coverage ok: {len(rows)} mitigations mapped to tests")
PY
```

---

## 5. Risk, Scoring & Coverage Invariants

Composite risk is the product of likelihood and impact; prioritization sorts
by this product and mitigation is mandatory at or above the threshold
$\theta$:

$$\text{Risk}(t) = \text{Likelihood}(t) \times \text{Impact}(t), \qquad \text{Risk}(t) \ge \theta \Rightarrow \text{mitigationRequired}(t)$$

DREAD scoring averages the five factors, each rated on the project's scale
(1-5 by default):

$$\text{DREAD}(t) = \frac{D + R + E + A + Di}{5}$$

Boundary coverage is total: every enumerated trust boundary contributes at
least one evidenced threat assessment (a confirmed "no threat found, with
reasons" entry counts as an assessment):

$$\forall b \in \text{TrustBoundaries}: \; \#\{t \in \text{Threats} : t.\text{boundary} = b\} \ge 1$$

Mitigation traceability is total for in-scope risks: every threat at or
above the threshold maps to at least one verification test:

$$\forall t : \text{Risk}(t) \ge \theta \Rightarrow \exists\, v \in \text{Tests} : v.\text{covers}(t)$$

---

## 6. Guardrails

### Operational Restrictions

- **Evidence-Backed Threats Only**: Focus on actionable threats backed by
  architectural evidence; avoid speculative or irrelevant vulnerability
  scenarios. A threat without a real crossing, data class, and attacker is
  excluded or explicitly marked as an open question.
- **Pre-Implementation Timing**: Run the model before feature development or
  architectural overhaul; a model produced after implementation is a
  review, not a threat model, and should route to the `security-review`
  workflow instead.
- **Complete Boundary Enumeration**: Enumerate every trust boundary in the
  data flow graph before scoring; do not score threats against a partial
  graph.
- **Reuse Project Scales**: Use the project's declared scoring model and
  risk threshold when they exist; never mix scales within one model.
- **Single-Agent Executable**: An optional security-reviewer subagent can
  inspect data flow graphs for a second pass, but one agent can complete
  this workflow independently.

### Security Invariants

- **No Live Exploitation**: Do not execute penetration tests or exploits
  against live systems. Threats are reasoned from architecture and code
  evidence; validation happens through scoped tests, not attacks.
- **No Secret Material in Models**: Never record real credentials, keys, or
  tokens in the threat model; reference secret-store entries with
  `<placeholder>` names only.
- **Data Minimization in Artifacts**: The model names data classes and
  flows, not production records; never paste customer data, real payloads,
  or internal identifiers beyond what the trace requires.
- **Honest Residual Risk**: Residual risk is recorded with an accountable
  owner; the model never claims all threats are eliminated.

---

## 7. Atomic Failure Recovery & Rollback Handler

Threat modeling writes only analysis artifacts (the threat-model handoff,
verification ledgers, sign-off records); it never modifies system code. If
artifact generation fails or produces an inconsistent document that cannot
be repaired within 2 iterations, execute targeted rollback restricted ONLY
to files created or modified during this run:

```bash
# Revert ONLY modified files tracked during this execution run
# (normally none: the workflow edits no system code)
if [ -n "${MODIFIED_FILES:-}" ]; then
  git checkout -- ${MODIFIED_FILES} 2>/dev/null
fi

# Remove ONLY newly created untracked artifacts from this execution run
# (e.g. the partial threat-model handoff and scratch ledgers)
if [ -n "${CREATED_FILES:-}" ]; then
  rm -rf ${CREATED_FILES} 2>/dev/null
fi
```

After executing targeted rollback, confirm the repository contains no
partial model artifacts from this run, then output the exact error trace
and state failure causes. Never delete prior threat-model versions or
sign-off records that predate this run.

---

## 8. Verification Plan & Analysis Toolchain Commands

Execute the following read-only commands to build and validate the model;
adapt tool names to the project's declared scripts:

```bash
# 1. Reconstruct the data flow surface from code evidence
rg -n "fetch\(|axios|grpc|amqp|pg\.|redis\." src/ --glob '!*.test.*'
rg -n "router\.(get|post|put|patch|delete)" src/routes/

# 2. Enumerate authentication and authorization controls per component
rg -n "requireAuth|verifyToken|mTLS|signing|authorize" src/

# 3. Confirm external dependencies and outbound channels
rg -n "https?://" src/ --glob '!*.test.*' | rg -v "localhost|example"

# 4. Validate the handoff artifact structure against the template
python scripts/validate_handoff.py templates/handoffs/threat-model.md

# 5. Run the mitigation-to-test coverage check (Section 4)
python scripts/check_threat_coverage.py threat-model-verification.tsv  # or inline python heredoc

# 6. Re-run after implementation begins: tests mapped in the ledger must
#    exist and pass before the model is marked closed.
npm run test -- tests/security/
```

---

## 9. Completion Report

Report the system scope and evidence sources used (documents read, code
paths reconstructed); the assets mapped with their data classifications; the
trust boundaries evaluated with channels and auth mechanisms; the threats
enumerated by STRIDE category per boundary with their evidence; the risk
ratings and the scoring scale applied; the proposed mitigations with their
component owners and mapped verification tests; the residual risks with
accountable sign-offs; the open questions escalated for decision; and the
location of the recorded handoff artifact (`templates/handoffs/threat-model.md`
or the project equivalent).
