---
name: event-sourcing-architecture
description: Design immutable event logs, CQRS command/query models, and materialized view projections.
---

# Event Sourcing Architecture

Design append-only immutable event stores, Command Query Responsibility Segregation (CQRS) architectures, materialized view projection engines, aggregate root state hydration, outbox pattern transaction publishers, and deterministic event replay pipelines.

The skill is **append-only and replay-verified**: event schemas, versioning semantics, optimistic concurrency checks (`expected_version`), snapshot intervals, projection idempotency, and deterministic state re-hydration ($\text{State} = \text{Fold}(Init, \text{Events}_{1..n})$) are verified before implementation.

---

## 1. Required I/O Context Schemas & Natural Language Auto-Inference

The skill supports **two invocation modes**:

1. **🤖 Orchestrator / Technical Mode (JSON Manifest)**: Pass the JSON context manifest below.
2. **💬 Non-Technical Mode (Plain English Prompts)**: If the user provides a natural language prompt (e.g. *"Design an event-sourced order management system with PostgreSQL append-only event store, snapshotting, and materialized view projections"*), the agent **must automatically infer and populate** `aggregate_name`, `event_types`, `persistence_engine`, `projection_strategy`, and `snapshot_frequency` from the user's text.

### JSON Context Manifest Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "EventSourcingContextManifest",
  "type": "object",
  "required": ["aggregate_spec", "event_store_context"],
  "properties": {
    "aggregate_spec": {
      "type": "object",
      "required": ["aggregate_name", "event_types"],
      "properties": {
        "aggregate_name": { "type": "string", "pattern": "^[a-zA-Z0-9_-]+$" },
        "event_types": { 
          "type": "array", 
          "items": { "type": "string" },
          "minItems": 1 
        },
        "snapshot_frequency": { "type": "integer", "default": 100 }
      }
    },
    "event_store_context": {
      "type": "object",
      "required": ["persistence_engine", "concurrency_mode"],
      "properties": {
        "persistence_engine": { 
          "type": "string", 
          "enum": ["postgresql", "eventstore_db", "dynamodb", "kafka", "sqlite"] 
        },
        "concurrency_mode": { 
          "type": "string", 
          "enum": ["optimistic_version", "pessimistic_lock", "sequence_number"] 
        },
        "outbox_pattern_enabled": { "type": "boolean", "default": true }
      }
    },
    "projection_context": {
      "type": "object",
      "properties": {
        "projection_strategy": { 
          "type": "string", 
          "enum": ["inline_synchronous", "async_outbox_worker", "event_bus_listener"] 
        },
        "read_model_db": { "type": "string", "default": "postgresql_views" }
      }
    }
  }
}
```

### Automatic Natural Language Inference & Mutation Rejection

If no raw JSON payload is provided, apply these defaults and strict safety checks:

- **Event Mutation Rejection**: If prompt attempts to execute `UPDATE` or `DELETE` on historical event records, **ABORT execution immediately** and reject with `MUTATION_OF_IMMUTABLE_LOG_FORBIDDEN`.
- **`aggregate_name`**: Extracted from prompt noun (e.g. "orders" $\rightarrow$ `OrderAggregate`).
- **`event_types`**: Inferred from lifecycle transitions (e.g. `OrderCreated`, `OrderPaid`, `OrderShipped`, `OrderCancelled`).
- **`persistence_engine`**: Defaults to PostgreSQL with append-only event tables (`event_store`).

---

## 2. Deterministic State Machine Execution Flow

Follow this exact sequential protocol. Do not skip steps or alter execution ordering.

### Step 1: Domain Event & Aggregate Root Schema Specification

1. Define immutable event schemas (`v1.0.0`) with explicit metadata:
   ```json
   {
     "eventId": "evt-uuid-12345",
     "aggregateId": "ord-7890",
     "aggregateType": "OrderAggregate",
     "eventType": "OrderCreated",
     "eventVersion": 1,
     "sequenceNumber": 1,
     "timestamp": "2026-08-23T18:34:00Z",
     "payload": { "totalAmount": 150.00, "customerId": "cust-42" },
     "metadata": { "correlationId": "req-99", "actorId": "usr-1" }
   }
   ```
2. Design Aggregate Root reducer function (`applyEvent(state, event)`) that updates state purely in-memory without side-effects.

### Step 2: Append-Only Event Store & Optimistic Concurrency

1. Implement append-only event insertion with Optimistic Concurrency Control (OCC):
   - Check if `current_version == expected_version` before appending.
   - Raise `CONCURRENCY_VERSION_MISMATCH` if a race condition occurs.
2. Implement **Transactional Outbox Pattern**: Insert events into both `event_store` and `outbox` in the same DB transaction to guarantee atomic publishing to message brokers (Kafka / RabbitMQ).

### Step 3: Materialized View Projection Engine

1. Construct read-optimized materialized view tables for query operations (CQRS Read Model).
2. Implement idempotent projection handlers (`onEvent(event)`):
   - Handle out-of-order delivery using `sequenceNumber` tracking.
   - Ignore already-applied events (`if (event.sequenceNumber <= view.lastProcessedSequence) return;`).

### Step 4: Snapshotting & State Re-Hydration Protocol

1. Store aggregate state snapshots every $N$ events (e.g. every 100 events).
2. Re-hydrate Aggregate Root state efficiently:
   - Load latest snapshot if available ($State_{\text{snap}}$).
   - Fetch and replay events generated after the snapshot version ($Version > Version_{\text{snap}}$).
   - Fold state: $State_{\text{current}} = \text{Fold}(State_{\text{snap}}, \text{Events}_{\text{remaining}})$.

---

## 3. Reference Implementation: TypeScript Event Store & Projection Engine

```typescript
import { z } from 'zod';

// 1. Immutable Domain Event Schema
export const DomainEventSchema = z.object({
  eventId: z.string().uuid(),
  aggregateId: z.string(),
  aggregateType: z.string(),
  eventType: z.string(),
  eventVersion: z.number().int().positive(),
  sequenceNumber: z.number().int().positive(),
  timestamp: z.string().datetime(),
  payload: z.record(z.unknown()),
  metadata: z.record(z.unknown()),
});

export type DomainEvent = z.infer<typeof DomainEventSchema>;

// 2. Aggregate Root (OrderAggregate State & Reducer)
export interface OrderState {
  orderId: string;
  customerId: string;
  status: 'NONE' | 'CREATED' | 'PAID' | 'SHIPPED' | 'CANCELLED';
  totalAmount: number;
  version: number;
}

export class OrderAggregate {
  private state: OrderState = {
    orderId: '',
    customerId: '',
    status: 'NONE',
    totalAmount: 0,
    version: 0,
  };

  // Pure State Reducer: State = Fold(Init, Events)
  public apply(event: DomainEvent): void {
    switch (event.eventType) {
      case 'OrderCreated':
        this.state.orderId = event.aggregateId;
        this.state.customerId = event.payload.customerId as string;
        this.state.totalAmount = event.payload.totalAmount as number;
        this.state.status = 'CREATED';
        break;
      case 'OrderPaid':
        this.state.status = 'PAID';
        break;
      case 'OrderCancelled':
        this.state.status = 'CANCELLED';
        break;
    }
    this.state.version = event.sequenceNumber;
  }

  public getState(): Readonly<OrderState> {
    return this.state;
  }
}

// 3. Materialized View Projection Engine
export class OrderReadModelProjection {
  private lastProcessedSequence = 0;

  public async handle(event: DomainEvent, dbClient: any): Promise<void> {
    // Idempotency Check: Ignore already applied sequence numbers
    if (event.sequenceNumber <= this.lastProcessedSequence) {
      return;
    }

    if (event.eventType === 'OrderCreated') {
      await dbClient.query(
        `INSERT INTO view_orders (order_id, customer_id, total_amount, status, last_seq)
         VALUES ($1, $2, $3, $4, $5)
         ON CONFLICT (order_id) DO NOTHING`,
        [event.aggregateId, event.payload.customerId, event.payload.totalAmount, 'CREATED', event.sequenceNumber]
      );
    } else if (event.eventType === 'OrderPaid') {
      await dbClient.query(
        `UPDATE view_orders SET status = 'PAID', last_seq = $1 WHERE order_id = $2 AND last_seq < $1`,
        [event.sequenceNumber, event.aggregateId]
      );
    }

    this.lastProcessedSequence = event.sequenceNumber;
  }
}
```

---

## 4. Mathematical Invariants & Replay Theorem

$$\text{Replay Equivalence Theorem: } \text{State}_{\text{current}} \equiv \text{Fold}(Init, \text{Events}_{1..n})$$

$$\text{Optimistic Concurrency: } \text{Append}(E, V_{\text{expected}}) \implies \begin{cases} \text{SUCCESS}, & \text{if } V_{\text{current}} = V_{\text{expected}} \\ \mathbf{CONCURRENCY\_FAIL}, & \text{if } V_{\text{current}} \neq V_{\text{expected}} \end{cases}$$

$$\text{Projection Idempotency: } \text{Project}(\text{Event}_k) \circ \text{Project}(\text{Event}_k) = \text{Project}(\text{Event}_k)$$

---

## 5. Guardrails

### Operational Restrictions

- **Never Update or Delete Events**: Event log is strictly append-only (`INSERT` allowed; `UPDATE` / `DELETE` strictly forbidden).
- **Optimistic Concurrency Mandatory**: Every event append must supply `expected_version` to prevent lost updates under race conditions.
- **Idempotent Projections**: Materialized view projection handlers must track sequence numbers to ignore duplicate event deliveries safely.

### Architecture Invariants

- **Transactional Outbox**: Always write domain events and outbox messages within the same database transaction block.
- **Side-Effect Free Reducers**: Aggregate state reducers (`apply`) must be pure functions with zero network/disk side-effects.

---

## 6. Atomic Failure Recovery & Rollback Handler

Before running migration scripts, capture baseline state. If projection or event store tests fail:

```bash
# Revert read model projections or event store schema migrations
if [ -n "${MODIFIED_FILES:-}" ]; then
  git checkout -- ${MODIFIED_FILES} 2>/dev/null
fi
```

---

## 7. Verification Plan & Toolchain Commands

Execute event sourcing replay and projection unit tests:

```bash
# 1. Run event replay and aggregate reducer unit tests
npm test

# 2. Verify projection idempotency with duplicate event stream test
npx jest tests/event-sourcing/projection.test.ts
```

---

## 8. Completion Report

Report aggregate roots designed, event schemas created (`v1.0.0`), event store persistence engine, concurrency strategy, projection strategy, snapshot frequency, and deterministic event replay verification results.
