#!/usr/bin/env python3
"""Validate RBAC metadata using only the Python standard library."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

FRONTMATTER_DELIMITER = "---"
MAX_FRONTMATTER_LINES = 100
DOMAINS = {"core-engineering", "security-compliance", "cloud-devops", "frontend-design", "ai-ml"}
PERMISSION_MODES = {"read-only", "write-scoped"}
MUTATING_TOOLS = frozenset({"edit", "write", "patch", "delete", "replace", "writetofile", "replacefilecontent", "multireplacefilecontent", "scaffold", "scaffold_content", "write_to_file"})
KEY_VALUE = re.compile(r"^([A-Za-z][A-Za-z0-9_-]*):(?:[ \t]*(.*))?$")


def extract_frontmatter_bounded(path: Path) -> tuple[str | None, str | None]:
    lines: list[str] = []
    try:
        with path.open("r", encoding="utf-8") as handle:
            for index, line in enumerate(handle):
                if index >= MAX_FRONTMATTER_LINES:
                    break
                stripped = line.rstrip("\r\n")
                if index == 0 and stripped != FRONTMATTER_DELIMITER:
                    return None, "missing opening YAML frontmatter delimiter '---'"
                if index == 0:
                    continue
                if stripped == FRONTMATTER_DELIMITER:
                    return "".join(lines), None
                lines.append(line)
    except (OSError, UnicodeDecodeError) as error:
        return None, f"file I/O failure: {error}"
    return None, "malformed or missing YAML frontmatter delimiters"


def _scalar(value: str) -> Any:
    value = value.strip()
    if not value:
        return None
    if value[0:1] in {"'", '"'}:
        if len(value) < 2 or value[-1] != value[0]:
            raise ValueError(f"unterminated quoted value: {value}")
        return value[1:-1]
    if value.startswith("["):
        if not value.endswith("]"):
            raise ValueError(f"unterminated list: {value}")
        inner = value[1:-1].strip()
        return [] if not inner else [_scalar(item) for item in inner.split(",")]
    if value in {"true", "True"}:
        return True
    if value in {"false", "False"}:
        return False
    try:
        return float(value) if "." in value else int(value)
    except ValueError:
        return value


def parse_frontmatter(raw: str) -> dict[str, Any]:
    result: dict[str, Any] = {}
    current_list: str | None = None
    current_map: str | None = None
    for line in raw.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        stripped = line.strip()
        if stripped.startswith("-"):
            if current_list is None:
                raise ValueError(f"list item without list key: {line}")
            if isinstance(result.get(current_list), dict):
                result[current_list] = []
            result.setdefault(current_list, []).append(_scalar(stripped[1:].strip()))
            continue
        match = KEY_VALUE.match(stripped)
        if not match:
            raise ValueError(f"unsupported frontmatter line: {line!r}")
        key, value = match.groups()
        if line.startswith((" ", "\t")) and current_map:
            result.setdefault(current_map, {})[key] = _scalar(value or "")
            continue
        if key in result:
            raise ValueError(f"duplicate frontmatter field: {key}")
        if value is None or not value.strip():
            result[key] = {}
            current_list = key
            current_map = key
        else:
            result[key] = _scalar(value)
            current_list = key if isinstance(result[key], list) else None
            current_map = None
    return result


def _error(rel_path: str, message: str, error_type: str = "SchemaValidationError") -> dict[str, Any]:
    return {"level": "ERROR", "error_type": error_type, "file": rel_path, "message": message}


def _validate_common(manifest: dict[str, Any], required: tuple[str, ...]) -> list[str]:
    return [f"missing required field: {field}" for field in required if field not in manifest]


def validate_file_rbac(path: Path, root: Path) -> list[dict[str, Any]]:
    try:
        relative = path.relative_to(root)
        relative_text = str(relative)
    except ValueError:
        relative = path
        relative_text = str(path)
    raw, extraction_error = extract_frontmatter_bounded(path)
    if extraction_error or raw is None:
        return [_error(relative_text, extraction_error or "frontmatter extraction failed")]
    try:
        manifest = parse_frontmatter(raw)
    except ValueError as error:
        return [_error(relative_text, str(error), "ParseError")]

    root_dir = relative.parts[0] if relative.parts else ""
    if root_dir == "skills" or path.name == "SKILL.md":
        errors = _validate_common(manifest, ("name", "description"))
        if manifest.get("domain") is not None and manifest["domain"] not in DOMAINS:
            errors.append(f"invalid domain: {manifest['domain']}")
        if manifest.get("name") != path.parent.name:
            errors.append(f"skill name '{manifest.get('name')}' must match directory name '{path.parent.name}'")
        return [_error(relative_text, "; ".join(errors))] if errors else []

    if root_dir != "agents":
        return []
    strict = any(key in manifest for key in ("domain", "permission_mode", "model_routing", "api_version"))
    if not strict and set(("name", "description", "tools", "model")).issubset(manifest):
        return []
    errors = _validate_common(manifest, ("name", "description", "domain", "permission_mode", "tools", "model_routing", "api_version"))
    if manifest.get("domain") not in DOMAINS:
        errors.append(f"invalid domain: {manifest.get('domain')}")
    if manifest.get("permission_mode") not in PERMISSION_MODES:
        errors.append(f"invalid permission_mode: {manifest.get('permission_mode')}")
    if not isinstance(manifest.get("tools"), list) or not all(isinstance(tool, str) for tool in manifest.get("tools", [])):
        errors.append("tools must be a list of strings")
    routing = manifest.get("model_routing")
    if not isinstance(routing, dict) or not {"primary", "fallback"}.issubset(routing):
        errors.append("model_routing must contain primary and fallback")
    elif not isinstance(routing.get("temperature", 0.0), (int, float)):
        errors.append("model_routing.temperature must be numeric")
    if errors:
        return [_error(relative_text, "; ".join(errors))] if errors else []
    if manifest["permission_mode"] == "read-only":
        declared = {tool.casefold() for tool in manifest["tools"]}
        mutating = sorted(declared.intersection(MUTATING_TOOLS))
        if mutating:
            return [{"level": "CRITICAL", "error_type": "PrivilegeEscalationError", "file": relative_text,
                     "entity": manifest["name"], "prohibited_tools": mutating, "declared_tools": manifest["tools"],
                     "message": f"Read-only entity '{manifest['name']}' declared mutating tools: {', '.join(mutating)}"}]
    return []


def validate_catalog(target_dir: Path) -> tuple[list[dict[str, Any]], int]:
    if not target_dir.is_dir():
        return [_error(str(target_dir), "Target directory does not exist or is inaccessible", "DirectoryResolutionError")], 0
    files: list[Path] = []
    agents_dir = target_dir / "agents"
    skills_dir = target_dir / "skills"
    if agents_dir.is_dir():
        files.extend(path for path in agents_dir.glob("*.md") if not path.name.startswith("."))
    if skills_dir.is_dir():
        files.extend(skills_dir.glob("*/SKILL.md"))
    violations: list[dict[str, Any]] = []
    for path in sorted(files):
        violations.extend(validate_file_rbac(path, target_dir))
    return violations, len(files)


def validate_rbac_schema(target_dir: Path) -> tuple[list[dict[str, Any]], int]:
    return validate_catalog(target_dir)


def main() -> int:
    parser = argparse.ArgumentParser(description="Enforce RBAC schema limits across indium-agentkit.")
    parser.add_argument("--target-dir", type=Path, default=Path(__file__).resolve().parent.parent)
    args = parser.parse_args()
    target_dir = args.target_dir.resolve()
    violations, scanned_count = validate_catalog(target_dir)
    if violations:
        for violation in violations:
            print(json.dumps(violation), file=sys.stderr)
        return 1
    print(json.dumps({"level": "INFO", "status": "PASSED", "scanned_files": scanned_count, "violations": 0,
                      "message": f"RBAC schema validation passed cleanly across {scanned_count} catalog entities."}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
