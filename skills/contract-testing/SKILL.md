---
name: contract-testing
description: "Design and implement consumer-driven contract tests (Pact, MSW, Playwright) to verify interface compatibility between microservices and frontend/backend boundaries."
---

# Contract Testing

Design, implement, and verify consumer-driven contract tests between
independent services or frontend/backend API boundaries. The default tooling
is **Pact** (consumer contract tests, provider verification, and a Pact
Broker for publication and deployment gating), **MSW** for frontend network
seams, and **Playwright request contexts** where the project already tests
at the HTTP seam. Contract verification must prevent breaking API changes
without requiring a full end-to-end environment deployment.

Before writing any test, inspect the repository and adapt to existing
conventions: read the API specification (OpenAPI, GraphQL schema, or
protobuf definitions), existing contract or mock directories (`pacts/`,
`mocks/`, `src/mocks/`), the consumer's API client modules, the producer's
route handlers, and the CI pipeline to see where verification must plug in.
Reuse the project's contract tooling, fixture factories, and error envelope
instead of inventing parallel harnesses.

---

## 1. Required I/O Context Schemas & Natural Language Auto-Inference

The skill supports **two invocation modes**:

1. **Orchestrator / Technical Mode (JSON Manifest)**: Pass the JSON context
   manifest below.
2. **Non-Technical Mode (Plain English Prompts)**: If the user provides a
   natural language prompt (e.g. *"Add a Pact contract between billing-web
   and invoice-service for fetching a single invoice, including the 404
   case"*), the agent **must automatically infer and populate**
   `boundary_spec`, `interaction_spec`, and `broker_context` from the
   user's text and the existing repository conventions.

### JSON Context Manifest Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "ContractTestingContextManifest",
  "type": "object",
  "required": ["boundary_spec", "interaction_spec"],
  "properties": {
    "boundary_spec": {
      "type": "object",
      "required": ["consumer", "producer", "transport"],
      "properties": {
        "consumer": { "type": "string", "pattern": "^[a-z0-9-]+$" },
        "producer": { "type": "string", "pattern": "^[a-z0-9-]+$" },
        "transport": { "type": "string", "enum": ["http_rest", "graphql", "async_message", "grpc"] },
        "contract_tool": { "type": "string", "enum": ["pact", "msw", "playwright_request", "custom_mock"], "default": "pact" }
      }
    },
    "interaction_spec": {
      "type": "object",
      "required": ["interactions"],
      "properties": {
        "interactions": {
          "type": "array",
          "minItems": 1,
          "items": {
            "type": "object",
            "required": ["description", "method", "path", "response_status"],
            "properties": {
              "description": { "type": "string" },
              "provider_state": { "type": "string" },
              "method": { "type": "string", "enum": ["GET", "POST", "PUT", "PATCH", "DELETE"] },
              "path": { "type": "string", "pattern": "^/(?!.*(?:^|/)\\.\\.?(?:/|$)).*$" },
              "request_headers": { "type": "object" },
              "request_body": { "type": ["object", "null"] },
              "response_status": { "type": "integer", "minimum": 100, "maximum": 599 },
              "response_body": { "type": ["object", "null"] },
              "dynamic_fields": {
                "type": "array",
                "items": { "type": "string" },
                "description": "Fields that must use type or regex matchers, never exact values (timestamps, UUIDs, generated IDs)."
              }
            }
          }
        }
      }
    },
    "broker_context": {
      "type": "object",
      "required": ["publish_mode", "can_i_deploy_required"],
      "properties": {
        "publish_mode": { "type": "string", "enum": ["broker", "artifact_storage", "none"], "default": "none" },
        "broker_url": { "type": "string" },
        "can_i_deploy_required": { "type": "boolean", "default": false },
        "tags": { "type": "array", "items": { "type": "string" }, "default": ["main"] }
      }
    }
  }
}
```

### Automatic Natural Language Inference & Safety Validation Rules

If no raw JSON payload is provided, apply these defaults and safety checks:

- **`consumer` / `producer`**: Extracted from the prompt's service names or
  inferred from the repository layout (for example a `web/` application
  consuming an `api/` service). Names are normalized to kebab-case
  pacticipant names already known to the broker.
- **`transport`**: Defaults to `http_rest` unless a message queue, GraphQL
  schema, or protobuf definition is detected at the boundary.
- **`contract_tool`**: Detected from dependencies (`@pact-foundation/pact`,
  `msw`, `@playwright/test`). Defaults to `pact` for service-to-service
  boundaries and `msw` for frontend network seams.
- **`interactions`**: Derived from the consumer's API client functions.
  Every client function that crosses the boundary gets at least one success
  interaction and one error-envelope interaction.
- **`dynamic_fields`**: Auto-populated with `id`, `*Id`, `createdAt`,
  `updatedAt`, `requestId`, and any field whose value is a timestamp or
  UUID. These fields MUST use type or regex matchers.
- **`broker_context`**: Defaults to `publish_mode: "broker"` when a broker
  URL is configured in the environment or CI, otherwise `artifact_storage`.
- **Path safety**: every interaction `path` MUST NOT contain traversal
  segments (`.` or `..`); normalize and ABORT execution immediately if a
  traversal attempt is detected.
- **Safety validation**: ABORT execution immediately if the manifest
  hardcodes a timestamp, UUID, or random token as an exact-match assertion,
  or if provider verification is pointed at a production base URL. Provider
  verification targets local or ephemeral test environments only.

---

## 2. Deterministic State Machine Execution Flow

Follow this exact sequential protocol. Do not skip steps or alter execution
ordering.

### Step 1: Boundary & Convention Discovery

1. Read `AGENTS.md`, the API specification, the consumer's API client
   modules, and the producer's route handlers.
2. Identify the exact consumer/producer boundary: which service initiates
   requests, which owns the interface, and which pacticipant names the
   broker already knows.
3. Inventory existing contract artifacts (`pacts/`, MSW handlers, recorded
   fixtures) so new interactions extend them instead of forking them.

### Step 2: Interaction Contract Definition (Consumer Perspective)

1. Define each interaction from the consumer's perspective: HTTP method,
   path, headers, query parameters, request body schema, expected response
   status code, and response body schema.
2. Attach a provider state to every interaction (for example `invoice
   inv_42 exists and is payable`) so the producer can arrange fixture data
   deterministically.
3. Cover the error envelope explicitly: at least one 4xx interaction per
   resource so the consumer's error handling is part of the contract.

### Step 3: Consumer Contract Tests & Artifact Generation

1. Write consumer contract tests with the project's contract tool (Pact,
   MSW, Supertest, or a custom mock verifier), driving the real consumer
   client code against the mock — never testing the mock against itself.
2. Use type matchers and regex matchers for every dynamic value; exact
   literals are reserved for enum-like fields the consumer genuinely pins.
3. Generate verified contract artifacts (Pact JSON files) into the
   project's contract directory and confirm they serialize deterministically.

### Step 4: Producer Verification in Isolation

1. Implement provider verification that replays recorded contracts against
   the real producer endpoints in an isolated test environment with its own
   database or fixture seeding.
2. Implement state handlers that arrange and tear down fixture data for
   every provider state used by any consumer.
3. Publish verification results back to the broker with the provider
   version so deployment gating has evidence to evaluate.

### Step 5: Edge-Case & Dynamic-Value Matching

1. Verify matching behavior for edge cases: missing optional parameters,
   null values, empty collections, error envelopes, dynamic IDs, and type
   constraints (a string that must stay a string).
2. Confirm no assertion depends on wall-clock time, random UUIDs, or
   environment-specific host names; replay the suite twice and diff the
   generated pact files to prove determinism.

### Step 6: Contract Publication

1. Publish contracts to the Pact Broker (or repository artifact storage
   when no broker is configured) with the consumer version and branch tag.
2. Tag the mainline contract set so `can-i-deploy` can compare against the
   currently deployed versions of each participant.

### Step 7: CI Integration of Verification Gates

1. Add consumer contract test execution and publication to the consumer's
   pull-request checks.
2. Add provider verification to the producer's pull-request checks, wired
   to fetch pacts by consumer version selectors (`main`, `deployed`).
3. Add a `can-i-deploy` gate to the deployment pipeline when the project
   requires broker-driven release gating.

### Step 8: Evidence, Drift & Coverage Reporting

1. Record which endpoints of the boundary carry verified interactions and
   which do not; every consumer-invoked endpoint without a contract is a
   coverage gap to report.
2. Report breaking drift detected during verification (removed fields, type
   changes, tightened constraints) with the exact interaction that failed.

---

## 3. Reference Implementation: Pact Consumer Test & Provider Verification

```typescript
import { PactV3, MatchersV3, SpecificationVersion } from '@pact-foundation/pact';
import { describe, it, expect } from 'vitest';
import { fetchInvoice, type Invoice } from '../src/clients/invoiceClient';

const { like, eachLike, string, regex, iso8601DateTime, uuid, decimal, integer } = MatchersV3;

const provider = new PactV3({
  consumer: 'billing-web',
  provider: 'invoice-service',
  spec: SpecificationVersion.SPECIFICATION_VERSION_V3,
  dir: 'pacts',
  logLevel: 'warn',
});

describe('billing-web -> invoice-service contract', () => {
  it('GET /api/invoices/:id returns a typed invoice', () => {
    provider
      .given('invoice inv_42 exists and is payable')
      .uponReceiving('a request for a single invoice')
      .withRequest({
        method: 'GET',
        path: regex('/api/invoices/inv_42', '\\/api\\/invoices\\/[A-Za-z0-9_\\-]+'),
        headers: {
          Accept: like('application/json'),
          Authorization: regex('Bearer <token>', '^Bearer .+$'),
        },
      })
      .willRespondWith({
        status: 200,
        headers: { 'Content-Type': regex('application/json; charset=utf-8', 'application\\/json.*') },
        body: {
          id: string('inv_42'),
          customerId: uuid('8f3a2b1c-0000-4000-8000-000000000000'),
          currency: regex('USD', '^[A-Z]{3}$'),
          total: decimal(129.99),
          lineCount: integer(1),
          issuedAt: iso8601DateTime('2026-01-15T09:30:00Z'),
          lines: eachLike(
            { sku: like('sku_pro'), quantity: integer(1), unitPrice: decimal(129.99) },
            { min: 1 },
          ),
        },
      });

    return provider.executeTest(async (mockServer) => {
      const invoice: Invoice = await fetchInvoice(mockServer.url, 'inv_42', '<token>');
      expect(invoice.id).toBe('inv_42');
      expect(typeof invoice.total).toBe('number');
      expect(Array.isArray(invoice.lines)).toBe(true);
      expect(invoice.lines.length).toBeGreaterThanOrEqual(1);
    });
  });

  it('GET /api/invoices/:id returns the shared 404 envelope when missing', () => {
    provider
      .given('invoice inv_missing does not exist')
      .uponReceiving('a request for a missing invoice')
      .withRequest({
        method: 'GET',
        path: regex('/api/invoices/inv_missing', '\\/api\\/invoices\\/[A-Za-z0-9_\\-]+'),
        headers: { Accept: like('application/json') },
      })
      .willRespondWith({
        status: 404,
        headers: { 'Content-Type': regex('application/json; charset=utf-8', 'application\\/json.*') },
        body: {
          error: {
            code: string('INVOICE_NOT_FOUND'),
            message: like('Invoice not found.'),
            requestId: uuid('00000000-0000-4000-8000-000000000000'),
          },
        },
      });

    return provider.executeTest(async (mockServer) => {
      await expect(fetchInvoice(mockServer.url, 'inv_missing', '<token>'))
        .rejects.toMatchObject({ status: 404, code: 'INVOICE_NOT_FOUND' });
    });
  });
});
```

Provider-side verification replays every published pact against the real
service with deterministic fixture seeding:

```typescript
import { Verifier } from '@pact-foundation/pact';
import { describe, it } from 'vitest';
import { seedInvoice, purgeInvoice } from './fixtures/invoices';

describe('invoice-service provider verification', () => {
  it('replays every published consumer contract against the real service', async () => {
    const verifier = new Verifier({
      provider: 'invoice-service',
      providerBaseUrl: process.env.PROVIDER_BASE_URL ?? 'http://127.0.0.1:8081',
      pactBrokerUrl: process.env.PACT_BROKER_BASE_URL,
      pactBrokerToken: process.env.PACT_BROKER_TOKEN, // injected by CI; never committed
      publishVerificationResult: process.env.CI === 'true',
      providerVersion: process.env.GIT_SHA ?? 'local-dev',
      consumerVersionSelectors: [{ tag: 'main', latest: true }, { deployed: true }],
      enablePending: true,
      stateHandlers: {
        'invoice inv_42 exists and is payable': async () => {
          await seedInvoice({ id: 'inv_42', status: 'payable', total: 129.99 });
        },
        'invoice inv_missing does not exist': async () => {
          await purgeInvoice('inv_missing');
        },
      },
      requestFilter: (req, _res, next) => {
        req.headers['Authorization'] = 'Bearer <token>';
        next();
      },
    });

    await verifier.verifyProvider();
  }, 120000);
});
```

---

## 4. Broker Publication, can-i-deploy & MSW Seam Pattern

Publish contracts and gate deployment on verification status:

```bash
# 1. Publish the consumer contract with its version and branch tag
npx --no-install pact-broker publish pacts \
  --consumer-app-version "${GIT_SHA}" \
  --tag "${GIT_BRANCH}" \
  --broker-base-url "${PACT_BROKER_BASE_URL}" \
  --broker-token "${PACT_BROKER_TOKEN}"

# 2. Record the deployed version so provider selectors can target it
npx --no-install pact-broker record-deployment \
  --pacticipant billing-web --version "${GIT_SHA}" --environment production

# 3. Gate the release: refuse to deploy until all relevant pacts are verified
npx --no-install pact-broker can-i-deploy \
  --pacticipant invoice-service \
  --version "${GIT_SHA}" \
  --to-environment production \
  --retry-while-unknown 6 \
  --retry-interval 30
```

MSW handler mirroring the same contract for the frontend development seam:

```typescript
import { http, HttpResponse } from 'msw';

export const invoiceHandlers = [
  http.get('/api/invoices/:id', ({ params }) => {
    if (params.id === 'inv_missing') {
      return HttpResponse.json(
        { error: { code: 'INVOICE_NOT_FOUND', message: 'Invoice not found.', requestId: 'req_synth_1' } },
        { status: 404 },
      );
    }
    return HttpResponse.json({
      id: params.id,
      customerId: 'cus_synth_1',
      currency: 'USD',
      total: 129.99,
      lineCount: 1,
      issuedAt: '2026-01-15T09:30:00.000Z',
      lines: [{ sku: 'sku_pro', quantity: 1, unitPrice: 129.99 }],
    });
  }),
];
```

---

## 5. Contract Invariants & Coverage Mathematics

Matcher stability — every dynamic field carries a matcher; no hardcoded
timestamps or UUIDs appear in exact-match assertions:

$$\forall f \in \text{ResponseFields}:\quad \text{dynamic}(f) \;\Rightarrow\; \text{matcher}(f) \in \{\text{type}, \text{regex}, \text{iso8601}, \text{uuid}, \text{decimal}, \text{integer}\}$$

Contract coverage ratio across the consumer-invoked surface:

$$\text{coverage} = \frac{\#\{\text{endpoints with } \ge 1 \text{ verified interaction}\}}{\#\{\text{endpoints the consumer actually invokes}\}} \ge 0.9$$

Verification replay determinism — identical provider versions yield
identical verdicts:

$$\forall \text{ replays } r_1, r_2 \text{ of contract } c \text{ against provider } v:\quad \text{verdict}(c, v, r_1) = \text{verdict}(c, v, r_2)$$

Deployment gate — a participant version is deployable only when the broker
confirms compatibility with everything currently deployed:

$$\text{deployable}(p, v) \iff \text{can-i-deploy}(p, v, \text{target environment}) = \text{success}$$

---

## 6. Guardrails

### Operational Restrictions

- **Interface Shape, Not Business Logic**: Contract tests verify interface
  structure and schema constraints (methods, paths, status codes, field
  types, error envelopes). Do not encode deep business logic, pricing
  rules, or workflow outcomes into contract assertions — that belongs in
  unit and integration tests.
- **No Hardcoded Dynamic Values**: Never hardcode unstable dynamic values
  (timestamps, random UUIDs, generated IDs, tokens) in exact-matching
  assertions; use type matchers or regex matchers so contracts survive
  replay.
- **Consumer Perspective Only**: Interactions are authored from what the
  consumer actually sends and needs; do not mirror the producer's full
  response payload when the consumer reads three fields.
- **Single-Agent Executable**: An optional reviewer subagent can inspect
  API contracts in parallel, but one agent can complete this workflow end
  to end.

### Security Invariants

- **No Production Verification Targets**: Provider verification runs
  against local or ephemeral test environments only, never against
  production base URLs or production data.
- **Synthetic Example Data Only**: Contract examples use synthetic
  fixtures; never embed real customer data, credentials, or production
  identifiers in pact files or MSW handlers.
- **Broker Credentials From CI**: Broker tokens and webhook secrets are
  injected from the CI secret store at runtime and are never committed to
  the repository or printed in logs.

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
if [ -n "${CREATED_FILES:-}" ]; then
  rm -rf ${CREATED_FILES} 2>/dev/null
fi
```

After executing targeted rollback, output the exact error trace and state
failure causes. Never delete pact artifacts or broker publications produced
by earlier runs; unpublishing broker content is a separate, explicit
action.

---

## 8. Verification Plan & Contract Toolchain Commands

Execute the following commands using project-local runners; adapt to the
project's declared scripts:

```bash
# 1. Run consumer contract tests and generate pact artifacts
npm run test:contract

# 2. Prove replay determinism: run twice and diff the generated pact files
npm run test:contract && cp -r pacts /tmp/pacts-run1
npm run test:contract && diff -r /tmp/pacts-run1 pacts

# 3. Run provider verification against the isolated test service
npm run test:provider

# 4. Type check and lint the test code itself
npx --no-install tsc --noEmit
npm run lint
```

---

## 9. Completion Report

Report consumer/producer boundaries tested, contracts generated (with the
interaction list and matcher strategy per interaction), endpoints verified
on the producer side, breaking drift detected with the exact failing
interactions, coverage gaps across the boundary's API surface, broker
publication and `can-i-deploy` outcomes, CI integration points added, and
recommendations for closing remaining coverage or gating gaps.
