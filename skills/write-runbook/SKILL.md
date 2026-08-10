---
name: write-runbook
description: "Create or update an operational runbook for a service, feature, or failure mode with detection, diagnosis, mitigation, recovery, and escalation procedures."
---

# Write runbook

Produce a forward-looking operational playbook that helps operators detect,
diagnose, mitigate, and recover from a specific failure or operational
scenario. Extract procedures from code, configuration, and infrastructure;
do not invent steps that have not been tested.

## Workflow

1. Read `AGENTS.md`, service architecture, monitoring configuration, alert
   definitions, deployment procedures, and existing runbooks. Identify the
   failure mode or operational scenario to document.
2. Define the runbook's scope, owning team, service, and related alerts or
   dashboards. Link to existing monitoring.
3. Document detection: what signals indicate the problem, where to look, and
   how to distinguish this issue from similar ones.
4. Document diagnosis: specific commands, log queries, metric checks, and
   health endpoints to confirm root cause. Include exact commands with
   expected outputs.
5. Document mitigation: step-by-step actions to reduce user impact, with
   expected effect, abort conditions, and authority requirements for each
   step.
6. Document recovery: steps to restore full functionality after mitigation,
   including verification checks.
7. Document escalation: when to escalate, to whom, and what information to
   provide.
8. Keep credentials, tokens, and sensitive configuration out of runbook
   content. Reference secret-management systems instead.

## Guardrails

- Runbooks document procedures; they do not execute them. Do not run
  production commands or modify infrastructure as part of writing a runbook.
- Mark untested procedures explicitly. A runbook with untested steps should
  be labeled as draft.
- An optional explorer subagent can map infrastructure, but one agent can
  complete this workflow.

## Completion report

Report the runbook produced, failure modes covered, procedures documented,
commands verified, untested steps, and maintenance recommendations.
