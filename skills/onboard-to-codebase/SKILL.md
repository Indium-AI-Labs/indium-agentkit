---
name: onboard-to-codebase
description: "Generate a developer onboarding guide or codebase orientation by analyzing architecture, conventions, dependencies, workflows, and common tasks from the existing project."
---

# Onboard to codebase

Produce a developer-facing orientation document that helps a new contributor
become productive. Extract all content from the codebase; do not invent
architecture or conventions.

## Workflow

1. Read `AGENTS.md`, README, package metadata, directory structure, and
   existing developer documentation. Map the project's purpose, users, and
   high-level architecture.
2. Identify the runtime, language, framework, build system, and package
   manager. Document setup prerequisites and the exact steps to get a working
   development environment.
3. Map the source layout: where features live, how code is organized, key
   abstractions, entry points, and the boundaries between components.
4. Document the test infrastructure: frameworks, test commands, fixture
   patterns, and how to run focused versus full suites. Include lint and
   format commands.
5. Identify deployment targets, environments, configuration patterns, and
   how local development differs from production.
6. List the most common development tasks: adding a feature, fixing a bug,
   adding a test, running migrations, and deploying. Reference existing
   skills or conventions.
7. Note gotchas, known pain points, required environment variables, and
   undocumented conventions that new contributors commonly encounter.
8. Structure the guide using the project's existing documentation style or
   the `onboarding-guide` handoff template when available.

## Guardrails

- Extract facts from code and configuration. Do not describe aspirational
  architecture or planned features as current state.
- Preserve existing onboarding documentation; augment rather than replace
  unless explicitly asked.
- An optional explorer subagent can map the codebase in parallel, but one
  agent can complete this workflow.

## Completion report

Report the onboarding guide produced, sources used, verified and unverified
setup steps, coverage gaps, and recommendations for maintaining the guide.
