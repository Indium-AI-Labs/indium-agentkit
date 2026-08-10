<!--
Read natively by Codex, Cursor, Gemini CLI/Antigravity, Copilot, Aider,
Windsurf, and Zed. This file contains instructions for developing
indium-agentkit itself. Consumer projects receive templates/AGENTS.md instead.
-->

# What this project is

indium-agentkit distributes portable AI coding-agent skills, Claude Code
subagents, and project-context templates. Skills are authored as SKILL.md and
converted to Cursor rules; subagents use Claude Code-compatible frontmatter.

# Conventions

- Language/framework: Markdown, Python 3 standard library, Bash, and PowerShell.
- Test command: `python -m unittest discover -s tests -v`
- Lint command: `python scripts/validate_content.py`
- Source code lives in: `skills/`, `agents/`, `scripts/`, and `templates/`.
- Tests live in: `tests/`.
- Generated Cursor rules are intentionally ignored at `.cursor/rules/`.

# Notes for agents

- Keep SKILL.md frontmatter limited to `name` and `description`; validate every
  content change before committing.
- Keep skills usable by one agent. Treat subagent delegation as optional so the
  Cursor conversion remains useful.
- After adding, removing, or changing any skill or subagent, regenerate
  `CATALOG.md` with `python scripts/generate_catalog.py` and run
  `python scripts/diff_catalog.py` before committing. Catalog changes belong in
  the same commit as the content change.
- Make frequent, scoped commits as coherent units of completed work. Use concise,
  professional imperative commit subjects that describe the shipped change (for
  example, `Add handoff template validation`); avoid vague labels such as
  `updates`, `changes`, or phase-based names such as `second wave`.
- Push each completed scoped commit directly to `origin/main`.
