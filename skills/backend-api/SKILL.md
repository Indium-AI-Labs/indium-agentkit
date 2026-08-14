---
name: backend-api
description: Build robust typed API endpoints with safe contracts.
---

# Backend API

Implement a server-side capability with a clear, compatible contract. The
default stack is **TypeScript** with a typed HTTP API (Express, Fastify, or
Next.js Route Handlers), **Zod** boundary validation, and **PostgreSQL**
persistence; adapt to the consumer project's established runtime, transport,
serialization, and persistence patterns before writing any code.

The skill is **contract-first**: the API contract (resource, operation,
schemas, errors, auth) is agreed before the handler is implemented, and the
implementation is verified against that contract through the public HTTP seam.

---

## 1. Required I/O Context Schemas & Natural Language Auto-Inference

The skill supports **two invocation modes**:

1. **Orchestrator / Technical Mode (JSON Manifest)**: Pass the JSON context
   manifest below.
2. **Non-Technical Mode (Plain English Prompts)**: If the user provides a
   natural language prompt (e.g. *"Add a typed POST /api/projects endpoint
   that creates a project for the authenticated user"*), the agent **must
   automatically infer and populate** `resource_name`, `base_path`,
   `operations`, `auth_model`, and `persistence_context` from the user's text
   and the existing repository conventions.

### JSON Context Manifest Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "BackendApiContextManifest",
  "type": "object",
  "required": ["endpoint_spec", "contract_context"],
  "properties": {
    "endpoint_spec": {
      "type": "object",
      "required": ["resource_name", "base_path", "operations"],
      "properties": {
        "resource_name": { "type": "string", "pattern": "^[a-z0-9-]+$" },
        "base_path": { "type": "string", "pattern": "^/(?!.*(?:^|/)\\.\\.?(?:/|$))[a-zA-Z0-9/_.:-]+$" },
        "operations": {
          "type": "array",
          "items": { "type": "string", "enum": ["list", "get", "create", "update", "delete"] },
          "minItems": 1
        }
      }
    },
    "contract_context": {
      "type": "object",
      "required": ["auth_model", "error_envelope"],
      "properties": {
        "auth_model": { "type": "string", "enum": ["session", "bearer_jwt", "api_key", "none"] },
        "error_envelope": { "type": "string" },
        "versioning_scheme": { "type": "string", "enum": ["path", "header", "none"], "default": "none" }
      }
    },
    "persistence_context": {
      "type": "object",
      "required": ["engine", "migration_required"],
      "properties": {
        "engine": { "type": "string", "enum": ["postgresql", "mysql", "sqlite", "mongodb", "none"] },
        "migration_required": { "type": "boolean", "default": false },
        "transaction_boundary": { "type": "string", "enum": ["per_request", "per_operation", "none"], "default": "per_operation" }
      }
    }
  }
}
```

### Automatic Natural Language Inference & Path Traversal Validation Rules

If no raw JSON payload is provided, apply these defaults and safety checks:

- **`resource_name`**: Extracted from the prompt noun (e.g. "projects" becomes
  `project`) in kebab-case singular form.
- **`base_path`**: Extracted from the prompt URL or defaults to
  `/api/<resource_name>s`. `base_path` MUST NOT contain path traversal
  segments (`.` or `..`). Normalize the path and **ABORT execution
  immediately** if a traversal attempt is detected.
- **`operations`**: Inferred from verbs in the prompt ("list", "create",
  "update", "delete"). Defaults to `["list", "get", "create"]`.
- **`auth_model`**: Detected from existing middleware and session helpers in
  the repository. Defaults to the model used by the nearest sibling endpoint;
  if none exists, ask before assuming `none`.
- **`error_envelope`**: Reuse the project's existing error shape (inspect at
  least one sibling route handler). Never invent a new envelope format.
- **`persistence_context.engine`**: Detected from `package.json`, ORM config,
  or existing connection modules. `migration_required` defaults to `false`
  unless the endpoint needs a schema change.

---

## 2. Deterministic State Machine Execution Flow

Follow this exact sequential protocol. Do not skip steps or alter execution
ordering.

### Step 1: Context Ingestion & Convention Discovery

1. Read `AGENTS.md`, the feature brief, the current API contract, and the data
   migration plan if one exists.
2. Inspect at least two sibling endpoint implementations to inherit routing,
   validation, serialization, error, and auth conventions.
3. Identify callers, authorization boundaries, ownership rules, and
   compatibility constraints before editing code.
4. Validate the resolved `base_path` for zero traversal segments.

### Step 2: Contract-First Specification

1. Write or update the API contract before the handler: resource, operation,
   request schema, response schema, error cases, authentication,
   authorization, pagination or idempotency semantics, and versioning impact.
2. Confirm the contract does not conflict with existing consumers. If the
   change is breaking, stop and escalate with an explicit compatibility note.

### Step 3: Boundary Validation & Serialization

1. Reuse the project's validation and serialization libraries (Zod, io-ts,
   Pydantic, etc.). Validate **all** external input at the boundary: path
   params, query strings, headers, and bodies.
2. Return consistent, documented errors using the project's error envelope.
   Never leak stack traces, SQL, or internal identifiers in error responses.

### Step 4: Server-Side Authentication & Authorization

1. Enforce authentication on every protected operation through the project's
   established middleware or guard.
2. Enforce authorization (ownership, role, tenant scope) **on the server** for
   every read and write. Never rely on a UI check as the authorization
   control.
3. Return `401` for unauthenticated and `403` for authenticated-but-forbidden
   callers, per the existing convention.

### Step 5: Transactional Persistence & Concurrency Safety

1. Make persistence operations transactional where partial writes would
   violate invariants. Wrap multi-statement mutations in a single transaction.
2. Consider concurrent requests, retries, uniqueness, and stale writes
   explicitly: use uniqueness constraints, idempotency keys, optimistic
   concurrency (`updated_at` / version columns), or `ON CONFLICT` clauses as
   appropriate.
3. Never change a database schema without a reviewed migration plan; delegate
   schema design to the `database-design` skill output.

### Step 6: Observability Without Credential Exposure

1. Add structured logs, metrics, or trace context through the project's
   existing observability patterns: request entry, authorization decision,
   mutation result, and dependency call outcome.
2. Never log credentials, tokens, session identifiers, or sensitive payloads.
   Redact or omit fields listed in the project's sensitive-data policy.

### Step 7: Focused Tests at the Public HTTP Seam

1. Add focused tests for successful behavior, invalid input, auth failures,
   boundary conditions, and any regression.
2. Exercise the public HTTP seam when practical (Supertest, Playwright API
   request contexts, or the project's harness), not only the handler unit.

### Step 8: Handoff & Verification Evidence

1. Run the project's type check, lint, and test commands; capture exact output.
2. Record changed contracts, migrations required, verification evidence,
   risks, and follow-up work in the verification-report handoff.

---

## 3. Reference Implementation: Typed Endpoint with Transactional Handler

```typescript
import { z } from 'zod';

// 1. Boundary contract: single source of truth for input validation.
const CreateProjectRequestSchema = z.object({
  name: z.string().min(1).max(120),
  description: z.string().max(2000).optional(),
  ownerTeamId: z.string().uuid(),
});

const ProjectResponseSchema = z.object({
  id: z.string().uuid(),
  name: z.string(),
  description: z.string().nullable(),
  ownerTeamId: z.string().uuid(),
  createdAt: z.string().datetime(),
});

type CreateProjectRequest = z.infer<typeof CreateProjectRequestSchema>;
type ProjectResponse = z.infer<typeof ProjectResponseSchema>;

// 2. Consistent error envelope reused across the API surface.
class ApiError extends Error {
  constructor(
    public readonly statusCode: number,
    public readonly code: string,
    message: string,
    public readonly fieldErrors?: Record<string, string[]>,
  ) {
    super(message);
  }
}

// 3. Handler: auth -> validate -> authorize -> transact -> serialize.
export async function createProjectHandler(
  req: AuthenticatedRequest,
  res: Response,
  db: Database,
  logger: StructuredLogger,
): Promise<void> {
  const requestId = req.requestId;
  logger.info('project.create.start', { requestId, actorId: req.actor?.id });

  if (!req.actor) {
    throw new ApiError(401, 'UNAUTHENTICATED', 'Authentication is required.');
  }

  const parsed = CreateProjectRequestSchema.safeParse(req.body);
  if (!parsed.success) {
    throw new ApiError(422, 'VALIDATION_FAILED', 'Request body is invalid.', parsed.error.flatten().fieldErrors);
  }
  const input: CreateProjectRequest = parsed.data;

  // Authorization is enforced on the server, never delegated to the client.
  const canCreate = await db.teams.userHasRole(input.ownerTeamId, req.actor.id, ['owner', 'maintainer']);
  if (!canCreate) {
    throw new ApiError(403, 'FORBIDDEN', 'You cannot create projects for this team.');
  }

  // Transactional write: partial failure leaves no orphaned rows.
  const project = await db.transaction(async (trx) => {
    const created = await trx.projects.insert({
      name: input.name,
      description: input.description ?? null,
      ownerTeamId: input.ownerTeamId,
      createdBy: req.actor!.id,
    });
    await trx.auditLog.insert({
      actorId: req.actor!.id,
      action: 'project.created',
      entityId: created.id,
      requestId,
    });
    return created;
  });

  const body: ProjectResponse = ProjectResponseSchema.parse({
    id: project.id,
    name: project.name,
    description: project.description,
    ownerTeamId: project.ownerTeamId,
    createdAt: project.createdAt.toISOString(),
  });

  logger.info('project.create.success', { requestId, projectId: project.id });
  res.status(201).json({ data: body });
}
```

---

## 4. Public-Seam HTTP Test Pattern

```typescript
import { test, expect } from '@playwright/test';

test.describe('POST /api/projects seam', () => {
  test('creates a project for an authorized team member', async ({ request }) => {
    const response = await request.post('/api/projects', {
      headers: { Authorization: `Bearer ${maintainerToken}` },
      data: { name: 'Billing Revamp', ownerTeamId: teamId },
    });
    expect(response.status()).toBe(201);
    const body = await response.json();
    expect(body.data.name).toBe('Billing Revamp');
    expect(body.data.id).toMatch(/^[0-9a-f-]{36}$/);
  });

  test('rejects invalid payloads with the shared error envelope', async ({ request }) => {
    const response = await request.post('/api/projects', {
      headers: { Authorization: `Bearer ${maintainerToken}` },
      data: { name: '', ownerTeamId: 'not-a-uuid' },
    });
    expect(response.status()).toBe(422);
    const body = await response.json();
    expect(body.error.code).toBe('VALIDATION_FAILED');
    expect(body.error.fieldErrors.name).toBeDefined();
  });

  test('returns 401 without credentials and 403 for non-members', async ({ request }) => {
    expect((await request.post('/api/projects', { data: {} })).status()).toBe(401);
    const forbidden = await request.post('/api/projects', {
      headers: { Authorization: `Bearer ${outsiderToken}` },
      data: { name: 'Nope', ownerTeamId: teamId },
    });
    expect(forbidden.status()).toBe(403);
  });
});
```

---

## 5. Latency, Error-Rate & Integrity Invariants

$$P95(t_{\text{request}}) \le 250\text{ms for read endpoints}, \quad P99 \le 800\text{ms}$$

$$\text{5xx rate} = \frac{\#\{\text{responses with status} \ge 500\}}{\#\{\text{responses}\}} < 0.1\%$$

$$\forall \text{ mutation } m: \quad \text{committed}(m) \Rightarrow \text{audit-logged}(m) \wedge \text{authorized}(m)$$

$$\text{Idempotency: } \text{effect}(op \circ op) = \text{effect}(op) \text{ for retried writes with the same idempotency key}$$

---

## 6. Guardrails

### Operational Restrictions

- **Contract Before Code**: Do not implement a handler before the request and
  response contract is written down and checked against existing consumers.
- **No Unplanned Schema Changes**: Do not change a database schema without a
  reviewed migration plan from the `database-design` workflow.
- **No Invented Fields**: Do not invent response fields or error semantics
  that conflict with consumers; reuse shared types and envelopes.
- **Single-Agent Executable**: Optional subagent delegation (explorer,
  backend-builder, reviewer) can accelerate exploration or review; one agent
  must still be able to perform this workflow end to end.

### Security Invariants

- **Server-Enforced Authorization**: Every protected operation authenticates
  and authorizes on the server. A missing UI button is not a control.
- **Boundary Validation**: All external input is parsed through typed
  contracts before touching business logic or persistence.
- **Zero Credential Exposure**: Never log or return credentials, tokens,
  connection strings, or raw SQL errors.
- **Parameterized Persistence**: Use the ORM/query builder's parameter
  binding; never interpolate user input into SQL strings.

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
failure causes. Never roll back migrations that were not created by this run.

---

## 8. Verification Plan & Toolchain Commands

Execute the following commands using project-local runners; adapt to the
project's declared scripts:

```bash
# 1. Type check endpoint code and contracts
npx --no-install tsc --noEmit

# 2. Execute code linter
npm run lint

# 3. Run unit and integration tests
npm run test

# 4. Exercise the public HTTP seam (when configured)
npx --no-install playwright test
```

---

## 9. Completion Report

Report endpoints changed, contract decisions, authorization and validation
coverage, data effects (tables written, transactions, audit events), commands
run with results, and unverified risks or follow-up work.
