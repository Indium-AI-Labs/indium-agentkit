# indium-agentkit

`indium-agentkit` is a distribution scaffold for sharing AI coding-agent skills, subagents, and project context across Claude Code, Codex, Antigravity CLI (formerly Gemini CLI), OpenCode, and Cursor.

---

## ⚡ 1-Line Quick Installation (Install Whole Repo)

To install **all 36 portable skills, 21 subagents, and Cursor rules** into any project repository in under 2 seconds:

```bash
# Auto-detect active IDE and install all skills & subagents
npx @indium-ai-labs/agentkit install
```

### 🎯 Target Specific AI Editors & IDEs:
```bash
# Antigravity IDE (.antigravity/skills & .antigravity/agents)
npx @indium-ai-labs/agentkit install --target=antigravity

# OpenCode (.opencode/skills)
npx @indium-ai-labs/agentkit install --target=opencode

# Cursor IDE (.cursor/rules/*.mdc)
npx @indium-ai-labs/agentkit install --target=cursor

# Claude Code (.claude/skills & .claude/agents)
npx @indium-ai-labs/agentkit install --target=claude
```

---

## Architecture

The repository uses two open, cross-agent formats:

- `SKILL.md` is a task-triggered capability. Each skill has YAML frontmatter (`name` and `description`), a Markdown body, and optionally helper files next to it. Claude Code, Codex, OpenCode, and Gemini CLI/Antigravity discover this format natively.
- `AGENTS.md` is always-loaded project context: architecture, conventions, commands, and working notes. Codex, Cursor, Gemini CLI/Antigravity, Copilot, Aider, Windsurf, and Zed read it natively. The root file governs this repository; `templates/AGENTS.md` is the neutral file installers link into consumer projects, along with `CLAUDE.md` for Claude Code.

Cursor does not natively discover `SKILL.md`. The included Python builder turns each `skills/*/SKILL.md` into `.cursor/rules/<skill-directory>.mdc`, carrying over the skill description and Markdown body and setting `alwaysApply: false`. Skills therefore have one source of truth while remaining available to Cursor.

Subagents do not yet share a cross-tool schema. This repository uses Claude Code's format as the common denominator: YAML frontmatter containing `name`, `description`, `tools`, and `model`, followed by the subagent's Markdown prompt. Use [`templates/subagent.md`](templates/subagent.md) when authoring a new role; it is based on the repository's `agent-orchestrator` inspection structure and keeps safety, contracts, limits, and handoffs explicit.

## Repository layout

```text
indium-agentkit/
├── README.md
├── AGENTS.md
├── templates/
│   └── AGENTS.md
├── skills/
│   ├── author-agentkit-content/
│   ├── plan-change/
│   ├── safe-migration/
│   ├── security-review/
│   ├── ...
│   └── verify-and-ship/
├── agents/
│   ├── explorer.md
│   ├── migration-planner.md
│   ├── security-reviewer.md
│   ├── ...
│   └── verifier.md
├── scripts/
│   ├── install.sh
│   ├── install.ps1
│   ├── build_cursor_rules.py
│   ├── validate_content.py
│   ├── check_install.py
│   ├── scaffold_content.py
│   └── list_content.py
├── tests/
├── .github/workflows/validate.yml
├── docs/
├── CATALOG.md
├── CHANGELOG.md
├── SECURITY.md
├── CONTRIBUTING.md
└── .gitignore
```

## Validation

Validate content and run the dependency-free test suite before publishing:

```bash
python scripts/validate_content.py
python scripts/validate_handoff.py --templates-dir templates/handoffs
python -m unittest discover -s tests -v
```

GitHub Actions runs the same checks on pushes and pull requests.

## Tools and compatibility

Use `python scripts/check_install.py --project /path/to/project` to inspect an installation, `scripts/scaffold_content.py` to create valid starter content, and `scripts/list_content.py --format json` to consume the catalog programmatically. For Codex delegation, use `scripts/codex_delegate.py` to produce a structured packet from an `agents/<name>.md` role.
See [compatibility details](docs/compatibility.md), [security guidance](SECURITY.md), and [release guidance](docs/releasing.md).

## Status

The current bundle contains thirty-six portable skills, twenty-one read-only specialists, and two scoped implementation subagents. See `CATALOG.md` for the generated inventory.
