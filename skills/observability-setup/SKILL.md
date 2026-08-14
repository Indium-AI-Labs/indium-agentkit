---
name: observability-setup
description: "Instrument code with structured logging, metrics, distributed tracing, or alerting following existing observability patterns and avoiding credential exposure."
---

# Observability Setup

Add or improve observability instrumentation so operators can detect,
diagnose, and resolve issues from production signals: structured logs,
metrics, distributed traces, and actionable alerts. The default target
stack is a **structured JSON logger with field redaction**,
**Prometheus-style metrics (counters, histograms, gauges)**,
**OpenTelemetry tracing with context propagation**, and **threshold-based
alert rules with runbook links and owners**.

Inspect the project's existing logging, metrics, and tracing patterns
before introducing new conventions: reuse the established libraries,
formats, and destinations, and never add a competing framework without
explicit approval.

---

## 1. Required I/O Context Schemas & Natural Language Auto-Inference

The skill supports **two invocation modes**:

1. **Orchestrator / Technical Mode (JSON Manifest)**: Pass the JSON context
   manifest below.
2. **Non-Technical Mode (Plain English Prompts)**: If the user provides a
   natural language prompt (e.g. *"Add request latency metrics and error
   alerts to the billing service"*), the agent **must automatically infer
   and populate** `instrumentation_spec`, `stack_context`, and
   `alert_context` from the user's text and the existing repository
   conventions.

### JSON Context Manifest Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "ObservabilitySetupContextManifest",
  "type": "object",
  "required": ["instrumentation_spec", "stack_context"],
  "properties": {
    "instrumentation_spec": {
      "type": "object",
      "required": ["services", "signals"],
      "properties": {
        "services": {
          "type": "array",
          "items": { "type": "string", "pattern": "^[a-z0-9-]+$" },
          "minItems": 1
        },
        "signals": {
          "type": "array",
          "items": { "type": "string", "enum": ["logs", "metrics", "traces", "alerts"] },
          "minItems": 1
        },
        "operator_questions": {
          "type": "array",
          "items": { "type": "string" }
        }
      }
    },
    "stack_context": {
      "type": "object",
      "required": ["logging_library", "metrics_library"],
      "properties": {
        "logging_library": { "type": "string" },
        "metrics_library": { "type": "string" },
        "tracing_library": { "type": "string" },
        "destinations": {
          "type": "array",
          "items": { "type": "string" }
        }
      }
    },
    "alert_context": {
      "type": "object",
      "properties": {
        "severity_levels": {
          "type": "array",
          "items": { "type": "string", "enum": ["page", "ticket", "info"] },
          "default": ["page", "ticket"]
        },
        "max_alerts_per_service": { "type": "integer", "default": 10 },
        "runbook_url_template": { "type": "string" }
      }
    }
  }
}
```

### Automatic Natural Language Inference & Safety Rules

If no raw JSON payload is provided, apply these defaults and safety checks:

- **`services`**: Extracted from the prompt noun or the module being
  edited; defaults to the service that owns the files in the change set.
- **`signals`**: Inferred from prompt keywords ("log", "metric", "trace",
  "alert"). Defaults to the signals the service currently lacks, per the
  gap analysis in Step 2.
- **`stack_context`**: Detected from dependency manifests
  (`package.json`, `pyproject.toml`, `go.mod`) and existing
  instrumentation modules. If no metrics library exists, ask before
  introducing one; never run two metrics frameworks side by side.
- **`destinations`**: Detected from existing exporter configuration (for
  example a `/metrics` endpoint or a collector address). Do not invent new
  destinations.
- **`alert_context.max_alerts_per_service`**: Defaults to 10; treat the
  budget as a hard ceiling and consolidate or drop low-value rules before
  adding new ones.
- **Sensitive-data safety**: Field names such as `password`, `token`,
  `secret`, `authorization`, `cookie`, `session_id`, and `email` are always
  redacted by default, even when the user does not mention them.

---

## 2. Deterministic State Machine Execution Flow

Follow this exact sequential protocol. Do not skip steps or alter execution
ordering.

### Step 1: Context Ingestion & Stack Discovery

1. Read `AGENTS.md`, existing observability code, logging configuration,
   metrics exports, tracing setup, and alert definitions.
2. Identify the established libraries, formats (JSON versus text), field
   naming conventions, severity levels, and destinations.
3. Record the discovered stack in `stack_context`; any deviation requires
   explicit user approval before implementation.

### Step 2: Operator Need & Gap Analysis

1. Define what operators need to observe: request flow, error rates,
   latency distributions, resource utilization, business outcomes, or
   dependency health.
2. Map each need to a concrete signal and state precisely what is
   currently missing; do not instrument what no operator question
   requires.

### Step 3: Structured Logging at Decision Points

1. Add structured log statements at meaningful decision points: request
   entry, authorization decisions, data mutations, external calls, errors,
   and retry or fallback paths.
2. Use consistent field names and severity levels matching the project's
   existing conventions (`request_id`, `actor_id`, `duration_ms`, and so
   on).

### Step 4: Sensitive-Data Redaction

1. Never log credentials, tokens, session identifiers, personal data, or
   request bodies that contain sensitive content.
2. Redact or omit fields through the logger's central redaction layer;
   keep the denylist in a single auditable location rather than scattering
   ad-hoc filters across call sites.

### Step 5: Metrics for Alerting Signals

1. Add metrics for the signals that drive alerts and dashboards: counters
   for operations, histograms for latency, gauges for queue depth or
   connection pools.
2. Reuse the project's metrics library and naming scheme
   (`<service>_<operation>_<unit>`); keep label cardinality inside the
   budget from Section 5.

### Step 6: Trace Context Propagation & Spans

1. Propagate trace context through service boundaries (HTTP headers,
   message metadata) wherever distributed tracing is in use.
2. Add spans for I/O-bound or high-latency operations (database queries,
   outbound HTTP, queue publishes); do not wrap trivial CPU-only helpers.

### Step 7: Actionable Alert Rules

1. Define or update alert rules with actionable thresholds, severity,
   runbook links, and clear ownership.
2. Avoid alert fatigue: every `page`-level rule must map to a documented
   operator action; deduplicate rules that fire on the same condition.

### Step 8: Local Verification

1. Verify instrumentation compiles and the project's tests pass.
2. Verify logs and metrics appear in local or test output without exposing
   sensitive data, using the pattern in Section 4.

---

## 3. Reference Implementation: Structured Logging, RED Metrics & Span Propagation

```typescript
import { trace, context, SpanStatusCode, propagation } from '@opentelemetry/api';
import client from 'prom-client';

// --- 1. Structured logger with a single auditable redaction denylist ---
const SENSITIVE_FIELDS = new Set([
  'password', 'token', 'secret', 'authorization', 'cookie', 'session_id',
  'email', 'ssn', 'credit_card',
]);

type LogFields = Record<string, unknown>;

function redact(fields: LogFields): LogFields {
  const out: LogFields = {};
  for (const [key, value] of Object.entries(fields)) {
    out[key] = SENSITIVE_FIELDS.has(key.toLowerCase()) ? '[REDACTED]' : value;
  }
  return out;
}

function write(level: 'info' | 'error', event: string, fields: LogFields): void {
  const line = JSON.stringify({
    level,
    event,
    ts: new Date().toISOString(),
    ...redact(fields),
  });
  process.stdout.write(line + '\n');
}

export const logger = {
  info: (event: string, fields: LogFields = {}) => write('info', event, fields),
  error: (event: string, fields: LogFields = {}) => write('error', event, fields),
};

// --- 2. Prometheus-style RED metrics; low-cardinality labels only ---
const register = new client.Registry();
client.collectDefaultMetrics({ register });

export const httpRequestsTotal = new client.Counter({
  name: 'billing_http_requests_total',
  help: 'Total HTTP requests by route template, method, and status class.',
  // Route templates only: never raw paths, IDs, or query strings.
  labelNames: ['route', 'method', 'status_class'],
  registers: [register],
});

export const httpRequestDuration = new client.Histogram({
  name: 'billing_http_request_duration_seconds',
  help: 'HTTP request latency distribution.',
  labelNames: ['route', 'method'],
  buckets: [0.005, 0.025, 0.1, 0.25, 0.5, 1, 2.5],
  registers: [register],
});

export const queueDepth = new client.Gauge({
  name: 'billing_outbound_queue_depth',
  help: 'Current depth of the outbound webhook queue.',
  registers: [register],
});

// --- 3. Request middleware: logs, metrics, and a server span in one seam ---
const tracer = trace.getTracer('billing-service');

export function observabilityMiddleware(req, res, next): void {
  const startedAt = process.hrtime.bigint();
  const requestId = req.headers['x-request-id'] ?? crypto.randomUUID();
  const routeTemplate = req.route?.path ?? 'unknown';

  // Extract upstream trace context so this span joins the caller's trace.
  const parentContext = propagation.extract(context.active(), req.headers);

  context.with(parentContext, () => {
    tracer.startActiveSpan(`${req.method} ${routeTemplate}`, (span) => {
      span.setAttribute('http.request.method', req.method);
      span.setAttribute('http.route', routeTemplate);
      logger.info('http.request.start', {
        request_id: requestId,
        route: routeTemplate,
        method: req.method,
      });

      res.on('finish', () => {
        const durationSeconds = Number(process.hrtime.bigint() - startedAt) / 1e9;
        const statusClass = `${Math.floor(res.statusCode / 100)}xx`;
        httpRequestsTotal.inc({ route: routeTemplate, method: req.method, status_class: statusClass });
        httpRequestDuration.observe({ route: routeTemplate, method: req.method }, durationSeconds);
        span.setAttribute('http.response.status_code', res.statusCode);
        if (res.statusCode >= 500) {
          span.setStatus({ code: SpanStatusCode.ERROR });
        }
        logger.info('http.request.finish', {
          request_id: requestId,
          status: res.statusCode,
          duration_ms: Math.round(durationSeconds * 1000),
        });
        span.end();
      });

      next();
    });
  });
}

// --- 4. Outbound call seam: inject trace context for the downstream hop ---
export async function callDownstream(url: string, payload: unknown, requestId: string) {
  return tracer.startActiveSpan('downstream.payments.authorize', async (span) => {
    const headers: Record<string, string> = {};
    propagation.inject(context.active(), headers); // W3C traceparent headers
    try {
      logger.info('downstream.call.start', { request_id: requestId, target: 'payments' });
      const response = await fetch(url, { method: 'POST', headers, body: JSON.stringify(payload) });
      span.setAttribute('http.response.status_code', response.status);
      return response;
    } catch (err) {
      span.setStatus({ code: SpanStatusCode.ERROR });
      logger.error('downstream.call.error', { request_id: requestId, target: 'payments', error_kind: 'network' });
      throw err;
    } finally {
      span.end();
    }
  });
}

export { register };
```

---

## 4. Local Verification Pattern: Redaction & Metrics Scrape Tests

```typescript
import { test, expect, vi } from 'vitest';
import { logger, register, httpRequestsTotal } from './observability';

test('logger redacts sensitive fields before writing', () => {
  const writeSpy = vi.spyOn(process.stdout, 'write').mockImplementation(() => true);

  logger.info('payment.attempt', {
    request_id: 'req-123',
    authorization: 'Bearer <test-token>',
    password: '<test-password>',
    amount_cents: 4200,
  });

  const written = writeSpy.mock.calls.map((call) => String(call[0])).join('');
  expect(written).toContain('"request_id":"req-123"');
  expect(written).toContain('"amount_cents":4200');
  expect(written).not.toContain('<test-token>');
  expect(written).not.toContain('<test-password>');
  expect(written).toContain('[REDACTED]');
  writeSpy.mockRestore();
});

test('metrics registry exposes RED series with low-cardinality labels', async () => {
  httpRequestsTotal.inc({ route: '/v1/charges', method: 'POST', status_class: '2xx' });

  const metricsText = await register.metrics();
  expect(metricsText).toContain(
    'billing_http_requests_total{route="/v1/charges",method="POST",status_class="2xx"} 1',
  );
  // Guard: no bearer material, emails, or UUID-shaped IDs in label values.
  expect(metricsText).not.toMatch(/Bearer/i);
  expect(metricsText).not.toMatch(/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}/);
});
```

Run the scrape check against a locally started instance as well:
`curl -sf http://127.0.0.1:9464/metrics | grep -E 'billing_http_requests_total'`
and confirm the emitted series carry only the declared label names.

---

## 5. Cardinality, Noise & Coverage Invariants

$$\text{SeriesCardinality}(m) = \prod_{l \in \text{labels}(m)} |\text{values}(l)| \le 1000 \quad \forall \text{ metric } m$$

$$\text{ActionableAlertRatio} = \frac{\#\{\text{alerts with a documented operator action}\}}{\#\{\text{alerts fired}\}} \ge 0.9$$

$$\text{PageBudget}(\text{service}) \le 2 \text{ pages} / \text{week}, \qquad \#\{\text{alert rules per service}\} \le \texttt{max\_alerts\_per\_service}$$

$$\text{TraceSamplingRate} = \begin{cases} 1.0 & \text{errors and slow traces} \\ \le 0.1 & \text{nominal traffic} \end{cases}$$

$$\text{RedUseCoverage} = \frac{\#\{\text{critical ops with counter} \wedge \text{latency histogram} \wedge \text{error signal}\}}{\#\{\text{critical ops}\}} = 1$$

---

## 6. Guardrails

### Operational Restrictions

- **Follow the Existing Stack**: Reuse the project's logging, metrics, and
  tracing libraries and destinations. Do not introduce a competing logging
  or metrics framework without explicit approval.
- **Lightweight Instrumentation**: Do not add high-cardinality labels
  (user IDs, request IDs, raw URLs) or verbose per-request debug logging
  that could impact performance or observability cost.
- **Bounded Alert Surface**: Stay within the alert budget; every new
  `page`-level rule needs a documented operator action, a severity, and a
  runbook link.
- **Single-Agent Executable**: Optional performance-profiler delegation
  can verify instrumentation overhead, but one agent must be able to
  complete this workflow end to end.

### Security Invariants

- **Zero Credential Exposure**: Never log credentials, tokens, session
  identifiers, personal data, or request bodies containing sensitive
  content; redact or omit through the central denylist.
- **No Sensitive Label Values**: Metric label values and span attributes
  must never contain credentials, personal data, or raw identifiers.
- **Safe Destinations**: Do not add exporters that ship telemetry to
  unapproved third-party endpoints; reuse the configured destinations
  only.

---

## 7. Atomic Failure Recovery & Rollback Handler

Before creating or modifying files, capture a baseline list of modified and
untracked files. If any verification command in Section 8 fails and cannot
be resolved within 2 iterations, execute targeted rollback restricted ONLY
to files created or modified during this run:

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
failure causes. Do not delete pre-existing dashboards, alert rules, or
exporter configuration that were not created by this run.

---

## 8. Verification Plan & Runtime Toolchain Commands

Execute the following commands using project-local runners; adapt to the
project's declared scripts and runtime:

```bash
# 1. Type check and lint the instrumented code
npx --no-install tsc --noEmit
npm run lint

# 2. Run the test suite including redaction and metrics tests
npm run test

# 3. Start the service locally and confirm the metrics endpoint emits
npm run start &
sleep 3
curl -sf http://127.0.0.1:9464/metrics | grep -E 'billing_http_requests_total'

# 4. Exercise one request and confirm structured logs contain no secrets
curl -sf -H 'Authorization: Bearer <redacted-test-token>' \
  http://127.0.0.1:8080/v1/charges -o /dev/null
# Inspect local log output: expect [REDACTED] placeholders, never token values.
```

---

## 9. Completion Report

Report the instrumentation added (log events, metric series, spans, and
alert rules), the operator questions each signal answers, the libraries and
destinations reused, the sensitive-data safeguards applied (denylist
fields, label restrictions), the alert thresholds with owners and runbook
links, the commands run with their results, any instrumentation overhead
notes, and the areas that remain unobserved with a recommended follow-up.
