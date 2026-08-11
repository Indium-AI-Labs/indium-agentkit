#!/usr/bin/env python3
"""Validate RBAC schema rules and detect privilege escalation in indium-agentkit content."""

from __future__ import annotations

import argparse
import json
import sys
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import yaml
from pydantic import BaseModel, Field, ValidationError, field_validator


FRONTMATTER_DELIMITER = "---"
MAX_FRONTMATTER_LINES = 100

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


class PermissionModeEnum(str, Enum):
    READ_ONLY = "read-only"
    WRITE_SCOPED = "write-scoped"


class DomainEnum(str, Enum):
    CORE_ENGINEERING = "core-engineering"
    SECURITY_COMPLIANCE = "security-compliance"
    CLOUD_DEVOPS = "cloud-devops"
    FRONTEND_DESIGN = "frontend-design"
    AI_ML = "ai-ml"
    AI_ML_ALT = "ai_ml"


class ModelRouting(BaseModel):
    primary: str
    fallback: str
    temperature: float = Field(default=0.0)


class SubagentFrontmatter(BaseModel):
    name: str
    description: str
    tools: List[str] = Field(default_factory=list)
    permission_mode: Optional[PermissionModeEnum] = None
    domain: Optional[str] = None
    model: Optional[Union[str, Dict[str, Any], ModelRouting]] = None

    @field_validator("tools", mode="before")
    @classmethod
    def parse_tools_field(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            return [tool.strip() for tool in v.replace(";", ",").split(",") if tool.strip()]
        if isinstance(v, list):
            return [str(tool).strip() for tool in v if str(tool).strip()]
        return []

    @field_validator("permission_mode", mode="before")
    @classmethod
    def parse_permission_mode(cls, v: Any) -> Optional[PermissionModeEnum]:
        if not v:
            return None
        v_str = str(v).strip().lower()
        if v_str == "read-only":
            return PermissionModeEnum.READ_ONLY
        if v_str in ("write-scoped", "write"):
            return PermissionModeEnum.WRITE_SCOPED
        return None


class SkillFrontmatter(BaseModel):
    name: str
    description: str
    domain: Optional[str] = None


def extract_frontmatter_bounded(path: Path) -> Tuple[Optional[str], Optional[str]]:
    """Extract frontmatter string using bounded line-reading to avoid reading entire file into memory."""
    lines: List[str] = []
    found_opening = False
    found_closing = False

    try:
        with path.open("r", encoding="utf-8") as handle:
            for idx, line in enumerate(handle):
                if idx >= MAX_FRONTMATTER_LINES:
                    break
                stripped = line.rstrip("\r\n")
                if idx == 0:
                    if stripped == FRONTMATTER_DELIMITER:
                        found_opening = True
                        continue
                    else:
                        return None, "missing opening YAML frontmatter delimiter"

                if stripped == FRONTMATTER_DELIMITER:
                    found_closing = True
                    break
                lines.append(line)
    except OSError as error:
        return None, f"file I/O failure: {error}"

    if not found_opening:
        return None, "missing opening YAML frontmatter delimiter"
    if not found_closing:
        return None, "missing closing YAML frontmatter delimiter"

    return "".join(lines), None


def validate_file_rbac(path: Path, root: Path) -> List[Dict[str, Any]]:
    violations: List[Dict[str, Any]] = []
    try:
        relative_path = path.relative_to(root)
        rel_path = str(relative_path)
    except ValueError:
        rel_path = str(path)
        relative_path = path

    raw_yaml, extract_error = extract_frontmatter_bounded(path)
    if extract_error:
        violations.append(
            {
                "level": "ERROR",
                "error_type": "SchemaValidationError",
                "file": rel_path,
                "message": extract_error,
            }
        )
        return violations

    try:
        data = yaml.safe_load(raw_yaml)
        if not isinstance(data, dict):
            violations.append(
                {
                    "level": "ERROR",
                    "error_type": "SchemaValidationError",
                    "file": rel_path,
                    "message": "frontmatter YAML did not parse into a dictionary mapping",
                }
            )
            return violations
    except yaml.YAMLError as error:
        violations.append(
            {
                "level": "ERROR",
                "error_type": "YAMLError",
                "file": rel_path,
                "message": f"malformed YAML frontmatter syntax: {error}",
            }
        )
        return violations

    root_dir = relative_path.parts[0] if relative_path.parts else ""
    is_skill = (root_dir == "skills") or path.name == "SKILL.md"

    if is_skill:
        try:
            skill_model = SkillFrontmatter.model_validate(data)
        except ValidationError as error:
            violations.append(
                {
                    "level": "ERROR",
                    "error_type": "SchemaValidationError",
                    "file": rel_path,
                    "message": f"Skill schema validation failure: {error.errors()}",
                }
            )
            return violations

        if skill_model.name != path.parent.name:
            violations.append(
                {
                    "level": "ERROR",
                    "error_type": "SchemaValidationError",
                    "file": rel_path,
                    "message": f"Skill frontmatter name '{skill_model.name}' must match directory name '{path.parent.name}'",
                }
            )
    else:
        try:
            subagent_model = SubagentFrontmatter.model_validate(data)
        except ValidationError as error:
            violations.append(
                {
                    "level": "ERROR",
                    "error_type": "SchemaValidationError",
                    "file": rel_path,
                    "message": f"Subagent schema validation failure: {error.errors()}",
                }
            )
            return violations

        name = subagent_model.name or path.stem
        tools = subagent_model.tools

        # Resolve effective permission mode
        effective_permission = subagent_model.permission_mode
        if effective_permission is None:
            if name.lower() in READONLY_SUBAGENTS:
                effective_permission = PermissionModeEnum.READ_ONLY
            else:
                effective_permission = PermissionModeEnum.WRITE_SCOPED

        if effective_permission == PermissionModeEnum.READ_ONLY and tools:
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


def validate_rbac_schema(target_dir: Path) -> Tuple[List[Dict[str, Any]], int]:
    violations: List[Dict[str, Any]] = []
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

    # Explicitly scan agents/*.md (excluding .gitkeep or non-subagent markdown files)
    agents_dir = target_dir / "agents"
    if agents_dir.is_dir():
        for agent_file in sorted(agents_dir.glob("*.md")):
            if agent_file.name.startswith("."):
                continue
            scanned_count += 1
            violations.extend(validate_file_rbac(agent_file, target_dir))

    # Explicitly scan skills/*/SKILL.md (ignoring general markdown docs like README.md or CHANGELOG.md)
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
