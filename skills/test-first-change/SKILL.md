---
name: test-first-change
description: "Plan and implement a behavior change, bug fix, or refactor with focused behavior-level tests, public seams, and incremental red-green-refactor cycles. Use when writing or changing production code."
---

# Test first change

1. Read project context and the existing tests near the target behavior. Identify the test command and established conventions.
2. Define the observable behavior to preserve or introduce. Prefer public interfaces over internal implementation details.
3. Choose the narrowest useful test seam. Reuse existing fixtures and helpers before introducing new test infrastructure.
4. Write one focused test or reproduce an existing failing test. Confirm it fails for the intended reason before implementation when practical.
5. Make the smallest production change that makes the behavior pass. Avoid unrelated refactors during the red-green loop.
6. Refactor only after the focused behavior passes. Keep test names descriptive of user-visible behavior.
7. Run the focused test, then the relevant broader suite. Report coverage gaps or untestable assumptions instead of pretending they are covered.
