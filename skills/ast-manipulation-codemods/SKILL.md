---
name: ast-manipulation-codemods
description: Write Abstract Syntax Tree (AST) transformers to automate large-scale, syntax-aware codebase migrations.
---

# AST Manipulation Codemods

Implement Abstract Syntax Tree (AST) transformers, syntax-aware refactoring tools, and automated codemods (jscodeshift, Babel AST, TypeScript Compiler API, libcst for Python, tree-sitter, Rust syn/quote) to execute large-scale, lossless codebase migrations without regex fragility or broken syntax errors.

The skill is **syntax-aware and idempotent**: target node selectors, replacement visitors, comment preservation, dry-run diff previews, and AST transformation idempotency ($\text{Codemod}(\text{Codemod}(code)) = \text{Codemod}(code)$) are verified before mutating target files.

---

## 1. Required I/O Context Schemas & Natural Language Auto-Inference

The skill supports **two invocation modes**:

1. **🤖 Orchestrator / Technical Mode (JSON Manifest)**: Pass the JSON context manifest below.
2. **💬 Non-Technical Mode (Plain English Prompts)**: If the user provides a natural language prompt (e.g. *"Write a jscodeshift codemod to refactor deprecated `logger.warn(msg)` calls to `logger.warning({ message: msg })` across all TypeScript files"*), the agent **must automatically infer and populate** `target_language`, `ast_parser`, `transformation_pattern`, and `file_glob` from the user's text.

### JSON Context Manifest Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "AstCodemodContextManifest",
  "type": "object",
  "required": ["transformer_spec", "target_scope"],
  "properties": {
    "transformer_spec": {
      "type": "object",
      "required": ["target_language", "ast_parser"],
      "properties": {
        "target_language": { 
          "type": "string", 
          "enum": ["typescript", "javascript", "python", "rust", "go", "java"] 
        },
        "ast_parser": { 
          "type": "string", 
          "enum": ["jscodeshift", "babel_parser", "ts_morph", "libcst", "syn_quote", "tree_sitter"] 
        },
        "idempotent_required": { "type": "boolean", "default": true },
        "preserve_comments": { "type": "boolean", "default": true }
      }
    },
    "target_scope": {
      "type": "object",
      "required": ["file_glob"],
      "properties": {
        "file_glob": { "type": "string", "default": "src/**/*.{ts,tsx,js,jsx}" },
        "exclude_glob": { "type": "string", "default": "**/node_modules/**" },
        "dry_run_first": { "type": "boolean", "default": true }
      }
    }
  }
}
```

### Automatic Natural Language Inference & Regex Rejection

If no raw JSON payload is provided, apply these defaults and strict safety checks:

- **Regex Refactoring Rejection**: If prompt attempts to use naive regex search-and-replace for complex multi-line code refactoring, **ABORT execution immediately** and enforce AST-based parsing via `jscodeshift` / `libcst` / `ts-morph` (`NAIVE_REGEX_FORBIDDEN`).
- **`target_language`**: Auto-detected from target file extensions (`.ts`/`.tsx` $\rightarrow$ `typescript`, `.py` $\rightarrow$ `python`, `.rs` $\rightarrow$ `rust`).
- **`ast_parser`**: Defaults to `jscodeshift` / Recast for TS/JS, `libcst` for Python, `syn`/`quote` for Rust.

---

## 2. Deterministic State Machine Execution Flow

Follow this exact sequential protocol. Do not skip steps or alter execution ordering.

### Step 1: AST Node Pattern Discovery & Visitor Mapping

1. Parse representative sample code fixtures into AST node structures (inspect AST nodes via ASTExplorer representations).
2. Map source AST node patterns (`CallExpression`, `ImportDeclaration`, `JSXElement`, `FunctionDef`, `Attribute`) to target replacement nodes.

### Step 2: Lossless Transformer Visitor Implementation

1. Implement Visitor/Transform logic using Recast or `libcst` to preserve formatting, trailing commas, and inline comments:
   ```javascript
   export default function transformer(fileInfo, api) {
     const j = api.jscodeshift;
     const root = j(fileInfo.source);
     // Traversal & transformation logic
     return root.toSource({ quote: 'single' });
   }
   ```
2. Filter target nodes precisely (e.g. match `callee.object.name === 'logger'` and `callee.property.name === 'warn'`).

### Step 3: Idempotency & Edge-Case Protection

1. Enforce AST Idempotency: Re-running the transformer over already-transformed code must leave the AST unchanged ($\text{Codemod}(\text{Codemod}(code)) = \text{Codemod}(code)$).
2. Handle edge cases: nested calls, alias imports (`import { warn as logWarn }`), optional chaining (`logger?.warn()`), and destructured functions.

### Step 4: Dry-Run & Unit Test Verification

1. Run codemod unit tests using input/output code fixture pairs.
2. Execute dry-run preview across target repository (`npx jscodeshift -d -p --transform codemods/transform.js src/`).
3. Inspect `git diff` to ensure zero unintended syntax changes or formatting mangling occurred.

---

## 3. Reference Implementation: jscodeshift AST Transformer Script

```javascript
/**
 * jscodeshift Codemod: Refactor `logger.warn(msg)` to `logger.warning({ message: msg })`
 * Preserves comments, optional chaining, and handles import aliases idempotently.
 */
module.exports = function transformer(fileInfo, api, options) {
  const j = api.jscodeshift;
  const root = j(fileInfo.source);

  let hasModifications = false;

  // Find all CallExpressions matching `logger.warn(...)`
  root
    .find(j.CallExpression, {
      callee: {
        type: 'MemberExpression',
        property: { name: 'warn' },
      },
    })
    .forEach((path) => {
      const { node } = path;

      // Filter for `logger` object or identifier
      const calleeObj = node.callee.object;
      if (calleeObj && (calleeObj.name === 'logger' || calleeObj.name === 'log')) {
        // Skip if already refactored (Idempotency Check)
        if (
          node.arguments.length === 1 &&
          node.arguments[0].type === 'ObjectExpression'
        ) {
          return;
        }

        const originalArgs = node.arguments;

        // Construct new replacement CallExpression: logger.warning({ message: originalArg })
        const newCallee = j.memberExpression(
          calleeObj,
          j.identifier('warning')
        );

        const newArgument = j.objectExpression([
          j.property(
            'init',
            j.identifier('message'),
            originalArgs[0] || j.literal('')
          ),
        ]);

        // Preserve comments attached to the original CallExpression
        const replacement = j.callExpression(newCallee, [newArgument]);
        replacement.comments = node.comments;

        j(path).replaceWith(replacement);
        hasModifications = true;
      }
    });

  // Return transformed source only if modifications occurred; preserves original formatting
  return hasModifications
    ? root.toSource({ quote: 'single', trailingComma: true })
    : null;
};
```

---

## 4. AST Transformation Invariants & Idempotency Rules

$$\text{AST Idempotency: } \text{Codemod}(\text{Codemod}(\text{SourceCode})) \equiv \text{Codemod}(\text{SourceCode})$$

$$\text{Comment Preservation: } \text{Count}(\text{Comments}_{\text{source}}) = \text{Count}(\text{Comments}_{\text{transformed}})$$

$$\text{AST Validity: } \text{Parse}(\text{Codemod}(\text{SourceCode})) \neq \mathbf{SYNTAX\_ERROR}$$

---

## 5. Guardrails

### Operational Restrictions

- **No Naive Regex Refactoring**: Never use global string/regex replacements for code refactoring; use AST parsers (`jscodeshift`, `libcst`, `ts-morph`).
- **Mandatory Dry-Run First**: Always execute dry-run diff preview (`-d -p`) before applying bulk codebase writes.
- **Idempotent Visitors Only**: Every AST node visitor must check if nodes have already been transformed before applying replacements.

### Syntax Safety Invariants

- **Comment & Formatting Preservation**: Use lossless AST parsers (Recast for JS/TS, `libcst` for Python) that preserve comments and whitespace.
- **Zero Unparsed Syntax Errors**: Every modified file must pass static syntax compilation after transformation.

---

## 6. Atomic Failure Recovery & Rollback Handler

Before running bulk codemods, capture git baseline state. If transformed code fails syntax compilation or unit tests:

```bash
# Revert modified files
git checkout -- src/ 2>/dev/null

# Remove generated codemod artifacts
if [ -n "${CREATED_FILES:-}" ]; then
  rm -rf ${CREATED_FILES} 2>/dev/null
fi
```

---

## 7. Verification Plan & Toolchain Commands

Execute AST transformer tests and dry-runs:

```bash
# 1. Run jscodeshift unit tests over fixture pairs
npx jscodeshift -t codemods/my_transform.js __testfixtures__/sample.input.ts

# 2. Run dry-run AST diff preview across codebase
npx jscodeshift -d -p -t codemods/my_transform.js src/

# 3. Verify TypeScript type checking on transformed code
npx tsc --noEmit
```

---

## 8. Completion Report

Report AST parser used, total files matched vs modified, node visitors executed, dry-run diff summaries, syntax verification results, and idempotency validation proofs.
