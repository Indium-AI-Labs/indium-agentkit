---
name: verify-and-ship
description: Verify completed repository changes, run test and lint commands, audit diffs for secrets, and commit/publish cleanly according to repository rules.
---

# Verify and Ship

Verify completed repository changes, execute project test suites and linter suites, audit git diffs for un-tracked temporary files or secret leaks (`git diff --check`), regenerate catalog manifests (`CATALOG.md`), build Cursor rules (`.cursor/rules/`), and execute concise imperative git commits and remote pushes (`git push origin main`).

The skill is **contract-first, zero-defect, and repository-validated**: secret scanning, RBAC schema validation, Cursor rule generation, catalog synchronization, unit testing, and atomic git commit policies are strictly verified before shipping changes.

---

## 1. Required I/O Context Schemas & Natural Language Auto-Inference

The skill supports **two invocation modes**:

1. **🤖 Orchestrator / Technical Mode (JSON Manifest)**: Pass the JSON context manifest below.
2. **💬 Non-Technical Mode (Plain English Prompts)**: If the user provides a natural language prompt (e.g. *"Verify our changes, run the test suite, update the catalog, and commit and push to origin/main"*), the agent **must automatically infer and populate** `target_branch`, `run_full_validation_suite`, `auto_regenerate_catalog`, and `git_commit_config` from the user's text.

### JSON Context Manifest Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "VerifyAndShipContextManifest",
  "type": "object",
  "required": ["ship_spec", "verification_config"],
  "properties": {
    "ship_spec": {
      "type": "object",
      "required": ["commit_message"],
      "properties": {
        "commit_message": { "type": "string" },
        "target_branch": { "type": "string", "default": "main" },
        "push_to_remote": { "type": "boolean", "default": true }
      }
    },
    "verification_config": {
      "type": "object",
      "required": ["run_full_validation_suite"],
      "properties": {
        "run_full_validation_suite": { "type": "boolean", "default": true },
        "build_cursor_rules": { "type": "boolean", "default": true },
        "regenerate_catalog": { "type": "boolean", "default": true },
        "secret_scan_enabled": { "type": "boolean", "default": true }
      }
    }
  }
}
```

### Automatic Natural Language Inference & Repository Ship Rules

If no raw JSON payload is provided, apply these defaults and strict repository rules:

- **Imperative Commit Subject Rule**: Use concise, professional imperative commit subjects (e.g., `Add rtos-firmware-development skill`); avoid vague labels like `changes` or `updates`.
- **Catalog Sync Rule**: Catalog changes (`CATALOG.md`) MUST be included in the same commit as content modifications.
- **Zero Secret Commits**: Never commit `.env`, private keys, API credentials, or temporary build artifacts.

---

## 2. Deterministic State Machine Execution Flow

Follow this exact sequential protocol. Do not skip steps or alter execution ordering.

### Step 1: Pre-Flight Diff Audit & Secret Scanning

1. Check repository status and trailing whitespace errors:
   ```bash
   git status
   git diff --check
   ```
2. Scan working tree for accidentally staged `.env`, `.pem`, `.key`, or temporary scratch files (`scratch/`, `.pyc`, `node_modules`).

### Step 2: Content & RBAC Schema Validation

Execute content validators to verify frontmatter and role permissions:
```bash
python3 scripts/validate_content.py && python3 scripts/validate_rbac_schema.py
```

### Step 3: Cursor Rule Generation & Catalog Synchronization

1. Generate updated Cursor rules:
   ```bash
   python3 scripts/build_cursor_rules.py --skills-dir skills --out-dir .cursor/rules
   ```
2. Regenerate catalog and check diff:
   ```bash
   python3 scripts/generate_catalog.py && python3 scripts/diff_catalog.py
   ```

### Step 4: Full Unit & Integration Test Execution

Execute full test suite:
```bash
python3 -m unittest discover -s tests -v
```

### Step 5: Scoped Git Commit & Push to Remote

1. Stage scoped files:
   ```bash
   git add skills/ agents/ CATALOG.md scripts/
   ```
2. Commit with concise imperative message:
   ```bash
   git commit -m "Add verify-and-ship skill"
   ```
3. Push directly to remote when authorized by repository policy or user:
   ```bash
   git push origin main
   ```

---

## 3. Reference Implementation: Python Pre-Ship Automation Script

```python
import subprocess
import sys

def run_command(cmd: str) -> bool:
    print(f"[Pre-Ship Step] Running: {cmd}")
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if res.returncode == 0:
        print(" -> PASSED")
        return True
    else:
        print(f" -> FAILED (Exit Code {res.returncode})")
        print(res.stdout + res.stderr)
        return False

def verify_and_ship_pipeline(commit_message: str, push: bool = False) -> bool:
    print("==================================================")
    print("      INDIUM-AGENTKIT PRE-SHIP VERIFICATION       ")
    print("==================================================")

    steps = [
        "python3 scripts/validate_content.py",
        "python3 scripts/validate_rbac_schema.py",
        "python3 scripts/build_cursor_rules.py --skills-dir skills --out-dir .cursor/rules",
        "python3 scripts/generate_catalog.py",
        "python3 scripts/diff_catalog.py",
        "python3 -m unittest discover -s tests -v"
    ]

    for step in steps:
        if not run_command(step):
            print("\n[PRE-SHIP ABORTED] Verification step failed. Fix issues before shipping.")
            return False

    print("\n[SUCCESS] All verification steps passed cleanly.")
    
    if push:
        run_command(f'git add skills/ agents/ CATALOG.md scripts/ && git commit -m "{commit_message}" && git push origin main')

    return True

if __name__ == "__main__":
    msg = sys.argv[1] if len(sys.argv) > 1 else "Update skills and catalog"
    verify_and_ship_pipeline(msg, push=False)
```

---

## 4. Ship Verification Invariants & Rules

$$\text{Secret Scan Invariant: } \text{Count}(\text{SecretsStaged}) \equiv 0$$

$$\text{Test & Validation Invariant: } \text{ExitCode}(\text{TestSuite}) \equiv 0 \land \text{ExitCode}(\text{Validators}) \equiv 0$$

$$\text{Catalog Synchronization: } \text{Diff}(\text{CATALOG.md}) \equiv 0 \quad (\text{after } \text{generate\_catalog.py})$$

---

## 5. Guardrails

### Operational Restrictions

- **Never Ignore Command Failures**: If any validation or test command fails, stop immediately. Do not commit or push broken code.
- **Scoped Commits Only**: Include `CATALOG.md` in the same commit as skill/agent modifications.
- **Concise Imperative Commit Messages**: Avoid vague messages like `updates` or `bug fixes`.

---

## 6. Atomic Failure Recovery & Rollback Handler

If shipping fails during local commit or remote push:

```bash
# Revert unpushed local commit if necessary
git reset --soft HEAD~1 2>/dev/null
```

---

## 7. Verification Plan & Toolchain Commands

Execute full pre-ship verification pipeline:

```bash
# 1. Execute complete pre-ship verification pipeline
python3 scripts/validate_content.py && \
python3 scripts/validate_rbac_schema.py && \
python3 scripts/build_cursor_rules.py --skills-dir skills --out-dir .cursor/rules && \
python3 scripts/generate_catalog.py && \
python3 scripts/diff_catalog.py && \
python3 -m unittest discover -s tests -v
```

---

## 8. Completion Report

Report pre-ship checks executed, secret scan result, Cursor rules generated, `CATALOG.md` sync status, unittest results, local commit hash, and remote push destination.
