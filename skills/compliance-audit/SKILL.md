---
name: compliance-audit
description: "Audit code, configuration, and data flows against GDPR, SOC 2, HIPAA, and PCI-DSS compliance controls including PII redaction and audit logging."
---

# Compliance Audit

Audit a codebase, its configuration, and its data flows for compliance
readiness against **GDPR**, **SOC 2**, **HIPAA**, or **PCI-DSS** control
frameworks. The audit focuses on data privacy, access control, audit
logging, encryption, and data retention/deletion hooks, and produces a
severity-ranked findings register with framework control references and
remediation guidance.

Default tooling: repository-wide static scans with a small standard-library
Python script for regulated-data exposure patterns, the project's own test
runner for redaction regression tests, and read-only queries against log or
audit stores. Before scanning, inspect the repository and adapt to existing
conventions: read `AGENTS.md`, data models, logging and telemetry
configuration, auth modules, infrastructure definitions, and any existing
compliance documentation. The audit is evidence-driven: every finding cites
a file, line, or configuration value observed in the tree, and every
excerpt is redacted before it enters the evidence record.

---

## 1. Required I/O Context Schemas & Natural Language Auto-Inference

The skill supports **two invocation modes**:

1. **Orchestrator / Technical Mode (JSON Manifest)**: Pass the JSON context
   manifest below.
2. **Non-Technical Mode (Plain English Prompts)**: If the user provides a
   natural language prompt (e.g. *"Audit the billing service for GDPR
   readiness, focused on PII in logs and the deletion workflow"*), the
   agent **must automatically infer and populate** `audit_scope`,
   `data_classification_context`, and `evidence_context` from the user's
   text and the existing repository conventions.

### JSON Context Manifest Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "ComplianceAuditContextManifest",
  "type": "object",
  "required": ["audit_scope", "data_classification_context"],
  "properties": {
    "audit_scope": {
      "type": "object",
      "required": ["frameworks", "services"],
      "properties": {
        "frameworks": {
          "type": "array",
          "items": { "type": "string", "enum": ["gdpr", "soc2", "hipaa", "pci_dss"] },
          "minItems": 1
        },
        "services": { "type": "array", "items": { "type": "string", "pattern": "^[a-z0-9-]+$" }, "minItems": 1 },
        "in_scope_paths": { "type": "array", "items": { "type": "string" }, "default": [] }
      }
    },
    "data_classification_context": {
      "type": "object",
      "required": ["data_classes"],
      "properties": {
        "data_classes": {
          "type": "array",
          "items": { "type": "string", "enum": ["pii", "phi", "pci", "credentials", "telemetry"] },
          "minItems": 1
        },
        "regulated_fields": {
          "type": "array",
          "items": { "type": "string" },
          "description": "Concrete model fields under regulation, e.g. customer.email, patient.diagnosis, card.number."
        }
      }
    },
    "evidence_context": {
      "type": "object",
      "required": ["output_format", "evidence_dir"],
      "properties": {
        "output_format": { "type": "string", "enum": ["yaml_register", "markdown_report", "json"], "default": "yaml_register" },
        "evidence_dir": { "type": "string", "pattern": "^[a-z0-9/_.-]+$" },
        "fail_on_severity": { "type": "string", "enum": ["critical", "high", "medium", "low", "none"], "default": "high" }
      }
    }
  }
}
```

### Automatic Natural Language Inference & Safety Validation Rules

If no raw JSON payload is provided, apply these defaults and safety checks:

- **`frameworks`**: Extracted from the prompt or detected from existing
  compliance documentation and policy files. If the framework is ambiguous
  after inspecting the repository, ask before assuming one.
- **`services`**: Inferred from the prompt's service names or the
  repository layout (top-level service directories, workspace packages).
- **`data_classes`**: Inferred from data models and migrations: fields such
  as email, phone, address, or date of birth imply `pii`; diagnosis or
  treatment fields imply `phi`; card number or CVV fields imply `pci`.
- **`regulated_fields`**: Enumerated from schema definitions and ORM models
  so scanning rules match the project's actual field names.
- **`evidence_context`**: Defaults to `output_format: "yaml_register"` and
  `evidence_dir: "compliance/evidence/<audit-date>"`.
- **Safety validation**: ABORT execution immediately if the audit is asked
  to modify production authorization rules or audit-log settings, to scan a
  production write path, or to copy raw regulated values into evidence
  files. Audits are read-only and every captured excerpt is redacted.

---

## 2. Deterministic State Machine Execution Flow

Follow this exact sequential protocol. Do not skip steps or alter execution
ordering.

### Step 1: Scope, Framework & Repository Discovery

1. Read `AGENTS.md`, compliance requirements, data models, logging
   configurations, auth schemes, and storage definitions.
2. Identify the target compliance framework(s) and enumerate the concrete
   controls each finding will reference (for example SOC 2 CC7.2, GDPR
   Art. 17, PCI-DSS 3.3, HIPAA 164.312).
3. Fix the audit scope in writing: services, paths, and data classes under
   review, so findings stay attributable.

### Step 2: Regulated Data Flow Tracing

1. Trace Personally Identifiable Information (PII), Protected Health
   Information (PHI), or Payment Card Data (PCI) across entry points
   (HTTP handlers, message consumers, importers), storage (tables, object
   stores, caches), and egress points (API responses, webhooks, exports,
   third-party analytics).
2. Build a data inventory mapping each regulated field to its stores and
   flows; this inventory anchors every later finding.
3. Mark uncontrolled copies (debug dumps, local caches, analytics events)
   as candidate findings immediately.

### Step 3: PII Redaction in Logs, Telemetry & Error Traces

1. Verify PII redaction in logs, telemetry, error traces, and third-party
   analytics. Check that sensitive fields are never logged in plaintext.
2. Scan log call sites for regulated field references that bypass the
   project's redaction helpers; scan error handling for stack traces or
   request dumps that embed user data.
3. Confirm redaction helpers themselves cannot be bypassed by string
   interpolation of raw model objects.

### Step 4: Encryption Controls & Key Management

1. Verify encryption in transit: TLS 1.2 or higher on every external and
   internal channel carrying regulated data; reject configurations that
   negotiate TLS 1.0/1.1.
2. Verify encryption at rest: strong algorithms (AES-256 or equivalent) on
   databases, backups, object stores, and queue payloads holding regulated
   data.
3. Inspect secret and key management: keys come from a managed store or
   KMS, rotate on a schedule, and never appear in the repository or in
   plaintext configuration.

### Step 5: Access Control, Tenancy & Session Policy

1. Inspect access control mechanisms: Principle of Least Privilege on
   service accounts and roles, role-based authorization enforced on the
   server, and multi-tenant isolation on every read and write path.
2. Verify session management: timeout policies, token lifetimes, and
   revocation behavior match the framework's expectations.
3. Confirm administrative and break-glass paths are themselves
   authenticated, authorized, and audit-logged.

### Step 6: Audit Logging Completeness & Immutability

1. Verify that security-critical events (login, permission change, data
   export, admin action) generate audit log records containing user ID,
   timestamp, source IP, and action.
2. Verify audit records are immutable or tamper-evident (append-only
   storage, signed entries, or WORM export) and retained for the framework's
   required window.
3. Cross-check a sample of security events against the audit store to
   measure completeness rather than trusting the instrumentation.

### Step 7: Data Lifecycle, Retention & Erasure Hooks

1. Audit data lifecycle management: verify the existence of data deletion
   hooks (Right to be Forgotten / GDPR Art. 17) reachable for every
   regulated store, including backups and derived analytics.
2. Verify retention policy enforcement mechanisms actually execute
   (scheduled jobs, lifecycle rules), not merely that a policy document
   exists.
3. Measure the erasure path end to end against the deletion SLA and flag
   any store the erasure workflow cannot reach.

### Step 8: Findings Register, Severity & Remediation Reporting

1. Compile compliance gaps categorized by severity, framework control
   reference, affected files, and remediation guidance into the findings
   register.
2. Assign every finding an owner and a remediation SLA proportional to its
   severity.
3. State explicitly what was not verified (runtime behavior, third-party
   processor posture) so the report cannot be misread as certification.

---

## 3. Reference Implementation: Regulated-Data Log Scanner & Findings Register

```python
#!/usr/bin/env python3
"""Scan a checked-out repository for unredacted regulated-data logging.

Read-only: this script never modifies scanned files. It emits a JSON list of
candidate findings for human triage into the findings register, with every
excerpt redacted before output.
"""

from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass, asdict

LOG_CALL = re.compile(
    r"\b(logger|console|log|print|trace)\s*\.\s*(debug|info|warn|error|fatal|log)\s*\(",
    re.IGNORECASE,
)
PATTERNS = {
    "email": re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    "us_ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "card_candidate": re.compile(r"\b(?:\d[ -]*?){13,16}\b"),
}
REDACTION_HINT = re.compile(r"(redact|mask|scrub|sanitize|hash)\w*\s*\(", re.IGNORECASE)
SKIP_DIRS = {".git", "node_modules", "vendor", "dist", "build", ".venv"}
TEXT_EXTENSIONS = {".ts", ".tsx", ".js", ".jsx", ".py", ".go", ".rb", ".java", ".cs"}


@dataclass
class Finding:
    rule_id: str
    path: str
    line: int
    excerpt: str
    severity: str
    framework_refs: list[str]


def iter_source_files(root: str):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            if os.path.splitext(name)[1] in TEXT_EXTENSIONS:
                yield os.path.join(dirpath, name)


def mask(excerpt: str) -> str:
    # Never copy raw regulated values into the evidence output.
    excerpt = PATTERNS["email"].sub("<email>", excerpt)
    excerpt = PATTERNS["us_ssn"].sub("<ssn>", excerpt)
    excerpt = PATTERNS["card_candidate"].sub("<card-number>", excerpt)
    return excerpt.strip()


def scan(root: str) -> list[Finding]:
    findings: list[Finding] = []
    for path in iter_source_files(root):
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as handle:
                lines = handle.readlines()
        except OSError:
            continue
        for index, line in enumerate(lines, start=1):
            if not LOG_CALL.search(line):
                continue
            if REDACTION_HINT.search(line):
                continue  # field passes through a redaction helper first
            for rule_id, pattern in PATTERNS.items():
                if pattern.search(line):
                    findings.append(Finding(
                        rule_id=f"LOG-{rule_id.upper()}",
                        path=os.path.relpath(path, root),
                        line=index,
                        excerpt=mask(line),
                        severity="high",
                        framework_refs=["SOC2-CC7.2", "GDPR-Art.5", "PCI-DSS-3.3"],
                    ))
    return findings


def main() -> int:
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    findings = scan(root)
    print(json.dumps([asdict(f) for f in findings], indent=2))
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
```

The triaged findings register that the scanner output feeds into:

```yaml
# compliance/evidence/<audit-date>/findings-register.yaml
audit:
  frameworks: [gdpr, soc2, pci_dss]
  scope: [billing-service, accounts-api]
  auditor: agent
  date: "<audit-date>"
findings:
  - id: F-001
    rule_id: LOG-EMAIL
    severity: high
    status: open
    framework_refs: ["GDPR Art. 5(1)(f)", "SOC 2 CC7.2"]
    location: { file: src/billing/invoiceService.ts, line: 87 }
    evidence: "logger.info('invoice issued for <email>')"
    impact: "Customer email addresses are written to plaintext application logs."
    remediation: "Route the customer identifier through the shared redact() helper or log the internal customer ID instead."
    owner: billing-team
    sla_days: 30
  - id: F-002
    rule_id: ENC-TLS-MIN
    severity: medium
    status: open
    framework_refs: ["PCI-DSS 4.2.1", "HIPAA 164.312(e)(1)"]
    location: { file: infra/terraform/alb.tf, line: 22 }
    evidence: "ssl_policy pinned below the TLS 1.2 baseline"
    impact: "Load balancer can negotiate TLS 1.1, below the minimum transport version."
    remediation: "Pin the listener to a TLS 1.2+ policy and verify with a TLS handshake scan."
    owner: platform-team
    sla_days: 14
```

---

## 4. Redaction Regression Test & Audit-Log Completeness Pattern

A redaction regression test that fails the build if regulated identifiers
reach log output:

```python
import logging
import re

EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
SSN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")


def test_log_records_exclude_regulated_identifiers(caplog):
    from billing.invoice_service import issue_invoice  # module under audit

    with caplog.at_level(logging.INFO):
        issue_invoice(customer_email="alice@example.com", ssn="123-45-6789")

    rendered = "\n".join(record.getMessage() for record in caplog.records)
    assert not EMAIL.search(rendered), "customer email leaked into log output"
    assert not SSN.search(rendered), "customer SSN leaked into log output"
```

An audit-log completeness query run against a read-only replica; a non-zero
result is a completeness gap, not a logging nit:

```sql
-- Every security-critical event in the last 24h must have an audit row
-- carrying actor, timestamp, and source IP.
SELECT COUNT(*) AS missing_audit_rows
FROM security_event e
LEFT JOIN audit_log a
  ON a.event_id = e.id
WHERE e.occurred_at >= NOW() - INTERVAL '24 hours'
  AND (a.id IS NULL OR a.actor_id IS NULL OR a.source_ip IS NULL);
```

---

## 5. Compliance Invariants & Severity Mathematics

Encryption minimums across every channel and store holding regulated data:

$$\forall c \in \text{Channels}: \text{TLS}(c) \ge 1.2 \qquad \wedge \qquad \forall s \in \text{Stores}: \text{encryption}(s) \ge \text{AES-256}$$

Audit-log completeness for security-critical events:

$$\forall e \in \text{SecurityEvents}: \exists\, r \in \text{AuditLog}:\quad r \supseteq \{\text{actor\_id}, \text{action}, \text{timestamp}, \text{source\_ip}\} \wedge \text{immutable}(r)$$

Data-subject erasure SLA (Right to be Forgotten):

$$\forall u \in \text{ErasureRequests}:\quad t_{\text{deleted}}(u) - t_{\text{requested}}(u) \le 30 \text{ days}$$

Severity taxonomy as a weighted score mapped to bands:

$$\text{severity}(f) = \text{band}\big(w_e \cdot \text{exposure}(f) + w_s \cdot \text{sensitivity}(f) + w_x \cdot \text{exploitability}(f)\big),\quad \text{band} \in \{\text{critical}, \text{high}, \text{medium}, \text{low}\}$$

Audit pass condition against the configured fail threshold:

$$\text{audit-pass} \iff \#\{f : \text{severity}(f) \ge \text{fail\_on\_severity}\} = 0$$

---

## 6. Guardrails

### Operational Restrictions

- **No Legal Certification**: This skill performs code and configuration
  auditing against framework controls; it does not issue legal compliance
  certifications, attestations, or legal advice. Say so in every report.
- **No Unauthorized Production Changes**: Do not modify production
  authorization rules or audit log settings without authorization. The
  audit observes and reports; remediation is a separate, approved change.
- **Evidence Is Redacted**: Every excerpt captured into evidence files is
  masked before it is written; raw regulated values never enter the report,
  the scanner output, or the conversation transcript.
- **Single-Agent Executable**: An optional compliance-auditor subagent can
  analyze data flows in parallel, but one agent can complete this workflow
  end to end.

### Security Invariants

- **Read-Only Against Production**: Live checks run against read replicas
  and exported configuration only; never against production write paths,
  and never with credentials beyond read scope.
- **Evidence Access Control**: Findings registers and evidence directories
  are stored with access controls proportionate to their sensitivity; they
  describe vulnerabilities and must not become an attack map.
- **No Weakening to Pass**: The fail threshold, severity bands, and
  framework control mappings are never relaxed mid-audit to make a report
  look green; gaps are reported, not hidden.

---

## 7. Atomic Failure Recovery & Rollback Handler

Before creating or modifying files, the agent must capture a baseline list
of modified and untracked files. If any verification command in Section 8
fails and cannot be resolved within 2 iterations, the agent **must execute
targeted rollback restricted ONLY to files created or modified during this
run**:

```bash
# Revert ONLY modified files tracked during this execution run
if [ -n "${MODIFIED_FILES:-}" ]; then
  git checkout -- ${MODIFIED_FILES} 2>/dev/null
fi

# Remove ONLY newly created untracked files from this execution run
# (audit evidence files, scanner scripts, and reports from this run)
if [ -n "${CREATED_FILES:-}" ]; then
  rm -rf ${CREATED_FILES} 2>/dev/null
fi
```

After executing targeted rollback, output the exact error trace and state
failure causes. Never delete evidence, findings registers, or scan output
produced by earlier audit runs; audit history is itself a compliance
artifact.

---

## 8. Verification Plan & Audit Toolchain Commands

Execute the following commands using project-local runners; adapt to the
project's declared scripts and data platform:

```bash
# 1. Scan the checked-out tree for unredacted regulated-data logging
python scripts/scan_regulated_logging.py . > compliance/evidence/pii-scan.json

# 2. Run redaction and audit-logging regression tests
python -m pytest tests/security/ -v

# 3. Review transport and at-rest encryption configuration baselines
grep -RInE "ssl_policy|min_tls_version|minimum_tls_version|encrypt" infra/ config/ || true

# 4. Run the audit-log completeness query against a read-only replica
psql "$READ_ONLY_REPLICA_DSN" -v ON_ERROR_STOP=1 -f queries/audit_log_completeness.sql
```

---

## 9. Completion Report

Report the compliance frameworks assessed, the PII/PHI/PCI inventory mapped
across entry points, stores, and egress, control findings by severity with
framework control references and affected files, logging and encryption
audit results, audit-log completeness measurements, data lifecycle and
erasure coverage against the deletion SLA, prioritized remediation actions
with owners and SLA windows, evidence locations, and an explicit statement
of what was not verified and that the audit is not a legal certification.
