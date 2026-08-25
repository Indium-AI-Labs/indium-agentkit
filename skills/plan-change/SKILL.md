---
name: plan-change
description: Turn feature requests, bug reports, refactors, or technical proposals into implementation-ready plans with scope, acceptance criteria, affected areas, test seams, risks, and ordered steps.
---

# Plan Change

Turn feature requests, bug reports, refactoring proposals, and architecture migrations into implementation-ready plans featuring explicit scope bounds, observable acceptance criteria, affected file matrices, test seams, risk mitigation strategies, and ordered, reviewable execution steps.

The skill is **contract-first and implementation-ready**: problem statements, non-goals, architectural constraints, public interface contracts, backward-compatibility requirements, and rollback plans are verified and approved before executing source code changes.

---

## 1. Required I/O Context Schemas & Natural Language Auto-Inference

The skill supports **two invocation modes**:

1. **🤖 Orchestrator / Technical Mode (JSON Manifest)**: Pass the JSON context manifest below.
2. **💬 Non-Technical Mode (Plain English Prompts)**: If the user provides a natural language prompt (e.g. *"Plan the implementation for adding multi-factor authentication (MFA) to our user login system including schema changes and API contracts"*), the agent **must automatically infer and populate** `change_type`, `affected_modules`, `acceptance_criteria`, and `rollback_strategy` from the user's text.

### JSON Context Manifest Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "PlanChangeContextManifest",
  "type": "object",
  "required": ["change_spec", "plan_config"],
  "properties": {
    "change_spec": {
      "type": "object",
      "required": ["change_type", "title"],
      "properties": {
        "change_type": { 
          "type": "string", 
          "enum": ["feature", "bug_fix", "refactor", "architecture_migration", "security_patch"],
          "default": "feature"
        },
        "title": { "type": "string" },
        "problem_statement": { "type": "string" },
        "affected_modules": { "type": "array", "items": { "type": "string" } }
      }
    },
    "plan_config": {
      "type": "object",
      "required": ["planning_depth"],
      "properties": {
        "planning_depth": { 
          "type": "string", 
          "enum": ["lightweight_spike", "standard_implementation_plan", "multi_phase_architecture_plan"],
          "default": "standard_implementation_plan" 
        },
        "require_user_approval": { "type": "boolean", "default": true },
        "backward_compatibility_mode": { "type": "string", "enum": ["strict_no_breaking", "deprecated_alias", "breaking_major"] }
      }
    },
    "verification_seams": {
      "type": "object",
      "properties": {
        "unit_test_coverage_required": { "type": "boolean", "default": true },
        "integration_test_required": { "type": "boolean", "default": true },
        "rollback_automation_script": { "type": "boolean", "default": true }
      }
    }
  }
}
```

### Automatic Natural Language Inference & Planning Rules

If no raw JSON payload is provided, apply these defaults and strict planning rules:

- **Planning Mode Rule**: Do NOT write or modify application source code during the planning phase. Creating/updating implementation plans is allowed.
- **User Approval Barrier**: Stop and wait for explicit user approval of `implementation_plan.md` before proceeding to execution.
- **Non-Goals Requirement**: Every implementation plan MUST explicitly declare "Non-Goals" to prevent scope creep.

---

## 2. Deterministic State Machine Execution Flow

Follow this exact sequential protocol. Do not skip steps or alter execution ordering.

### Step 1: Problem Ingestion & Scope Definition

1. Read the user request, issue description, and related documentation.
2. Formulate explicit Scope Bounds:
   - **Goals / Intended Outcomes**: What this change accomplishes.
   - **Non-Goals**: Out-of-scope items explicitly excluded from this effort.
   - **Constraints**: Performance SLAs, memory limits, backward-compatibility requirements.

### Step 2: Codebase Impact & Interface Seams Analysis

1. Inspect affected files and component boundaries using `Grep`, `Glob`, and `Read`.
2. Map public interface changes (API DTOs, database schemas, function signatures).
3. Identify test seams: locate existing unit tests and integration test suites that cover the affected areas.

### Step 3: Acceptance Criteria & Observable Verification Seams

1. Define concrete, observable Acceptance Criteria (ACs) for each requirement:
   - **AC 1**: User submits valid MFA token $\rightarrow$ returns 200 OK + JWT.
   - **AC 2**: User submits invalid MFA token $\rightarrow$ returns 401 Unauthorized.
2. Pair every AC with an exact automated test command (`npm test`, `pytest`) that verifies it.

### Step 4: Step-by-Step Execution Ordering (DAG Sequence)

Break the change into ordered, independently reviewable execution steps:
- **Phase 1 (Data & Contract)**: Database schema migration, DTO types, interfaces.
- **Phase 2 (Core Business Logic)**: Service layer implementations, unit tests.
- **Phase 3 (API & Handlers)**: HTTP controllers, middleware, integration tests.
- **Phase 4 (Documentation & Rollout)**: OpenAPI docs, feature flag configuration.

### Step 5: Risk Matrix, Rollback & Compatibility Audit

1. Evaluate security, performance, and data migration risks.
2. Formulate an explicit **Rollback Strategy**: step-by-step instructions to revert changes safely if production issues arise.

---

## 3. Reference Implementation: Python Implementation Plan Validator

```python
import sys
import re
from pathlib import Path
from typing import Dict, List, Tuple

REQUIRED_PLAN_HEADINGS = [
  "# ",
  "## User Review Required",
  "## Proposed Changes",
  "## Verification Plan",
]


def validate_implementation_plan(plan_path: Path) -> Tuple[bool, List[str]]:
  """Validate that implementation_plan.md conforms to required structure."""
  if not plan_path.exists():
    return False, ["Plan file does not exist."]

  content = plan_path.read_text(encoding="utf-8")
  errors = []

  for heading in REQUIRED_PLAN_HEADINGS:
    if heading not in content:
      errors.append(f"Missing required section heading: '{heading}'")

  # Check for Non-Goals declaration
  if "Non-Goal" not in content and "non-goal" not in content.lower():
    errors.append(
        "Missing explicit 'Non-Goals' declaration to prevent scope creep."
    )

  return len(errors) == 0, errors


if __name__ == "__main__":
  p = Path("implementation_plan.md")
  if len(sys.argv) > 1:
    p = Path(sys.argv[1])

  valid, errs = validate_implementation_plan(p)
  if valid:
    print("Implementation plan is valid and ready for user approval.")
  else:
    print(f"Plan validation failed with {len(errs)} errors:")
    for e in errs:
      print(f" - {e}")
```

---

## 4. Planning Invariants & Verification Rules

$$\text{Step Independence Invariant: } \forall s_i \in \text{ExecutionSteps}, \quad s_i \text{ is independently reviewable and testable}$$

$$\text{Acceptance Completeness: } \forall \text{ AC}_k, \quad \exists \text{ Test } T_k \text{ that explicitly verifies } \text{AC}_k$$

$$\text{Scope Control: } \text{ExecutionScope} \cap \text{NonGoals} \equiv \emptyset$$

---

## 5. Guardrails

### Operational Restrictions

- **No Code Editing in Planning Mode**: Never edit application source code until the implementation plan is fully written and approved by the user.
- **Mandatory User Approval**: Set `request_feedback: true` on implementation plan artifacts and await explicit user sign-off.
- **Backward Compatibility**: Never break existing public API contracts without explicit deprecation paths or major version bumps.

---

## 6. Atomic Failure Recovery & Rollback Handler

If planning reveals that a proposed approach is unviable due to deep architectural conflicts:

```bash
# Revert draft implementation plan or reset planning state
rm -f implementation_plan.md 2>/dev/null
```

---

## 7. Verification Plan & Toolchain Commands

Verify implementation plan structure:

```bash
# 1. Run implementation plan validator
python3 scripts/validate_handoff.py --plan implementation_plan.md

# 2. Run RBAC schema check on planned component changes
python3 scripts/validate_rbac_schema.py
```

---

## 8. Completion Report

Report change title, change type (`feature`, `bug_fix`, `refactor`), affected modules matrix, acceptance criteria list, verification test plan commands, risk matrix findings, rollback strategy summary, and user approval request status.
