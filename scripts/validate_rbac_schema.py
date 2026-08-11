#!/usr/bin/env python3
"""Validate RBAC schema rules and detect privilege escalation in indium-agentkit content."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Set, Tuple


FRONTMATTER_DELIMITER = "---"
KEY_VALUE = re.compile(r"^([A-Za-z][A-Za-z0-9_-]*):[ \t]*(.+?)[ \t]*$")

MUTATING_TOOLS: Set[str] = {
    "edit",
    "write",
    "patch",
    "delete",
    "replace",
    "writetofile",
    "replacefilecontent",
    "multireplacefilecontent",
    "scaffold",
    "scaffold_content",
    "write_to_file",
}

READONLY_SUBAGENTS: Set[str] = {
    "ebpf-specialist",
    "webgpu-architect",
    "formal-verifier",
    "wasm-specialist",
    "iot-embedded-auditor",
    "agent-orchestrator",
    "synthetic-data-architect",
    "local-model-specialist",
    "reviewer",
    "verifier",
    "security-reviewer",
    "compliance-auditor",
    "resilience-reviewer",
    "accessibility-checker",
    "ci-verifier",
    "dependency-auditor",
    "doc-writer",
    "estimator",
    "explorer",
    "llm-evaluator",
    "migration-planner",
    "performance-profiler",
    "runbook-writer",
}


class RBACValidationError(Exception):
    """Base exception for RBAC schema validation errors."""


class PrivilegeEscalationError(RBACValidationError):
    """Raised when a read-only entity declares mutating tools."""


class SchemaValidationError(RBACValidationError):
    """Raised when frontmatter fails structural schema parsing."""


@dataclass
class SubagentFrontmatter:
    name: str
    description: str
    tools: List[str]
    permission_mode: str
    domain: str
    model: str


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def parse_frontmatter(path: Path) -> tuple[dict[str, str], list[str]]:
    try:
        lines = read_text(path).splitlines()
    except Exception as error:
        return {}, [f"file read failure: {error}"]

    if not lines or lines[0] != FRONTMATTER_DELIMITER:
        return {}, ["missing opening YAML frontmatter delimiter"]

    try:
        close_index = lines.index(FRONTMATTER_DELIMITER, 1)
    except ValueError:
        return {}, ["missing closing YAML frontmatter delimiter"]

    fields: dict[str, str] = {}
    errors: list[str] = []
    for line in lines[1:close_index]:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        match = KEY_VALUE.match(line)
        if not match:
            errors.append(f"unsupported frontmatter line: {line!r}")
            continue
        key, value = match.groups()
        if key in fields:
            errors.append(f"duplicate frontmatter field: {key}")
        fields[key] = value.strip().strip('"').strip("'")

    return fields, errors


def parse_tools_list(tools_str: str) -> List[str]:
    if not tools_str:
        return []
    return [tool.strip() for tool in re.split(r"[,;]+", tools_str) if tool.strip()]


def is_readonly_entity(name: str, fields: dict[str, str]) -> bool:
    perm = fields.get("permission_mode") or fields.get("permission") or fields.get("rbac_role")
    if perm and perm.lower() == "read-only":
        return True

    desc = fields.get("description", "").lower()
    if "read-only" in desc:
        return True

    if name.lower() in READONLY_SUBAGENTS:
        return True

    return False


def validate_file_rbac(path: Path, root: Path) -> List[dict[str, Any]]:
    violations: List[dict[str, Any]] = []
    fields, parse_errors = parse_frontmatter(path)
    rel_path = str(path.relative_to(root)) if root in path.parents or path == root else str(path)

    if parse_errors:
        for err in parse_errors:
            violations.append(
                {
                    "level": "ERROR",
                    "error_type": "SchemaValidationError",
                    "file": rel_path,
                    "message": err,
                }
            )
        return violations

    name = fields.get("name", path.stem)
    tools = parse_tools_list(fields.get("tools", ""))
    readonly = is_readonly_entity(name, fields)

    if readonly and tools:
        declared_tools_lower = {tool.lower() for tool in tools}
        mutating = declared_tools_lower.intersection(MUTATING_TOOLS)
        if mutating:
            prohibited_sorted = sorted(list(mutating))
            violations.append(
                {
                    "level": "ERROR",
                    "error_type": "PrivilegeEscalationError",
                    "file": rel_path,
                    "entity": name,
                    "prohibited_tools": prohibited_sorted,
                    "declared_tools": tools,
                    "message": f"Read-only entity '{name}' declared mutating tools: {', '.join(prohibited_sorted)}",
                }
            )

    return violations


def validate_rbac_schema(target_dir: Path) -> Tuple[List[dict[str, Any]], int]:
    violations: List[dict[str, Any]] = []
    scanned_count = 0

    if not target_dir.exists() or not target_dir.is_dir():
        violations.append(
            {
                "level": "ERROR",
                "error_type": "SchemaValidationError",
                "file": str(target_dir),
                "message": f"target directory does not exist or is not a directory: {target_dir}",
            }
        )
        return violations, 0

    # Scan agents/*.md and skills/*/SKILL.md
    agents_dir = target_dir / "agents"
    if agents_dir.is_dir():
        for agent_file in sorted(agents_dir.glob("*.md")):
            scanned_count += 1
            violations.extend(validate_file_rbac(agent_file, target_dir))

    skills_dir = target_dir / "skills"
    if skills_dir.is_dir():
        for skill_file in sorted(skills_dir.glob("*/SKILL.md")):
            scanned_count += 1
            violations.extend(validate_file_rbac(skill_file, target_dir))

    return violations, scanned_count


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate RBAC schema and tool privilege limits across the catalog.")
    parser.add_argument(
        "--target-dir",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="Target directory to scan (default: repository root)",
    )
    parser.add_argument(
        "--json-output",
        action="store_true",
        help="Emit structured NDJSON output format to stdout/stderr",
    )
    args = parser.parse_args()

    target_dir = args.target_dir.expanduser().resolve()
    violations, scanned_count = validate_rbac_schema(target_dir)

    if violations:
        for violation in violations:
            log_line = json.dumps(violation)
            print(log_line, file=sys.stderr)
        return 1

    summary = {
        "level": "INFO",
        "status": "PASSED",
        "scanned_files": scanned_count,
        "violations": 0,
        "message": f"RBAC schema validation passed cleanly across {scanned_count} catalog entities.",
    }
    print(json.dumps(summary), file=sys.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
