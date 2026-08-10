# Contributing content

## Skills

Create one directory per skill at `skills/<skill-name>/SKILL.md`. Use a
lowercase hyphenated directory name that exactly matches frontmatter `name`.
Keep skill frontmatter limited to `name` and `description`; make the description
specific enough to trigger for the right work. Keep the body concise and
standalone. A skill may suggest subagent delegation, but it must not require it.

Add scripts or references only when they make the workflow more reliable or
avoid repeated work. Keep scripts portable and dependency-free when practical.
Do not copy third-party content without confirming its license and recording
its provenance.

## Subagents

Create subagents as `agents/<name>.md`. Include `name`, `description`, `tools`,
and `model` frontmatter. Define a narrow responsibility, clear output format,
and write restrictions. Prefer read-only specialist agents over generic
implementers.

## Required checks

Run these commands before committing:

```bash
python scripts/validate_content.py
python scripts/validate_handoff.py --templates-dir templates/handoffs
python -m unittest discover -s tests -v
python scripts/build_cursor_rules.py --skills-dir skills --out-dir .cursor/rules
python scripts/list_content.py --format markdown
```

Commit frequent, scoped, coherent units of completed work. Use concise,
professional imperative subjects that say what changed, such as `Add handoff
template validation`; avoid vague or phase-based subjects. Push each completed
scoped commit directly to `origin/main` as required by the root `AGENTS.md`.

Use `scripts/scaffold_content.py` to create a valid starter file and
`scripts/check_install.py` to diagnose an installation without changing it.
Use `scripts/codex_delegate.py` to turn a portable `agents/<name>.md` role into
a bounded packet for a native Codex orchestrator; it must remain side-effect
free and must not call a model directly.
