---
name: performance-optimization
description: "Measure, analyze, and optimize a specific performance bottleneck through profiling, targeted change, and comparative re-measurement with evidence."
---

# Performance optimization

Improve a measurable performance characteristic through evidence, not
intuition. Profile first, change second, re-measure third. Inspect the
project's runtime and tooling before choosing a profiling method.

## Workflow

1. Read `AGENTS.md`, the performance concern, and any existing benchmarks or
   profiling infrastructure. Define the metric, workload, environment, and
   acceptable target before optimizing.
2. Establish a reproducible baseline measurement with explicit workload,
   environment, and methodology. Record the exact commands, parameters, and
   results.
3. Profile the target under the representative workload. Use the project's
   existing profiling tools or standard runtime profilers. Identify the
   bottleneck from data, not assumption.
4. Form a hypothesis about the root cause, supported by profiling evidence.
   State the expected improvement and potential side effects.
5. Implement the smallest targeted change that addresses the measured
   bottleneck. Do not apply speculative optimizations or refactor unrelated
   code.
6. Re-measure with the identical workload and methodology. Compare results
   quantitatively against the baseline. Record improvement, regression, or
   no change.
7. Run the project's test suite to verify behavioral equivalence. An
   optimization that breaks correctness is not an optimization.
8. Document the baseline, change, re-measurement, side effects, and remaining
   opportunities. Do not claim performance improvements without comparative
   evidence.

## Guardrails

- Do not optimize without a measured bottleneck. Profiling before changing
  code is mandatory.
- Do not sacrifice readability, correctness, or maintainability for marginal
  gains without explicit approval.
- An optional performance-profiler subagent can gather measurements, but one
  agent can complete this workflow.

## Completion report

Report the metric, baseline, profiling method, bottleneck identified, change
made, re-measurement results, behavioral verification, and remaining
performance opportunities.
