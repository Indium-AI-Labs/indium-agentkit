#!/usr/bin/env python3
"""Check whether indium-agentkit content is linked into expected locations."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def link_matches(path: Path, target: Path) -> bool:
    try:
        return path.is_symlink() and path.resolve() == target.resolve()
    except OSError:
        return False


def check_collection(source: Path, destination: Path, items: list[Path]) -> list[dict[str, str]]:
    results: list[dict[str, str]] = []
    if link_matches(destination, source):
        return [{"status": "warning", "path": str(destination), "message": "legacy directory link; re-run installer to migrate"}]
    if not destination.is_dir():
        return [{"status": "error", "path": str(destination), "message": "collection directory is missing"}]
    for item in items:
        installed = destination / item.name
        if link_matches(installed, item):
            results.append({"status": "ok", "path": str(installed), "message": "linked"})
        elif installed.exists() or installed.is_symlink():
            results.append({"status": "error", "path": str(installed), "message": "not linked to agentkit source"})
        else:
            results.append({"status": "error", "path": str(installed), "message": "missing"})
    return results


def check_project(repo_root: Path, project: Path, skills: list[Path], agents: list[Path]) -> list[dict[str, str]]:
    template = repo_root / "templates" / "AGENTS.md"
    results: list[dict[str, str]] = []
    for filename in ("AGENTS.md", "CLAUDE.md"):
        path = project / filename
        status = "ok" if link_matches(path, template) else "error"
        message = "linked" if status == "ok" else "not linked to templates/AGENTS.md"
        results.append({"status": status, "path": str(path), "message": message})
    results.extend(check_collection(repo_root / "skills", project / ".claude" / "skills", skills))
    results.extend(check_collection(repo_root / "agents", project / ".claude" / "agents", agents))
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Check an indium-agentkit installation.")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--home", type=Path, default=Path.home(), help="Home directory to inspect")
    parser.add_argument("--project", type=Path, help="Optional installed project directory")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text")
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    skills = sorted(path for path in (repo_root / "skills").iterdir() if path.is_dir())
    agents = sorted((repo_root / "agents").glob("*.md"))
    home = args.home.expanduser().resolve()
    results: list[dict[str, str]] = []
    for tool in (".claude", ".codex", ".gemini", ".antigravity"):
        results.extend(check_collection(repo_root / "skills", home / tool / "skills", skills))
    results.extend(check_collection(repo_root / "agents", home / ".claude" / "agents", agents))
    if args.project:
        results.extend(check_project(repo_root, args.project.resolve(), skills, agents))

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        for result in results:
            print(f"{result['status']}: {result['path']}: {result['message']}")
    return 1 if any(result["status"] == "error" for result in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
