---
name: security-review
description: "Review a scoped code change, endpoint, integration, configuration, or infrastructure definition for security risks by tracing assets, trust boundaries, authorization, input handling, and exploit paths."
---

# Security Review

Perform a **read-only** security review of a scoped change: a diff, an
endpoint, an integration, a configuration change, or an infrastructure
definition. The review traces assets, trust boundaries, authorization
decisions, input handling, and exploit paths, and produces an evidenced
findings register rather than generic advice.

The default stance is **evidence over speculation**: every reported finding
names a concrete location, an exploit condition, and a verification step.
The review never claims compliance and never claims the absence of
vulnerabilities; it reports what was examined, what was found, and what was
not covered. Adapt checklist depth and tooling to the repository's stack,
policies, and existing security controls.

---

## 1. Required I/O Context Schemas & Natural Language Auto-Inference

The skill supports **two invocation modes**:

1. **Orchestrator / Technical Mode (JSON Manifest)**: Pass the JSON context
   manifest below.
2. **Non-Technical Mode (Plain English Prompts)**: If the user provides a
   natural language prompt (e.g. *"Review the new webhook endpoint in
   `src/routes/webhooks.ts` for security issues"*), the agent **must
   automatically infer and populate** `review_scope`, `threat_context`, and
   `policy_context` from the user's text and from repository evidence.

### JSON Context Manifest Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "SecurityReviewContextManifest",
  "type": "object",
  "required": ["review_scope", "threat_context"],
  "properties": {
    "review_scope": {
      "type": "object",
      "required": ["target_type", "refs"],
      "properties": {
        "target_type": { "type": "string", "enum": ["diff", "endpoint", "integration", "config", "iac"] },
        "refs": { "type": "array", "items": { "type": "string" }, "minItems": 1 },
        "commit_range": { "type": "string", "pattern": "^[0-9a-f]{7,40}(\\.\\.[0-9a-f]{7,40})?$" },
        "out_of_scope": { "type": "array", "items": { "type": "string" }, "default": [] }
      }
    },
    "threat_context": {
      "type": "object",
      "required": ["assets", "attackers", "trust_boundaries"],
      "properties": {
        "assets": { "type": "array", "items": { "type": "string" }, "minItems": 1 },
        "attackers": { "type": "array", "items": { "type": "string", "enum": ["anonymous_external", "authenticated_user", "malicious_insider", "compromised_dependency", "compromised_third_party"] }, "minItems": 1 },
        "trust_boundaries": { "type": "array", "items": { "type": "string" }, "minItems": 1 }
      }
    },
    "policy_context": {
      "type": "object",
      "properties": {
        "sensitive_data_classes": { "type": "array", "items": { "type": "string", "enum": ["pii", "payment", "health", "credentials", "none"] } },
        "crypto_policy": { "type": "string" },
        "severity_model": { "type": "string", "enum": ["cvss_like_bands", "project_defined"], "default": "cvss_like_bands" }
      }
    }
  }
}
```

### Automatic Natural Language Inference & Safety Rules

If no raw JSON payload is provided, apply these defaults and safety checks:

- **`review_scope.target_type`**: Inferred from the prompt artifact: a pull
  request or commit range maps to `diff`; a route file maps to `endpoint`; a
  third-party client or webhook maps to `integration`; environment or flag
  changes map to `config`; Terraform, Kubernetes, or pipeline definitions
  map to `iac`.
- **`refs`**: Extracted from file paths, branch names, or commit ranges in
  the prompt. Validate that every ref exists in the repository before
  reviewing; **ABORT and ask** if the scope cannot be resolved.
- **`assets`**: Derived from what the scoped code touches: records read or
  written, credentials handled, files accessed, network calls made.
- **`attackers`**: Defaults to `["anonymous_external", "authenticated_user"]`
  for internet-facing surfaces; add `malicious_insider` for admin tooling
  and `compromised_third_party` for integrations.
- **`trust_boundaries`**: Enumerated from the code path: client-to-server,
  server-to-database, server-to-third-party, process-to-secret-store.
- **`policy_context`**: Reuse the project's existing security policy,
  sensitive-data classification, and crypto standards. Never invent a new
  severity taxonomy when the project already defines one.
- **Read-only invariant**: Inference never modifies the reviewed code. The
  only writable artifact is the findings report, written only when the user
  asks for a persisted report.

---

## 2. Deterministic State Machine Execution Flow

Follow this exact sequential protocol. Do not skip steps or alter execution
ordering.

### Step 1: Scope Definition & Security Assumption Capture

1. Read `AGENTS.md`, the scoped refs, and the surrounding modules the scope
   interacts with (callers, callees, middleware, configuration).
2. Define the review scope explicitly: included files, endpoints, and commit
   ranges, plus an explicit out-of-scope list.
3. Record security-relevant assumptions (network exposure, authentication
   presence, deployment environment) so findings can be evaluated against
   stated conditions rather than guesses.

### Step 2: Asset, Attacker & Trust Boundary Mapping

1. Enumerate the assets the scope can touch: data records, credentials,
   files, money movement, identity assertions, infrastructure permissions.
2. Enumerate plausible attackers for each asset from `threat_context`.
3. Mark every trust boundary the scoped data crosses; each boundary crossing
   is a candidate exploit path and must be traced in Steps 3 and 4.

### Step 3: Taint Trace — Untrusted Input to Sensitive Sinks

1. Identify every source of untrusted input in scope: request bodies, query
   parameters, headers, path segments, webhook payloads, file uploads,
   environment values, third-party responses, and decoded tokens.
2. Trace each source through parsing, transformation, storage, and
   concatenation until it reaches a sink: SQL construction, HTML rendering,
   shell execution, file-system paths, redirect targets, deserialization,
   template evaluation, or log emission.
3. At each hop, record whether validation, escaping, or parameterization
   breaks the trace. A source-to-sink path with no effective control is a
   candidate finding with a concrete exploit condition.

### Step 4: Authorization Trace — Identity to Protected Action

1. For every protected action in scope, trace how identity is established
   (session, token, signature) and where the authorization decision is made.
2. Verify the decision happens on the server, covers object-level ownership
   and tenant scope (not only route-level role checks), and fails closed.
3. Check for confused-deputy paths: internal calls that drop the original
   caller context, and privileged helpers reachable without re-checking
   authorization.

### Step 5: Control Surface Checklist Sweep

Check each area **as relevant to the scope**; record "checked, not
applicable" explicitly rather than omitting silently:

1. **Secrets handling**: no hardcoded credentials, no secrets in logs,
   environment access scoped, rotation compatible.
2. **Authentication**: token validation, expiry, audience and issuer checks,
   signature algorithm allowlist.
3. **Authorization**: server-enforced, object-level, tenant-scoped,
   fail-closed defaults.
4. **Logging and error disclosure**: no stack traces, SQL, or internal
   identifiers in responses; audit events for security-relevant actions.
5. **Cryptography**: approved algorithms and key sizes per project policy,
   correct nonce/IV usage, no homegrown constructions, TLS everywhere.
6. **Dependency use**: newly introduced packages pinned, vulnerability
   status checked, no abandoned or typosquatted packages.
7. **Infrastructure permissions**: least-privilege IAM, network exposure
   minimized, public access blocked unless intended and documented.

### Step 6: Finding Triage & Prioritization

1. Keep only findings that are **exploitable and evidenced**: a concrete
   location plus a plausible attacker plus a working exploit condition.
2. Discard or downgrade speculative issues ("could theoretically") that lack
   a reachable path; note them as observations, not findings.
3. Rank findings by exploitability multiplied by impact (Section 5), not by
   checklist order or personal preference.

### Step 7: Findings Register Authoring

1. Report each finding with: severity, affected location (file, line,
   symbol), exploit conditions, impact, remediation direction, and the
   verification needed to confirm a fix.
2. Use the severity taxonomy in Section 4; never inflate severity to force
   attention, never deflate it to close the review faster.
3. State explicitly what was reviewed, what assumptions held, and which
   areas were not covered. **Do not claim compliance or absence of
   vulnerabilities.**

### Step 8: Read-Only Boundary & Optional Second Pass

1. Keep review mode read-only unless the user explicitly asks for
   remediation. Do not patch, refactor, or "improve" reviewed code.
2. For high-risk changes (auth, payments, permission models), an independent
   security-reviewer subagent may run a second pass over the same evidence;
   one agent must still be able to complete this workflow independently.
3. Deliver the register, the coverage statement, and the residual-risk note
   as the review output.

---

## 3. Reference Implementation: Findings Register & Annotated Taint Trace

```markdown
# Security review findings register
scope: diff main..feature/webhook-receivers (src/routes/webhooks.ts, src/lib/signature.ts)
reviewed_at: 2026-08-14
reviewer: security-review skill (single agent)

| ID  | Severity | Location                        | Exploit conditions                                   | Impact                                   | Remediation direction                              | Verification                          |
|-----|----------|---------------------------------|------------------------------------------------------|------------------------------------------|----------------------------------------------------|---------------------------------------|
| F-1 | Critical | webhooks.ts:41 handleStripe()   | Attacker replays a captured event; no timestamp check| Forge payment-confirmation state changes | Enforce signature timestamp tolerance (<= 5 min)   | Rejected replay test passes           |
| F-2 | High     | signature.ts:18 verifyHmac()    | timingSafeEqual skipped on length mismatch           | Byte-by-byte signature oracle            | Compare digests of equal length only               | Unit test with mismatched lengths     |
| F-3 | Medium   | webhooks.ts:57 error response   | Raw provider error body echoed to caller             | Internal identifier disclosure           | Map to shared error envelope; log details server-side| 4xx body contains no provider text  |
| F-4 | Low      | webhooks.ts:12 raw body limit   | No explicit body size cap on webhook route           | Memory pressure via oversized payloads   | Set explicit limit (e.g. 256 KB) per route         | Oversized payload returns 413         |

## Annotated taint trace (F-1)

Source: `req.body` in `handleStripe()` — attacker-controlled POST payload.
  hop 1: `JSON.parse(rawBody)`                    -> no schema validation
  hop 2: `event.data.object.customer_id`          -> used verbatim
  hop 3: `db.subscriptions.activate(customer_id)` -> SINK: state mutation

Control analysis: `verifyHmac(rawBody, signatureHeader)` authenticates the
payload but performs no timestamp or nonce check, so a previously captured,
validly signed event replays indefinitely. The source-to-sink path is
reachable by `anonymous_external` with a single captured request.

Exploit condition: attacker obtains one legitimate webhook delivery (e.g.
from a compromised log sink or an earlier misconfiguration) and re-POSTs it.

Evidence: `signature.ts` lines 10-24 contain no `timestamp` reference; the
route at `webhooks.ts:41` calls the sink unconditionally after verifyHmac.
```

---

## 4. Fix Verification & Severity Taxonomy Pattern

Every finding must name how its fix will be verified. Verification is
layered: a focused regression test, a re-scan of the same trace, and a
manual re-walk of the exploit path.

```bash
# Verification pattern for a fixed finding (F-1 replay example).

# 1. Focused regression test: the exploit condition now fails closed.
npx --no-install vitest run tests/security/webhook-replay.test.ts
#    Expected: replayed event with stale timestamp -> 400 REPLAY_REJECTED.

# 2. Re-scan the original trace with the same search that surfaced it.
rg -n "verifyHmac" src/ --context 6
#    Expected: timestamp tolerance check present at the verifier.

# 3. Re-run the project's security lint and dependency audit.
npm run lint
npm audit --audit-level=high

# 4. Manual re-trace: walk source -> sink again and confirm the control
#    breaks the path at every recorded hop. Record the re-trace date and
#    result in the findings register next to the finding ID.

# Severity taxonomy (CVSS-like bands; use project-defined bands if present):
#   Critical: 9.0 - 10.0  remote, unauthenticated, direct asset compromise
#   High:     7.0 - 8.9   remote with low complexity, or auth bypass
#   Medium:   4.0 - 6.9   meaningful preconditions or limited impact
#   Low:      0.1 - 3.9   hard to exploit or negligible impact
#   Info:     0.0         hardening observation, not an exploitable finding
```

A finding is closed only when its regression test passes, the re-scan shows
the control in place, and the manual re-trace no longer reaches the sink.

---

## 5. Exploitability, Impact & Evidence Invariants

Findings are prioritized by the product of exploitability and impact, so an
easy low-impact issue never outranks a harder catastrophic one without
justification:

$$\text{Priority}(f) = \text{Exploitability}(f) \times \text{Impact}(f), \quad \text{ranked descending}$$

The false-positive budget keeps the register credible: unverifiable or
speculative entries must stay below the threshold $\tau$ (default 10%) of
all reported items:

$$\frac{\#\{f \in F : \neg\,\text{evidenced}(f)\}}{\#F} < \tau, \quad \tau = 0.10$$

Every reported finding satisfies the evidence requirement: location,
attacker, exploit condition, and verification step are all present:

$$\forall f \in F: \; \text{location}(f) \wedge \text{attacker}(f) \wedge \text{exploitCondition}(f) \wedge \text{verification}(f)$$

Coverage is stated honestly; the review asserts bounded findings, never the
absence of vulnerabilities:

$$\text{Report} \vdash \text{Findings}(S) \;\not\Rightarrow\; \neg\,\exists f \notin S$$

---

## 6. Guardrails

### Operational Restrictions

- **Read-Only by Default**: Keep review mode read-only unless the user
  explicitly asks for remediation; report findings without editing reviewed
  code.
- **Scoped Discipline**: Review only the declared scope. Record nearby
  issues spotted outside the scope as observations for a follow-up review,
  not as in-scope findings.
- **Evidence-Backed Findings Only**: Every finding carries a location, an
  exploit condition, and a verification step; generic advice ("consider
  improving validation") is not a finding.
- **Prioritize Exploitable Issues**: Rank exploitable, evidenced issues
  above theoretical hardening notes; keep the speculative share under the
  false-positive budget.
- **No Absence or Compliance Claims**: Never state that code is "secure",
  "vulnerability-free", or "compliant" with any regime; report scope,
  findings, and residual risk only.
- **Single-Agent Executable**: An independent security-reviewer subagent is
  an optional second pass for high-risk changes; one agent can complete the
  full workflow alone.

### Security Invariants

- **No Secret Leakage in Reports**: Never embed real credentials, tokens,
  keys, or private payloads in findings, traces, or registers; use
  `<placeholder>` references and redacted samples.
- **No Exploit Execution**: Do not run exploits against live systems; an
  exploit condition is demonstrated by code evidence and reasoning, or by a
  test against a disposable local target only.
- **Sanitized Evidence**: Quote the minimum code needed to prove a finding;
  redact customer data, production URLs with embedded credentials, and
  internal identifiers not required for the trace.
- **Tooling Trust**: Security scanners and linters support the review but
  never replace the manual source-to-sink trace; tool output is cited as
  evidence, not as the conclusion.

---

## 7. Atomic Failure Recovery & Rollback Handler

Review runs are read-only against the target code, so rollback concerns only
artifacts created by this run (the findings register, scratch notes, evidence
logs). If report generation fails or produces a corrupted artifact that
cannot be fixed within 2 iterations, execute targeted rollback restricted
ONLY to files created or modified during this run:

```bash
# Revert ONLY modified files tracked during this execution run
# (normally none: reviewed code must remain untouched)
if [ -n "${MODIFIED_FILES:-}" ]; then
  git checkout -- ${MODIFIED_FILES} 2>/dev/null
fi

# Remove ONLY newly created untracked artifacts from this execution run
# (e.g. the partial findings register and scratch evidence logs)
if [ -n "${CREATED_FILES:-}" ]; then
  rm -rf ${CREATED_FILES} 2>/dev/null
fi
```

After executing targeted rollback, verify with a fresh status check that the
reviewed code is byte-identical to its pre-review state, then output the
exact error trace and state failure causes. Never delete findings evidence
that predates this run.

---

## 8. Verification Plan & Review Toolchain Commands

Execute the following read-only commands to gather and confirm review
evidence; adapt tool names to the project's declared scripts:

```bash
# 1. Enumerate the scoped change surface
git diff --stat main...HEAD && git diff main...HEAD -- src/

# 2. Trace candidate taint sources and sinks
rg -n "req\.(body|query|params|headers)" src/routes/
rg -n "dangerouslySetInnerHTML|eval\(|exec\(|query\(|redirect" src/

# 3. Confirm authorization middleware coverage on protected routes
rg -n "requireAuth|authorize|policy" src/routes/ src/middleware/

# 4. Run the project's security lint, type check, and test suite
npm run lint && npx --no-install tsc --noEmit && npm run test

# 5. Audit newly added dependencies for known vulnerabilities
git diff main...HEAD -- package.json
npm audit --audit-level=high
```

---

## 9. Completion Report

Report the reviewed scope (target type, refs, commit range) and explicit
out-of-scope list; the mapped assets, attackers, and trust boundaries; the
taint and authorization traces performed; the findings register with
severity, location, exploit conditions, impact, remediation direction, and
verification per finding; the checklist areas swept with their applicability
notes; the false-positive share against its budget; the verification plan
for each open finding; residual risk and uncovered areas; and a statement
that the review reports bounded findings only and does not assert compliance
or the absence of vulnerabilities.
