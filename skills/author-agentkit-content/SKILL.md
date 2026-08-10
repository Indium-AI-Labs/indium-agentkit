---
name: author-agentkit-content
description: "Create or update indium-agentkit skills, subagents, templates, validation, and documentation. Use when adding, revising, validating, or publishing content in this distribution repository."
---

# Author agentkit content

1. Read the root `AGENTS.md`, `CONTRIBUTING.md`, and nearby content before changing files.
2. Keep repository-specific policy in the root `AGENTS.md`; keep consumer-facing guidance in `templates/AGENTS.md`.
3. Create skills as `skills/<name>/SKILL.md` with only `name` and `description` frontmatter. Make the description state both capability and trigger.
4. Create Claude Code subagents as `agents/<name>.md` with `name`, `description`, `tools`, and `model` frontmatter. Give each a narrow responsibility and explicit write restrictions.
5. Keep skills executable by a single agent. If delegation helps, describe it as optional and preserve a single-agent path.
6. Update `README.md` and `CONTRIBUTING.md` when the distribution contract changes.
7. Run content validation, unit tests, and the Cursor-rule builder. Inspect generated rule output when a skill changes.
8. Review the scoped diff, commit it, and push directly to `origin/main` according to this repository's policy.
