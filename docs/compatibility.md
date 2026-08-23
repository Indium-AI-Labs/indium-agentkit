# Compatibility

| Capability | Claude Code | Codex | Gemini CLI / Antigravity | Cursor |
| --- | --- | --- | --- | --- |
| Project context | `CLAUDE.md` | `AGENTS.md` | `AGENTS.md` | `AGENTS.md` |
| `SKILL.md` skills | Native | Native | Native | Generated `.mdc` rules |
| Claude-style subagents | Native | Delegation adapter | Distributed role files | Adapt manually |
| Project installation | `.claude/` | `.codex/` | `.gemini/`, `.antigravity/` | `.cursor/rules/` |
| User installation | `~/.claude/` | `~/.codex/` | `~/.gemini/`, `~/.antigravity/` | `~/.cursor/rules/` |

Skills must remain usable by one agent because only Claude Code consumes the
subagent files directly. A skill may recommend delegation as an optional
acceleration path, but its core workflow must not depend on it.

Installation scope and target are independent. Project scope never writes to
the user home, and user scope never creates project files. `add <name>` installs
only that artifact; `install` installs the bundle. The npm CLI uses copies by
default, while local checkout wrappers use links by default.

Run `python scripts/build_cursor_rules.py --skills-dir skills --out-dir
<project>/.cursor/rules --skill <name>` to convert one skill for Cursor, or omit
`--skill` to convert the complete skill collection.
