---
name: dependency-audit
description: "Audit project dependencies for vulnerabilities, staleness, license risk, unused packages, and version-policy compliance using manifests, lockfiles, and available scanning tools."
---

# Dependency audit

Evaluate the health, security, and compliance of a project's dependency tree.
Inspect the project's package manager, manifests, and lockfiles before assuming
a toolchain.

## Workflow

1. Read `AGENTS.md`, dependency manifests, lockfiles, version constraints, and
   any declared update or license policy. Identify the package managers and
   registries in use.
2. Scan for known vulnerabilities using the project's declared audit command or
   standard tooling (`npm audit`, `pip-audit`, `cargo audit`, `bundler-audit`,
   or equivalent). Record exact commands and results.
3. Assess each dependency's maintenance status: last release, open security
   advisories, deprecation notices, and bus-factor signals.
4. Check license compatibility against the project's distribution model and any
   declared license policy. Flag copyleft, unknown, or missing licenses.
5. Identify unused, duplicated, or unnecessarily heavy dependencies by
   cross-referencing imports and build output.
6. Evaluate version constraints: overly broad ranges that risk breakage,
   pinned versions that block security patches, and lockfile freshness.
7. Recommend updates with a compatibility and risk assessment for each.
   Distinguish safe patch updates from breaking major-version upgrades.
8. Report findings with severity, evidence, affected packages, remediation
   direction, and follow-up actions.

## Guardrails

- Do not install, upgrade, or remove dependencies without explicit approval.
  This skill audits and recommends; it does not modify manifests by default.
- Do not run untrusted post-install scripts from unknown packages as part of
  an audit.
- An optional dependency-auditor subagent can analyze manifests and advisories
  in parallel, but one agent can complete this workflow.

## Completion report

Report packages audited, vulnerabilities found with severity, license issues,
staleness concerns, unused dependencies, recommended actions, and limitations
of the scan.
