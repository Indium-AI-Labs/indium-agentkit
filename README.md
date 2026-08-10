# indium-agentkit

`indium-agentkit` is a distribution scaffold for sharing AI coding-agent skills,
subagents, and project context across Claude Code, Codex, Antigravity CLI
(formerly Gemini CLI), and Cursor.

## Architecture

The repository uses two open, cross-agent formats:

- `SKILL.md` is a task-triggered capability. Each skill has YAML frontmatter
  (`name` and `description`), a Markdown body, and optionally helper files next
  to it. Claude Code, Codex, and Gemini CLI/Antigravity discover this format
  natively.
- `AGENTS.md` is always-loaded project context: architecture, conventions,
  commands, and working notes. Codex, Cursor, Gemini CLI/Antigravity, Copilot,
  Aider, Windsurf, and Zed read it natively. The root file governs this
  repository; `templates/AGENTS.md` is the neutral file installers link into
  consumer projects, along with `CLAUDE.md` for Claude Code.

Cursor does not natively discover `SKILL.md`. The included Python builder turns
each `skills/*/SKILL.md` into `.cursor/rules/<skill-directory>.mdc`, carrying
over the skill description and Markdown body and setting `alwaysApply: false`.
Skills therefore have one source of truth while remaining available to Cursor.

Subagents do not yet share a cross-tool schema. This repository uses Claude
Code's format as the common denominator: YAML frontmatter containing `name`,
`description`, `tools`, and `model`, followed by the subagent's Markdown prompt.

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

## Install

The installers create per-item symlinks rather than copies, so changes in this
checkout are immediately visible to supported agents while existing user skill
directories remain intact. They are safe to run again. An existing real item or
unknown symlink at a destination is reported and left alone.

### macOS and Linux

Install the shared skills for the current user and Claude Code subagents:

```bash
./scripts/install.sh
```

Optionally pass a project directory. This links the neutral
`templates/AGENTS.md` as `AGENTS.md` and `CLAUDE.md`, adds project-local Claude
Code skills and agents, and builds Cursor rules. Existing real project files
are left untouched:

```bash
./scripts/install.sh /path/to/project
```

### Windows

From PowerShell 7:

```powershell
pwsh ./scripts/install.ps1
pwsh ./scripts/install.ps1 -ProjectDir C:\path\to\project
```

From a plain PowerShell prompt:

```powershell
.\scripts\install.ps1
.\scripts\install.ps1 -ProjectDir C:\path\to\project
```

Creating symbolic links on Windows requires Developer Mode or an elevated
Administrator shell. The script warns when neither is detected and reports how
to resolve a link-creation failure.

## Adding content later

To add a skill, create `skills/<skill-name>/SKILL.md`. Give it YAML
frontmatter with `name` and `description`, then put its instructions in the
Markdown body. Helper scripts and references may live beside `SKILL.md`. Re-run
an installer with a project directory, or invoke the builder directly:

```bash
python3 scripts/build_cursor_rules.py \
  --skills-dir skills \
  --out-dir /path/to/project/.cursor/rules
```

To add a subagent, create `agents/<agent-name>.md` with `name`, `description`,
`tools`, and `model` in YAML frontmatter and its prompt in the Markdown body.
The installer exposes these files to Claude Code globally and, when requested,
inside a project.

Create a project-specific `AGENTS.md` before installation when the neutral
template is insufficient; the installer preserves an existing real file. Do
not put consumer-project policy in this repository's root `AGENTS.md`.

## Validation

Validate content and run the dependency-free test suite before publishing:

```bash
python scripts/validate_content.py
python scripts/validate_handoff.py --templates-dir templates/handoffs
python -m unittest discover -s tests -v
```

GitHub Actions runs the same checks on pushes and pull requests.

## Tools and compatibility

Use `python scripts/check_install.py --project /path/to/project` to inspect an
installation, `scripts/scaffold_content.py` to create valid starter content, and
`scripts/list_content.py --format json` to consume the catalog programmatically.
See [compatibility details](docs/compatibility.md), [security guidance](SECURITY.md),
and [release guidance](docs/releasing.md).

## Status

The current bundle contains thirty-five portable skills, twenty-one read-only
specialists, and two scoped implementation subagents. The product-engineering
pack includes frontend, backend API, database-design, CI, deployment-safety,
incident, and infrastructure-review workflows. See `CATALOG.md` for the
generated inventory.
