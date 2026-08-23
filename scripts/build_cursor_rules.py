#!/usr/bin/env python3
"""Convert agent skills from SKILL.md files to Cursor .mdc rules."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


FRONTMATTER_DELIMITER = "---"
DESCRIPTION_PATTERN = re.compile(r"^description\s*:(.*)$")


def read_text_preserving_newlines(path: Path) -> str:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return handle.read()


def split_frontmatter(path: Path) -> tuple[list[str], str, str]:
    text = read_text_preserving_newlines(path)
    lines = text.splitlines(keepends=True)

    if not lines or lines[0].rstrip("\r\n") != FRONTMATTER_DELIMITER:
        raise ValueError("missing opening YAML frontmatter delimiter")

    for index in range(1, len(lines)):
        if lines[index].rstrip("\r\n") == FRONTMATTER_DELIMITER:
            newline = "\r\n" if lines[index].endswith("\r\n") else "\n"
            return lines[1:index], "".join(lines[index + 1 :]), newline

    raise ValueError("missing closing YAML frontmatter delimiter")


def extract_description(frontmatter: list[str]) -> list[str]:
    for index, line in enumerate(frontmatter):
        content = line.rstrip("\r\n")
        match = DESCRIPTION_PATTERN.match(content)
        if not match:
            continue

        value = match.group(1).strip()
        if not value:
            raise ValueError("description field is empty")

        description = [content]
        if value in {"|", ">", "|-", ">-", "|+", ">+"}:
            for continuation in frontmatter[index + 1 :]:
                continuation_content = continuation.rstrip("\r\n")
                if continuation_content and not continuation_content[0].isspace():
                    break
                description.append(continuation_content)
        return description

    raise ValueError("missing description field")


def convert_skill(skill_file: Path, out_dir: Path) -> Path:
    frontmatter, body, newline = split_frontmatter(skill_file)
    description = extract_description(frontmatter)
    output_file = out_dir / f"{skill_file.parent.name}.mdc"

    generated_frontmatter = newline.join(
        [FRONTMATTER_DELIMITER, *description, "alwaysApply: false", FRONTMATTER_DELIMITER]
    )
    output = f"{generated_frontmatter}{newline}{body}"
    with output_file.open("w", encoding="utf-8", newline="") as handle:
        handle.write(output)

    return output_file


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert skills/*/SKILL.md files to Cursor .mdc rules.",
        allow_abbrev=False,
    )
    parser.add_argument(
        "--skills-dir", type=Path, required=True, help="Directory containing skills"
    )
    parser.add_argument(
        "--out-dir", type=Path, required=True, help="Directory for generated .mdc files"
    )
    parser.add_argument(
        "--skill", help="Convert only the skill whose directory has this name"
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    skills_dir = args.skills_dir.expanduser().resolve()
    out_dir = args.out_dir.expanduser().resolve()

    if not skills_dir.is_dir():
        print(f"error: skills directory does not exist: {skills_dir}", file=sys.stderr)
        return 2

    skill_files = sorted(skills_dir.glob("*/SKILL.md"))
    if args.skill:
        skill_files = [
            skill_file
            for skill_file in skill_files
            if skill_file.parent.name == args.skill
        ]
        if not skill_files:
            print(f"error: skill not found: {args.skill}", file=sys.stderr)
            return 2
    if not skill_files:
        print("no skills found")
        return 0

    out_dir.mkdir(parents=True, exist_ok=True)
    had_errors = False
    for skill_file in skill_files:
        try:
            output_file = convert_skill(skill_file, out_dir)
            print(f"generated {output_file}")
        except (OSError, ValueError) as error:
            had_errors = True
            print(f"error: {skill_file}: {error}", file=sys.stderr)

    return 1 if had_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
