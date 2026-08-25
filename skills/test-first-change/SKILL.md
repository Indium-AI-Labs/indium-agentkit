---
name: test-first-change
description: Plan and implement behavior changes, bug fixes, or refactors using Test-Driven Development (TDD) red-green-refactor cycles and behavior-level test seams.
---

# Test First Change

Plan, author, and implement production code changes, bug fixes, and feature additions using strict Test-Driven Development (TDD) Red-Green-Refactor iteration loops: write a failing behavior test first, confirm expected failure ("Red"), write minimal code to pass ("Green"), and refactor safely while maintaining passing tests.

The skill is **contract-first and TDD-validated**: public interface test seams, failing test verification, minimal production changes, zero untested public APIs, and complete regression suite passes are mathematically verified across every iteration cycle.

---

## 1. Required I/O Context Schemas & Natural Language Auto-Inference

The skill supports **two invocation modes**:

1. **🤖 Orchestrator / Technical Mode (JSON Manifest)**: Pass the JSON context manifest below.
2. **💬 Non-Technical Mode (Plain English Prompts)**: If the user provides a natural language prompt (e.g. *"Fix the password validation bug using TDD: write a failing test first for special character requirements, then implement the fix"*), the agent **must automatically infer and populate** `change_target`, `test_type`, `test_framework`, and `red_state_verified` from the user's text.

### JSON Context Manifest Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "TestFirstChangeContextManifest",
  "type": "object",
  "required": ["change_spec", "tdd_config"],
  "properties": {
    "change_spec": {
      "type": "object",
      "required": ["change_target", "observable_behavior"],
      "properties": {
        "change_target": { "type": "string" },
        "observable_behavior": { "type": "string" },
        "test_file_path": { "type": "string" },
        "production_file_path": { "type": "string" }
      }
    },
    "tdd_config": {
      "type": "object",
      "required": ["test_framework"],
      "properties": {
        "test_framework": { 
          "type": "string", 
          "enum": ["jest", "vitest", "pytest", "cargo_test", "go_test"],
          "default": "vitest" 
        },
        "test_type": { 
          "type": "string", 
          "enum": ["unit", "integration", "contract", "e2e"],
          "default": "unit" 
        },
        "require_explicit_red_phase": { "type": "boolean", "default": true }
      }
    }
  }
}
```

### Automatic Natural Language Inference & TDD Rules

If no raw JSON payload is provided, apply these defaults and strict TDD rules:

- **Red State Verification Rule**: Always run the newly written test BEFORE implementing production code to verify that it fails for the expected reason (prevents false-positive tests that pass vacuously).
- **Minimal Code Principle**: Write the simplest possible production code to turn the failing test green; avoid pre-emptive refactoring or un-tested feature logic during the Red-Green loop.
- **Behavior over Implementation Details**: Test public API contracts and user-visible behaviors, not private internal helper implementations.

---

## 2. Deterministic State Machine Execution Flow

Follow this exact sequential protocol. Do not skip steps or alter execution ordering.

### Step 1: Observable Behavior Definition & Seam Identification

1. Read requirement, issue report, and existing test patterns.
2. Define the observable behavior contract (input $\rightarrow$ expected output / error).
3. Identify test seam: locate existing test files or create `tests/unit/<component>.test.ts`.

### Step 2: Red Phase — Author & Verify Failing Test

1. Write a focused test describing the desired behavior:
   ```typescript
   it('should reject passwords missing special characters', () => {
     const result = validatePassword('Password123');
     expect(result.isValid).toBe(false);
     expect(result.error).toContain('special character');
   });
   ```
2. Execute the test command and verify **Expected Red Failure**:
   ```bash
   pnpm test -- filter=validatePassword
   ```
3. Confirm error message matches expected failure mode.

### Step 3: Green Phase — Minimal Production Code Implementation

1. Write the minimal production code necessary to pass the test:
   - Do NOT add extraneous features or un-tested helper methods.
2. Re-run focused test and verify **Green Pass**:
   ```bash
   pnpm test -- filter=validatePassword
   ```

### Step 4: Refactor Phase — Clean Code Optimization

1. Clean up production and test code (rename variables, extract pure functions, remove duplication).
2. Re-run test suite to ensure tests stay 100% green.

### Step 5: Full Regression Suite Verification

Execute full test suite to guarantee zero regressions across adjacent modules:
```bash
pnpm test || pytest || cargo test
```

---

## 3. Reference Implementation: Python TDD Red-Green Loop Harness

```python
import subprocess
import sys
from typing import Tuple

class TddRunner:
    """TDD Red-Green-Refactor Execution Loop Harness."""
    
    def __init__(self, test_cmd: str):
        self.test_cmd = test_cmd

    def run_tests() -> Tuple[bool, str]:
        try:
            res = subprocess.run(self.test_cmd, shell=True, capture_output=True, text=True, timeout=60)
            return res.returncode == 0, res.stdout + res.stderr
        except subprocess.TimeoutExpired:
            return False, "Test execution timed out."

    def verify_red_phase(self) -> bool:
        """Verify that the test suite fails as expected (Red Phase)."""
        print("[TDD Red Phase] Running newly written test to verify failure...")
        passed, log = self.run_tests()
        if not passed:
            print("[SUCCESS] Red phase confirmed: Test failed as expected.")
            return True
        else:
            print("[ERROR] Red phase failed: Test passed unexpectedly! Check test validity.")
            return False

    def verify_green_phase(self) -> bool:
        """Verify that the production code change makes tests pass (Green Phase)."""
        print("[TDD Green Phase] Running tests after implementation...")
        passed, log = self.run_tests()
        if passed:
            print("[SUCCESS] Green phase confirmed: Tests pass cleanly!")
            return True
        else:
            print("[ERROR] Green phase failed: Tests are still failing.")
            print(log[:800])
            return False

if __name__ == "__main__":
    runner = TddRunner("python3 -m unittest tests/test_auth.py")
    if len(sys.argv) > 1 and sys.argv[1] == "--red":
        sys.exit(0 if runner.verify_red_phase() else 1)
    elif len(sys.argv) > 1 and sys.argv[1] == "--green":
        sys.exit(0 if runner.verify_green_phase() else 1)
```

---

## 4. TDD Invariants & State Transition Rules

$$\text{Red State Invariant: } \text{TestOutcome}(T_{\text{new}}, \text{Code}_{\text{old}}) \equiv \mathbf{FAIL\_EXPECTED}$$

$$\text{Green State Invariant: } \text{TestOutcome}(T_{\text{new}}, \text{Code}_{\text{new}}) \equiv \mathbf{PASS}$$

$$\text{Refactor State Invariant: } \text{TestOutcome}(T_{\text{suite}}, \text{Code}_{\text{refactored}}) \equiv \mathbf{PASS}$$

---

## 5. Guardrails

### Operational Restrictions

- **No Unverified Green**: Never implement production code without writing and verifying the failing test first.
- **Minimal Production Code**: Avoid writing pre-emptive features or un-tested helper methods during the Green phase.
- **Public Contract Testing**: Focus tests on public interfaces and observable behavior, avoiding tight coupling to private implementation details.

---

## 6. Atomic Failure Recovery & Rollback Handler

If an implementation approach fails to turn tests green or creates unsolvable architectural friction:

```bash
# Revert production code edits while preserving the test file
git checkout -- src/ 2>/dev/null
```

---

## 7. Verification Plan & Toolchain Commands

Execute TDD loop commands:

```bash
# 1. Verify Red Phase (failing test)
python3 scripts/tdd_runner.py --red

# 2. Verify Green Phase (passing test)
python3 scripts/tdd_runner.py --green

# 3. Run full regression test suite
pnpm test || pytest || cargo test
```

---

## 8. Completion Report

Report observable behavior specified, test file created/updated, Red phase failure output verified, Green phase implementation summary, refactoring steps executed, full regression suite results, and final code coverage metrics.
