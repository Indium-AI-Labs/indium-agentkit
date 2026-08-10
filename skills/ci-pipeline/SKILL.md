---
name: ci-pipeline
description: Design reliable CI pipelines with useful required checks.
---

# CI pipeline

Design or improve continuous integration so failures are actionable, repeatable,
and fast enough to run on every change. GitHub Actions is the default example,
but adapt to the project's CI provider and existing conventions.

## Workflow

1. Read `AGENTS.md`, existing workflows, package metadata, test commands, and
   supported runtimes. Map every required check to a user-visible risk.
2. Separate fast feedback from slower integration, browser, security, and build
   jobs. Use explicit dependencies so a skipped prerequisite cannot look green.
3. Define a minimal version and platform matrix based on support policy. Pin
   third-party actions to reviewed major versions or immutable references.
4. Use least-privilege workflow permissions, protected environments, and
   narrowly scoped secret references. Never print secrets or trust unvalidated
   pull-request input in privileged jobs.
5. Add dependency and cache keys that include lockfiles and runtime versions;
   ensure caches cannot cross trust boundaries.
6. Upload useful test, coverage, build, and diagnostic artifacts with retention
   appropriate to their sensitivity. Make failures preserve enough evidence.
7. Make required checks deterministic: fixed commands, explicit timeouts,
   cancellation of superseded runs, and clear failure summaries.
8. Validate workflow syntax and run representative commands locally. Document
   changed gates, expected runtime, known flaky checks, and follow-up work.

## Guardrails

- Do not weaken a required check or bypass branch protection to make a build
  green; identify and fix the underlying failure.
- Do not grant write or cloud permissions to jobs that only test code.
- Optional ci-verifier delegation can inspect failures, but this skill remains
  usable by one agent.

## Completion report

Report workflows changed, trigger and permission behavior, matrix and cache
choices, commands run, artifacts produced, and any unverified provider behavior.
