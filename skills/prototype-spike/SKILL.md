---
name: prototype-spike
description: Investigate technical approaches through time-boxed, throwaway spikes that produce empirical evidence and go/no-go recommendations.
---

# Prototype Spike

Conduct time-boxed, focused technical investigations, proof-of-concepts (PoCs), and throwaway spikes to answer critical architectural questions, resolve technology integration risks, measure performance feasibility, and deliver empirical Go / Conditional-Go / No-Go recommendations before committing to production implementation.

The skill is **time-boxed, disposable, and evidence-backed**: hypotheses, evaluation criteria, throwaway directory isolation (`scratch/`), latency/memory benchmarks, integration limits, and teardown cleanup are strictly enforced without committing experimental code to production branches.

---

## 1. Required I/O Context Schemas & Natural Language Auto-Inference

The skill supports **two invocation modes**:

1. **🤖 Orchestrator / Technical Mode (JSON Manifest)**: Pass the JSON context manifest below.
2. **💬 Non-Technical Mode (Plain English Prompts)**: If the user provides a natural language prompt (e.g. *"Run a time-boxed spike to test if DuckDB can parse 100MB CSV files in Node.js within 500ms with a Go/No-Go recommendation"*), the agent **must automatically infer and populate** `spike_target`, `hypothesis`, `go_no_go_criteria`, and `timebox_hours` from the user's text.

### JSON Context Manifest Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "PrototypeSpikeContextManifest",
  "type": "object",
  "required": ["spike_spec", "experiment_config"],
  "properties": {
    "spike_spec": {
      "type": "object",
      "required": ["title", "hypothesis"],
      "properties": {
        "title": { "type": "string" },
        "hypothesis": { "type": "string" },
        "key_unknowns": { "type": "array", "items": { "type": "string" } },
        "technologies_tested": { "type": "array", "items": { "type": "string" } }
      }
    },
    "experiment_config": {
      "type": "object",
      "required": ["timebox_hours"],
      "properties": {
        "timebox_hours": { "type": "number", "default": 2.0 },
        "scratch_directory": { "type": "string", "default": "scratch/" },
        "max_latency_ms_sla": { "type": "integer", "default": 500 },
        "max_memory_mb_sla": { "type": "integer", "default": 256 }
      }
    },
    "go_no_go_criteria": {
      "type": "object",
      "required": ["go_condition", "no_go_condition"],
      "properties": {
        "go_condition": { "type": "string" },
        "no_go_condition": { "type": "string" },
        "conditional_go_terms": { "type": "string" }
      }
    }
  }
}
```

### Automatic Natural Language Inference & Disposable Code Rules

If no raw JSON payload is provided, apply these defaults and strict spike rules:

- **Disposable Code Rule**: Spike code is 100% throwaway. Do NOT write production-grade unit tests, documentation, or commit spike code to production branches.
- **Scratch Directory Isolation**: All experimental code must be created under `<appDataDir>/brain/<conversation-id>/scratch/` or `.spike/` to prevent repository contamination.
- **Explicit Go/No-Go Decision**: Every spike completion report MUST provide a clear decision: `GO`, `CONDITIONAL_GO`, or `NO_GO`.

---

## 2. Deterministic State Machine Execution Flow

Follow this exact sequential protocol. Do not skip steps or alter execution ordering.

### Step 1: Hypothesis Formulation & Boundary Definition

1. Define the specific question the spike must answer (e.g. "Can library X achieve < 200ms latency for streaming JSON responses?").
2. Establish explicit Go and No-Go threshold criteria.

### Step 2: Isolated Scratch Experiment Setup

1. Create disposable scratch directory (`scratch/spike_<name>/`).
2. Implement the minimum possible reproduction code (10–50 lines) to test the core technical assumption.

### Step 3: Empirical Benchmarking & Telemetry Capture

1. Execute the scratch script under realistic load or sample data.
2. Measure:
   - Response latency ($P_{50}, P_{95}$).
   - Peak RSS RAM memory consumption (MB).
   - Integration friction & API limitations.

### Step 4: Go / Conditional-Go / No-Go Decision Evaluation

Evaluate experiment findings against criteria:
- **GO**: Hypothesis proven; approach meets all SLA and integration requirements.
- **CONDITIONAL_GO**: Viable only if specific constraints are resolved (e.g., requires caching layer).
- **NO_GO**: Approach fails SLA thresholds or presents unacceptable security/complexity risks.

### Step 5: Teardown & Documentation Hand-Off

1. Summarize findings, performance evidence, and implementation recommendations.
2. Remove or clearly isolate throwaway scratch files.

---

## 3. Reference Implementation: Python Spike Experiment Runner

```python
import sys
import time
import tracemalloc
from typing import Callable, Dict, Any

def run_spike_experiment(
    name: str,
    target_fn: Callable[[], Any],
    max_latency_ms: float = 500.0,
    max_memory_mb: float = 256.0
) -> Dict[str, Any]:
    """Execute a time-boxed technical spike experiment and capture memory/latency metrics."""
    
    print(f"[Spike] Running investigation experiment: '{name}'...")
    tracemalloc.start()
    t0 = time.time()
    
    success = False
    error_msg = None
    
    try:
        target_fn()
        success = True
    except Exception as e:
        error_msg = str(e)
        
    latency_ms = (time.time() - t0) * 1000.0
    current_mem, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    peak_mem_mb = peak_mem / (1024.0 * 1024.0)
    
    # Evaluate Go / No-Go Decision
    verdict = "GO"
    if not success:
        verdict = "NO_GO"
    elif latency_ms > max_latency_ms or peak_mem_mb > max_memory_mb:
        verdict = "CONDITIONAL_GO" if latency_ms < max_latency_ms * 1.5 else "NO_GO"
        
    return {
        "experiment_name": name,
        "verdict": verdict,
        "latency_ms": round(latency_ms, 2),
        "max_latency_sla": max_latency_ms,
        "peak_memory_mb": round(peak_mem_mb, 2),
        "max_memory_sla": max_memory_mb,
        "error": error_msg
    }

if __name__ == "__main__":
    def sample_heavy_computation():
        # Simulated spike logic
        _ = [x ** 2 for x in range(500000)]
        
    result = run_spike_experiment("List Compression Bench", sample_heavy_computation)
    print(f"Spike Result: {result['verdict']} (Latency: {result['latency_ms']} ms, Peak RAM: {result['peak_memory_mb']} MB)")
```

---

## 4. Spike Decision Formulas & Isolation Rules

$$\text{Scratch Isolation Invariant: } \text{SpikePath} \subseteq \{\text{"scratch/"}, \text{".spike/"}\}$$

$$\text{Go Condition: } \text{Latency} \le \text{SLA}_{\text{lat}} \land \text{RAM} \le \text{SLA}_{\text{mem}} \land \text{Errors} = 0 \implies \mathbf{GO}$$

$$\text{No-Go Condition: } \text{Latency} > 1.5 \cdot \text{SLA}_{\text{lat}} \lor \text{UnresolvableBlocker} \implies \mathbf{NO\_GO}$$

---

## 5. Guardrails

### Operational Restrictions

- **No Production Code Commits**: Spike code must never be merged into production source trees.
- **Time-Box Enforcement**: Do not exceed the allocated time-box (default 2 hours) for exploratory spikes.
- **Do Not Polish Disposable Code**: Avoid writing production unit tests, JSDoc, or refactoring throwaway spike code.

---

## 6. Atomic Failure Recovery & Rollback Handler

Upon completing or abandoning a spike:

```bash
# Remove throwaway scratch spike files
rm -rf scratch/spike_* .spike/ 2>/dev/null
```

---

## 7. Verification Plan & Toolchain Commands

Execute spike experiment script:

```bash
# 1. Run isolated spike script in scratch directory
python3 scratch/spike_experiment.py

# 2. Verify git status to ensure zero production file modifications
git status --short
```

---

## 8. Completion Report

Report technical question investigated, experiment design, latency/memory benchmark evidence, Go / Conditional-Go / No-Go decision verdict, alternative approaches evaluated, and actionable guidance for the implementing engineer.
