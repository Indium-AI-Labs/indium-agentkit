---
name: plan-change
description: "Turn a feature request, bug report, refactor, or technical proposal into an implementation-ready plan with scope, acceptance criteria, affected areas, test seams, risks, and ordered steps."
---

# Plan change

1. Read the request, repository context, and relevant code or documentation.
2. State the problem, intended outcome, non-goals, constraints, and unresolved assumptions.
3. Identify affected files, interfaces, data flows, dependencies, and public behavior seams.
4. Define observable acceptance criteria and the tests or verification that demonstrate each one.
5. Break the work into ordered, independently reviewable steps. Call out parallelizable investigation only when it will not create conflicting edits.
6. Identify compatibility, security, migration, rollout, and rollback risks.
7. Present a concise plan with the decision points that require user input. Do not implement until the requested planning depth is complete.
