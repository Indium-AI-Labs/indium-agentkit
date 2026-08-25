---
name: refactor-code
description: Restructure, extract, inline, or simplify code to improve cohesion and maintainability while strictly preserving observable behavior verified by tests.
---

# Refactor Code

Restructure, extract, inline, rename, split, or simplify internal code architecture to improve maintainability, reduce cyclomatic complexity, and increase cohesion while strictly preserving 100% of public API contracts, error semantics, side effects, and observable system behavior.

The skill is **behavior-preserving and test-verified**: baseline test runs, atomic step-by-step refactoring transformations, continuous test re-verification, dead code removal, and strict non-modification of test assertions are enforced before committing refactoring diffs.

---

## 1. Required I/O Context Schemas & Natural Language Auto-Inference

The skill supports **two invocation modes**:

1. **🤖 Orchestrator / Technical Mode (JSON Manifest)**: Pass the JSON context manifest below.
2. **💬 Non-Technical Mode (Plain English Prompts)**: If the user provides a natural language prompt (e.g. *"Refactor the order processing service in `src/services/order.ts` to extract validation logic into a separate module while keeping tests passing"*), the agent **must automatically infer and populate** `target_files`, `refactoring_pattern`, `baseline_test_command`, and `strict_contract_preservation` from the user's text.

### JSON Context Manifest Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "RefactorCodeContextManifest",
  "type": "object",
  "required": ["target_scope", "refactor_config"],
  "properties": {
    "target_scope": {
      "type": "object",
      "required": ["target_files"],
      "properties": {
        "target_files": { "type": "array", "items": { "type": "string" }, "minItems": 1 },
        "baseline_test_command": { "type": "string", "default": "pnpm test" }
      }
    },
    "refactor_config": {
      "type": "object",
      "required": ["refactoring_pattern"],
      "properties": {
        "refactoring_pattern": { 
          "type": "string", 
          "enum": ["extract_method", "extract_module", "inline_variable", "replace_conditional_with_polymorphism", "rename_symbol", "decouple_dependencies"],
          "default": "extract_module" 
        },
        "strict_contract_preservation": { "type": "boolean", "default": true },
        "max_cyclomatic_complexity": { "type": "integer", "default": 10 }
      }
    }
  }
}
```

### Automatic Natural Language Inference & Refactoring Safety Rules

If no raw JSON payload is provided, apply these defaults and strict refactoring rules:

- **Never Change Test Assertions**: NEVER alter existing unit test assertions to force a failing refactored test to pass. Failing tests indicate a behavioral regression in the refactoring code.
- **Separate Refactor from Feature Work**: Refactoring commits MUST NOT contain new feature logic, bug fixes, or dependency upgrades.
- **Green Baseline Requirement**: Refactoring MUST NOT begin if the existing baseline test suite is failing.

---

## 2. Deterministic State Machine Execution Flow

Follow this exact sequential protocol. Do not skip steps or alter execution ordering.

### Step 1: Baseline Verification & Test Suite Execution

1. Run the existing test suite covering target files (`pnpm test`, `pytest`, `cargo test`).
2. Verify 100% green baseline pass. If tests fail, report baseline issues before refactoring.

### Step 2: Atomic Refactoring Step Isolation

Apply the smallest micro-refactoring transformation:
1. **Extract Method / Module**: Pull complex nested logic into pure, testable helper functions.
2. **Rename Symbol**: Rename variables or functions for domain clarity using AST-aware refactoring tools.
3. **Decouple Dependencies**: Replace hardcoded class instantiations with Dependency Injection (DI) interfaces.

### Step 3: Continuous Re-Test Verification

1. Re-run baseline test suite immediately after EACH micro-step:
   ```bash
   pnpm test -- filter=target_module
   ```
2. If any test fails, revert the immediate micro-step and diagnose the contract breach.

### Step 4: Dead Code & Orphaned Import Cleanup

1. Remove unused imports, dead local variables, and unreferenced internal methods.
2. Verify linting and formatting compliance (`eslint --fix`, `prettier`, `black`, `clippy`).

### Step 5: Final Diff Audit & Behavioral Equivalence Verification

Inspect `git diff` to ensure:
- Public function signatures and export types are unchanged.
- No accidental feature logic or parameter alterations were introduced.

---

## 3. Reference Implementation: Python Refactoring Test Equivalence Verifier

```python
import subprocess
import sys
from typing import Tuple

def run_test_suite(test_cmd: str) -> Tuple[bool, str]:
    """Execute test suite and return success status and console output."""
    try:
        res = subprocess.run(
            test_cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=120
        )
        return res.returncode == 0, res.stdout + res.stderr
    except subprocess.TimeoutExpired:
        return False, "Test suite timed out after 120 seconds."

def verify_refactoring_equivalence(test_cmd: str, micro_step_desc: str) -> bool:
    """Re-verify test suite after a refactoring micro-step."""
    print(f"[Refactor Verification] Re-running tests after step: '{micro_step_desc}'...")
    passed, log = run_test_suite(test_cmd)
    
    if passed:
        print(f"[SUCCESS] Tests passed cleanly. Refactoring step '{micro_step_desc}' is behavior-preserving.")
        return True
    else:
        print(f"[FAILURE] Behavioral regression detected in step '{micro_step_desc}'!")
        print("--- Test Error Output ---")
        print(log[:1000]) # Print first 1000 chars of log
        return False

if __name__ == "__main__":
    cmd = "python3 -m unittest discover -s tests -v"
    if not verify_refactoring_equivalence(cmd, "Extract validation logic to validator.py"):
        sys.exit(1)
```

---

## 4. Behavioral Equivalence Invariants

$$\text{Behavioral Equivalence Theorem: } \forall x \in \text{Inputs}, \quad f_{\text{refactored}}(x) \equiv f_{\text{original}}(x)$$

$$\text{Test Assertion Immutability: } \text{Diff}(\text{TestAssertions}) \equiv 0$$

$$\text{Cyclomatic Complexity Reduction: } M_{\text{refactored}} < M_{\text{original}} \quad \text{where } M = E - N + 2P$$

---

## 5. Guardrails

### Operational Restrictions

- **Never Modify Test Assertions**: Refactoring must make existing tests pass without changing assertion values.
- **No Mixed Commits**: Keep refactoring commits strictly separated from new feature additions or bug fixes.
- **Stop on Regression**: If a micro-step breaks behavioral equivalence and cannot be fixed cleanly, revert the step (`git checkout -- <file>`).

---

## 6. Atomic Failure Recovery & Rollback Handler

If a refactoring step introduces subtle regressions that break test suites:

```bash
# Revert target files to previous green state
git checkout -- src/ 2>/dev/null

# Re-run baseline test suite to confirm recovery
pnpm test || pytest || cargo test
```

---

## 7. Verification Plan & Toolchain Commands

Verify behavioral equivalence before and after refactoring:

```bash
# 1. Run baseline test suite
pnpm test

# 2. Run refactoring test equivalence verifier
python3 scripts/verify_refactoring_equivalence.py

# 3. Check code complexity and linting
npx eslint src/ --max-warnings 0
```

---

## 8. Completion Report

Report target files refactored, refactoring patterns applied (`extract_module`, `rename_symbol`), baseline vs post-refactoring test results, cyclomatic complexity reduction, linting compliance, and behavioral equivalence confirmation.
