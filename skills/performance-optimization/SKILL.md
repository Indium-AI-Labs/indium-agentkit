---
name: performance-optimization
description: "Measure, analyze, and optimize a specific performance bottleneck through profiling, targeted change, and comparative re-measurement with evidence."
---

# Performance Optimization

Improve a measurable performance characteristic through evidence, not
intuition: **profile first, change second, re-measure third**. The default
tooling is a repeatable benchmark harness (`autocannon` or `k6` for HTTP
services, a `timeit`-style microbenchmark for library code), a runtime
profiler with flamegraph output (`py-spy`, `perf`, Node `--cpu-prof`,
browser tooling), and a statistical comparison over repeated runs.

Inspect the project's runtime and existing benchmarking or profiling
infrastructure before choosing a method; reuse the project's harness where
one exists and record every command, parameter, and environment detail so
results are reproducible by another engineer.

---

## 1. Required I/O Context Schemas & Natural Language Auto-Inference

The skill supports **two invocation modes**:

1. **Orchestrator / Technical Mode (JSON Manifest)**: Pass the JSON context
   manifest below.
2. **Non-Technical Mode (Plain English Prompts)**: If the user provides a
   natural language prompt (e.g. *"The /v1/search endpoint feels slow since
   the ranking change; p95 looks like it doubled"*), the agent **must
   automatically infer and populate** `benchmark_spec`,
   `profiling_context`, and `change_budget` from the user's text and the
   repository layout.

### JSON Context Manifest Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "PerformanceOptimizationContextManifest",
  "type": "object",
  "required": ["benchmark_spec"],
  "properties": {
    "benchmark_spec": {
      "type": "object",
      "required": ["metric", "workload", "environment", "target"],
      "properties": {
        "metric": { "type": "string", "enum": ["latency_p50", "latency_p95", "latency_p99", "throughput_rps", "memory_rss", "cpu_time", "cold_start_ms"] },
        "workload": { "type": "string" },
        "environment": { "type": "string" },
        "target": { "type": "string" },
        "duration_seconds": { "type": "integer", "default": 30 },
        "warmup_seconds": { "type": "integer", "default": 5 }
      }
    },
    "profiling_context": {
      "type": "object",
      "properties": {
        "profiler": { "type": "string", "enum": ["py_spy", "perf", "node_cpu_prof", "browser_devtools", "project_existing", "unknown"], "default": "unknown" },
        "profile_format": { "type": "string", "enum": ["flamegraph", "speedscope", "pprof", "text"], "default": "flamegraph" }
      }
    },
    "change_budget": {
      "type": "object",
      "properties": {
        "max_files_changed": { "type": "integer", "default": 5 },
        "allow_dependency_changes": { "type": "boolean", "default": false },
        "significance_threshold_pct": { "type": "number", "default": 5.0 },
        "min_runs": { "type": "integer", "default": 5 }
      }
    }
  }
}
```

### Automatic Natural Language Inference & Safety Rules

If no raw JSON payload is provided, apply these defaults and safety checks:

- **`metric`**: Inferred from the complaint ("slow endpoint" becomes
  `latency_p95`; "slow to boot" becomes `cold_start_ms`; "falls over under
  load" becomes `throughput_rps`). If the metric is ambiguous, ask before
  measuring.
- **`workload`**: Extracted from the prompt or the nearest existing
  benchmark. A concrete workload is mandatory; never optimize against an
  undefined one.
- **`environment`**: Captured from the current machine and runtime (OS,
  CPU count, runtime version); recorded verbatim in the evidence log.
- **`target`**: Inferred from the prompt (e.g. "back under 200ms"). If none
  is stated, propose an improvement of at least
  `significance_threshold_pct` and confirm before implementing.
- **`profiling_context.profiler`**: Detected from the runtime (`py_spy`
  for Python, `node_cpu_prof` for Node, `perf` for native) unless
  `project_existing` tooling is declared in `AGENTS.md` or scripts.
- **Safety**: Benchmarks and profilers run only against local or
  explicitly designated non-production targets. Never run load generators
  against production without written authorization.

---

## 2. Deterministic State Machine Execution Flow

Follow this exact sequential protocol. Do not skip steps or alter execution
ordering.

### Step 1: Context Ingestion & Metric Definition

1. Read `AGENTS.md`, the performance concern, and any existing benchmarks
   or profiling infrastructure.
2. Define the metric, workload, environment, and acceptable target before
   optimizing; write them into the evidence log as the run contract.
3. Confirm the target under test is non-production and the workload
   generator is safe to run.

### Step 2: Reproducible Baseline

1. Establish a reproducible baseline measurement with an explicit
   workload, environment, and methodology.
2. Record the exact commands, parameters, seeds, runtime versions, and
   results (`min_runs` repetitions, median and p95).
3. Freeze the environment as far as practical: eliminate background load,
   keep power and thermal conditions stable, and note anything that could
   not be controlled.

### Step 3: Profile Under Representative Load

1. Profile the target under the representative workload using the
   project's existing tools or standard runtime profilers.
2. Identify the bottleneck from data, not assumption: the top self-time
   frames must account for a meaningful share of total time before they
   qualify as the bottleneck.

### Step 4: Hypothesis & Expected Effect

1. Form a hypothesis about the root cause, supported by profiling
   evidence.
2. State the expected improvement as a quantitative range, the mechanism,
   and the potential side effects (memory, readability, tail latency,
   correctness risk).

### Step 5: Smallest Targeted Change

1. Implement the smallest targeted change that addresses the measured
   bottleneck, within `max_files_changed`.
2. Do not apply speculative optimizations, unrelated refactors, or
   dependency upgrades (`allow_dependency_changes` defaults to `false`) as
   part of this change.

### Step 6: Comparative Re-Measurement

1. Re-measure with the identical workload, methodology, and environment.
2. Compare results quantitatively against the baseline using the
   statistical method in Section 4; record improvement, regression, or no
   change.

### Step 7: Behavioral Equivalence

1. Run the project's full test suite to verify behavioral equivalence.
2. An optimization that breaks correctness is not an optimization: revert
   it and record the failure.

### Step 8: Evidence Report

1. Document the baseline, profile evidence, change, re-measurement, side
   effects, and remaining opportunities.
2. Do not claim performance improvements without comparative evidence from
   identical workloads.

---

## 3. Reference Implementation: Benchmark Harness & Flamegraph Interpretation

```python
#!/usr/bin/env python3
"""Repeatable latency benchmark harness (baseline vs candidate).

Usage:
  python scripts/bench_endpoint.py --label baseline  --runs 7 --out bench/baseline.json
  python scripts/bench_endpoint.py --label candidate --runs 7 --out bench/candidate.json
"""
import argparse
import json
import statistics
import time
import urllib.request


def percentile(sorted_samples: list[float], p: float) -> float:
    if not sorted_samples:
        raise ValueError("no samples")
    k = (len(sorted_samples) - 1) * p
    lo = int(k)
    hi = min(lo + 1, len(sorted_samples) - 1)
    return sorted_samples[lo] + (sorted_samples[hi] - sorted_samples[lo]) * (k - lo)


def run_once(url: str, payload: bytes) -> float:
    req = urllib.request.Request(
        url, data=payload, headers={"Content-Type": "application/json"}
    )
    start = time.perf_counter_ns()
    with urllib.request.urlopen(req, timeout=10) as resp:
        resp.read()
    return (time.perf_counter_ns() - start) / 1e6  # milliseconds


def benchmark(label: str, url: str, payload: bytes, runs: int, warmup: int) -> dict:
    for _ in range(warmup):
        run_once(url, payload)  # warm caches, JIT, and connection pools
    samples = sorted(run_once(url, payload) for _ in range(runs))
    return {
        "label": label,
        "url": url,
        "runs": runs,
        "warmup": warmup,
        "min_ms": samples[0],
        "median_ms": statistics.median(samples),
        "p95_ms": percentile(samples, 0.95),
        "max_ms": samples[-1],
        "stdev_ms": statistics.stdev(samples) if runs > 1 else 0.0,
        "samples_ms": samples,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", required=True, choices=["baseline", "candidate"])
    parser.add_argument("--url", default="http://127.0.0.1:8080/v1/search")
    parser.add_argument("--runs", type=int, default=7)
    parser.add_argument("--warmup", type=int, default=3)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    payload = json.dumps({"query": "red sneakers", "limit": 20}).encode()
    result = benchmark(args.label, args.url, payload, args.runs, args.warmup)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2)
    print(f"{result['label']}: median={result['median_ms']:.1f}ms p95={result['p95_ms']:.1f}ms")


if __name__ == "__main__":
    main()
```

Flamegraph interpretation walkthrough (profiling evidence, Step 3):

1. Capture the profile under the same workload, for example
   `py-spy record -o bench/profile.svg --format flamegraph --duration 30 -- python -m app.server`
   while the harness drives load.
2. Read width, not color: a frame's width is its share of sampled on-CPU
   time. Frames under roughly 2 percent of total width are noise for
   optimization purposes.
3. In the example profile, `rank_results` occupies 61 percent of total
   width, and 48 of those 61 points are self-time inside a nested
   `score_document` loop that recompiles a regular expression per
   document: that is the bottleneck, stated from data.
4. Follow the stack upward to confirm the call path belongs to the
   reported endpoint (`handle_search` to `rank_results`), ruling out
   background tasks and unrelated workers.
5. Hypothesis (Step 4): hoisting the compiled pattern out of the loop
   removes the per-document compile; expected 35-50 percent median latency
   reduction; side effects: one cached compiled pattern, negligible memory.
6. If the top frames are I/O waits (`recv`, `epoll_wait`) rather than CPU
   work, switch tooling to an off-CPU profile or trace-level timing
   instead of guessing at CPU optimizations.

---

## 4. Statistical Comparison & Behavioral Equivalence Verification

Compare medians over at least `min_runs` runs per variant; an improvement
counts only when it clears both the significance threshold and the noise
band. The results table template keeps the evidence auditable:

```text
| variant   | runs | median_ms | p95_ms | stdev_ms | vs baseline |
|-----------|------|-----------|--------|----------|-------------|
| baseline  | 7    | 412.3     | 468.9  | 21.4     | -           |
| candidate | 7    | 261.8     | 299.5  | 14.1     | -36.5%      |
```

```bash
# 1. Interleaved runs reduce drift bias: A/B/A/B rather than all A then all B.
for i in 1 2 3 4 5 6 7; do
  python scripts/bench_endpoint.py --label baseline  --out "bench/base_$i.json"
  python scripts/bench_endpoint.py --label candidate --out "bench/cand_$i.json"
done

# 2. Significance gate: the improvement must exceed both the threshold and the noise band.
python - <<'PY'
import glob, json, statistics

def medians(pattern):
    return [json.load(open(p))["median_ms"] for p in sorted(glob.glob(pattern))]

base = medians("bench/base_*.json")
cand = medians("bench/cand_*.json")
noise = max(statistics.stdev(base) / statistics.median(base), 0.02) * 100
delta = (statistics.median(cand) - statistics.median(base)) / statistics.median(base) * -100
print(f"baseline noise band: +/-{noise:.1f}%  candidate delta: {delta:+.1f}%")
assert delta >= max(5.0, 2 * noise), "improvement is not statistically meaningful"
PY

# 3. Behavioral equivalence: the full project test suite must pass unchanged.
python -m unittest discover -s tests -v   # or: npm run test / pytest
```

---

## 5. Significance, Noise & Regression Budget Mathematics

$$\Delta_{\text{improvement}} = \frac{\text{median}_{\text{base}} - \text{median}_{\text{cand}}}{\text{median}_{\text{base}}} \times 100 \;\ge\; \max(5\%,\; 2 \cdot \text{NoiseBand})$$

$$\text{NoiseBand} = \frac{\sigma(\text{median}_{\text{base, runs}})}{\text{median}(\text{median}_{\text{base, runs}})} \times 100, \qquad n_{\text{runs}} \ge 5$$

$$\text{CV}_{\text{workload}} = \frac{\sigma_{\text{samples}}}{\mu_{\text{samples}}} \le 0.10 \;\Rightarrow\; \text{methodology stable enough to trust}$$

$$\text{RegressionBudget}: \quad \Delta_{\text{secondary}} \ge -2\% \quad \forall \text{ secondary metrics (memory, throughput, tail latency)}$$

$$\text{Claim valid} \iff \text{same workload} \;\wedge\; \text{same environment} \;\wedge\; n_{\text{runs}} \ge 5 \;\wedge\; \text{test suite green}$$

---

## 6. Guardrails

### Operational Restrictions

- **Profiling Before Changing Is Mandatory**: Do not optimize without a
  measured bottleneck identified from profiling data, not assumption.
- **No Speculative Optimization**: Change only what the profile
  implicates; no unrelated refactors, drive-by cleanups, or dependency
  upgrades inside an optimization change.
- **Non-Production Measurement Only**: Run load generators and profilers
  only against local or explicitly designated non-production targets.
- **Single-Agent Executable**: An optional performance-profiler subagent
  can gather measurements, but one agent must be able to complete this
  workflow end to end.

### Security Invariants

- **No Production Data in Benchmarks**: Benchmark payloads and fixtures
  must be synthetic or fully anonymized; never copy production records,
  credentials, or tokens into benchmark scripts, profiles, or reports.
- **No Correctness Sacrifice**: Do not sacrifice readability, correctness,
  or maintainability for marginal gains without explicit approval; a
  failing test suite blocks the change unconditionally.
- **No Security-Control Weakening**: Never disable TLS verification, auth
  checks, rate limits, or caching safeguards to manufacture a latency win.

---

## 7. Atomic Failure Recovery & Rollback Handler

Before creating or modifying files, capture a baseline list of modified and
untracked files. If re-measurement shows a regression beyond the regression
budget, the significance gate fails, or the test suite breaks and cannot be
resolved within 2 iterations, execute targeted rollback restricted ONLY to
files created or modified during this run:

```bash
# Revert ONLY modified files tracked during this execution run
if [ -n "${MODIFIED_FILES:-}" ]; then
  git checkout -- ${MODIFIED_FILES} 2>/dev/null
fi

# Remove ONLY newly created untracked files from this execution run (e.g. bench artifacts)
if [ -n "${CREATED_FILES:-}" ]; then
  rm -rf ${CREATED_FILES} 2>/dev/null
fi
```

After executing targeted rollback, output the exact error trace or
measurement table that triggered the rollback, and record the attempt
(hypothesis, evidence, outcome) so the next attempt does not repeat it.
Benchmark JSON artifacts and profiles may be retained for the report even
when code changes are reverted; state which artifacts were kept.

---

## 8. Verification Plan & Benchmark Toolchain Commands

Execute the following commands; adapt tool names to the runtime and the
harness already present in the repository:

```bash
# 1. Capture the baseline with the frozen workload
python scripts/bench_endpoint.py --label baseline --runs 7 --out bench/baseline.json

# 2. Capture the profile under the same workload
py-spy record -o bench/profile.svg --format flamegraph --duration 30 -- python -m app.server &
python scripts/bench_endpoint.py --label baseline --runs 7 --out bench/profile_run.json

# 3. After the targeted change: candidate measurement, identical methodology
python scripts/bench_endpoint.py --label candidate --runs 7 --out bench/candidate.json

# 4. Statistical significance gate (Section 4)
python scripts/compare_benchmarks.py "bench/base_*.json" "bench/cand_*.json"

# 5. Behavioral equivalence: full project test suite
python -m unittest discover -s tests -v
```

---

## 9. Completion Report

Report the metric, workload, and environment contract; the baseline results
with exact commands and parameters; the profiling method and the bottleneck
identified from the evidence; the hypothesis and the targeted change made
(files touched, change summary); the candidate re-measurement with the
statistical comparison (median, p95, noise band, delta); the behavioral
verification results; side effects on secondary metrics; and the remaining
performance opportunities ranked by expected value.
