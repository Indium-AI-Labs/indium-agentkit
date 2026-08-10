---
name: estimate-work
description: "Break down a feature, fix, or change into estimated effort with scope, risk factors, assumptions, and sequencing before prioritization."
---

# Estimate work

Produce a scope and effort assessment for a proposed change. Extract sizing
evidence from the codebase; do not guess complexity without inspecting the
affected areas.

## Workflow

1. Read `AGENTS.md`, the request, and the affected code, APIs, data, tests,
   and deployment constraints. Clarify ambiguity before estimating.
2. Decompose the work into independently deliverable slices. For each slice
   identify the affected files, interfaces, tests, and integration points.
3. Assess complexity factors: number of systems touched, data migration needs,
   backward-compatibility constraints, unfamiliar code paths, and external
   dependencies.
4. Identify risks and unknowns that could expand scope: unclear requirements,
   missing test coverage, fragile integrations, and unproven technologies.
5. Provide a relative size assessment with explicit assumptions. State what
   would make the estimate larger or smaller. Do not invent precise hour
   counts without evidence.
6. Suggest a delivery sequence with dependencies between slices. Flag slices
   that can be parallelized and those that gate others.
7. Report the decomposition, sizing, risk factors, assumptions, sequencing,
   and anything that needs clarification before committing to the estimate.

## Guardrails

- Estimates are advisory. Do not commit to timelines on behalf of the team.
- State assumptions explicitly; an estimate without visible assumptions is
  unreliable by definition.
- An optional explorer subagent can map the codebase, but one agent can
  complete this workflow.

## Completion report

Report work slices, relative sizing, risk factors, dependencies, delivery
sequence, assumptions, and open questions.
