---
name: backend-api
description: Build robust typed API endpoints with safe contracts.
---

# Backend API

Implement a server-side capability with a clear, compatible contract. The
default stack is TypeScript with a typed HTTP API and PostgreSQL; adapt to the
consumer project's established runtime, transport, and persistence patterns.

## Workflow

1. Read `AGENTS.md`, the feature brief, current API contract, and data
   migration plan. Identify callers, authorization boundaries, and compatibility
   constraints before editing code.
2. Write or update the API contract first: resource, operation, request schema,
   response schema, error cases, authentication, authorization, pagination or
   idempotency semantics, and versioning impact.
3. Reuse the project's validation and serialization libraries. Validate all
   external input at the boundary; return consistent, documented errors.
4. Enforce authentication and authorization on the server for every protected
   operation. Never rely on a UI check as the authorization control.
5. Make persistence operations transactional where partial writes would violate
   invariants. Consider concurrent requests, retries, uniqueness, and stale
   writes explicitly.
6. Add structured logs, metrics, or trace context through existing observability
   patterns without logging credentials, tokens, or sensitive payloads.
7. Add focused tests for successful behavior, invalid input, auth failures,
   boundary conditions, and any regression. Exercise the public HTTP seam when
   practical.
8. Record changed contracts, migrations required, verification evidence, risks,
   and follow-up work in the verification-report handoff.

## Guardrails

- Do not change a database schema without a reviewed migration plan.
- Do not invent response fields or error semantics that conflict with consumers.
- Optional subagent delegation can accelerate exploration or review; one agent
  must still be able to perform this workflow end to end.

## Completion report

Report endpoints changed, contract decisions, authorization and validation
coverage, data effects, commands run with results, and unverified risks.
