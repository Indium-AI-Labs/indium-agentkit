---
name: release-notes
description: Create accurate user-facing release notes or changelog entries from a commit range, tags, issues, and repository history.
---

# Release Notes

Generate user-facing release notes, changelog entries (`CHANGELOG.md`), GitHub Release descriptions, and migration guides from git commit ranges, release tags, pull request histories, and conventional commit specifications.

The skill is **contract-first and evidence-backed**: commit logs (`git log v1.0.0..v1.1.0`), Conventional Commit classifications (`feat`, `fix`, `BREAKING CHANGE`), breaking change callouts, database migration steps, upgrade instructions, and draft/final version labels are extracted directly from git history.

---

## 1. Required I/O Context Schemas & Natural Language Auto-Inference

The skill supports **two invocation modes**:

1. **🤖 Orchestrator / Technical Mode (JSON Manifest)**: Pass the JSON context manifest below.
2. **💬 Non-Technical Mode (Plain English Prompts)**: If the user provides a natural language prompt (e.g. *"Generate release notes for version 1.1.0 comparing tag v1.0.0 to main highlighting breaking changes and new features"*), the agent **must automatically infer and populate** `release_version`, `commit_range`, `changelog_format`, and `audience` from the user's text.

### JSON Context Manifest Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "ReleaseNotesContextManifest",
  "type": "object",
  "required": ["release_spec", "formatting_config"],
  "properties": {
    "release_spec": {
      "type": "object",
      "required": ["release_version", "commit_range"],
      "properties": {
        "release_version": { "type": "string", "default": "1.1.0" },
        "commit_range": { "type": "string", "default": "v1.0.0..HEAD" },
        "previous_version": { "type": "string", "default": "1.0.0" }
      }
    },
    "formatting_config": {
      "type": "object",
      "required": ["changelog_format"],
      "properties": {
        "changelog_format": { 
          "type": "string", 
          "enum": ["keep_a_changelog", "conventional_commits", "github_release_markdown"],
          "default": "keep_a_changelog" 
        },
        "target_audience": { 
          "type": "string", 
          "enum": ["end_users", "developers", "internal_stakeholders"],
          "default": "developers" 
        },
        "highlight_breaking_changes": { "type": "boolean", "default": true },
        "include_contributors": { "type": "boolean", "default": true }
      }
    }
  }
}
```

### Automatic Natural Language Inference & Factual Accuracy Rules

If no raw JSON payload is provided, apply these defaults and strict changelog rules:

- **Factual Verification Rule**: Extract claims directly from git commits and pull request diffs. Do NOT invent unverified performance or compatibility claims.
- **`changelog_format`**: Defaults to `keep_a_changelog` standard (Keep a Changelog 1.0.0).
- **Breaking Changes Prominence**: Breaking changes MUST be placed at the top of the release notes with explicit upgrade steps.

---

## 2. Deterministic State Machine Execution Flow

Follow this exact sequential protocol. Do not skip steps or alter execution ordering.

### Step 1: Git Log & Range Extraction

1. Resolve release version tags (`git tag -l`, `git log v1.0.0..v1.1.0 --oneline`).
2. Extract commit logs, commit subjects, authors, and pull request links.

### Step 2: Conventional Commit Classification

Categorize commits according to Keep a Changelog 1.0.0 / Conventional Commit standards:
- 🚀 **Added (`feat:`)**: New user-facing capabilities or APIs.
- 🐛 **Fixed (`fix:`)**: Bug fixes and patch resolution.
- ⚠️ **Breaking Changes (`feat!:`, `BREAKING CHANGE:`)**: API contract changes requiring developer migration.
- ⚡ **Performance (`perf:`)**: Speed and memory efficiency improvements.
- 🔒 **Security (`sec:`)**: Vulnerability fixes and patch alerts.
- 🛠️ **Changed / Deprecated (`refactor:`, `deprecate:`)**: Internal alterations or deprecation warnings.

### Step 3: Migration & Upgrade Step Formulation

1. Inspect breaking change commit diffs (`git show <commit_hash>`).
2. Write explicit, actionable upgrade instructions for developers updating to this release.

### Step 4: Formatting & Changelog Generation

1. Structure release notes in GitHub Markdown or append to `CHANGELOG.md`.
2. Include date, version header, comparison link (`https://github.com/org/repo/compare/v1.0.0...v1.1.0`), and contributor list.

---

## 3. Reference Implementation: Python Git Changelog Generator

```python
import subprocess
import sys
import re
from typing import Dict, List

def get_git_commits(commit_range: str) -> List[str]:
    """Fetch git commit subjects for given commit range."""
    try:
        res = subprocess.run(
            ["git", "log", commit_range, "--oneline", "--no-merges"],
            capture_output=True, text=True, check=True
        )
        return [line.strip() for line in res.stdout.splitlines() if line.strip()]
    except subprocess.CalledProcessError as e:
        print(f"Error reading git log for range {commit_range}: {e}", file=sys.stderr)
        return []

def generate_changelog(version: str, commit_range: str) -> str:
    commits = get_git_commits(commit_range)
    
    categories: Dict[str, List[str]] = {
        "Breaking Changes": [],
        "Added": [],
        "Fixed": [],
        "Performance": [],
        "Security": [],
        "Changed": []
    }
    
    for c in commits:
        # Strip short commit hash
        parts = c.split(" ", 1)
        if len(parts) < 2:
            continue
        msg = parts[1]
        
        if "BREAKING CHANGE" in msg or "!" in msg.split(":")[0]:
            categories["Breaking Changes"].append(msg)
        elif msg.startswith("feat"):
            categories["Added"].append(msg)
        elif msg.startswith("fix"):
            categories["Fixed"].append(msg)
        elif msg.startswith("perf"):
            categories["Performance"].append(msg)
        elif msg.startswith("sec"):
            categories["Security"].append(msg)
        else:
            categories["Changed"].append(msg)
            
    # Format Keep a Changelog Markdown
    output = [f"## [{version}] - 2026-08-25\n"]
    for cat, items in categories.items():
        if items:
            output.append(f"### {cat}")
            for item in items:
                output.append(f"- {item}")
            output.append("")
            
    return "\n".join(output)

if __name__ == "__main__":
    rng = "HEAD~10..HEAD"
    if len(sys.argv) > 1:
        rng = sys.argv[1]
    print(generate_changelog("1.1.0", rng))
```

---

## 4. Changelog Invariants & Formatting Rules

$$\text{Keep a Changelog Categories: } C \in \{\text{Added, Changed, Deprecated, Removed, Fixed, Security}\}$$

$$\text{Commit Range Completeness: } \text{IncludedCommits} \equiv \text{GitLog}(v_{\text{prev}}..v_{\text{new}})$$

$$\text{Breaking Change Prominence: } \text{Index}(\text{BreakingChanges}) < \text{Index}(\text{AddedFeatures})$$

---

## 5. Guardrails

### Operational Restrictions

- **No Invented Claims**: Never state performance improvements or bug fixes that cannot be verified in git commit history.
- **Highlight Breaking Changes**: Breaking changes must never be buried inside minor fix lists; place them under a prominent `⚠️ Breaking Changes` section.
- **Draft Status Identification**: Unreleased release notes must be clearly labeled `[Draft / Unreleased]`.

---

## 6. Atomic Failure Recovery & Rollback Handler

If git tag extraction fails or incorrect commit ranges are specified:

```bash
# Clean up draft changelog files
rm -f DRAFT_RELEASE_NOTES.md 2>/dev/null
```

---

## 7. Verification Plan & Toolchain Commands

Verify git changelog generation:

```bash
# 1. Run git changelog generator script
python3 scripts/generate_changelog.py "v1.0.0..HEAD"

# 2. Check git log tag range validity
git tag -l
```

---

## 8. Completion Report

Report release version, commit/tag range compared, conventional commit breakdown count, breaking changes identified, upgrade instructions generated, and final markdown changelog artifact.
