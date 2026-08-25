---
name: review-change
description: Review local diffs, branches, commit ranges, or pull requests for correctness, regressions, security, performance, conventions, and test coverage.
---

# Review Change

Review local git diffs, feature branches, pull requests (PRs), and commit ranges for architectural correctness, behavioral regressions, security vulnerabilities (OWASP Top 10), performance bottlenecks, error handling paths, project conventions, and test coverage completeness.

The skill is **read-only, evidence-backed, and non-destructive**: review targets (`git diff HEAD~1`), actionable findings, severity classifications (`BLOCKER`, `CRITICAL`, `MAJOR`, `MINOR`, `NITPICK`), exact line numbers, and concrete remediation suggestions are produced without editing target source files.

---

## 1. Required I/O Context Schemas & Natural Language Auto-Inference

The skill supports **two invocation modes**:

1. **🤖 Orchestrator / Technical Mode (JSON Manifest)**: Pass the JSON context manifest below.
2. **💬 Non-Technical Mode (Plain English Prompts)**: If the user provides a natural language prompt (e.g. *"Review the changes in the current branch against main for security risks, error handling, and test coverage"*), the agent **must automatically infer and populate** `review_target`, `diff_scope`, `severity_threshold`, and `review_dimensions` from the user's text.

### JSON Context Manifest Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "ReviewChangeContextManifest",
  "type": "object",
  "required": ["review_target", "review_config"],
  "properties": {
    "review_target": {
      "type": "object",
      "required": ["target_scope"],
      "properties": {
        "target_scope": { 
          "type": "string", 
          "enum": ["working_tree", "staged_changes", "commit_range", "pull_request"],
          "default": "working_tree" 
        },
        "commit_range": { "type": "string", "default": "origin/main..HEAD" },
        "pr_number": { "type": "integer" }
      }
    },
    "review_config": {
      "type": "object",
      "required": ["review_dimensions"],
      "properties": {
        "review_dimensions": {
          "type": "array",
          "items": { 
            "type": "string", 
            "enum": ["correctness", "security", "performance", "test_coverage", "error_handling", "conventions"] 
          },
          "default": ["correctness", "security", "error_handling", "test_coverage"]
        },
        "min_severity_threshold": { 
          "type": "string", 
          "enum": ["BLOCKER", "CRITICAL", "MAJOR", "MINOR", "NITPICK"],
          "default": "MINOR"
        },
        "read_only_mode": { "type": "boolean", "default": true }
      }
    }
  }
}
```

### Automatic Natural Language Inference & Review Guardrail Rules

If no raw JSON payload is provided, apply these defaults and strict code review rules:

- **Read-Only Default**: Reviewing code MUST NOT modify source files or apply diffs unless explicitly requested.
- **Evidence Requirement**: Every reported finding MUST include exact file paths, line numbers, code snippets, concrete impact, and remediation steps.
- **No Fabricated Defects**: Do NOT report speculative or unverified defects. Verify claims against codebase evidence or static analyzers.

---

## 2. Deterministic State Machine Execution Flow

Follow this exact sequential protocol. Do not skip steps or alter execution ordering.

### Step 1: Diff Scope & Context Baseline

1. Establish review target:
   ```bash
   git status
   git diff --stat origin/main..HEAD
   ```
2. Read project architectural context (`AGENTS.md`, design patterns, existing tests).

### Step 2: Multi-Dimensional Code Inspection

Trace changed lines across 5 core audit dimensions:
1. **Correctness & Edge Cases**: Off-by-one errors, null/undefined pointers, state mutations, async race conditions.
2. **Security & Data Sanitization**: SQL injection, XSS, un-authenticated endpoints, sensitive log leaks, hardcoded secrets.
3. **Error Handling & Resilience**: Unhandled promise rejections, missing try/catch blocks, swallowed exceptions.
4. **Performance & Memory**: $O(N^2)$ loops, N+1 database queries, memory leaks, un-closed streams.
5. **Test Coverage Completeness**: Ensure every new feature path or bug fix has corresponding unit/integration tests.

### Step 3: Finding Categorization & Severity Scoring

Classify each finding:
- 🚨 **`BLOCKER`**: Crashes application, security vulnerability, data loss risk. Must fix before merge.
- 🔴 **`CRITICAL`**: Functional defect or missing error handling. Strong recommendation to block merge.
- 🟠 **`MAJOR`**: Sub-optimal performance, missing unit test coverage for edge cases.
- 🟡 **`MINOR` / `NITPICK`**: Code style, naming convention, minor formatting suggestion.

### Step 4: Verification Run

Run static analysis and test tools to verify findings:
```bash
pnpm test || pytest || cargo test
npx eslint src/ || ruff check .
```

### Step 5: Structured Review Report Generation

Generate formatted markdown review report specifying findings by file, line number, severity, impact, and remediation snippet.

---

## 3. Reference Implementation: Python Code Review Diff Analyzer

```python
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Any

def get_git_diff_summary(commit_range: str = "origin/main..HEAD") -> Dict[str, Any]:
    """Analyze git diff summary and modified file stats."""
    try:
        stat_res = subprocess.run(
            ["git", "diff", "--stat", commit_range],
            capture_output=True, text=True, check=True
        )
        diff_res = subprocess.run(
            ["git", "diff", "-U3", commit_range],
            capture_output=True, text=True, check=True
        )
        return {
            "stat_summary": stat_res.stdout.strip(),
            "raw_diff": diff_res.stdout,
            "success": True
        }
    except subprocess.CalledProcessError as e:
        return {"success": False, "error": str(e)}

def audit_diff_security_heuristics(raw_diff: str) -> List[Dict[str, str]]:
    """Scan raw diff for common security red flags (secrets, dangerous functions)."""
    findings = []
    suspicious_patterns = [
        (r"eval\(", "Use of eval() creates arbitrary code execution vulnerabilities.", "CRITICAL"),
        (r"password\s*=\s*['\"][^'\"]+['\"]", "Hardcoded password string detected in diff.", "BLOCKER"),
        (r"api_key\s*=\s*['\"][^'\"]+['\"]", "Hardcoded API key detected in diff.", "BLOCKER"),
        (r"console\.log\(", "Debug console.log statement leftover in production diff.", "NITPICK")
    ]
    
    import re
    lines = raw_diff.splitlines()
    for idx, line in enumerate(lines, start=1):
        if line.startswith("+") and not line.startswith("+++"):
            for pattern, msg, severity in suspicious_patterns:
                if re.search(pattern, line):
                    findings.append({
                        "line_content": line[1:].strip(),
                        "diff_line_idx": idx,
                        "finding": msg,
                        "severity": severity
                    })
                    
    return findings

if __name__ == "__main__":
    diff_data = get_git_diff_summary("HEAD~1..HEAD")
    if diff_data["success"]:
        findings = audit_diff_security_heuristics(diff_data["raw_diff"])
        print(f"[Code Review] Inspected diff. Found {len(findings)} security heuristic alerts:")
        for f in findings:
            print(f" - [{f['severity']}] Line {f['diff_line_idx']}: {f['finding']}")
```

---

## 4. Code Review Invariants & Metrics

$$\text{Evidence Invariant: } \forall f \in \text{Findings}, \quad \exists \text{FilePath}(f) \land \text{LineNumber}(f) \land \text{Impact}(f)$$

$$\text{Read-Only Execution: } \text{Diff}(\text{SourceTree}_{\text{post-review}}) \equiv 0$$

$$\text{Severity Classification: } \text{Severity} \in \{\text{BLOCKER, CRITICAL, MAJOR, MINOR, NITPICK}\}$$

---

## 5. Guardrails

### Operational Restrictions

- **Read-Only Mode**: Do not modify source code or apply fixes during code review unless explicitly requested.
- **Actionable Findings Only**: Avoid generic advice ("clean up code"); provide exact line references, concrete risks, and fix examples.
- **Separate Blockers from Nitpicks**: Clearly group blocking defects separately from optional code style suggestions.

---

## 6. Atomic Failure Recovery & Rollback Handler

If git diff commands fail due to invalid commit ranges:

```bash
# Fall back to inspecting working tree diff
git diff HEAD
```

---

## 7. Verification Plan & Toolchain Commands

Execute review verification commands:

```bash
# 1. Inspect git diff stat for target branch
git diff --stat origin/main..HEAD

# 2. Run security and diff analyzer script
python3 scripts/analyze_code_review_diff.py

# 3. Verify project test suite passes cleanly
pnpm test || pytest || cargo test
```

---

## 8. Completion Report

Report review target (`git diff HEAD~1`), commit range inspected, file count and line count analyzed, findings grouped by severity (`BLOCKER`, `CRITICAL`, `MAJOR`, `MINOR`), evidence snippets, and overall merge approval recommendation.
