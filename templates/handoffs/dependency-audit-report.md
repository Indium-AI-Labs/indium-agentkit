# Dependency audit report

## Scope

State the project, package managers, manifests, lockfiles, and audit tools used.

## Inventory summary

| Package manager | Total dependencies | Direct | Transitive | Lockfile fresh |
| --- | --- | --- | --- | --- |
| `manager` | count | count | count | yes / no |

## Vulnerability findings

| Package | Version | Severity | Advisory | Fix available | Notes |
| --- | --- | --- | --- | --- | --- |
| `package` | version | critical / high / medium / low | link or ID | yes / no | Impact summary. |

## License analysis

| Package | License | Compatible | Notes |
| --- | --- | --- | --- |
| `package` | license | yes / no / unknown | Concerns or exceptions. |

## Staleness and maintenance

| Package | Current | Latest | Last release | Maintenance signal |
| --- | --- | --- | --- | --- |
| `package` | version | version | date | active / slow / abandoned |

## Recommendations

Prioritized update and remediation actions with compatibility assessment.

## Handoff

**Changed contract:** Describe any externally visible behavior or state `none`.

**Files / systems affected:** List manifests, lockfiles, and build outputs.

**Evidence and tests:** List audit commands run and their results.

**Risks / rollback:** State risks of recommended updates.

**What the next agent needs:** List blockers and follow-up actions.
