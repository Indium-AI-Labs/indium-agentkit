---
name: llm-eval-harness
description: "Design and execute evaluation benchmarks for prompts, RAG retrieval pipelines, and agent tools to measure token cost, latency, accuracy, and guardrail compliance."
---

# LLM eval harness

Design, implement, and run evaluation suites for LLM prompts, RAG pipelines,
agent tools, and guardrails. Measure latency, token cost, accuracy, and output
safety against quantitative benchmarks before deploying model changes.

## Workflow

1. Read `AGENTS.md`, prompt definitions, model configuration, RAG retrieval code,
   and test datasets. Identify the evaluation goal: prompt regression, model
   upgrade, RAG accuracy, or safety boundary verification.
2. Establish golden evaluation datasets with representative input samples, expected
   ground truth, edge cases, adversarial inputs, and target metrics.
3. Define quantitative metrics: deterministic assertions (exact match, JSON schema,
   regex), LLM-as-a-judge criteria, semantic similarity, retrieval precision/recall,
   latency distribution, and token usage cost.
4. Execute the evaluation harness under consistent environment conditions. Record
   raw outputs, latency, token consumption, and pass/fail statuses.
5. Analyze failures and regressions. Distinguish prompt brittleness, retrieval
   context gaps, model reasoning errors, and guardrail false positives.
6. Benchmark baseline vs. candidate model or prompt changes. Report quantitative
   delta in accuracy, cost, and latency.
7. Integrate evaluation checks into automated test commands or CI pipelines where
   practical.
8. Capture evaluation evidence in `templates/handoffs/llm-eval-report.md` or
   the project's equivalent artifact.

## Guardrails

- Never expose credentials, API keys, or private user data in evaluation datasets
  or test output.
- Do not claim model reliability without statistical evidence over representative
  sample sizes.
- An optional llm-evaluator subagent can run evaluation passes in parallel, but one
  agent must be able to complete this workflow.

## Completion report

Report evaluation scope, dataset sample size, metrics evaluated, baseline vs.
candidate performance, cost/latency delta, safety findings, and deployment recommendations.
