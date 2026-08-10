---
name: write-documentation
description: "Author, update, or audit project documentation — READMEs, architecture decisions, API references, onboarding guides, and inline doc — from code evidence without inventing behavior."
---

# Write documentation

Create or improve documentation that accurately reflects the project's current
state. Inspect the codebase before writing; do not invent capabilities,
performance claims, or compatibility that the code does not demonstrate.

## Workflow

1. Read `AGENTS.md`, existing documentation, public API surface, tests, and
   commit history. Identify the documentation gap: new file, stale section,
   missing audience, or structural problem.
2. Determine the audience (end user, contributor, operator, or API consumer)
   and match the project's existing voice, format, and location conventions.
3. Extract facts from code, tests, configuration, and history. Cross-reference
   claims against the implementation. Flag anything that cannot be verified.
4. Structure content with a clear hierarchy: purpose, prerequisites, usage,
   configuration, architecture, troubleshooting, and references as applicable.
5. Include working examples, commands, and expected outputs drawn from actual
   project behavior. Mark examples as untested when they cannot be verified.
6. Check all internal links, code references, file paths, and command snippets
   for accuracy. Remove or update stale references.
7. Keep documentation scoped. Do not rewrite unrelated sections, change code to
   match documentation, or add dependencies for documentation tooling without
   approval.
8. Report what was documented, sources used, accuracy limitations, and any
   code behavior that contradicts existing documentation.

## Guardrails

- Do not fabricate features, performance characteristics, or compatibility.
  State what the code does, not what it should do.
- Preserve existing documentation structure and conventions unless the change
  explicitly calls for restructuring.
- An optional doc-writer subagent can draft content in parallel, but this
  workflow is executable by one agent.

## Completion report

Report documentation created or updated, sources of truth used, verified and
unverified claims, broken links fixed, and follow-up documentation needs.
