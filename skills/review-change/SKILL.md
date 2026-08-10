---
name: review-change
description: "Review a local diff, branch, commit range, or pull request for correctness, regressions, security concerns, project conventions, and missing tests. Use when asked for a code review; report findings without editing by default."
---

# Review change

1. Establish the review target and comparison point. If none is supplied, inspect the working tree and state the assumed scope.
2. Read the relevant project context, issue or specification, and tests before judging the diff.
3. Trace changed behavior through callers, error paths, data boundaries, and configuration. Check compatibility, security-sensitive input handling, and failure modes.
4. Verify tests cover meaningful changed behavior and run available checks when they are inexpensive and safe.
5. Report only actionable findings. For each finding include severity, file and line, evidence, impact, and a concrete remediation direction.
6. Separate blocking defects from important follow-ups and non-blocking suggestions. Do not edit files, approve a change, or fabricate findings unless explicitly asked.
7. End with the checks run and any scope or verification limitations. An independent read-only reviewer may be used as an optional second pass.
