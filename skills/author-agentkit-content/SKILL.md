---
name: author-agentkit-content
description: Create or update indium-agentkit skills, subagents, templates, validation, and catalog distribution files.
---

# Author Agentkit Content

Create, revise, validate, and publish portable AI coding-agent skills (`skills/<name>/SKILL.md`), Claude Code subagents (`agents/<name>.md`), project context templates (`templates/`), Cursor rules (`.cursor/rules/`), and catalog distribution manifests (`CATALOG.md`) for `indium-agentkit`.

The skill is **contract-first and repository-validated**: frontmatter constraints, RBAC read-only tool scoping, catalog synchronization, Cursor rule generation, and unit test suites are strictly verified before committing content changes.

---

## 1. Required I/O Context Schemas & Natural Language Auto-Inference

The skill supports **two invocation modes**:

1. **🤖 Orchestrator / Technical Mode (JSON Manifest)**: Pass the JSON context manifest below.
2. **💬 Non-Technical Mode (Plain English Prompts)**: If the user provides a natural language prompt (e.g. *"Create a new skill named 'rtos-firmware-development' for writing embedded FreeRTOS drivers"*), the agent **must automatically infer and populate** `content_type`, `content_name`, `target_directory`, and `validation_pipeline` from the user's text.

### JSON Context Manifest Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "AuthorAgentkitContentContextManifest",
  "type": "object",
  "required": ["content_spec", "authoring_config"],
  "properties": {
    "content_spec": {
      "type": "object",
      "required": ["content_type", "content_name"],
      "properties": {
        "content_type": { 
          "type": "string", 
          "enum": ["skill", "subagent", "template", "utility_script"] 
        },
        "content_name": { "type": "string", "pattern": "^[a-z0-9-]+$" },
        "description": { "type": "string" },
        "domain": { 
          "type": "string", 
          "enum": ["core_engineering", "security_compliance", "cloud_devops", "frontend_design", "ai_ml"] 
        }
      }
    },
    "authoring_config": {
      "type": "object",
      "required": ["run_validation_suite"],
      "properties": {
        "run_validation_suite": { "type": "boolean", "default": true },
        "build_cursor_rules": { "type": "boolean", "default": true },
        "regenerate_catalog": { "type": "boolean", "default": true },
        "run_unittests": { "type": "boolean", "default": true }
      }
    },
    "subagent_metadata": {
      "type": "object",
      "properties": {
        "permission_mode": { "type": "string", "enum": ["read-only", "write-scoped"] },
        "tools": { "type": "array", "items": { "type": "string" } },
        "model": { "type": "string", "default": "inherit" }
      }
    }
  }
}
```

### Automatic Natural Language Inference & Strict Validation Rules

If no raw JSON payload is provided, apply these defaults and strict repository rules:

- **Skill Frontmatter Rule**: `SKILL.md` frontmatter MUST contain **ONLY** `name` and `description` (no extra fields like `tools` or `domain`).
- **Directory Name Match**: The skill name in frontmatter (`name: my-skill`) MUST match its directory (`skills/my-skill/SKILL.md`).
- **Subagent Tool Scoping**: Subagents (`agents/*.md`) designated as read-only MUST NOT declare mutating tools (`edit`, `write`, `patch`, `replace_file_content`, `write_to_file`).

---

## 2. Deterministic State Machine Execution Flow

Follow this exact sequential protocol. Do not skip steps or alter execution ordering.

### Step 1: Content Scaffolding & Frontmatter Validation

1. For a **Skill** (`skills/<name>/SKILL.md`):
   - Scaffold directory `skills/<name>/`.
   - Write `SKILL.md` with strictly valid YAML frontmatter:
     ```yaml
     ---
     name: <name>
     description: <description describing capability and trigger>
     ---
     ```
2. For a **Subagent** (`agents/<name>.md`):
   - Write `agents/<name>.md` with frontmatter:
     ```yaml
     ---
     name: <name>
     description: <description>
     tools: Read, Grep, Glob, Bash
     model: inherit
     ---
     ```

### Step 2: Content Authoring & Depth Standards

1. Skills must be **250+ lines** and contain:
   - Section 1: JSON Context Manifest Schema & Natural Language Auto-Inference.
   - Section 2: Deterministic State Machine Execution Flow (Sequential steps).
   - Section 3: Reference Code Implementation (Full production-ready code).
   - Section 4: Invariants, Math Formulas & Technical SLA Bounds.
   - Section 5: Guardrails & Operational Restrictions.
   - Section 6: Atomic Failure Recovery & Rollback Handler.
   - Section 7: Verification Plan & Toolchain Commands.
   - Section 8: Completion Report.

### Step 3: Rule Generation & Catalog Synchronization

1. Execute the Cursor rule builder:
   ```bash
   python3 scripts/build_cursor_rules.py --skills-dir skills --out-dir .cursor/rules
   ```
2. Regenerate `CATALOG.md` and verify catalog consistency:
   ```bash
   python3 scripts/generate_catalog.py && python3 scripts/diff_catalog.py
   ```

### Step 4: Validation & Unit Testing Suite

1. Run content and RBAC validators:
   ```bash
   python3 scripts/validate_content.py && python3 scripts/validate_rbac_schema.py
   ```
2. Execute full Python unittest discovery:
   ```bash
   python3 -m unittest discover -s tests -v
   ```

---

## 3. Reference Implementation: Python Content Scaffolder & Validator

```python
import sys
import re
from pathlib import Path
from typing import Dict, Tuple

def validate_skill_frontmatter(skill_path: Path) -> Tuple[bool, str]:
    """Verify that SKILL.md frontmatter contains ONLY name and description."""
    content = skill_path.read_text(encoding="utf-8")
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    
    if not match:
        return False, "Missing or malformed YAML frontmatter (--- ... ---)"
        
    yaml_lines = [l.strip() for l in match.group(1).splitlines() if l.strip()]
    keys = []
    
    for line in yaml_lines:
        if ":" in line:
            key = line.split(":", 1)[0].strip()
            keys.append(key)
            
    allowed_keys = {"name", "description"}
    extra_keys = set(keys) - allowed_keys
    
    if extra_keys:
        return False, f"Forbidden extra frontmatter keys found: {extra_keys}. Only 'name' and 'description' are allowed."
        
    # Verify name matches directory name
    dir_name = skill_path.parent.name
    name_val = None
    for line in yaml_lines:
        if line.startswith("name:"):
            name_val = line.split(":", 1)[1].strip().strip('"\'')
            
    if name_val != dir_name:
        return False, f"Frontmatter name '{name_val}' does not match directory name '{dir_name}'."
        
    return True, "Skill frontmatter is valid."

if __name__ == "__main__":
    if len(sys.argv) > 1:
        valid, msg = validate_skill_frontmatter(Path(sys.argv[1]))
        print(f"Validation Result: {valid} - {msg}")
        sys.exit(0 if valid else 1)
```

---

## 4. Invariants & Repository Standards

$$\text{Skill Frontmatter Invariant: } \text{Keys}(\text{SKILL.md}) \equiv \{\text{"name"}, \text{"description"}\}$$

$$\text{Directory Name Matching: } \text{Frontmatter}(\text{name}) \equiv \text{DirName}(\text{skills/<name>})$$

$$\text{Catalog Synchronization: } \text{Diff}(\text{CATALOG.md}) \equiv 0 \quad (\text{after } \text{generate\_catalog.py})$$

---

## 5. Guardrails

### Operational Restrictions

- **No Unvalidated Content**: Never commit skills or subagents without running `validate_content.py` and `validate_rbac_schema.py`.
- **Single Commit Unit**: Catalog updates (`CATALOG.md`) MUST be included in the same commit as the content change.
- **Concise Imperative Commit Messages**: Use imperative subjects (e.g. `Add rtos-firmware-development skill`); avoid vague labels such as `changes` or `updates`.

---

## 6. Atomic Failure Recovery & Rollback Handler

If validation or tests fail during content authoring:

```bash
# Revert modified files
git checkout -- skills/ agents/ CATALOG.md 2>/dev/null

# Clean up uncommitted scaffold files
if [ -n "${NEW_SKILL_PATH:-}" ]; then
  rm -rf ${NEW_SKILL_PATH} 2>/dev/null
fi
```

---

## 7. Verification Plan & Toolchain Commands

Execute full verification suite before committing:

```bash
# 1. Run full validation, rule building, catalog sync, and test suite
python3 scripts/validate_content.py && \
python3 scripts/validate_rbac_schema.py && \
python3 scripts/build_cursor_rules.py --skills-dir skills --out-dir .cursor/rules && \
python3 scripts/generate_catalog.py && \
python3 scripts/diff_catalog.py && \
python3 -m unittest discover -s tests -v
```

---

## 8. Completion Report

Report content type created/updated (`skill`, `subagent`, `template`), path, line count, YAML frontmatter check results, Cursor rules generated, `CATALOG.md` sync status, unittest discovery outputs, and local git commit hash.
