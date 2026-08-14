---
name: api-design
description: "Design an API contract — resources, operations, schemas, errors, versioning, and pagination — from requirements before implementation, producing a completed api-contract handoff."
---

# API Design

Design a typed, versioned, consumer-safe API contract from feature requirements
before any endpoint is implemented. REST over HTTP with JSON payloads is the
default transport; inspect the repository and adapt to the project's established
API conventions (framework, envelope format, naming, error shape, auth scheme)
when they differ.

The skill is **contract-first and design-only**: the output is a completed
`api-contract` handoff (via `templates/handoffs/api-contract.md`) that an
implementing agent — typically the `backend-api` skill — can build against
without further design decisions. Before writing the contract, inspect the
local repository to inherit existing route layouts, shared schema types,
serialization conventions, and error envelopes.

---

## 1. Required I/O Context Schemas & Natural Language Auto-Inference

The skill supports **two invocation modes**:

1. **Orchestrator / Technical Mode (JSON Manifest)**: Pass the JSON context
   manifest below.
2. **Non-Technical Mode (Plain English Prompts)**: If the user provides a
   natural language prompt (e.g. *"Design the API for team billing: list
   invoices, get one invoice, and start a payment retry"*), the agent **must
   automatically infer and populate** `resource_spec`, `operation_spec`,
   `schema_context`, and `versioning_context` from the user's text and the
   existing repository conventions.

### JSON Context Manifest Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "ApiDesignContextManifest",
  "type": "object",
  "required": ["resource_spec", "operation_spec"],
  "properties": {
    "resource_spec": {
      "type": "object",
      "required": ["resource_name", "base_path", "ownership_model"],
      "properties": {
        "resource_name": { "type": "string", "pattern": "^[a-z0-9-]+$" },
        "base_path": { "type": "string", "pattern": "^/(?!.*(?:^|/)\\.\\.?(?:/|$))[a-zA-Z0-9/_.:{}-]+$" },
        "ownership_model": { "type": "string", "enum": ["user_owned", "team_owned", "tenant_scoped", "global"] },
        "lifecycle": {
          "type": "array",
          "items": { "type": "string", "enum": ["draft", "active", "archived", "deleted"] }
        },
        "relationships": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["target_resource", "cardinality"],
            "properties": {
              "target_resource": { "type": "string" },
              "cardinality": { "type": "string", "enum": ["one_to_one", "one_to_many", "many_to_many"] },
              "embedding": { "type": "string", "enum": ["embedded", "linked", "id_only"], "default": "id_only" }
            }
          }
        }
      }
    },
    "operation_spec": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "required": ["operation_id", "http_method", "mutating"],
        "properties": {
          "operation_id": { "type": "string", "pattern": "^[a-z][a-zA-Z0-9]*$" },
          "http_method": { "type": "string", "enum": ["GET", "POST", "PUT", "PATCH", "DELETE"] },
          "mutating": { "type": "boolean" },
          "idempotency": { "type": "string", "enum": ["intrinsic", "idempotency_key", "none"], "default": "intrinsic" },
          "pagination": { "type": "string", "enum": ["cursor", "offset", "none"], "default": "none" }
        }
      }
    },
    "schema_context": {
      "type": "object",
      "required": ["envelope_format", "error_envelope"],
      "properties": {
        "envelope_format": { "type": "string", "enum": ["data_wrapped", "bare", "jsonapi"], "default": "data_wrapped" },
        "error_envelope": { "type": "string" },
        "shared_types": { "type": "array", "items": { "type": "string" } },
        "field_naming": { "type": "string", "enum": ["camelCase", "snake_case"], "default": "camelCase" }
      }
    },
    "versioning_context": {
      "type": "object",
      "required": ["scheme"],
      "properties": {
        "scheme": { "type": "string", "enum": ["path", "header", "none"], "default": "none" },
        "current_version": { "type": "string", "pattern": "^v[0-9]+$" },
        "deprecation_policy": { "type": "string" },
        "breaking_change": { "type": "boolean", "default": false }
      }
    }
  }
}
```

### Automatic Natural Language Inference & Path Traversal Validation Rules

If no raw JSON payload is provided, apply these defaults and safety checks:

- **`resource_name`**: Extracted from the prompt noun (e.g. "invoices" becomes
  `invoice`) in kebab-case singular form.
- **`base_path`**: Extracted from the prompt URL or defaults to
  `/api/<resource_name>s`. `base_path` MUST NOT contain path traversal
  segments (`.` or `..`). Normalize the path and **ABORT execution
  immediately** if a traversal attempt is detected.
- **`operation_spec`**: Inferred from verbs in the prompt ("list", "get",
  "create", "update", "delete", plus domain verbs like "retry" mapped to
  sub-resource actions). Defaults to `list`, `get`, and `create`.
- **`schema_context`**: Reuse the project's existing envelope format and error
  envelope (inspect at least one sibling contract or route handler). Never
  invent a new envelope format when one already exists.
- **`versioning_context.scheme`**: Detected from existing route prefixes
  (`/v1/...`) or version headers. Defaults to the scheme used by sibling
  resources; `none` only when the whole API surface is unversioned.
- **`ownership_model`**: Inferred from the feature brief's authorization
  language ("a user's ...", "team-scoped ..."). When unclear, state the
  assumption explicitly in the contract handoff instead of guessing silently.

---

## 2. Deterministic State Machine Execution Flow

Follow this exact sequential protocol. Do not skip steps or alter execution
ordering.

### Step 1: Context Ingestion & Assumption Declaration

1. Read `AGENTS.md`, the feature brief, existing API conventions, consumer
   needs, the data model, and the authentication model.
2. Inspect at least two existing contracts, route modules, or OpenAPI
   documents to inherit naming, envelope, and error conventions.
3. State assumptions and missing requirements **before** inventing any
   contract element; record each in the handoff's open-questions section.

### Step 2: Resource Modeling

1. Define resources, their relationships, ownership boundaries, lifecycle
   states, and naming conventions consistent with the existing API surface.
2. Decide embedded versus linked representations for each relationship:
   `embedded` for always-needed children, `linked` or `id_only` for large or
   independently paginated collections.
3. Confirm resource names do not collide with existing routes and follow the
   repository's pluralization and casing conventions.

### Step 3: Operation Design

1. Design operations for each resource: HTTP method, URL, idempotency
   semantics, and expected side effects.
2. Separate read-only from mutating operations; every mutating operation
   declares its idempotency strategy (`intrinsic` for GET/PUT/DELETE,
   `idempotency_key` for POST creates that clients may retry).
3. Map domain actions that do not fit CRUD (e.g. "retry payment") to explicit
   sub-resource operations (`POST /invoices/{id}/payment-retries`) rather than
   overloaded PATCH semantics.

### Step 4: Request Schema Specification

1. Specify request schemas with required and optional fields, types,
   validation rules, and format constraints (min/max, regex patterns, enum
   values, string formats such as `uuid` or `date-time`).
2. Reuse existing shared types from the project instead of redefining them;
   note every reuse explicitly in the contract.
3. Mark every field's mutability: create-only, updatable, or read-only.

### Step 5: Response Schema & Pagination Specification

1. Specify response schemas including the envelope format, pagination
   structure (cursor or offset with explicit field names), embedded versus
   linked relationships, and cache semantics (`Cache-Control`, `ETag`).
2. Define pagination bounds: default page size, maximum page size, and the
   cursor or offset field contract, including stable-sort requirements.
3. Declare which fields are always present versus conditionally present, and
   how nullability is expressed for each.

### Step 6: Error Contract Specification

1. Define error responses: HTTP status codes, machine-readable error-code
   identifiers, human-readable messages, and field-level validation feedback.
2. Align with existing error conventions exactly; reuse the project's error
   envelope rather than inventing a new one.
3. Enumerate the complete error matrix per operation: `400`/`422` validation,
   `401` unauthenticated, `403` forbidden, `404` not found, `409` conflict,
   and `429` rate limited.

### Step 7: Versioning, Deprecation & Compatibility Planning

1. Plan the versioning, deprecation, and backward-compatibility strategy.
2. State explicitly what constitutes a breaking change (removing a field,
   tightening a validation rule, changing a field's type or semantics,
   changing published error codes) versus a compatible change (adding an
   optional field, adding a new operation, widening accepted input).
3. Describe how consumers will be notified (changelog, deprecation headers,
   sunset dates) and the minimum overlap window for dual-version support.

### Step 8: Contract Handoff Assembly

1. Produce the completed `api-contract` handoff covering resources,
   operations, authentication, authorization, schemas, errors, compatibility,
   and the implementation's dependencies.
2. Cross-check every operation against the feature brief: each brief
   requirement must trace to at least one operation, and each operation must
   trace to a requirement.
3. Flag every unresolved question as an explicit open item; never silently
   resolve ambiguity by invention.

---

## 3. Reference Implementation: OpenAPI 3.1 Contract Fragment

The following fragment demonstrates the expected contract depth for one
resource: a request schema, a paginated response, a shared error envelope, and
an explicit cursor pagination contract.

```yaml
openapi: 3.1.0
info:
  title: Billing API
  version: "1.0.0"
paths:
  /v1/invoices:
    get:
      operationId: listInvoices
      summary: List invoices for the authenticated tenant
      parameters:
        - name: cursor
          in: query
          required: false
          schema: { type: string }
          description: Opaque pagination cursor from a previous response.
        - name: limit
          in: query
          required: false
          schema: { type: integer, minimum: 1, maximum: 100, default: 25 }
        - name: status
          in: query
          required: false
          schema: { $ref: "#/components/schemas/InvoiceStatus" }
      responses:
        "200":
          description: Paginated invoice list.
          content:
            application/json:
              schema:
                type: object
                required: [data, pagination]
                properties:
                  data:
                    type: array
                    items: { $ref: "#/components/schemas/Invoice" }
                  pagination:
                    $ref: "#/components/schemas/CursorPage"
        "401": { $ref: "#/components/responses/Unauthenticated" }
        "429": { $ref: "#/components/responses/RateLimited" }
    post:
      operationId: createInvoice
      summary: Create an invoice (idempotent via Idempotency-Key header)
      parameters:
        - name: Idempotency-Key
          in: header
          required: true
          schema: { type: string, maxLength: 128 }
      requestBody:
        required: true
        content:
          application/json:
            schema: { $ref: "#/components/schemas/CreateInvoiceRequest" }
      responses:
        "201":
          description: Invoice created.
          content:
            application/json:
              schema:
                type: object
                required: [data]
                properties:
                  data: { $ref: "#/components/schemas/Invoice" }
        "422": { $ref: "#/components/responses/ValidationFailed" }
components:
  schemas:
    InvoiceStatus:
      type: string
      enum: [draft, open, paid, void, uncollectible]
    Invoice:
      type: object
      required: [id, status, currency, amountDueCents, createdAt]
      properties:
        id: { type: string, format: uuid }
        status: { $ref: "#/components/schemas/InvoiceStatus" }
        currency: { type: string, pattern: "^[A-Z]{3}$" }
        amountDueCents: { type: integer, minimum: 0 }
        dueAt: { type: string, format: date-time, nullable: true }
        createdAt: { type: string, format: date-time }
    CreateInvoiceRequest:
      type: object
      required: [currency, amountDueCents]
      properties:
        currency: { type: string, pattern: "^[A-Z]{3}$" }
        amountDueCents: { type: integer, minimum: 1, maximum: 100000000 }
        dueAt: { type: string, format: date-time }
    CursorPage:
      type: object
      required: [hasMore, nextCursor]
      properties:
        hasMore: { type: boolean }
        nextCursor: { type: string, nullable: true }
    ErrorEnvelope:
      type: object
      required: [error]
      properties:
        error:
          type: object
          required: [code, message]
          properties:
            code: { type: string }
            message: { type: string }
            fieldErrors:
              type: object
              additionalProperties:
                type: array
                items: { type: string }
  responses:
    Unauthenticated:
      description: Missing or invalid credentials.
      content:
        application/json:
          schema: { $ref: "#/components/schemas/ErrorEnvelope" }
    ValidationFailed:
      description: Request failed field-level validation.
      content:
        application/json:
          schema: { $ref: "#/components/schemas/ErrorEnvelope" }
    RateLimited:
      description: Rate limit exceeded; retry after the Retry-After hint.
      content:
        application/json:
          schema: { $ref: "#/components/schemas/ErrorEnvelope" }
```

---

## 4. Contract Lint & Compatibility Check Pattern

Verify the contract mechanically before handoff: lint it for structural
validity, then diff it against the previously published contract to prove the
change is additive-only.

```bash
# 1. Lint the OpenAPI document for structural and style violations
npx --no-install @stoplight/spectral-cli lint openapi/invoices.yaml \
  --ruleset .spectral.yaml --format stylish

# 2. Diff against the previously published contract; fail on breaking changes
npx --no-install oasdiff breaking openapi/invoices.published.yaml \
  openapi/invoices.yaml --fail-on ERR
```

```typescript
// 3. Schema-level compatibility assertions (TypeScript, node:test)
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { parse } from 'yaml';

test('invoice contract changes are additive-only', () => {
  const published = parse(readFileSync('openapi/invoices.published.yaml', 'utf8'));
  const proposed = parse(readFileSync('openapi/invoices.yaml', 'utf8'));

  const pubSchema = published.components.schemas.CreateInvoiceRequest;
  const newSchema = proposed.components.schemas.CreateInvoiceRequest;

  // No previously published field may be removed.
  for (const field of Object.keys(pubSchema.properties)) {
    assert.ok(field in newSchema.properties, `breaking: removed field ${field}`);
  }

  // No previously optional field may become required.
  const pubRequired = new Set(pubSchema.required ?? []);
  const newRequired = new Set(newSchema.required ?? []);
  for (const field of newRequired) {
    assert.ok(pubRequired.has(field), `breaking: ${field} became required`);
  }

  // The error envelope shape must remain identical across revisions.
  assert.deepEqual(
    proposed.components.schemas.ErrorEnvelope,
    published.components.schemas.ErrorEnvelope,
    'error envelope drift detected',
  );
});
```

---

## 5. Compatibility, Pagination & Consistency Invariants

$$\forall c \in \Delta(\text{contract}_{old}, \text{contract}_{new}): \quad c \in \text{Additive} \;\Rightarrow\; \neg\,\text{Breaking}(c)$$

$$\text{Additive} = \{\text{add optional field},\ \text{add operation},\ \text{widen accepted input},\ \text{add response enum value}\}$$

$$1 \le \text{limit} \le \text{MAX\_PAGE\_SIZE} = 100, \qquad \text{default limit} = 25$$

$$\forall\, op \in \text{Operations}: \quad \text{errorShape}(op) = \text{ErrorEnvelope} \;\wedge\; \text{status}(op) \in \text{DeclaredMatrix}(op)$$

$$\text{ConsumersBroken}(v_n \rightarrow v_{n+1}) = 0 \quad \text{for all changes within one major version}$$

---

## 6. Guardrails

### Operational Restrictions

- **Design-Only Scope**: This skill designs contracts; it does **not**
  implement endpoints, handlers, or persistence. Use the `backend-api` skill
  for implementation against the completed contract.
- **No Invented Domain Rules**: Do not invent authorization rules, data
  models, or business logic that conflict with the feature brief or existing
  conventions. Ambiguity becomes an open question in the handoff, never a
  silent guess.
- **Convention Inheritance**: Do not introduce a new envelope format, error
  shape, naming scheme, or versioning scheme when the repository already
  establishes one; divergences require explicit justification in the handoff.
- **Single-Agent Executable**: An optional api-designer subagent can analyze
  requirements in parallel, but this workflow is executable end to end by one
  agent.

### Security Invariants

- **AuthZ per Operation**: Every operation in the contract must declare its
  authentication requirement and its server-side authorization rule
  (ownership or tenant scope). An operation without an authorization story is
  an incomplete contract.
- **No Sensitive Data in Contracts**: Never embed credentials, tokens,
  internal hostnames, or real PII samples in contract examples; use obvious
  placeholders such as `<token>`.
- **Error Non-Disclosure**: Contract error responses must not promise stack
  traces, SQL fragments, or internal identifiers; the error envelope carries
  only safe, consumer-actionable information.
- **Path Safety**: All paths written into the contract must be validated
  against traversal segments before being recorded in the handoff.

---

## 7. Atomic Failure Recovery & Rollback Handler

Before creating or modifying files, capture a baseline list of modified and
untracked files. If any verification command in Section 8 fails and cannot be
resolved within 2 iterations, execute targeted rollback restricted ONLY to
files created or modified during this run:

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
failure causes. Never delete or revert a previously published contract file
that this run did not create or modify.

---

## 8. Verification Plan & Contract Toolchain Commands

Execute the following commands using project-local runners; adapt to the
project's declared lint and schema tooling:

```bash
# 1. Validate the OpenAPI/contract document structure
npx --no-install @stoplight/spectral-cli lint openapi/<resource>.yaml

# 2. Prove additive-only evolution against the published contract
npx --no-install oasdiff breaking openapi/<resource>.published.yaml \
  openapi/<resource>.yaml --fail-on ERR

# 3. Type check any generated or hand-maintained contract types
npx --no-install tsc --noEmit

# 4. Run the project's contract/schema test suite when one exists
npm run test
```

---

## 9. Completion Report

The final report must contain: the designed contract (or a precise pointer to
the contract artifact), the complete resource and operation inventory, schema
decisions including envelope, pagination, and shared-type reuse, the full
error matrix, the versioning and deprecation strategy, compatibility
constraints with the additive-only evidence produced in Section 8, the
implementation's dependencies prepared for the `backend-api` handoff, and
every open question the implementing agent must resolve with the requester
rather than by invention.
