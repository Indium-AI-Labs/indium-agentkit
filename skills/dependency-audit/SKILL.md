---
name: dependency-audit
description: "Audit project dependencies for vulnerabilities, staleness, license risk, unused packages, and version-policy compliance using manifests, lockfiles, and available scanning tools."
---

# Dependency Audit

Evaluate the security, freshness, license compliance, and structural health of
a project's dependency tree across ecosystems. The default tooling covers
**npm/yarn/pnpm** (`npm audit --json`), **Python** (`pip-audit --format json`),
**Rust** (`cargo audit --json`), and **Ruby** (`bundler-audit check`), with all
findings normalized into a single severity-ordered register.

The skill is **audit-only by default**: it inspects manifests, lockfiles, and
advisory feeds, then recommends. It never mutates the dependency tree without
explicit approval. Before assuming a toolchain, inspect the repository to
detect the package managers, registries, manifest formats, and any declared
update or license policies actually in use.

---

## 1. Required I/O Context Schemas & Natural Language Auto-Inference

The skill supports **two invocation modes**:

1. **Orchestrator / Technical Mode (JSON Manifest)**: Pass the JSON context
   manifest below.
2. **Non-Technical Mode (Plain English Prompts)**: If the user provides a
   natural language prompt (e.g. *"Audit our npm and Python dependencies for
   vulnerabilities and license problems"*), the agent **must automatically
   infer and populate** `ecosystem_context`, `policy_context`, and
   `scan_context` from the user's text and the repository's manifests.

### JSON Context Manifest Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "DependencyAuditContextManifest",
  "type": "object",
  "required": ["ecosystem_context", "scan_context"],
  "properties": {
    "ecosystem_context": {
      "type": "object",
      "required": ["package_manager", "manifests"],
      "properties": {
        "package_manager": { "type": "string", "enum": ["npm", "yarn", "pnpm", "pip", "poetry", "cargo", "bundler", "multi"] },
        "manifests": {
          "type": "array",
          "items": { "type": "string", "pattern": "^(?!.*(?:^|/)\\.\\.?(?:/|$))[A-Za-z0-9/_.-]+$" },
          "minItems": 1
        },
        "lockfiles": {
          "type": "array",
          "items": { "type": "string", "pattern": "^(?!.*(?:^|/)\\.\\.?(?:/|$))[A-Za-z0-9/_.-]+$" }
        },
        "registries": { "type": "array", "items": { "type": "string" } }
      }
    },
    "policy_context": {
      "type": "object",
      "required": ["license_policy"],
      "properties": {
        "license_policy": { "type": "string", "enum": ["permissive_only", "copyleft_allowed", "custom", "none"], "default": "none" },
        "update_policy": { "type": "string", "enum": ["patch_only", "minor_allowed", "any", "none"], "default": "none" },
        "max_critical": { "type": "integer", "minimum": 0, "default": 0 },
        "max_high": { "type": "integer", "minimum": 0, "default": 0 },
        "staleness_threshold_days": { "type": "integer", "minimum": 1, "default": 365 }
      }
    },
    "scan_context": {
      "type": "object",
      "required": ["scope", "write_allowed"],
      "properties": {
        "scope": { "type": "string", "enum": ["production_only", "all_dependencies"], "default": "all_dependencies" },
        "write_allowed": { "type": "boolean", "default": false },
        "include_transitive": { "type": "boolean", "default": true }
      }
    }
  }
}
```

### Automatic Natural Language Inference & Path Traversal Validation Rules

If no raw JSON payload is provided, apply these defaults and safety checks:

- **`package_manager`**: Detected from manifests present in the repository
  (`package.json` maps to npm/yarn/pnpm, `requirements.txt` or
  `pyproject.toml` maps to pip/poetry, `Cargo.toml` maps to cargo, `Gemfile`
  maps to bundler). Multiple ecosystems yield `multi`.
- **`manifests` / `lockfiles`**: Enumerated by globbing the repository root
  and workspace subdirectories. Every path MUST remain confined to the
  repository: reject any manifest path containing traversal segments (`.` or
  `..`) and **ABORT execution immediately** if one is detected.
- **`policy_context`**: Read from the repository's declared policy sources
  (license allowlists, `AGENTS.md` dependency rules, dependabot or renovate
  configuration). Defaults to `license_policy: "none"` and
  `update_policy: "none"` when undeclared; record the absence as a finding.
- **`scan_context.write_allowed`**: Always `false` unless the user explicitly
  authorizes modifications in the prompt. Auditing never implies write access.
- **`scope`**: `all_dependencies` unless the user restricts the audit to
  production dependencies only.

---

## 2. Deterministic State Machine Execution Flow

Follow this exact sequential protocol. Do not skip steps or alter execution
ordering.

### Step 1: Context Ingestion & Ecosystem Discovery

1. Read `AGENTS.md`, dependency manifests, lockfiles, version constraints, and
   any declared update or license policy.
2. Identify the package managers and registries in use, including private
   registries and mirrored advisory feeds.
3. Enumerate every manifest/lockfile pair; record lockfile presence, format
   version, and age. A manifest without a lockfile is itself a finding.

### Step 2: Vulnerability Scanning with Recorded Commands

1. Scan for known vulnerabilities using the project's declared audit command
   or standard tooling: `npm audit --json`, `pip-audit --format json`,
   `cargo audit --json`, `bundler-audit check`, or the ecosystem equivalent.
2. Record the exact commands executed, tool versions, advisory database
   timestamps, and raw output locations so the scan is reproducible.
3. Never execute install-time scripts as part of scanning; prefer
   lockfile-only analysis (`npm audit --package-lock-only` style) wherever the
   toolchain supports it.

### Step 3: Maintenance & Staleness Assessment

1. Assess each dependency's maintenance status: last release date, open
   security advisories, deprecation notices, and bus-factor signals (single
   maintainer, archived repository, unanswered security issues).
2. Compute staleness per package against `staleness_threshold_days` and
   classify each as fresh, aging, stale, or abandoned.

### Step 4: License Compatibility Review

1. Extract the declared license of every direct and transitive dependency
   from manifest metadata and license files.
2. Check compatibility against the project's distribution model (proprietary
   SaaS, distributed binary, published open source) and the declared license
   policy. Flag copyleft (GPL, AGPL, SSPL), weak-copyleft in doubt (LGPL,
   MPL), unknown, or missing licenses.

### Step 5: Usage & Weight Analysis

1. Identify unused, duplicated, or unnecessarily heavy dependencies by
   cross-referencing static imports, build configuration, and bundler or
   installer output.
2. Mark removal candidates as recommendations only; never remove a package
   without explicit approval.

### Step 6: Version Constraint Evaluation

1. Evaluate constraint ranges: overly broad ranges (`*`, `>=x`) that risk
   uncontrolled breakage, and hard pins that silently block security patches.
2. Check lockfile freshness: a lockfile older than its manifest, or resolved
   versions that have drifted from declared ranges, is a finding.

### Step 7: Remediation Recommendation

1. Recommend updates with a compatibility and risk assessment for each:
   distinguish safe patch updates (semver-compatible, no API change) from
   breaking major-version upgrades that require code changes.
2. For each vulnerable package, state the fixed version, the upgrade path
   (direct bump versus parent-dependency override), and a fallback mitigation
   (feature disable, network control, replacement candidate) when no fix
   exists.

### Step 8: Findings Report & Handoff

1. Report findings with severity, evidence, affected packages, remediation
   direction, and follow-up actions.
2. Populate the `templates/handoffs/dependency-audit-report.md` handoff
   artifact with the normalized findings register and policy evaluation.
3. Record scan limitations explicitly: ecosystems not covered, advisory
   databases not consulted, and any packages skipped.

---

## 3. Reference Implementation: Multi-Ecosystem Audit Aggregation Script

```python
#!/usr/bin/env python3
"""Normalize ecosystem audit output into a single findings register."""
from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone

SEVERITY_ORDER = {"critical": 4, "high": 3, "moderate": 2, "low": 1, "info": 0}

@dataclass
class Finding:
    package: str
    ecosystem: str
    installed_version: str
    severity: str
    advisory_id: str
    title: str
    fixed_version: str | None
    direct: bool
    remediation: str

def run_json_command(command: list[str]) -> dict:
    """Run a read-only audit command; never triggers install scripts."""
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    # Most audit tools exit 1 when findings exist; anything else is a failure.
    if result.returncode not in (0, 1):
        raise RuntimeError(f"audit command failed: {' '.join(command)}\n{result.stderr}")
    return json.loads(result.stdout or "{}")

def parse_npm_audit(audit_json: dict) -> list[Finding]:
    findings: list[Finding] = []
    for name, entry in audit_json.get("vulnerabilities", {}).items():
        advisories = [v for v in entry.get("via", []) if isinstance(v, dict)]
        fix = entry.get("fixAvailable")
        fixed_version = fix.get("version") if isinstance(fix, dict) else None
        for advisory in advisories or [{}]:
            findings.append(Finding(
                package=name,
                ecosystem="npm",
                installed_version=entry.get("range", "unknown"),
                severity=entry.get("severity", "info"),
                advisory_id=str(advisory.get("source", "npm-advisory")),
                title=advisory.get("title", "unspecified advisory"),
                fixed_version=fixed_version,
                direct=bool(entry.get("isDirect", False)),
                remediation=(f"npm update {name}" if fix else
                             "no fix published; override parent or mitigate"),
            ))
    return findings

def parse_pip_audit(audit_json: dict) -> list[Finding]:
    findings: list[Finding] = []
    for dep in audit_json.get("dependencies", []):
        for vuln in dep.get("vulns", []):
            fix_versions = vuln.get("fix_versions") or []
            findings.append(Finding(
                package=dep["name"],
                ecosystem="pip",
                installed_version=dep["version"],
                severity="high" if not fix_versions else "moderate",
                advisory_id=vuln.get("id", "unknown"),
                title=(vuln.get("description") or "")[:120],
                fixed_version=fix_versions[0] if fix_versions else None,
                direct=True,
                remediation=(f"pip install {dep['name']}=={fix_versions[0]}"
                             if fix_versions else
                             "no fix published; mitigate or replace"),
            ))
    return findings

def policy_gate(findings: list[Finding], max_critical: int = 0,
                max_high: int = 0) -> bool:
    critical = sum(1 for f in findings if f.severity == "critical")
    high = sum(1 for f in findings if f.severity == "high")
    return critical <= max_critical and high <= max_high

def main() -> int:
    register: list[Finding] = []
    register.extend(parse_npm_audit(run_json_command(
        ["npm", "audit", "--json", "--package-lock-only"])))
    register.extend(parse_pip_audit(run_json_command(
        ["pip-audit", "--format", "json"])))
    register.sort(key=lambda f: -SEVERITY_ORDER.get(f.severity, 0))
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "finding_count": len(register),
        "findings": [asdict(f) for f in register],
    }
    print(json.dumps(report, indent=2))
    return 0 if policy_gate(register) else 1

if __name__ == "__main__":
    sys.exit(main())
```

### Example Normalized Findings Table

| Severity | Package     | Ecosystem | Installed | Fixed In | Advisory       | Direct | Remediation                            |
|----------|-------------|-----------|-----------|----------|----------------|--------|----------------------------------------|
| critical | lodash      | npm       | 4.17.20   | 4.17.21  | GHSA-xxxx-0001 | yes    | `npm update lodash`                    |
| high     | requests    | pip       | 2.28.0    | 2.31.0   | PYSEC-2023-74  | yes    | `pip install requests==2.31.0`         |
| high     | openssl-sys | cargo     | 0.9.80    | 0.9.92   | RUSTSEC-0000-0 | no     | bump parent crate and refresh lockfile |
| moderate | rack        | bundler   | 2.2.3     | 2.2.8    | CVE-0000-00000 | yes    | `bundle update rack`                   |

---

## 4. Reproducible Re-Scan & Severity Classification Verification Pattern

An audit is only trustworthy if a second run over unchanged inputs reproduces
it. Re-run the recorded commands and diff the normalized registers; classify
every finding through a single deterministic severity function so policy gates
are stable across runs.

```bash
# 1. Re-run the identical recorded audit commands into fresh output files
npm audit --json --package-lock-only > audit-rerun-npm.json
pip-audit --format json > audit-rerun-pip.json

# 2. Regenerate the normalized register from the re-run output
python aggregate_audit.py > register-rerun.json

# 3. Deterministic comparison: unchanged inputs must yield identical findings
diff \
  <(jq -S '.findings | sort_by(.package, .advisory_id)' register-run1.json) \
  <(jq -S '.findings | sort_by(.package, .advisory_id)' register-rerun.json) \
  && echo "REPRODUCIBLE: registers identical" \
  || echo "DRIFT DETECTED: investigate advisory feed or lockfile changes"

# 4. Confirm the audit-only invariant: no manifest or lockfile was modified
git status --porcelain -- 'package*.json' 'requirements*.txt' 'Cargo.*' 'Gemfile*'
```

```python
def classify_cvss(score: float) -> str:
    """Map a CVSS v3 base score to the register's severity bands."""
    if score <= 0.0:
        return "none"
    if score < 4.0:
        return "low"
    if score < 7.0:
        return "moderate"
    if score < 9.0:
        return "high"
    return "critical"

def policy_gate_verdict(findings: list, max_critical: int = 0,
                        max_high: int = 0) -> str:
    critical = sum(1 for f in findings if f.severity == "critical")
    high = sum(1 for f in findings if f.severity == "high")
    if critical > max_critical:
        return f"FAIL: {critical} critical findings exceed policy max {max_critical}"
    if high > max_high:
        return f"FAIL: {high} high findings exceed policy max {max_high}"
    return "PASS: within declared vulnerability policy thresholds"
```

---

## 5. CVSS Severity Bands & Policy Invariant Mathematics

$$\text{severity}(s) = \begin{cases} \text{critical} & 9.0 \le s \le 10.0 \\ \text{high} & 7.0 \le s < 9.0 \\ \text{moderate} & 4.0 \le s < 7.0 \\ \text{low} & 0.1 \le s < 4.0 \\ \text{none} & s = 0.0 \end{cases}$$

$$\#\{f \in F : \text{severity}(f) = \text{critical}\} \le N_{\text{critical}}^{\max} = 0, \qquad \#\{f \in F : \text{severity}(f) = \text{high}\} \le N_{\text{high}}^{\max}$$

$$\text{staleness}(p) = t_{\text{now}} - t_{\text{last\_release}}(p), \qquad \text{staleness}(p) > \theta_{\text{stale}} = 365\,\text{days} \Rightarrow \text{flag}(p)$$

$$\text{license\_risk}(\ell) = \begin{cases} \text{blocking} & \ell \in \{\text{GPL}, \text{AGPL}, \text{SSPL}\} \wedge \text{artifact is distributed} \\ \text{review} & \ell \in \{\text{LGPL}, \text{MPL}, \text{unknown}, \text{missing}\} \\ \text{clear} & \ell \in \{\text{MIT}, \text{BSD-2/3}, \text{Apache-2.0}, \text{ISC}\} \end{cases}$$

$$\forall\, \text{run } r: \quad \text{write\_allowed}(r) = \text{false} \;\Rightarrow\; \text{manifests}(r_{\text{before}}) = \text{manifests}(r_{\text{after}}) \;\wedge\; \text{lockfiles}(r_{\text{before}}) = \text{lockfiles}(r_{\text{after}})$$

---

## 6. Guardrails

### Operational Restrictions

- **Audit-Only by Default**: Do **NOT** install, upgrade, or remove
  dependencies without explicit approval. This skill audits and recommends;
  it does not modify manifests by default. Any approved change is executed as
  a separate, separately verified run.
- **Read-Only Scanning**: Prefer lockfile-only analysis modes. Record every
  command executed, its tool version, and its raw output location so the
  audit is reproducible by another operator.
- **Single-Agent Executable**: An optional dependency-auditor subagent can
  analyze manifests and advisories in parallel, but one agent can complete
  this workflow end to end.

### Security Invariants

- **No Untrusted Install Scripts**: Never run untrusted post-install scripts
  from unknown packages as part of an audit; use script-suppressed or
  lockfile-only resolution (`--ignore-scripts`, `--package-lock-only`).
- **No Uncontrolled Data Egress**: Never transmit manifests, lockfiles, or
  findings to external services without approval; private package names leak
  internal system topology.
- **Credential Hygiene**: Treat advisory database credentials and private
  registry tokens as secrets. Reference them by environment variable name
  only, and keep them out of reports, registers, and command logs.

---

## 7. Atomic Failure Recovery & Rollback Handler

Before creating or modifying any file (reports, registers, scratch output),
capture a baseline list of modified and untracked files. If any verification
command in Section 8 fails and cannot be resolved within 2 iterations,
execute targeted rollback restricted ONLY to files created or modified during
this run:

```bash
# Revert ONLY modified files tracked during this execution run
if [ -n "${MODIFIED_FILES:-}" ]; then
  git checkout -- ${MODIFIED_FILES} 2>/dev/null
fi

# Remove ONLY newly created untracked files from this execution run
if [ -n "${CREATED_FILES:-}" ]; then
  rm -rf ${CREATED_FILES} 2>/dev/null
fi
```

After executing targeted rollback, output the exact error trace and state
failure causes. For an audit-only run, manifests and lockfiles must never
appear in `MODIFIED_FILES`; if they do, the run has violated its guardrails —
revert them first and disclose the violation in the completion report.

---

## 8. Verification Plan & Multi-Ecosystem Audit Toolchain Commands

Execute the following commands using project-local runners; skip ecosystems
not present in the repository and record each skip:

```bash
# 1. npm ecosystem scan (lockfile-only; no script execution)
npm audit --json --package-lock-only > audit-npm.json

# 2. Python ecosystem scan
pip-audit --format json > audit-pip.json

# 3. Rust ecosystem scan
cargo audit --json > audit-cargo.json

# 4. Ruby ecosystem scan
bundler-audit check --format json > audit-bundler.json

# 5. Aggregate all ecosystem output into the normalized findings register
python aggregate_audit.py > findings-register.json

# 6. Confirm the audit-only invariant: manifests and lockfiles untouched
git status --porcelain -- 'package*.json' 'requirements*.txt' 'Cargo.*' 'Gemfile*'
```

---

## 9. Completion Report

Report packages audited per ecosystem with exact scan commands and tool
versions, vulnerabilities found with severity and CVSS evidence, license
issues with policy classification, staleness concerns with age data, unused
or duplicated dependencies with cross-reference evidence, recommended actions
ranked by risk and split into safe patch updates versus breaking upgrades,
policy gate results against the declared max critical/high thresholds, and
the explicit limitations of the scan (uncovered ecosystems, advisory feed
timestamps, skipped packages).
