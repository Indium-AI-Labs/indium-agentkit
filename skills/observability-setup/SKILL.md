---
name: observability-setup
description: "Instrument code with structured logging, metrics, distributed tracing, or alerting following existing observability patterns and avoiding credential exposure."
---

# Observability setup

Add or improve observability instrumentation so operators can detect, diagnose,
and resolve issues from production signals. Inspect the project's existing
logging, metrics, and tracing patterns before introducing new conventions.

## Workflow

1. Read `AGENTS.md`, existing observability code, logging configuration,
   metrics exports, tracing setup, and alert definitions. Identify the
   established libraries, formats, and destinations.
2. Define what operators need to observe: request flow, error rates, latency
   distributions, resource utilization, business outcomes, or dependency
   health. State what is currently missing.
3. Add structured log statements at meaningful decision points: request entry,
   authorization, data mutation, external calls, errors, and retry or fallback
   paths. Use consistent field names and severity levels.
4. Never log credentials, tokens, session identifiers, personal data, or
   request bodies that contain sensitive content. Redact or omit.
5. Add metrics for the signals that drive alerts and dashboards: counters for
   operations, histograms for latency, gauges for queue depth or connection
   pools. Reuse the project's metrics library.
6. Propagate trace context through service boundaries where distributed tracing
   is in use. Add spans for I/O-bound or high-latency operations.
7. Define or update alert rules with actionable thresholds, severity, runbook
   links, and clear ownership. Avoid alert fatigue from noisy or duplicate
   signals.
8. Verify instrumentation compiles, tests pass, and logs and metrics appear in
   local or test output without exposing sensitive data.

## Guardrails

- Follow the project's existing observability stack. Do not introduce a
  competing logging or metrics framework without approval.
- Keep instrumentation lightweight; do not add high-cardinality labels or
  verbose logging that could impact performance or cost.
- Optional performance-profiler delegation can verify overhead, but one agent
  can complete this workflow.

## Completion report

Report instrumentation added, signals covered, libraries used, alert
definitions, sensitive-data safeguards, tests run, and unobserved areas.
