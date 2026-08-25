---
name: onboard-to-codebase
description: Generate comprehensive developer onboarding guides, architecture orientations, dependency graphs, and environment setup specs.
---

# Onboard to Codebase

Generate developer-facing orientation documentation, architecture topographies, environment setup bootstrap guides, dependency graphs, test execution workflows, and common task runbooks by analyzing existing project source code and configuration.

The skill is **contract-first and empirical**: repository layout, framework entry points, local environment setup commands, database seed paths, test commands, and developer gotchas are extracted directly from code without introducing unverified assumptions.

---

## 1. Required I/O Context Schemas & Natural Language Auto-Inference

The skill supports **two invocation modes**:

1. **🤖 Orchestrator / Technical Mode (JSON Manifest)**: Pass the JSON context manifest below.
2. **💬 Non-Technical Mode (Plain English Prompts)**: If the user provides a natural language prompt (e.g. *"Generate a developer onboarding guide for this repository explaining how to set up the dev environment, run tests, and add a new API route"*), the agent **must automatically infer and populate** `target_repository_path`, `onboarding_depth`, `target_audience`, and `auto_generate_architecture_map` from the user's text.

### JSON Context Manifest Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "OnboardToCodebaseContextManifest",
  "type": "object",
  "required": ["repository_spec", "orientation_config"],
  "properties": {
    "repository_spec": {
      "type": "object",
      "required": ["repository_name"],
      "properties": {
        "repository_name": { "type": "string" },
        "primary_language": { "type": "string" },
        "frameworks": { "type": "array", "items": { "type": "string" } }
      }
    },
    "orientation_config": {
      "type": "object",
      "required": ["onboarding_depth"],
      "properties": {
        "onboarding_depth": { 
          "type": "string", 
          "enum": ["quickstart_bootstrap", "full_architecture_guide", "deep_contributor_manual"],
          "default": "full_architecture_guide" 
        },
        "target_audience": { 
          "type": "string", 
          "enum": ["frontend_dev", "backend_dev", "fullstack_dev", "devops_engineer"],
          "default": "fullstack_dev" 
        },
        "auto_generate_architecture_map": { "type": "boolean", "default": true },
        "include_gotchas_matrix": { "type": "boolean", "default": true }
      }
    }
  }
}
```

### Automatic Natural Language Inference & Empirical Fact Rules

If no raw JSON payload is provided, apply these defaults and strict orientation rules:

- **Empirical Accuracy Rule**: Extract all architecture descriptions directly from source code files and build scripts. Do NOT document aspirational or planned features as current state.
- **Augment Existing Docs**: Preserve existing `README.md` or `CONTRIBUTING.md` files; produce an onboarding guide that complements existing documentation.
- **Setup Time-to-First-Build SLA**: Ensure local setup instructions enable a new developer to achieve a passing test build within 15 minutes.

---

## 2. Deterministic State Machine Execution Flow

Follow this exact sequential protocol. Do not skip steps or alter execution ordering.

### Step 1: Repository Anatomy & Framework Discovery

1. Inspect project root build manifests:
   - Node.js / TS: `package.json`, `tsconfig.json`, `pnpm-workspace.yaml`.
   - Python: `pyproject.toml`, `setup.py`, `requirements.txt`.
   - Rust: `Cargo.toml`.
   - Go: `go.mod`.
2. Map framework entry points (e.g., `src/index.ts`, `src/app.ts`, `cmd/main.go`, `app/main.py`).

### Step 2: Local Environment Bootstrap Mapping

1. Extract environment variables from `.env.example` or `config/`.
2. Document local database/service bootstrap instructions (`docker-compose up`, local database migrations, seed scripts).
3. Document exact package manager commands (`pnpm install`, `pip install -r requirements.txt`).

### Step 3: Source Code Directory Topology & Layer Boundaries

Map the repository layout and module boundaries:
- **Presentation Layer**: UI components, pages, routes, controllers.
- **Business Logic Layer**: Domain services, state machines, handlers.
- **Data Access Layer**: ORM models, repositories, database schemas.
- **Infrastructure / Shared**: Logger, auth middleware, utility helpers.

### Step 4: Test Infrastructure & Verification Commands

1. Document test frameworks (`Jest`, `Vitest`, `PyTest`, `Cargo Test`).
2. Document test execution commands:
   - Full test suite execution (`pnpm test`, `pytest`).
   - Single test file / method execution (`npx jest path/to/file.test.ts`).
   - Linting and code formatting (`eslint`, `prettier`, `black`, `ruff`).

### Step 5: Common Development Tasks & Gotchas Matrix

Provide step-by-step developer recipes for common tasks:
1. **Recipe 1**: Adding a new API endpoint.
2. **Recipe 2**: Modifying a database schema model and running migrations.
3. **Recipe 3**: Adding unit and integration tests for a new feature.
4. **Developer Gotchas Matrix**: Document known pain points, required env variables, and non-obvious conventions.

---

## 3. Reference Implementation: Python Codebase Orientation Analyzer

```python
import os
import json
from pathlib import Path
from typing import Dict, List, Any

def analyze_repository_structure(repo_root: Path) -> Dict[str, Any]:
    """Scan repository for key manifests and onboarding indicators."""
    summary = {
        "project_name": repo_root.name,
        "manifests": [],
        "entry_points": [],
        "has_docker": False,
        "has_env_example": False,
        "test_frameworks": [],
    }

    # Detect package manifests
    manifest_files = ["package.json", "pyproject.toml", "Cargo.toml", "go.mod"]
    for m in manifest_files:
        if (repo_root / m).exists():
            summary["manifests"].append(m)

    # Detect Docker & Env setup
    summary["has_docker"] = (repo_root / "docker-compose.yml").exists() or (repo_root / "Dockerfile").exists()
    summary["has_env_example"] = (repo_root / ".env.example").exists()

    # Detect primary entry points
    candidate_entries = [
        "src/index.ts", "src/main.ts", "src/app.ts", "cmd/main.go", "app/main.py", "main.py"
    ]
    for e in candidate_entries:
        if (repo_root / e).exists():
            summary["entry_points"].append(e)

    # Detect tests
    if (repo_root / "tests").exists() or (repo_root / "test").exists():
        summary["test_frameworks"].append("Test directory found")

    return summary

if __name__ == "__main__":
    info = analyze_repository_structure(Path.cwd())
    print("Codebase Orientation Summary:")
    print(json.dumps(info, indent=2))
```

---

## 4. Onboarding Metrics & Invariants

$$\text{Time-to-First-Green-Build SLA: } T_{\text{first\_build}} \le 15\text{ minutes}$$

$$\text{Zero-Unstated-Prerequisites Invariant: } \text{MissingPrereqs} \equiv 0$$

$$\text{Architecture Accuracy: } \text{DocumentedModules} \equiv \text{ActualCodebaseDirectories}$$

---

## 5. Guardrails

### Operational Restrictions

- **No Speculative Architecture**: Never describe planned or aspirational architecture as current implementation.
- **Preserve Existing Docs**: Augment rather than overwrite existing `README.md` or `CONTRIBUTING.md` unless explicitly instructed.
- **Empirical Command Testing**: Verify that all setup and build commands listed in the onboarding guide actually execute cleanly.

---

## 6. Atomic Failure Recovery & Rollback Handler

If onboarding documentation generation encounters missing setup files:

```bash
# Clean up temporary orientation files
rm -f scratch_onboarding_guide.md 2>/dev/null
```

---

## 7. Verification Plan & Toolchain Commands

Verify setup steps in the onboarding guide:

```bash
# 1. Run codebase orientation analyzer script
python3 scripts/analyze_repo_orientation.py

# 2. Test repository build and test commands documented in onboarding guide
pnpm test || pytest || cargo test
```

---

## 8. Completion Report

Report repository name, primary frameworks detected, local bootstrap setup commands verified, source code layer breakdown, test commands documented, common developer recipes generated, gotchas matrix items, and final onboarding guide artifact location.
