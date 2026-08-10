---
name: compliance-audit
description: "Audit code, configuration, and data flows against GDPR, SOC 2, HIPAA, and PCI-DSS compliance controls including PII redaction and audit logging."
---

# Compliance audit

Audit a codebase for compliance readiness against SOC 2, GDPR, HIPAA, or PCI-DSS
control frameworks. Focus on data privacy, access control, audit logging, encryption,
and data retention/deletion hooks.

## Workflow

1. Read `AGENTS.md`, compliance requirements, data models, logging configurations, auth
   schemes, and storage definitions. Identify target compliance framework(s).
2. Trace Personally Identifiable Information (PII), Protected Health Information (PHI), or
   Payment Card Data (PCI) handling across entry points, storage, and egress points.
3. Verify PII redaction in logs, telemetry, error traces, and third-party analytics.
   Check that sensitive fields are never logged in plaintext.
4. Verify encryption controls: TLS 1.2+ in transit, strong encryption algorithms at rest,
   and secret key management patterns.
5. Inspect access control mechanisms: Principle of Least Privilege, role-based authorization,
   multi-tenant isolation, and session management timeout policies.
6. Verify audit logging: ensure security-critical events (login, permission change, data
   export, admin action) generate immutable audit log records with user ID, timestamp, and IP.
7. Audit data lifecycle management: verify existence of data deletion hooks (Right to be
   Forgotten) and data retention policy enforcement mechanisms.
8. Report compliance gaps categorized by severity, framework control reference, affected
   files, and remediation guidance.

## Guardrails

- This skill performs code and configuration auditing; it does not issue legal compliance
  certifications.
- Do not modify production authorization rules or audit log settings without authorization.
- An optional compliance-auditor subagent can analyze data flows in parallel, but one agent
  can complete this workflow.

## Completion report

Report compliance framework assessed, PII/PHI inventory mapped, control findings by severity,
logging and encryption audit results, and prioritized remediation actions.
