---
name: load-testing-suite
description: Design, configure, and execute performance load and stress testing suites (k6, Locust) with latency SLAs and throughput targets.
---

# Load Testing Suite

Design, configure, and execute performance load, stress, spike, and endurance testing suites (k6, Locust, Autocannon, JMeter) to validate system throughput (RPS), response latency SLAs ($P_{95} / P_{99}$), error rates, database connection pool saturation, and system recovery under traffic surges.

The skill is **SLA-bounded and Little's Law validated**: traffic profiles, virtual user (VU) ramp-ups, HTTP thresholds, concurrent connections ($L = \lambda \cdot W$), database thread pools, and production safety guardrails are verified before executing test suites.

---

## 1. Required I/O Context Schemas & Natural Language Auto-Inference

The skill supports **two invocation modes**:

1. **🤖 Orchestrator / Technical Mode (JSON Manifest)**: Pass the JSON context manifest below.
2. **💬 Non-Technical Mode (Plain English Prompts)**: If the user provides a natural language prompt (e.g. *"Run a k6 load test targeting 2,000 RPS on /api/v1/orders with p95 latency under 200ms and error rate under 0.1%"*), the agent **must automatically infer and populate** `target_url`, `runner_tool`, `load_profile`, and `sla_targets` from the user's text.

### JSON Context Manifest Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "LoadTestingSuiteContextManifest",
  "type": "object",
  "required": ["target_scope", "test_config"],
  "properties": {
    "target_scope": {
      "type": "object",
      "required": ["target_url"],
      "properties": {
        "target_url": { "type": "string" },
        "environment": { "type": "string", "enum": ["staging", "performance_lab", "local_docker"], "default": "staging" },
        "endpoints": { "type": "array", "items": { "type": "string" } }
      }
    },
    "test_config": {
      "type": "object",
      "required": ["runner_tool", "load_profile"],
      "properties": {
        "runner_tool": { 
          "type": "string", 
          "enum": ["k6", "locust", "autocannon", "jmeter"],
          "default": "k6" 
        },
        "load_profile": { 
          "type": "string", 
          "enum": ["ramp_up_peak", "stress_surge", "soak_endurance", "spike_test"],
          "default": "ramp_up_peak" 
        },
        "target_vus": { "type": "integer", "default": 200 },
        "duration_minutes": { "type": "integer", "default": 10 }
      }
    },
    "sla_targets": {
      "type": "object",
      "properties": {
        "target_rps": { "type": "integer", "default": 1000 },
        "max_p95_latency_ms": { "type": "integer", "default": 200 },
        "max_p99_latency_ms": { "type": "integer", "default": 500 },
        "max_error_rate_pct": { "type": "number", "default": 0.1 }
      }
    }
  }
}
```

### Automatic Natural Language Inference & Production Safety Rules

If no raw JSON payload is provided, apply these defaults and strict load testing rules:

- **No Production Testing Without Consent**: NEVER execute unthrottled load or stress tests against shared production environments without explicit user consent.
- **`runner_tool`**: Auto-detected from installed dependencies (defaults to `k6`).
- **SLA Threshold Defaults**: $P_{95} \le 200\text{ ms}$, Error Rate $\le 0.1\%$.

---

## 2. Deterministic State Machine Execution Flow

Follow this exact sequential protocol. Do not skip steps or alter execution ordering.

### Step 1: Target Endpoint & Scenario Identification

1. Read API specifications, database query patterns, and target routes.
2. Identify critical traffic scenarios: high-frequency read routes, write transactions, auth bottlenecks.

### Step 2: Script Parameterization & Dynamic Tokens

1. Write parameterized test scripts using k6 or Locust:
   - Dynamic user authentication tokens (`Bearer token`).
   - Think-time pauses (`sleep(1)` to simulate real user behavior).
   - Parameterized request payloads generated dynamically per VU.

### Step 3: Load Profile Stage Construction

Configure test execution stages:
1. **Warm-up Ramp-up**: Gradually increase VUs (0 $\rightarrow$ 50 VUs in 2m).
2. **Sustained Peak Load**: Maintain peak traffic (200 VUs for 5m).
3. **Stress Surge**: Push VUs beyond normal capacity (500 VUs for 2m) to discover breaking points.
4. **Cool-down Ramp-down**: Ramp VUs down smoothly to 0.

### Step 4: System Resource Monitoring

Monitor host system metrics during execution: CPU utilization, RAM memory leaks, DB connection pool saturation, garbage collection (GC) pauses.

### Step 5: SLA Threshold Analysis & Reporting

Calculate results against k6 threshold criteria: $P_{50}, P_{90}, P_{95}, P_{99}$ latencies, HTTP 5xx error rates, throughput (RPS).

---

## 3. Reference Implementation: Production k6 Load Test Script

```javascript
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('error_rate');
const orderLatency = new Trend('order_processing_time');

export const options = {
  // Load Profile Stages
  stages: [
    { duration: '1m', target: 50 },  // Ramp up to 50 VUs
    { duration: '3m', target: 200 }, // Sustained peak at 200 VUs
    { duration: '1m', target: 400 }, // Stress surge to 400 VUs
    { duration: '1m', target: 0 },   // Ramp down
  ],
  // SLA Thresholds
  thresholds: {
    http_req_duration: ['p(95)<200', 'p(99)<500'], // p95 < 200ms, p99 < 500ms
    error_rate: ['rate<0.001'],                     // Error rate < 0.1%
  },
};

const BASE_URL = __ENV.TARGET_URL || 'http://localhost:3000';

export default function () {
  const params = {
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer fake-jwt-token-${__VU}`,
    },
  };

  const payload = JSON.stringify({
    productId: 'prod-12345',
    quantity: 1,
  });

  const res = http.post(`${BASE_URL}/api/v1/orders`, payload, params);

  // SLA Checks
  const success = check(res, {
    'status is 201': (r) => r.status === 201,
    'response time < 200ms': (r) => r.timings.duration < 200,
  });

  errorRate.add(!success);
  orderLatency.add(res.timings.duration);

  sleep(1); // Simulate think time
}
```

---

## 4. Queuing Mathematics & Performance Formulas

### 1. Little's Law (Queuing Capacity)

$$L = \lambda \cdot W$$

Where:
- $L$ = Average number of concurrent requests / users in system.
- $\lambda$ = Arrival rate / Throughput (Requests Per Second, RPS).
- $W$ = Average response latency / residence time (Seconds).

### 2. Required Virtual Users ($VU$) Calculation

$$VU = RPS \times (\text{Latency}_{\text{sec}} + \text{ThinkTime}_{\text{sec}})$$

### 3. Error Rate Percentage ($E$)

$$E = \frac{N_{\text{errors}}}{N_{\text{total}}} \times 100\% \le 0.1\%$$

---

## 5. Guardrails

### Operational Restrictions

- **No Unthrottled Production Stressing**: Never run unthrottled load or stress tests against shared production environments without explicit consent.
- **Isolated Non-Production Test Data**: All data created during load tests must be isolated in staging databases and cleaned up post-test.
- **Third-Party API Protection**: Mock third-party APIs during load testing to avoid external rate-limiting or accidental billing spikes.

---

## 6. Atomic Failure Recovery & Rollback Handler

If a load test destabilizes a staging environment:

```bash
# Cancel running k6 / Locust load testing processes
pkill -f k6 2>/dev/null || true
pkill -f locust 2>/dev/null || true

# Reset test database connection pools or staging containers
docker-compose restart db 2>/dev/null
```

---

## 7. Verification Plan & Toolchain Commands

Execute load test suite:

```bash
# 1. Execute k6 load test script in staging environment
k6 run --env TARGET_URL=http://staging.internal:3000 tests/load/order_load.js

# 2. Run Autocannon for rapid HTTP bench checks
npx autocannon -c 100 -d 30 -m POST http://localhost:3000/api/v1/orders
```

---

## 8. Completion Report

Report target URL/endpoints tested, runner tool used (k6), load stages executed, peak VUs reached, peak RPS achieved, $P_{50}, P_{90}, P_{95}, P_{99}$ latencies measured, error rate percentage, identified database connection pool bottlenecks, and infrastructure scaling recommendations.
