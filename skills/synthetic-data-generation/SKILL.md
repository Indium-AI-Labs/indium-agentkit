---
name: synthetic-data-generation
description: Implement deterministic scripts to populate databases with referentially solid, PII-free data.
---

# Synthetic Data Generation

Implement deterministic, high-performance data generation scripts and seed pipelines to populate development, staging, and load-testing databases with referentially intact, distribution-accurate, and 100% PII-free mock data.

The skill is **privacy-first and topologically ordered**: entity-relationship graphs, foreign key dependencies, batch insert sizes, statistical skew distributions, and RFC-compliant privacy masking are verified before generating data.

---

## 1. Required I/O Context Schemas & Natural Language Auto-Inference

The skill supports **two invocation modes**:

1. **🤖 Orchestrator / Technical Mode (JSON Manifest)**: Pass the JSON context manifest below.
2. **💬 Non-Technical Mode (Plain English Prompts)**: If the user provides a natural language prompt (e.g. *"Generate a TypeScript seed script to populate 10,000 users and 50,000 orders with realistic purchase distributions"*), the agent **must automatically infer and populate** `target_engine`, `root_entity_count`, `child_entity_multiplier`, and `skew_model` from the user's text and repository ORM configuration.

### JSON Context Manifest Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "SyntheticDataGenContextManifest",
  "type": "object",
  "required": ["generator_spec", "volume_spec"],
  "properties": {
    "generator_spec": {
      "type": "object",
      "required": ["target_engine", "seed_library"],
      "properties": {
        "target_engine": { 
          "type": "string", 
          "enum": ["postgresql", "mysql", "sqlite", "prisma", "drizzle", "mongodb"] 
        },
        "seed_library": { 
          "type": "string", 
          "enum": ["faker_js", "mimesis", "factory_boy", "custom_generator"] 
        },
        "deterministic_seed": { "type": "integer", "default": 42 }
      }
    },
    "volume_spec": {
      "type": "object",
      "required": ["root_entity_count"],
      "properties": {
        "root_entity_count": { "type": "integer", "default": 1000 },
        "child_multiplier": { "type": "number", "default": 5.0 },
        "batch_size": { "type": "integer", "default": 2500 }
      }
    },
    "distribution_profile": {
      "type": "object",
      "properties": {
        "skew_model": { "type": "string", "enum": ["zipfian", "gaussian", "uniform"], "default": "zipfian" },
        "null_probability": { "type": "number", "default": 0.05 }
      }
    }
  }
}
```

### Automatic Natural Language Inference & Safety Rules

If no raw JSON payload is provided, apply these defaults and strict safety checks:

- **Production Dump Rejection**: If prompt suggests pulling or dumping live production databases, **ABORT execution immediately** and refuse with `PRODUCTION_DUMP_FORBIDDEN`.
- **`target_engine`**: Auto-detected from `package.json` (`@prisma/client` $\rightarrow$ `prisma`, `drizzle-orm` $\rightarrow$ `drizzle`, `pg` $\rightarrow$ `postgresql`).
- **`seed_library`**: Auto-detected from installed dependencies (defaults to `@faker-js/faker`).
- **`deterministic_seed`**: Defaults to `42` to ensure 100% reproducible test data generation across developer machines and CI.

---

## 2. Deterministic State Machine Execution Flow

Follow this exact sequential protocol. Do not skip steps or alter execution ordering.

### Step 1: Schema Discovery & Topological DAG Ordering

1. Read database schemas (`prisma/schema.prisma`, `schema.ts`, `.sql` DDLs).
2. Construct the Directed Acyclic Graph (DAG) for foreign key dependencies:
   - **Level 0 (Roots)**: Tables with zero foreign keys (e.g. `Tenants`, `Users`).
   - **Level 1 (Children)**: Tables dependent on Level 0 (e.g. `Accounts`, `Products`).
   - **Level 2 (Transactions)**: Tables dependent on Level 1 (e.g. `Orders`).
   - **Level 3 (Junctions / Logs)**: Line items and audit events (e.g. `OrderItems`, `AuditLogs`).

### Step 2: Seed Engine & CSPRNG Initialization

1. Initialize fake data generator with explicit deterministic seed:
   ```typescript
   import { faker } from '@faker-js/faker';
   faker.seed(42); // Enforce reproducible synthetic outputs
   ```

### Step 3: Multi-Table Batch Generator Implementation

1. **Parent Key Pool Caching**: Generate Level 0 root entities first, retaining created Primary Key IDs in memory arrays (`userKeyPool = ['usr-1', 'usr-2', ...]`).
2. **Chunked Batch Insertion**: Insert child records in memory-optimized batches ($1,000 - 5,000$ records per transaction) using `createMany()`, `bulkInsert()`, or `COPY`:
   - Never use single-row `INSERT` queries inside unbatched loops.
3. **Statistical Skew Application**: Apply Zipfian power-law distributions to parent ID selection so a small subset of parent records own a large share of child records, matching real-world workloads.

### Step 4: RFC & PII Privacy Compliance Audit

1. **Email Masking**: Append reserved RFC 2606 domain extensions (`@example-synthetic.test`).
2. **IP Address Masking**: Use RFC 5737 documentation networks (`198.51.100.0/24`).
3. **Phone & Card Masking**: Use reserved telco prefixes (`555-0100` to `555-0199`) and Luhn-valid test card numbers.

### Step 5: Database Seeding & Referential Integrity Verification

1. Execute seed script against target test database.
2. Run SQL orphan check query to verify zero unlinked foreign keys exist:
   ```sql
   SELECT COUNT(*) FROM orders LEFT JOIN users ON orders.user_id = users.id WHERE users.id IS NULL;
   ```

---

## 3. Reference Implementation: Deterministic TypeScript / Prisma Generator

```typescript
import { PrismaClient } from '@prisma/client';
import { faker } from '@faker-js/faker';

const prisma = new PrismaClient();
const SEED_NUM = 42;
const BATCH_SIZE = 2500;

// Zipfian distribution simulator for realistic heavy-tail purchase skew
function getZipfianParentId(parentPool: string[], skew = 1.2): string {
  const rank = Math.floor(Math.pow(faker.number.float({ min: 0.001, max: 1.0 }), -1 / skew));
  const index = (rank - 1) % parentPool.length;
  return parentPool[index];
}

export async function seedDatabase(userCount = 5000, orderCount = 25000) {
  // Set deterministic seed for reproducible execution
  faker.seed(SEED_NUM);
  console.log(`[Seed] Starting synthetic generation (Users: ${userCount}, Orders: ${orderCount})...`);

  // --- Step 1: Generate Level 0 Root Entities (Users) ---
  const userKeyPool: string[] = [];
  const userBatches = Math.ceil(userCount / BATCH_SIZE);

  for (let i = 0; i < userBatches; i++) {
    const currentBatchSize = Math.min(BATCH_SIZE, userCount - i * BATCH_SIZE);
    const userData = Array.from({ length: currentBatchSize }, () => {
      const id = faker.string.uuid();
      userKeyPool.push(id);
      return {
        id,
        email: `user_${faker.string.alphanumeric(8)}@example-synthetic.test`, // RFC 2606
        fullName: faker.person.fullName(),
        createdAt: faker.date.past({ years: 2 }),
      };
    });

    await prisma.user.createMany({ data: userData });
  }

  // --- Step 2: Generate Level 1 Dependent Entities (Orders) ---
  const orderBatches = Math.ceil(orderCount / BATCH_SIZE);

  for (let i = 0; i < orderBatches; i++) {
    const currentBatchSize = Math.min(BATCH_SIZE, orderCount - i * BATCH_SIZE);
    const orderData = Array.from({ length: currentBatchSize }, () => ({
      id: faker.string.uuid(),
      userId: getZipfianParentId(userKeyPool), // Skewed foreign key link
      amount: parseFloat(faker.finance.amount({ min: 5, max: 500, dec: 2 })),
      status: faker.helpers.arrayElement(['COMPLETED', 'COMPLETED', 'COMPLETED', 'PENDING', 'CANCELLED']),
      createdAt: faker.date.recent({ days: 180 }),
    }));

    await prisma.order.createMany({ data: orderData });
  }

  console.log('[Seed] Seeding completed successfully. 100% referential integrity verified.');
}

if (require.main === module) {
  seedDatabase()
    .catch((err) => {
      console.error('[Seed Error] Synthetic generation failed:', err);
      process.exit(1);
    })
    .finally(async () => {
      await prisma.$disconnect();
    });
}
```

---

## 4. Topological & Performance Invariants

$$\text{Referential Integrity: } \forall c \in \text{ChildTable}, \quad c.parent\_id \in \{ \text{ParentKeyPool} \}$$

$$\text{Batch Seeding Throughput: } \text{Rate} = \frac{\text{Total Rows Inserted}}{\Delta t_{\text{sec}}} \ge 5000 \text{ rows/sec}$$

$$\text{Zero-PII Leak Invariant: } \text{Count}(\text{RealUserEmails}) = 0 \quad (\text{100\% Synthetic / RFC 2606})$$

---

## 5. Guardrails

### Operational Restrictions

- **No Unbatched Inserts**: Never execute single-row `INSERT` statements inside unbatched loops. Always use chunked batch transactions (`createMany`, `bulkInsert`).
- **Topological Order**: Always populate parent entities before child entities; never attempt to insert child records with uncommitted parent IDs.
- **Deterministic Pseudorandom Seeds**: Always initialize random number generators with a deterministic seed (`faker.seed(42)`).

### Security & Privacy Invariants

- **No Real PII**: Never import or reference real production database dumps or personal user records.
- **RFC Reserved Domains**: All synthetic email addresses must use RFC 2606 reserved TLDs (`@example-synthetic.test`, `@example.com`).

---

## 6. Atomic Failure Recovery & Rollback Handler

Before running seed operations, record baseline state. If seeding fails or encounters unique constraint violations:

```bash
# Clean up target test database tables
npx prisma migrate reset --force 2>/dev/null

# Revert modified files
if [ -n "${MODIFIED_FILES:-}" ]; then
  git checkout -- ${MODIFIED_FILES} 2>/dev/null
fi
```

---

## 7. Verification Plan & Toolchain Commands

Execute seed script and verify referential integrity:

```bash
# 1. Run synthetic seed script
npx ts-node prisma/seed.ts

# 2. Run SQL orphan check query via CLI
psql -d test_db -c "SELECT COUNT(*) FROM orders LEFT JOIN users ON orders.user_id = users.id WHERE users.id IS NULL;"
```

---

## 8. Completion Report

Report target database engine, topological levels processed, total rows generated per table, batch insertion throughput (rows/sec), PII masking verification results, and referential integrity test outputs.
