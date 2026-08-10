---
name: load-testing-suite
description: "Design, configure, and execute load and stress testing suites (k6, Locust) with target latency SLAs, throughput targets, and tear-down verification."
---

# Load testing suite

Design, configure, and execute performance load and stress testing suites to establish throughput,
latency SLAs (p95/p99), system saturation limits, and recovery characteristics under heavy traffic.

## Workflow

1. Read `AGENTS.md`, service architecture, expected traffic volume, key user workflows, and
   performance target SLAs (e.g. 1000 RPS, p95 < 200ms, error rate < 0.1%).
2. Identify critical traffic scenarios: high-frequency read endpoints, resource-intensive write
   operations, authentication bottlenecks, and background queue processors.
3. Write load test scripts using k6, Locust, Autocannon, or Apache JMeter following project patterns.
   Parameterize request payloads, dynamic user tokens, and think-time pauses.
4. Structure load test stages: warm-up ramp-up, sustained peak load, stress surge limit test,
   and cool-down ramp-down.
5. Configure system metrics monitoring during execution: CPU/Memory utilization, database connection
   pool saturation, network I/O, and garbage collection pauses.
6. Execute the load test in a dedicated staging or performance environment. Never run destructive
   stress testing against shared production environments without explicit authorization.
7. Analyze results against SLAs: throughput, p50/p90/p95/p99 response latencies, HTTP error codes,
   and unhandled exceptions.
8. Document performance bottlenecks, concurrency locks, resource exhaustion thresholds, and recommended
   infrastructure or code optimizations.

## Guardrails

- Do not execute unthrottled load tests against third-party external APIs or production infrastructure.
- Ensure all test data generated during load testing is cleaned up or isolated in non-production stores.
- An optional performance-profiler subagent can analyze execution telemetry, but one agent can complete this workflow.

## Completion report

Report scenarios tested, peak RPS achieved, p50/p95/p99 latencies measured, error rates, resource saturation
points, identified bottlenecks, and optimization recommendations.
