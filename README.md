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
  Aider, Windsurf, and Zed read it natively. The installers link `CLAUDE.md` to
  the same file so Claude Code gets the context without maintaining a duplicate.

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
├── skills/
│   └── .gitkeep
├── agents/
│   └── .gitkeep
├── scripts/
│   ├── install.sh
│   ├── install.ps1
│   └── build_cursor_rules.py
└── .gitignore
```

## Install

The installers create symlinks rather than copies, so changes in this checkout
are immediately visible to the supported agents. They are safe to run again.
An existing real file or directory at a destination is reported and left alone;
an existing symlink is kept or updated as needed.

### macOS and Linux

Install the shared skills for the current user and Claude Code subagents:

```bash
./scripts/install.sh
```

Optionally pass a project directory. This also links `AGENTS.md` and
`CLAUDE.md`, adds project-local Claude Code skills and agents, and builds Cursor
rules:

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

Edit the root `AGENTS.md` template with a project's actual stack, test command,
lint command, layout, and conventions before linking it into that project.

## Status

`skills/` and `agents/` are currently empty. This commit is scaffold-only: it
contains documentation and install/build tooling, but no skills or subagents.
