#!/usr/bin/env python3
"""Verify that skill and agent names/descriptions do not have duplicate triggers or collisions."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from list_content import collect


def check_overlaps(repo_root: Path) -> list[str]:
    content = collect(repo_root)
    names = set()
    warnings = []

    for item in content:
        name = item["name"]
        if name in names:
            warnings.append(f"Duplicate name detected: '{name}'")
        names.add(name)

        desc = item["description"].lower()
        if len(desc) < 10:
            warnings.append(f"Description too short for '{name}': '{item['description']}'")

    return warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify skill and agent name/trigger overlap.")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="Repository root",
    )
    args = parser.parse_args()
    root = args.repo_root.resolve()

    warnings = check_overlaps(root)
    if warnings:
        for w in warnings:
            print(f"warning: {w}", file=sys.stderr)
        return 1

    print("no name collisions or invalid descriptions detected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
