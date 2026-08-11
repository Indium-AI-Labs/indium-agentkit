#!/usr/bin/env python3
"""Validate RBAC schema rules and detect privilege escalation in indium-agentkit content."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import yaml
from pydantic import BaseModel, Field, ValidationError

FRONTMATTER_DELIMITER = "---"
MAX_FRONTMATTER_LINES = 100

MUTATING_TOOLS: frozenset[str] = frozenset({
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
})

class ModelRouting(BaseModel):
    primary: str
    fallback: str
    temperature: float = Field(default=0.0)

class SubagentFrontmatter(BaseModel):
    name: str
    description: str
    domain: str = Field(pattern=r"^(core-engineering|security-compliance|cloud-devops|frontend-design|ai-ml)$")
    permission_mode: str = Field(pattern=r"^(read-only|write-scoped)$")
    tools: List[str]
    model_routing: ModelRouting
    api_version: str

class SkillFrontmatter(BaseModel):
    name: str
    description: str
    domain: str | None = Field(default=None, pattern=r"^(core-engineering|security-compliance|cloud-devops|frontend-design|ai-ml)$")

def extract_frontmatter_bounded(path: Path) -> Tuple[str | None, str | None]:
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
                        return None, f"missing opening YAML frontmatter delimiter '{FRONTMATTER_DELIMITER}'"

                if stripped == FRONTMATTER_DELIMITER:
                    found_closing = True
                    break
                lines.append(line)
    except OSError as error:
        return None, f"file I/O failure: {error}"

    if not found_opening or not found_closing:
        return None, "malformed or missing YAML frontmatter delimiters"

    return "".join(lines), None

def validate_file_rbac(path: Path, root: Path) -> List[Dict[str, Any]]:
    violations: List[Dict[str, Any]] = []
    
    try:
        relative_path = path.relative_to(root)
        rel_path_str = str(relative_path)
    except ValueError:
        rel_path_str = str(path)
        relative_path = path

    raw_yaml, extract_error = extract_frontmatter_bounded(path)
    if extract_error or raw_yaml is None:
        violations.append({
            "level": "ERROR",
            "error_type": "SchemaValidationError",
            "file": rel_path_str,
            "message": extract_error or "Unknown extraction error",
        })
        return violations

    try:
        raw_dict = yaml.safe_load(raw_yaml)
        if not isinstance(raw_dict, dict):
            raise ValueError("YAML frontmatter must map to a dictionary.")
            
        root_dir = relative_path.parts[0] if relative_path.parts else ""
            
        if root_dir == "agents":
            manifest = SubagentFrontmatter.model_validate(raw_dict)
            
            if manifest.permission_mode == "read-only":
                declared_tools_lower = {tool.lower() for tool in manifest.tools}
                mutating = declared_tools_lower.intersection(MUTATING_TOOLS)
                
                if mutating:
                    prohibited_sorted = sorted(list(mutating))
                    violations.append({
                        "level": "CRITICAL",
                        "error_type": "PrivilegeEscalationError",
                        "file": rel_path_str,
                        "entity": manifest.name,
                        "prohibited_tools": prohibited_sorted,
                        "declared_tools": manifest.tools,
                        "message": f"Read-only entity '{manifest.name}' declared mutating tools: {', '.join(prohibited_sorted)}",
                    })

        elif root_dir == "skills" or path.name == "SKILL.md":
            skill_manifest = SkillFrontmatter.model_validate(raw_dict)
            if skill_manifest.name != path.parent.name and path.name == "SKILL.md":
                violations.append({
                    "level": "ERROR",
                    "error_type": "SchemaValidationError",
                    "file": rel_path_str,
                    "message": f"Skill name '{skill_manifest.name}' must match directory name '{path.parent.name}'.",
                })

    except ValidationError as e:
        violations.append({
            "level": "ERROR",
            "error_type": "SchemaValidationError",
            "file": rel_path_str,
            "message": f"Pydantic schema failure: {e.errors()}",
        })
    except (OSError, ValueError, yaml.YAMLError) as e:
        violations.append({
            "level": "ERROR",
            "error_type": "ParseError",
            "file": rel_path_str,
            "message": str(e),
        })

    return violations

def validate_catalog(target_dir: Path) -> Tuple[List[Dict[str, Any]], int]:
    violations: List[Dict[str, Any]] = []
    scanned_count = 0

    if not target_dir.exists() or not target_dir.is_dir():
        violations.append({
            "level": "ERROR",
            "error_type": "DirectoryResolutionError",
            "file": str(target_dir),
            "message": "Target directory does not exist or is inaccessible.",
        })
        return violations, 0

    target_files: List[Path] = []
    
    agents_dir = target_dir / "agents"
    if agents_dir.is_dir():
        target_files.extend([f for f in agents_dir.glob("*.md") if not f.name.startswith(".")])

    skills_dir = target_dir / "skills"
    if skills_dir.is_dir():
        target_files.extend(skills_dir.glob("*/SKILL.md"))

    for target_file in sorted(target_files):
        scanned_count += 1
        violations.extend(validate_file_rbac(target_file, target_dir))

    return violations, scanned_count

def validate_rbac_schema(target_dir: Path) -> Tuple[List[Dict[str, Any]], int]:
    """Helper alias for backwards compatibility."""
    return validate_catalog(target_dir)

def main() -> int:
    parser = argparse.ArgumentParser(description="Enforce strict RBAC schema limits across indium-agentkit.")
    parser.add_argument(
        "--target-dir",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="Absolute path to the target repository catalog.",
    )
    args = parser.parse_args()

    target_dir = args.target_dir.resolve()
    violations, scanned_count = validate_catalog(target_dir)

    if violations:
        for violation in violations:
            print(json.dumps(violation), file=sys.stderr)
        return 1

    print(json.dumps({
        "level": "INFO",
        "status": "PASSED",
        "scanned_files": scanned_count,
        "violations": 0,
        "message": f"RBAC schema validation passed cleanly across {scanned_count} catalog entities."
    }), file=sys.stdout)
    return 0

if __name__ == "__main__":
    sys.exit(main())
