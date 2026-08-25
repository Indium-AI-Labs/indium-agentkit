---
name: estimate-work
description: Decompose technical tasks into scope, story points, PERT effort estimations, risk multipliers, and delivery sequences.
---

# Estimate Work

Produce empirical, evidence-backed scope assessments, Work Breakdown Structures (WBS), PERT three-point effort estimations ($E = \frac{O + 4M + P}{6}$), risk multipliers, and critical path dependency sequences for technical features, refactorings, and migrations.

The skill is **evidence-backed and mathematically bounded**: codebase file inspection, dependency graphs, API contract breaking changes, data migration complexities, PERT standard deviations ($\sigma = \frac{P - O}{6}$), and explicit assumptions are verified before publishing effort metrics.

---

## 1. Required I/O Context Schemas & Natural Language Auto-Inference

The skill supports **two invocation modes**:

1. **🤖 Orchestrator / Technical Mode (JSON Manifest)**: Pass the JSON context manifest below.
2. **💬 Non-Technical Mode (Plain English Prompts)**: If the user provides a natural language prompt (e.g. *"Estimate the effort and risk to migrate our auth database from MySQL to PostgreSQL with zero downtime"*), the agent **must automatically infer and populate** `target_feature_or_issue`, `estimation_model`, `complexity_factors`, and `risk_tolerance` from the user's text.

### JSON Context Manifest Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "EstimateWorkContextManifest",
  "type": "object",
  "required": ["estimation_target", "estimation_config"],
  "properties": {
    "estimation_target": {
      "type": "object",
      "required": ["target_feature_or_issue"],
      "properties": {
        "target_feature_or_issue": { "type": "string" },
        "affected_modules": { "type": "array", "items": { "type": "string" } },
        "target_sprint_weeks": { "type": "integer", "default": 2 }
      }
    },
    "estimation_config": {
      "type": "object",
      "required": ["estimation_model"],
      "properties": {
        "estimation_model": { 
          "type": "string", 
          "enum": ["pert_three_point", "tshirt_sizing", "fibonacci_story_points"],
          "default": "pert_three_point" 
        },
        "confidence_level_pct": { "type": "integer", "default": 95 },
        "include_risk_buffer": { "type": "boolean", "default": true }
      }
    },
    "complexity_factors": {
      "type": "object",
      "properties": {
        "touches_database_schema": { "type": "boolean", "default": false },
        "touches_external_apis": { "type": "boolean", "default": false },
        "requires_data_migration": { "type": "boolean", "default": false },
        "test_coverage_gap": { "type": "boolean", "default": false }
      }
    }
  }
}
```

### Automatic Natural Language Inference & Evidence Rules

If no raw JSON payload is provided, apply these defaults and strict estimation rules:

- **No Ungrounded Guesses**: Never output precise numeric hours without inspecting affected code, existing tests, and architecture references.
- **`estimation_model`**: Defaults to `pert_three_point` for rigorous statistical effort estimation.
- **Explicit Assumptions Required**: Every estimate report MUST list explicit assumptions (e.g., "Assumes schema changes are backward-compatible").

---

## 2. Deterministic State Machine Execution Flow

Follow this exact sequential protocol. Do not skip steps or alter execution ordering.

### Step 1: Codebase Impact & Dependency Discovery

1. Inspect affected files, API endpoints, schema definitions, and unit test suites (`Grep`, `Glob`, `Read`).
2. Map integration boundaries: database migrations, external HTTP clients, cache invalidations, and UI component cascades.

### Step 2: Work Breakdown Structure (WBS) Slicing

1. Decompose the request into independently deliverable, testable slices:
   - **Slice 1 (Schema & Model)**: Database DDLs, migrations, entity definitions.
   - **Slice 2 (Core Business Logic)**: Service layer, domain rules, unit tests.
   - **Slice 3 (API & Controller)**: HTTP handlers, input validation, integration tests.
   - **Slice 4 (UI / Client)**: Component state, forms, accessibility, end-to-end tests.

### Step 3: PERT Three-Point Estimation & Standard Deviation

For each slice, estimate three values in Person-Hours or Story Points:
- **Optimistic ($O$)**: Everything goes perfectly with zero integration blockers.
- **Most Likely ($M$)**: Normal expected complexity under standard conditions.
- **Pessimistic ($P$)**: Worst-case scenario encountering maximum risks and refactorings.

Calculate Expected Effort ($E$) and Standard Deviation ($\sigma$):

$$E = \frac{O + 4M + P}{6}$$

$$\sigma = \frac{P - O}{6}$$

### Step 4: Risk Multipliers & Critical Path Scheduling

1. Apply risk multipliers based on codebase health:
   - Missing unit test coverage: $+25\%$ buffer.
   - Live data migration required: $+35\%$ buffer.
   - Third-party API dependency: $+20\%$ buffer.
2. Identify the Critical Path (longest sequence of dependent tasks).

---

## 3. Reference Implementation: Python PERT & WBS Estimator

```python
import math
from typing import List, Dict, Any

class WorkEstimator:
    """PERT Three-Point Estimation and Risk Multiplier Calculator."""
    
    def __init__(self, confidence_level: str = "95%"):
        self.confidence_level = confidence_level
        # Z-score for 95% confidence interval is 1.96
        self.z_score = 1.96 if confidence_level == "95%" else 1.645

    def calculate_slice(self, name: str, o: float, m: float, p: float, risk_factors: List[str]) -> Dict[str, Any]:
        expected = (o + 4 * m + p) / 6.0
        std_dev = (p - o) / 6.0
        variance = std_dev ** 2
        
        # Apply risk factor multipliers
        multiplier = 1.0
        if "data_migration" in risk_factors:
            multiplier += 0.35
        if "no_test_coverage" in risk_factors:
            multiplier += 0.25
        if "third_party_api" in risk_factors:
            multiplier += 0.20
            
        risk_adjusted_expected = expected * multiplier
        
        return {
            "slice_name": name,
            "optimistic": o,
            "most_likely": m,
            "pessimistic": p,
            "expected_effort": round(expected, 2),
            "std_deviation": round(std_dev, 2),
            "variance": round(variance, 2),
            "risk_multiplier": multiplier,
            "risk_adjusted_effort": round(risk_adjusted_expected, 2)
        }

    def Total_project_estimate(self, slices: List[Dict[str, Any]]) -> Dict[str, Any]:
        total_expected = sum(s["risk_adjusted_effort"] for s in slices)
        total_variance = sum(s["variance"] for s in slices)
        combined_std_dev = math.sqrt(total_variance)
        
        upper_bound_95 = total_expected + (self.z_score * combined_std_dev)
        
        return {
            "total_expected_hours": round(total_expected, 2),
            "combined_std_dev": round(combined_std_dev, 2),
            "upper_bound_95_pct_confidence": round(upper_bound_95, 2),
            "total_slices": len(slices)
        }

if __name__ == "__main__":
    estimator = WorkEstimator()
    s1 = estimator.calculate_slice("DB Schema & Migration", o=4, m=8, p=16, risk_factors=["data_migration"])
    s2 = estimator.calculate_slice("Auth API Handlers", o=3, m=6, p=12, risk_factors=["no_test_coverage"])
    
    summary = estimator.Total_project_estimate([s1, s2])
    print(f"Total Expected Effort: {summary['total_expected_hours']} hrs (95% CI Upper Bound: {summary['upper_bound_95_pct_confidence']} hrs)")
```

---

## 4. Mathematical Formulas & Statistical Invariants

### 1. PERT Expected Value ($E$)

$$E = \frac{O + 4M + P}{6}$$

### 2. PERT Standard Deviation ($\sigma$) & Variance ($\sigma^2$)

$$\sigma = \frac{P - O}{6}, \quad \sigma^2 = \left( \frac{P - O}{6} \right)^2$$

### 3. Total Project Standard Deviation ($\sigma_{\text{total}}$)

$$\sigma_{\text{total}} = \sqrt{\sum_{i=1}^{N} \sigma_i^2}$$

### 4. Confidence Interval Upper Bound ($CI_{95\%}$)

$$CI_{95\%} = E_{\text{total}} + 1.96 \cdot \sigma_{\text{total}}$$

---

## 5. Guardrails

### Operational Restrictions

- **Advisory Only**: Estimates are planning indicators, not binding contract commitments.
- **Mandatory Risk Buffer**: Always state explicit risk multipliers when touching unfamiliar code or live databases.
- **Explicit Assumptions**: Every estimate report MUST include a dedicated "Assumptions & Unknowns" section.

---

## 6. Atomic Failure Recovery & Rollback Handler

If code exploration reveals hidden architectural complexity during estimation:

```bash
# Clean up temporary estimation artifacts or scratch files
rm -f scratch_estimate.json 2>/dev/null
```

---

## 7. Verification Plan & Toolchain Commands

Verify code impact before finalizing estimates:

```bash
# 1. Inspect lines of code changed in similar past pull requests
git log -S "auth" --stat -n 5

# 2. Run static test coverage checks to determine risk buffer
python3 -m unittest discover -s tests -v
```

---

## 8. Completion Report

Report WBS task slices, PERT optimistic/most-likely/pessimistic inputs, expected efforts ($E$), standard deviations ($\sigma$), 95% confidence upper bounds, risk multipliers applied, critical path sequence, and explicit assumptions.
