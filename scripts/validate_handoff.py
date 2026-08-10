#!/usr/bin/env python3
"""Validate the structure of indium-agentkit handoff documents."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


HANDOFF_LABELS = {
    "changed contract",
    "files / systems affected",
    "evidence and tests",
    "risks / rollback",
    "what the next agent needs",
}
REQUIRED_HEADINGS = {
    "feature-brief": {
        "goal",
        "non-goals",
        "acceptance criteria",
        "user experience and states",
        "api and data implications",
        "risks and rollout",
        "handoff",
    },
    "api-contract": {
        "resources and operations",
        "authentication and authorization",
        "requests and responses",
        "errors",
        "compatibility",
        "handoff",
    },
    "data-migration-plan": {
        "current and target state",
        "preflight",
        "rollout",
        "rollback",
        "verification",
        "handoff",
    },
    "verification-report": {
        "scope",
        "commands and results",
        "evidence",
        "limitations",
        "handoff",
    },
    "onboarding-guide": {
        "project overview",
        "prerequisites",
        "development setup",
        "source layout",
        "key abstractions",
        "common workflows",
        "gotchas and tips",
        "handoff",
    },
    "dependency-audit-report": {
        "scope",
        "inventory summary",
        "vulnerability findings",
        "license analysis",
        "staleness and maintenance",
        "recommendations",
        "handoff",
    },
    "accessibility-audit-report": {
        "scope",
        "conformance summary",
        "findings",
        "areas not tested",
        "handoff",
    },
}
HEADING = re.compile(r"^#{1,6}\s+(.+?)\s*$", re.MULTILINE)
HANDOFF_LABEL = re.compile(r"^\*\*([^*]+):\*\*", re.MULTILINE)


def normalize(value: str) -> str:
    return " ".join(value.casefold().strip().split())


def validate_handoff(path: Path, kind: str) -> list[str]:
    if not path.is_file():
        return ["file does not exist"]
    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return ["file is not valid UTF-8"]

    headings = {normalize(match.group(1)) for match in HEADING.finditer(content)}
    labels = {normalize(match.group(1)) for match in HANDOFF_LABEL.finditer(content)}
    errors = [
        f"missing required heading: {heading}"
        for heading in sorted(REQUIRED_HEADINGS[kind] - headings)
    ]
    errors.extend(
        f"missing handoff field: {label}"
        for label in sorted(HANDOFF_LABELS - labels)
    )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate handoff document structure.")
    parser.add_argument("path", nargs="?", type=Path, help="Handoff Markdown file")
    parser.add_argument("--kind", choices=sorted(REQUIRED_HEADINGS), help="Document kind")
    parser.add_argument(
        "--templates-dir",
        type=Path,
        help="Validate every canonical handoff template in this directory",
    )
    args = parser.parse_args()

    if bool(args.path) == bool(args.templates_dir):
        parser.error("provide exactly one of a path or --templates-dir")
    if args.path and not args.kind:
        parser.error("--kind is required when validating a single path")

    targets = (
        [(args.path, args.kind)]
        if args.path
        else [(args.templates_dir / f"{kind}.md", kind) for kind in REQUIRED_HEADINGS]
    )
    failures: list[tuple[Path, str]] = []
    for path, kind in targets:
        for error in validate_handoff(path, kind):
            failures.append((path, error))

    if failures:
        for path, error in failures:
            print(f"error: {path}: {error}", file=sys.stderr)
        return 1
    print("handoff validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
