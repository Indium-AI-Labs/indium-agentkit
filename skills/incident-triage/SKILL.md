---
name: incident-triage
description: Triage incidents with evidence, mitigation, and follow-up.
---

# Incident triage

Turn an active or suspected production problem into a bounded response. Keep a
timeline, distinguish facts from hypotheses, and optimize first for user safety
and service stability.

## Workflow

1. Establish incident start time, current impact, affected users or regions,
   severity, incident owner, communications channel, and decision authority.
2. Preserve evidence: deploy history, metrics, logs, traces, alerts, request
   examples, and configuration changes. Record exact timestamps and queries.
3. Form a small set of testable hypotheses ranked by impact and evidence. Avoid
   speculative changes that destroy the ability to compare signals.
4. Choose the lowest-risk mitigation: disable a feature, stop a rollout, shed
   load, fail over, or revert a compatible artifact. State expected effect and
   abort condition before acting.
5. Verify mitigation against user-impact and dependency-health signals. Continue
   the timeline and communicate status, uncertainty, and next update time.
6. After stabilization, identify root cause separately from contributing
   factors. Reproduce safely and preserve a regression test or detection rule.
7. Define corrective actions with owners and due dates: code, infrastructure,
   monitoring, runbooks, permissions, and process.
8. Complete an incident report without credentials or sensitive payloads, and
   review it for blameless, evidence-backed language.

## Guardrails

- Do not perform production changes, credential operations, or destructive
  recovery without explicit authority and a recorded rollback or stop plan.
- Prefer reversible mitigations and preserve logs before restarting or deleting
  resources.
- An incident-commander subagent can coordinate notes and hypotheses, but one
  agent must be able to run this workflow.

## Completion report

Report impact, timeline, evidence, hypotheses, mitigation and verification,
root cause status, residual risk, and owned follow-up actions.
