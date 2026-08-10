# Compatibility

| Capability | Claude Code | Codex | Gemini CLI / Antigravity | Cursor |
| --- | --- | --- | --- | --- |
| `AGENTS.md` project context | Via linked `CLAUDE.md` | Native | Native | Native |
| `SKILL.md` skills | Native | Native | Native | Generated `.mdc` rules |
| Claude-style subagents | Native | Adapt manually | Adapt manually | Adapt manually |
| Per-item installation | `~/.claude/` | `~/.codex/` | `~/.gemini/`, `~/.antigravity/` | Project `.cursor/rules/` |

Skills must remain usable by one agent because only Claude Code consumes the
subagent files directly. A skill may recommend delegation as an optional
acceleration path, but its core workflow must not depend on it.

Run `python scripts/build_cursor_rules.py --skills-dir skills --out-dir
<project>/.cursor/rules` after adding or changing a skill for Cursor.
