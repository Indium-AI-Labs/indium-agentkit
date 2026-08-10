#!/usr/bin/env python3
"""Check that CATALOG.md matches the current content frontmatter."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from generate_catalog import generate_catalog


def main() -> int:
    parser = argparse.ArgumentParser(description="Check CATALOG.md freshness.")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="Repository root",
    )
    args = parser.parse_args()
    root = args.repo_root.resolve()
    catalog_path = root / "CATALOG.md"

    if not catalog_path.is_file():
        print("error: CATALOG.md does not exist", file=sys.stderr)
        return 1

    expected = generate_catalog(root)
    actual = catalog_path.read_text(encoding="utf-8")

    if actual == expected:
        print("CATALOG.md is up to date")
        return 0

    print("error: CATALOG.md is stale; run: python scripts/generate_catalog.py", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
