---
name: api-design
description: "Design an API contract — resources, operations, schemas, errors, versioning, and pagination — from requirements before implementation, producing a completed api-contract handoff."
---

# API design

Design a typed, versioned API contract from feature requirements. Complete the
contract before implementation begins. REST over HTTP is the default transport;
adapt to the project's established patterns when they differ.

## Workflow

1. Read `AGENTS.md`, the feature brief, existing API conventions, consumer
   needs, data model, and authentication model. State assumptions and missing
   requirements before inventing a contract.
2. Define resources, their relationships, ownership, lifecycle, and naming
   conventions consistent with the existing API surface.
3. Design operations for each resource: method, URL, idempotency, and expected
   side effects. Separate read-only from mutating operations.
4. Specify request schemas with required and optional fields, types,
   validation rules, and format constraints. Reuse existing shared types.
5. Specify response schemas including envelope format, pagination structure,
   embedded versus linked relationships, and cache semantics.
6. Define error responses: status codes, error-code identifiers, human-readable
   messages, and field-level validation feedback. Align with existing error
   conventions.
7. Plan versioning, deprecation, and backward-compatibility strategy. State
   what constitutes a breaking change and how consumers will be notified.
8. Produce a completed `api-contract` handoff covering resources, operations,
   authentication, authorization, schemas, errors, compatibility, and the
   implementation's dependencies.

## Guardrails

- This skill designs contracts; it does not implement endpoints. Use the
  `backend-api` skill for implementation.
- Do not invent authorization rules, data models, or business logic that
  conflict with the feature brief or existing conventions.
- An optional api-designer subagent can analyze requirements in parallel, but
  this workflow is executable by one agent.

## Completion report

Report the designed contract, resource and operation inventory, schema
decisions, versioning strategy, compatibility constraints, and open questions
for the implementing agent.
