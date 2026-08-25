---
name: write-documentation
description: Author, update, or audit project documentation — READMEs, architecture decisions, API references, onboarding guides, and inline doc — from code evidence.
---

# Write Documentation

Author, update, audit, and restructure technical project documentation, README files, Architecture Decision Records (ADRs), API reference guides, OpenAPI schemas, and developer manuals directly from empirical codebase evidence.

The skill is **contract-first and evidence-backed**: code snippet verification, relative markdown link validation, public interface contract alignment, audience targeting, and zero un-verified claims are strictly enforced before publishing documentation updates.

---

## 1. Required I/O Context Schemas & Natural Language Auto-Inference

The skill supports **two invocation modes**:

1. **🤖 Orchestrator / Technical Mode (JSON Manifest)**: Pass the JSON context manifest below.
2. **💬 Non-Technical Mode (Plain English Prompts)**: If the user provides a natural language prompt (e.g. *"Write an Architecture Decision Record (ADR) explaining why we chose PostgreSQL for event sourcing over MongoDB"*), the agent **must automatically infer and populate** `doc_type`, `doc_target_path`, `target_audience`, and `verify_code_snippets` from the user's text.

### JSON Context Manifest Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "WriteDocumentationContextManifest",
  "type": "object",
  "required": ["doc_spec", "formatting_config"],
  "properties": {
    "doc_spec": {
      "type": "object",
      "required": ["doc_type", "doc_target_path"],
      "properties": {
        "doc_type": { 
          "type": "string", 
          "enum": ["readme", "architecture_decision_record", "api_reference", "user_guide", "inline_jsdoc_docstrings"],
          "default": "readme" 
        },
        "doc_target_path": { "type": "string" },
        "title": { "type": "string" }
      }
    },
    "formatting_config": {
      "type": "object",
      "required": ["target_audience"],
      "properties": {
        "target_audience": { 
          "type": "string", 
          "enum": ["end_user", "api_consumer", "core_contributor", "system_operator"],
          "default": "core_contributor" 
        },
        "verify_code_snippets": { "type": "boolean", "default": true },
        "validate_relative_links": { "type": "boolean", "default": true }
      }
    }
  }
}
```

### Automatic Natural Language Inference & Evidence Rules

If no raw JSON payload is provided, apply these defaults and strict documentation rules:

- **Empirical Accuracy Rule**: Extract all technical features, performance figures, and compatibility metrics directly from source code and passing test cases. Do NOT invent unverified capabilities.
- **Audience Alignment**: Match document depth to the intended audience (e.g. high-level setup for end users vs internal module architecture for contributors).
- **Executable Code Snippets**: Code snippets included in documentation must be runnable against the codebase or explicitly marked as pseudo-code.

---

## 2. Deterministic State Machine Execution Flow

Follow this exact sequential protocol. Do not skip steps or alter execution ordering.

### Step 1: Codebase Evidence Harvesting & Fact Extraction

1. Read `AGENTS.md`, source code files, build scripts, OpenAPI specs, and test files.
2. Extract verified usage examples, configuration parameters, and environment requirements.

### Step 2: Document Structure & Template Selection

Select standard document structure based on `doc_type`:
- **Architecture Decision Record (ADR)**: Status, Context, Decision, Consequences, Alternatives Considered.
- **README / User Guide**: Purpose, Quickstart Setup, Features, Configuration, Testing, License.
- **API Reference**: Endpoint, Method, Headers, Request Body Schema, Response Schema, Error Codes.

### Step 3: Working Code Snippet Verification

1. Test code snippets locally or verify syntax against project compiler/linter.
2. Ensure command-line snippets reflect actual project scripts (`pnpm test`, `pytest`).

### Step 4: Relative Link & File Path Audit

1. Audit all relative file links (`[filename](../../AGENTS.md)`).
2. Fix broken anchor tags and missing relative documentation references.

### Step 5: Final Review & Style Compliance

Verify clean GitHub Flavored Markdown (GFM) formatting, consistent heading hierarchy (`#` $\rightarrow$ `##` $\rightarrow$ `###`), and concise technical prose.

---

## 3. Reference Implementation: Python Documentation & Link Verifier

```python
import os
import re
from pathlib import Path
from typing import List, Tuple

def verify_markdown_links(doc_path: Path) -> List[str]:
    """Verify that relative file links in a markdown file actually exist on disk."""
    if not doc_path.exists():
        return [f"File not found: {doc_path}"]
        
    content = doc_path.read_text(encoding="utf-8")
    # Match markdown relative links: [text](#anchor)
    link_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
    
    broken_links = []
    base_dir = doc_path.parent
    
    for match in link_pattern.finditer(content):
        label, link = match.groups()
        # Skip external http/https links and anchors
        if link.startswith(("http://", "https://", "mailto:", "#")):
            continue
            
        # Clean relative path
        target_path = base_dir / link.split("#")[0]
        if not target_path.exists():
            broken_links.append(f"Broken link '{label}' -> '{link}' in {doc_path.name}")
            
    return broken_links

if __name__ == "__main__":
    doc = Path("README.md")
    if len(sys.argv) > 1:
        doc = Path(sys.argv[1])
        
    broken = verify_markdown_links(doc)
    if not broken:
        print(f"[Documentation Verifier] All relative links in '{doc}' are valid!")
    else:
        print(f"[Documentation Verifier] Found {len(broken)} broken links:")
        for b in broken:
            print(f" - {b}")
```

---

## 4. Documentation Invariants & Quality Rules

$$\text{Snippet Executability: } \forall s \in \text{CodeSnippets}, \quad \text{SyntaxValid}(s) \lor \text{IsPseudoCode}(s)$$

$$\text{Link Integrity Invariant: } \text{Count}(\text{BrokenRelativeLinks}) \equiv 0$$

$$\text{Heading Hierarchy: } \forall h_k \in \text{Headings}, \quad \text{Level}(h_k) \le \text{Level}(h_{k-1}) + 1$$

---

## 5. Guardrails

### Operational Restrictions

- **No Speculative Features**: Do not document planned or un-implemented capabilities as existing features.
- **Preserve Project Voice**: Match existing project tone and formatting conventions; avoid blanket structural rewrites unless requested.
- **Scoped Edits Only**: Do not rewrite unrelated documentation sections or change source code files during a documentation task.

---

## 6. Atomic Failure Recovery & Rollback Handler

If documentation generation produces incorrect formatting or broken relative links:

```bash
# Revert modified documentation files
git checkout -- *.md docs/ 2>/dev/null
```

---

## 7. Verification Plan & Toolchain Commands

Verify documentation links and code snippets:

```bash
# 1. Run Python Markdown link verifier script
python3 scripts/verify_markdown_links.py README.md

# 2. Validate markdown formatting with markdownlint
npx markdownlint-cli "**.md"
```

---

## 8. Completion Report

Report documentation file created or updated (`README.md`, `ADR-001.md`), target audience addressed, sources of truth used, verified code snippets, broken links fixed, and follow-up documentation recommendations.
