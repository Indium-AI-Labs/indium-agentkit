---
name: contract-testing
description: "Design and implement consumer-driven contract tests (Pact, MSW, Playwright) to verify interface compatibility between microservices and frontend/backend boundaries."
---

# Contract testing

Design, implement, and verify consumer-driven contract tests between independent services
or frontend/backend API boundaries. Ensure contract verification prevents breaking API
changes without requiring full end-to-end environment deployment.

## Workflow

1. Read `AGENTS.md`, API specification, consumer expectations, and producer implementation.
   Identify consumer and producer service boundaries.
2. Define interaction contracts from the consumer's perspective: HTTP method, path, headers,
   query parameters, request body schema, expected response status code, and response body schema.
3. Write consumer contract tests using the project's contract testing tool (Pact, MSW,
   Supertest, or custom mock verifiers). Generate verified contract artifacts (e.g. Pact files).
4. Implement producer verification tests that replay recorded contracts against the real producer
   implementation endpoints in an isolated test environment.
5. Verify matching handling for edge cases: missing optional parameters, null values, error
   envelopes, dynamic IDs, and type constraints.
6. Publish contracts to a contract broker or repository artifact storage as required by CI policy.
7. Integrate contract verification step into pull request validation checks.
8. Report verified contracts, breaking changes detected, and coverage gaps across API endpoints.

## Guardrails

- Focus contract tests on interface structure and schema constraints; do not use contract tests
  for deep business logic verification.
- Do not hardcode unstable dynamic values (e.g. timestamps, random UUIDs) in exact matching assertions;
  use type matchers or regex matchers.
- An optional reviewer subagent can inspect API contracts in parallel, but one agent can complete this workflow.

## Completion report

Report consumer/producer boundaries tested, contracts generated, endpoints verified, breaking drift detected,
and CI integration recommendations.
