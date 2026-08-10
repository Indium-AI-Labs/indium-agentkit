#!/usr/bin/env python3
"""Create valid starting files for an indium-agentkit skill or subagent."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


VALID_NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def write_new_file(path: Path, content: str) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite existing path: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Scaffold an indium-agentkit skill or subagent.")
    parser.add_argument("kind", choices=("skill", "agent"))
    parser.add_argument("name")
    parser.add_argument("--description", required=True)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--tools", default="Read, Grep, Glob, Bash", help="Agent tools")
    parser.add_argument("--model", default="inherit", help="Agent model")
    args = parser.parse_args()

    if not VALID_NAME.fullmatch(args.name):
        parser.error("name must use lowercase letters, digits, and single hyphens")
    if not args.description.strip():
        parser.error("description must not be empty")
    root = args.repo_root.resolve()
    if args.kind == "skill":
        path = root / "skills" / args.name / "SKILL.md"
        content = f"---\nname: {args.name}\ndescription: \"{args.description}\"\n---\n\n# {args.name.replace('-', ' ').title()}\n\n1. Define the workflow.\n"
    else:
        path = root / "agents" / f"{args.name}.md"
        content = f"---\nname: {args.name}\ndescription: \"{args.description}\"\ntools: {args.tools}\nmodel: {args.model}\n---\n\n# {args.name.replace('-', ' ').title()}\n\nDefine the focused responsibility and report format.\n"
    try:
        write_new_file(path, content)
    except FileExistsError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(f"created {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
