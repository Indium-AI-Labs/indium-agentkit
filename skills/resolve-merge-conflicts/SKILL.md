---
name: resolve-merge-conflicts
description: Resolve Git merge or rebase conflicts by recovering each side's intent, preserving compatible behavior, validating the result, and documenting trade-offs.
---

# Resolve Merge Conflicts

Identify, inspect, and resolve Git merge, rebase, and cherry-pick conflicts across source code files, configuration manifests, build scripts, and package lockfiles by recovering the intent of both branches (`ours` and `theirs`) and verifying the integrated resolution against automated test suites.

The skill is **contract-first and intent-preserving**: conflict marker discovery (`<<<<<<< HEAD`), three-way diff inspection (`:1:base`, `:2:ours`, `:3:theirs`), zero un-resolved conflict markers ($\text{Count}(\text{"<<<<<<<"}) = 0$), lockfile regeneration, and test suite verification are strictly enforced before completing commits.

---

## 1. Required I/O Context Schemas & Natural Language Auto-Inference

The skill supports **two invocation modes**:

1. **🤖 Orchestrator / Technical Mode (JSON Manifest)**: Pass the JSON context manifest below.
2. **💬 Non-Technical Mode (Plain English Prompts)**: If the user provides a natural language prompt (e.g. *"Resolve the merge conflicts in `src/auth.ts` and `package.json` between main and feature/oauth while keeping both changes working"*), the agent **must automatically infer and populate** `conflict_type`, `conflicting_files`, `ours_branch`, `theirs_branch`, and `resolution_strategy` from the user's text.

### JSON Context Manifest Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "ResolveMergeConflictsContextManifest",
  "type": "object",
  "required": ["conflict_spec", "resolution_config"],
  "properties": {
    "conflict_spec": {
      "type": "object",
      "required": ["conflict_type", "conflicting_files"],
      "properties": {
        "conflict_type": { 
          "type": "string", 
          "enum": ["merge_conflict", "rebase_conflict", "cherry_pick_conflict"],
          "default": "merge_conflict" 
        },
        "conflicting_files": { "type": "array", "items": { "type": "string" }, "minItems": 1 },
        "ours_branch": { "type": "string", "default": "main" },
        "theirs_branch": { "type": "string" }
      }
    },
    "resolution_config": {
      "type": "object",
      "required": ["resolution_strategy"],
      "properties": {
        "resolution_strategy": { 
          "type": "string", 
          "enum": ["combine_intents", "favor_ours", "favor_theirs", "manual_rearchitect"],
          "default": "combine_intents" 
        },
        "run_test_suite_post_resolution": { "type": "boolean", "default": true },
        "regenerate_lockfiles": { "type": "boolean", "default": true }
      }
    }
  }
}
```

### Automatic Natural Language Inference & Conflict Safety Rules

If no raw JSON payload is provided, apply these defaults and strict conflict safety rules:

- **Zero Unresolved Markers**: NEVER commit files containing un-resolved git conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`).
- **No Unrelated Code Edits**: Do NOT add unrelated feature changes or formatting refactorings while resolving merge conflicts.
- **Lockfile Rule**: For lockfiles (`pnpm-lock.yaml`, `package-lock.json`), prefer regenerating via the package manager over manual line-by-line conflict editing.

---

## 2. Deterministic State Machine Execution Flow

Follow this exact sequential protocol. Do not skip steps or alter execution ordering.

### Step 1: Conflict Discovery & State Inspection

1. Check current git status:
   ```bash
   git status --short
   git diff --name-only --diff-filter=U
   ```
2. Identify unmerged paths (`diff-filter=U`).

### Step 2: Three-Way Intent Recovery

For each conflicting file, inspect the 3-way stage objects:
- **Base Version (`:1:<file>`)**: The common ancestor commit before branching.
- **Ours / Current (`:2:<file>`)**: Local branch changes (`HEAD`).
- **Theirs / Incoming (`:3:<file>`)**: Incoming branch changes.

Inspect commit logs for both sides (`git log --merge -p <file>`) to understand the exact motivation behind each change.

### Step 3: Conflict Marker Resolution

1. Open conflicting file and locate markers (`<<<<<<< HEAD` ... `=======` ... `>>>>>>>`).
2. Resolve conflict by combining compatible logic:
   - Keep both non-conflicting imports.
   - Combine feature additions.
   - Resolve parameter order conflicts.
3. Remove all conflict marker lines completely.

### Step 4: Lockfile & Generated File Handling

If lockfiles conflict (`pnpm-lock.yaml`, `package-lock.json`, `Cargo.lock`):
1. Checkout `ours` version or accept current state.
2. Run package manager install command to regenerate lockfile cleanly (`pnpm install`, `npm install`, `cargo check`).

### Step 5: Verification & Merge Finalization

1. Search repository for any missed conflict markers:
   ```bash
   git grep -E "^<<<<<<< "
   ```
2. Run test suite to verify integration success (`pnpm test`, `pytest`, `cargo test`).
3. Stage resolved files and complete merge/rebase:
   ```bash
   git add <resolved_files>
   git merge --continue  # or git rebase --continue
   ```

---

## 3. Reference Implementation: Python Git Conflict Inspector

```python
import subprocess
import sys
from pathlib import Path
from typing import List

def get_conflicting_files() -> List[str]:
    """Get list of unmerged conflicting files in git repository."""
    try:
        res = subprocess.run(
            ["git", "diff", "--name-only", "--diff-filter=U"],
            capture_output=True, text=True, check=True
        )
        return [f.strip() for f in res.stdout.splitlines() if f.strip()]
    except subprocess.CalledProcessError:
        return []

def check_unresolved_markers(files: List[str]) -> List[str]:
    """Check if any files still contain un-resolved conflict markers."""
    flagged_files = []
    markers = ["<<<<<<< ", "=======", ">>>>>>> "]
    
    for filePath in files:
        p = Path(filePath)
        if not p.exists():
            continue
        content = p.read_text(encoding="utf-8", errors="ignore")
        for m in markers:
            if m in content:
                flagged_files.append(filePath)
                break
                
    return flagged_files

if __name__ == "__main__":
    conflicts = get_conflicting_files()
    if not conflicts:
        print("[Git Conflict Inspector] No active merge conflicts detected.")
    else:
        print(f"[Git Conflict Inspector] Found {len(conflicts)} conflicting files:")
        for c in conflicts:
            print(f" - {c}")
            
        unresolved = check_unresolved_markers(conflicts)
        if unresolved:
            print(f"\n[WARNING] {len(unresolved)} files still contain unresolved conflict markers!")
        else:
            print("\n[SUCCESS] All conflict markers have been removed cleanly.")
```

---

## 4. Conflict Resolution Invariants

$$\text{Marker Invariant: } \text{Count}(\text{"<<<<<<< "}) \equiv 0 \quad (\text{across all tracked files})$$

$$\text{Intent Equivalence: } \text{Preserved}(\text{Ours}) \land \text{Preserved}(\text{Theirs}) \equiv \mathbf{TRUE}$$

$$\text{Lockfile Consistency: } \text{LockfileStatus} \equiv \text{RegeneratedByPackageManager}$$

---

## 5. Guardrails

### Operational Restrictions

- **Zero Leftover Markers**: Never commit code containing git conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`).
- **No Scope Creep**: Do not add unrelated code fixes or formatting refactoring while resolving merge conflicts.
- **Regenerate Lockfiles**: Never attempt manual line-by-line editing of 10,000-line lockfiles; use `pnpm install` / `npm install` to regenerate cleanly.

---

## 6. Atomic Failure Recovery & Rollback Handler

If merge resolution encounters un-resolvable conflicts or severe breakage:

```bash
# Abort current merge or rebase cleanly
git merge --abort 2>/dev/null || git rebase --abort 2>/dev/null
```

---

## 7. Verification Plan & Toolchain Commands

Verify conflict resolution:

```bash
# 1. Check for leftover conflict markers across entire repository
git grep -E "^<<<<<<< "

# 2. Run Python Git Conflict Inspector
python3 scripts/check_git_conflicts.py

# 3. Run full test suite to verify integrated behavior
pnpm test || pytest || cargo test
```

---

## 8. Completion Report

Report conflict type (`merge`, `rebase`), list of conflicting files resolved, intent recovery summary for both sides, lockfiles regenerated, conflict marker check results, test suite verification results, and merge completion status.
