---
name: frontend-ship
description: Build accessible, typed frontend features end to end.
---

# Frontend ship

Implement a user-facing feature from an agreed brief through verified handoff.
The default stack is Next.js and TypeScript, but first inspect the project and
follow its existing framework, routing, styling, and test conventions.

## Workflow

1. Read the project's `AGENTS.md`, the feature brief, and any API contract.
   State missing decisions before inventing a server route, data shape, or
   authorization rule.
2. Identify the affected route, component boundaries, design-system primitives,
   and client/server rendering boundaries. Keep server-only code out of client
   bundles.
3. Turn acceptance criteria into observable UI states: initial, loading,
   success, empty, error, retry, and permission-denied where applicable.
4. Build semantic, keyboard-operable, responsive UI. Use existing tokens and
   components; do not introduce a competing design system without approval.
5. Integrate only with documented typed contracts. Validate untrusted values at
   the boundary and present useful, non-sensitive error feedback.
6. Preserve accessibility: labels, focus order, focus visibility, landmarks,
   reduced motion where relevant, and meaningful status announcements.
7. Add behavior-focused tests at the nearest public seam. Prefer user-visible
   assertions over implementation details; run browser checks when available.
8. Update `templates/handoffs/verification-report.md` or the project's chosen
   handoff artifact with changed UI behavior, commands and results, risks, and
   the next agent's needs.

## Guardrails

- Keep work scoped to the requested interface. Escalate API, schema, dependency,
  or product-policy changes rather than silently making them.
- Do not place credentials, authorization decisions, or trusted business rules
  solely in browser code.
- A subagent may explore or review in parallel, but this workflow must remain
  executable by one agent.

## Completion report

Report the routes and components changed, contract assumptions, accessibility
and responsive states covered, tests run and their results, and anything still
unverified.
