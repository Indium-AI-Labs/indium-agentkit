---
name: refactor-code
description: "Restructure, rename, extract, inline, or simplify code to improve clarity, cohesion, or maintainability while preserving observable behavior, verified by the existing test suite."
---

# Refactor code

Improve the internal structure of code without changing its observable behavior.
Keep refactoring separate from feature work and bug fixes.

## Workflow

1. Read `AGENTS.md`, project conventions, and the code targeted for
   refactoring. State the structural problem, intended improvement, and the
   observable behavior that must be preserved.
2. Identify and run the existing tests that cover the target behavior. Record
   the baseline result. If coverage is insufficient, note the gap and add
   focused tests before refactoring when practical.
3. Apply the smallest refactoring step that moves toward the goal: extract,
   inline, rename, move, split, or simplify. Change one structural concern at
   a time.
4. Re-run the baseline test suite after each step. A behavioral change signals
   an error in the refactoring, not a test to update.
5. Continue with additional steps only while tests remain green. Stop and
   report if a step introduces a behavioral change that cannot be resolved
   without altering the public contract.
6. Do not mix refactoring with feature additions, bug fixes, dependency
   upgrades, or formatting-only changes in the same unit of work.
7. Review the final diff for accidental behavior changes, orphaned imports,
   dead code, and naming consistency.

## Guardrails

- Preserve all existing public interfaces, return values, error semantics, and
  side effects unless the refactoring goal explicitly includes a contract
  change with approval.
- Do not change test assertions to make a refactoring pass. Tests define the
  behavior contract.
- Optional reviewer or verifier delegation can accelerate confidence, but one
  agent must be able to complete this workflow.

## Completion report

Report the structural changes made, tests run before and after, behavioral
equivalence evidence, any coverage gaps discovered, and remaining improvement
opportunities.
