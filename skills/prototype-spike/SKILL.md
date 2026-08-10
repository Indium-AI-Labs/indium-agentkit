---
name: prototype-spike
description: "Investigate a technical approach through a time-boxed, throwaway spike that produces evidence and a go-or-no-go recommendation before committing to a design."
---

# Prototype spike

Run a focused technical investigation to answer a specific question before
committing to a design or implementation. The output is evidence and a
recommendation, not production code.

## Workflow

1. State the question the spike must answer, the criteria for go and no-go,
   and the time or scope boundary. A spike without a clear question wastes
   effort.
2. Read `AGENTS.md`, the relevant code, and the constraints that motivated the
   investigation. Identify what is unknown and what evidence would resolve it.
3. Build the simplest possible experiment that tests the hypothesis. Use
   throwaway code, isolated scripts, or minimal reproductions. Do not build
   production infrastructure.
4. Execute the experiment and record results: does the approach work, what are
   the limitations, what is the performance, what are the integration
   challenges?
5. Assess the results against the go-or-no-go criteria. State clearly whether
   the approach is viable, conditionally viable, or not viable.
6. Document the evidence, alternative approaches considered, and the
   recommendation. Include enough detail for the implementing agent to
   proceed without repeating the investigation.
7. Clean up or clearly label throwaway code. Do not merge spike code into
   production branches.

## Guardrails

- Spike code is disposable. Do not optimize, test, or document it to
  production standards.
- Do not make production changes, install production dependencies, or modify
  shared infrastructure during a spike.
- An optional explorer subagent can map the codebase, but one agent can
  complete this workflow.

## Completion report

Report the question investigated, experiment design, results, go-or-no-go
recommendation, alternative approaches, evidence, and what the implementing
agent needs to proceed.
