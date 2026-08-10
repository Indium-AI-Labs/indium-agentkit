---
name: accessibility-audit
description: "Audit a user interface for WCAG conformance, keyboard operability, screen reader compatibility, color contrast, and inclusive design, reporting findings with severity and remediation."
---

# Accessibility audit

Evaluate a user interface for accessibility barriers. Inspect the project's
framework and rendering model before assuming a testing approach.

## Workflow

1. Read `AGENTS.md`, the target route or component, and the project's declared
   accessibility standards or conformance level. Default to WCAG 2.1 AA when
   no policy exists.
2. Check semantic HTML structure: headings hierarchy, landmark regions, lists,
   tables, form labels, and document language. Verify a single `h1` per page
   and logical heading order.
3. Verify keyboard operability: every interactive element is focusable and
   operable, focus order matches visual order, focus is visible, and no
   keyboard traps exist.
4. Check ARIA usage: roles, states, and properties are valid and necessary.
   Prefer native HTML semantics over ARIA when equivalent. Verify dynamic
   content changes are announced.
5. Evaluate color contrast ratios for text, interactive elements, and
   meaningful graphics against the target conformance level.
6. Check responsive and reduced-motion behavior: touch targets meet minimum
   sizes, content is usable at 200% zoom, and motion-sensitive animations
   respect `prefers-reduced-motion`.
7. Verify form accessibility: labels, error messages, required-field
   indicators, and autocomplete attributes. Check that validation feedback
   is announced to assistive technology.
8. Report each finding with WCAG criterion, severity, affected element or
   component, evidence, and concrete remediation direction.

## Guardrails

- This skill audits; it does not fix code by default. Separate the audit
  report from remediation implementation.
- Do not claim WCAG conformance or absence of barriers. Report what was
  tested, what was found, and what was not tested.
- An optional accessibility-checker subagent can analyze markup in parallel,
  but one agent can complete this workflow.

## Completion report

Report scope, conformance level assessed, findings by severity and criterion,
elements tested, tools and methods used, remediation priorities, and areas
not covered.
