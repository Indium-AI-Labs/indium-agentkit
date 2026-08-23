#!/usr/bin/env python3
"""Check one explicit indium-agentkit installation boundary."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from install import (
    AGENT_DESTINATIONS,
    SKILL_DESTINATIONS,
    expand_targets,
    paths_match,
    select_content,
)


def artifact_matches(source: Path, destination: Path, mode: str) -> bool:
    if mode in {"auto", "link"}:
        try:
            if destination.is_symlink() and destination.resolve() == source.resolve():
                return True
        except OSError:
            pass
    return mode in {"auto", "copy"} and paths_match(source, destination)


def check_artifact(
    source: Path, destination: Path, mode: str
) -> dict[str, str]:
    if artifact_matches(source, destination, mode):
        installed_as = "linked" if destination.is_symlink() else "copied"
        return {"status": "ok", "path": str(destination), "message": installed_as}
    if destination.exists() or destination.is_symlink():
        message = f"does not match agentkit source using {mode} mode"
    else:
        message = "missing"
    return {"status": "error", "path": str(destination), "message": message}


def check_collection(
    sources: list[Path], destination: Path, mode: str
) -> list[dict[str, str]]:
    if not destination.is_dir():
        return [
            {
                "status": "error",
                "path": str(destination),
                "message": "collection directory is missing",
            }
        ]
    return [
        check_artifact(source, destination / source.name, mode) for source in sources
    ]


def check_scope(
    repo_root: Path,
    install_root: Path,
    targets: list[str],
    skills: list[Path],
    agents: list[Path],
    mode: str,
    include_context: bool,
) -> list[dict[str, str]]:
    results: list[dict[str, str]] = []
    for target in targets:
        skill_destination = SKILL_DESTINATIONS.get(target)
        if skill_destination and skills:
            results.extend(
                check_collection(skills, install_root / skill_destination, mode)
            )

        agent_destination = AGENT_DESTINATIONS.get(target)
        if agent_destination and agents:
            results.extend(
                check_collection(agents, install_root / agent_destination, mode)
            )

        if target == "cursor" and skills:
            rules_dir = install_root / ".cursor" / "rules"
            if not rules_dir.is_dir():
                results.append(
                    {
                        "status": "error",
                        "path": str(rules_dir),
                        "message": "collection directory is missing",
                    }
                )
            else:
                for skill in skills:
                    rule = rules_dir / f"{skill.name}.mdc"
                    results.append(
                        {
                            "status": "ok" if rule.is_file() else "error",
                            "path": str(rule),
                            "message": "generated" if rule.is_file() else "missing",
                        }
                    )

    if include_context:
        template = repo_root / "templates" / "AGENTS.md"
        if "claude" in targets:
            results.append(check_artifact(template, install_root / "CLAUDE.md", mode))
        if any(target != "claude" for target in targets):
            results.append(check_artifact(template, install_root / "AGENTS.md", mode))
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Check an indium-agentkit installation.")
    parser.add_argument(
        "--repo-root", type=Path, default=Path(__file__).resolve().parent.parent
    )
    parser.add_argument("--home", type=Path, default=Path.home())
    parser.add_argument("--project", type=Path)
    parser.add_argument("--scope", choices=("user", "project", "both"))
    parser.add_argument("--target", action="append", default=[])
    parser.add_argument("--item", default="all")
    parser.add_argument("--mode", choices=("auto", "link", "copy"), default="auto")
    parser.add_argument(
        "--include-context",
        action="store_true",
        help="Require the target-specific project context file",
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    scope = args.scope or ("project" if args.project else "user")
    if scope in {"project", "both"} and not args.project:
        parser.error("--project is required for project or both scope")

    repo_root = args.repo_root.resolve()
    try:
        targets = expand_targets(args.target or ["all"])
        skills, agents = select_content(repo_root, args.item)
    except ValueError as error:
        parser.error(str(error))

    results: list[dict[str, str]] = []
    if scope in {"user", "both"}:
        results.extend(
            check_scope(
                repo_root,
                args.home.expanduser().resolve(),
                targets,
                skills,
                agents,
                args.mode,
                False,
            )
        )
    if scope in {"project", "both"}:
        results.extend(
            check_scope(
                repo_root,
                args.project.expanduser().resolve(),
                targets,
                skills,
                agents,
                args.mode,
                args.include_context or args.item == "all",
            )
        )

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        for result in results:
            print(f"{result['status']}: {result['path']}: {result['message']}")
    return 1 if any(result["status"] == "error" for result in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
