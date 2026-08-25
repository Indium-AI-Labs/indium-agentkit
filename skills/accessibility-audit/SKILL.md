---
name: accessibility-audit
description: Audit user interfaces for WCAG 2.1/2.2 AA/AAA conformance, ARIA semantics, keyboard operability, screen reader compatibility, and color contrast.
---

# Accessibility Audit

Audit modern web applications, design systems, and mobile interfaces for WCAG 2.1/2.2 (Level A, AA, AAA) conformance, ARIA semantics, keyboard focus management, screen reader tree compatibility, and mathematical color contrast thresholds.

The skill is **contract-first and WCAG-validated**: DOM tree landmarks, accessible name algorithms (accName 1.2), focus traps, relative luminance ratios, touch target dimensions, and ARIA live region behaviors are mathematically evaluated and verified before reporting remediation steps.

---

## 1. Required I/O Context Schemas & Natural Language Auto-Inference

The skill supports **two invocation modes**:

1. **🤖 Orchestrator / Technical Mode (JSON Manifest)**: Pass the JSON context manifest below.
2. **💬 Non-Technical Mode (Plain English Prompts)**: If the user provides a natural language prompt (e.g. *"Audit the login form and dashboard page for WCAG 2.1 AA compliance including keyboard focus traps and color contrast"*), the agent **must automatically infer and populate** `target_url_or_path`, `conformance_level`, `audit_scope`, and `automated_runner` from the user's text.

### JSON Context Manifest Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "AccessibilityAuditContextManifest",
  "type": "object",
  "required": ["target_scope", "audit_config"],
  "properties": {
    "target_scope": {
      "type": "object",
      "required": ["target_url_or_path"],
      "properties": {
        "target_url_or_path": { "type": "string" },
        "component_selector": { "type": "string", "default": "body" },
        "routes_to_audit": { "type": "array", "items": { "type": "string" } }
      }
    },
    "audit_config": {
      "type": "object",
      "required": ["conformance_level"],
      "properties": {
        "conformance_level": { 
          "type": "string", 
          "enum": ["WCAG21_A", "WCAG21_AA", "WCAG21_AAA", "WCAG22_AA"],
          "default": "WCAG21_AA" 
        },
        "automated_runner": { 
          "type": "string", 
          "enum": ["axe_core_playwright", "pa11y", "lighthouse_ci", "jsdom_accname"],
          "default": "axe_core_playwright" 
        },
        "include_experimental_wcag22": { "type": "boolean", "default": true },
        "min_touch_target_px": { "type": "integer", "default": 44 }
      }
    },
    "assistive_tech_profile": {
      "type": "object",
      "properties": {
        "screen_readers": { 
          "type": "array", 
          "items": { "type": "string", "enum": ["NVDA", "JAWS", "VoiceOver", "TalkBack"] } 
        },
        "keyboard_only_nav": { "type": "boolean", "default": true },
        "prefers_reduced_motion": { "type": "boolean", "default": true }
      }
    }
  }
}
```

### Automatic Natural Language Inference & Standards Fallbacks

If no raw JSON payload is provided, apply these defaults and strict compliance rules:

- **WCAG Level Fallback**: Defaults to `WCAG21_AA` when no explicit standard is specified.
- **`target_url_or_path`**: Inferred from repository routing files (`src/pages/`, `app/`, or local dev server `http://localhost:3000`).
- **`automated_runner`**: Defaults to `axe_core_playwright` for headless browser accessibility testing.

---

## 2. Deterministic State Machine Execution Flow

Follow this exact sequential protocol. Do not skip steps or alter execution ordering.

### Step 1: DOM Landmark & Semantic Tree Inspection

1. Inspect HTML semantic structure: verify landmark elements (`<header>`, `<nav>`, `<main>`, `<footer>`, `<aside>`, `<section>`).
2. Verify heading hierarchy: ensure exactly one `<h1>` per page, with strict logical descending nesting (`h1` $\rightarrow$ `h2` $\rightarrow$ `h3`). Reject skipped heading levels (`h1` $\rightarrow$ `h4`).
3. Check table accessibility (`<table>`, `<th> scope="col|row"`, `<caption>`).

### Step 2: Keyboard Operability & Focus Management

1. **Focusability**: Every interactive element (`<button>`, `<a>`, `<input>`, `<select>`, `<textarea>`, custom controls) must be keyboard-focusable (`tabindex="0"` or native elements).
2. **Focus Visibility**: Verify CSS `:focus-visible` styles are not removed via `outline: none` or `outline: 0` without a prominent fallback indicator (minimum 2px thickness with $3:1$ contrast ratio).
3. **Focus Traps**: Ensure modal dialogs and dropdown menus trap focus internally while open and restore focus to the trigger element upon closing.

### Step 3: ARIA Attributes & Accessible Name Computation

1. **First Rule of ARIA**: Prefer native HTML5 elements (`<button>` over `<div role="button">`).
2. **Accessible Name Algorithm (accName 1.2)**: Calculate accessible names for interactive elements:
   - Check `aria-labelledby` $\rightarrow$ `aria-label` $\rightarrow$ native `<label>` / `alt` $\rightarrow$ text content $\rightarrow$ `title`.
   - Flag elements missing accessible names (`<button><svg/></button>` without `aria-label`).
3. **Dynamic State Announcements**: Verify `aria-expanded`, `aria-checked`, `aria-selected`, `aria-invalid`, and `aria-live` regions (`polite` / `assertive`) announce dynamic updates to screen readers.

### Step 4: Mathematical Color Contrast & Luminance Computation

Calculate contrast ratios for all text, controls, and meaningful graphical objects against their backgrounds using the relative luminance formula defined in WCAG 2.1 Success Criterion 1.4.3 & 1.4.11.

---

## 3. Reference Implementation: Playwright + Axe-Core Audit Runner

```typescript
import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { writeFileSync } from 'fs';

export interface AuditResult {
  url: string;
  violationsCount: number;
  criticalViolations: Array<{
    id: string;
    impact: string;
    description: string;
    helpUrl: string;
    nodes: number;
  }>;
}

export async function runAccessibilityAudit(
  pageUrl: string,
  outputPath = 'accessibility-report.json'
): Promise<AuditResult> {
  const browser = await test.createPage();
  await browser.goto(pageUrl, { waitUntil: 'networkidle' });

  // Run Axe-core WCAG 2.1 AA & AAA checks
  const axeResults = await new AxeBuilder({ page: browser })
    .withTags(['wcag2a', 'wcag21a', 'wcag21aa', 'wcag22aa', 'best-practice'])
    .disableRules(['color-contrast-enhanced']) // Enable standard 4.5:1 AA ratio
    .analyze();

  const formattedViolations = axeResults.violations.map((v) => ({
    id: v.id,
    impact: v.impact || 'minor',
    description: v.description,
    helpUrl: v.helpUrl,
    nodes: v.nodes.length,
  }));

  const summary: AuditResult = {
    url: pageUrl,
    violationsCount: axeResults.violations.length,
    criticalViolations: formattedViolations,
  };

  writeFileSync(outputPath, JSON.stringify(axeResults, null, 2));
  console.log(`[A11y Audit] Found ${summary.violationsCount} violations on ${pageUrl}. Report saved to ${outputPath}.`);

  return summary;
}
```

---

## 4. WCAG Mathematical Formulas & Contrast Invariants

### 1. Relative Luminance ($L$)
Relative luminance of any point in a color space:

$$L = 0.2126 \cdot R + 0.7152 \cdot G + 0.0722 \cdot B$$

Where $R, G, B$ are normalized RGB components:

$$C_{\text{sRGB}} = \frac{C_{\text{8bit}}}{255}$$

$$C = \begin{cases} \frac{C_{\text{sRGB}}}{12.92}, & \text{if } C_{\text{sRGB}} \le 0.04045 \\ \left( \frac{C_{\text{sRGB}} + 0.055}{1.055} \right)^{2.4}, & \text{if } C_{\text{sRGB}} > 0.04045 \end{cases}$$

### 2. Color Contrast Ratio ($CR$)

$$CR = \frac{L_1 + 0.05}{L_2 + 0.05}$$

Where $L_1$ is the relative luminance of the lighter color, and $L_2$ is the relative luminance of the darker color.

### 3. WCAG Threshold Invariants

$$\text{Normal Text (AA): } CR \ge 4.5:1$$

$$\text{Large Text / UI Controls (AA): } CR \ge 3.0:1$$

$$\text{Enhanced Contrast (AAA): } CR \ge 7.0:1$$

$$\text{Touch Target Dimensions (WCAG 2.2 AA): } W \ge 24\text{px}, H \ge 24\text{px} \quad (\text{Recommended: } 44\text{px} \times 44\text{px})$$

---

## 5. Guardrails

### Operational Restrictions

- **Audit Only by Default**: Do not automatically rewrite component source files unless explicitly requested; produce a structured remediation report first.
- **No False Conformance Claims**: Never claim 100% WCAG conformance based solely on automated tools. Automated tools catch ~40% of accessibility issues; manual screen reader testing is required.
- **Outline Removal Protection**: Never allow `outline: none` or `outline: 0` in CSS without explicit custom `:focus-visible` styles.

---

## 6. Atomic Failure Recovery & Rollback Handler

If accessibility audit scripts fail or produce unexpected JSDOM errors:

```bash
# Clean up temporary audit reports
rm -f accessibility-report.json temp-axe-results.json 2>/dev/null

# Revert any transient test page modifications
if [ -n "${MODIFIED_FILES:-}" ]; then
  git checkout -- ${MODIFIED_FILES} 2>/dev/null
fi
```

---

## 7. Verification Plan & Toolchain Commands

Execute accessibility audit suite:

```bash
# 1. Run Playwright + Axe-core automated accessibility test suite
npx playwright test tests/a11y/

# 2. Run Pa11y CLI audit against target route
npx pa11y http://localhost:3000 --standard WCAG2AA

# 3. Validate HTML semantics using vnu-jar / W3C HTML validator
npx html-validate "src/**/*.html"
```

---

## 8. Completion Report

Report target URLs/components audited, WCAG conformance level assessed (e.g. WCAG 2.1 AA), violation count grouped by severity (Critical, Serious, Moderate, Minor), exact element selectors, contrast ratio calculations, keyboard focus trap findings, screen reader accessibility status, and prioritized remediation recommendations.
