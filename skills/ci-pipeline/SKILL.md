---
name: ci-pipeline
description: Design reliable CI pipelines with useful required checks.
---

# CI Pipeline

Design or improve continuous integration so failures are actionable,
repeatable, and fast enough to run on every change. The default target is
**GitHub Actions** with least-privilege permissions, SHA-pinned third-party
actions, dependency-aware caching, concurrency cancellation, explicit
timeouts, and a strict separation between fast merge-blocking checks and
slower integration, browser, security, and packaging jobs.

Before writing or editing any workflow, inspect the repository and adapt to
existing conventions: read the workflows already present under
`.github/workflows/`, the package metadata (`package.json`,
`pyproject.toml`, `go.mod`, `Cargo.toml`), the declared lint, typecheck,
test, and build commands, the supported runtime versions, and the current
branch protection policy. Every gate you add must map to a user-visible
risk, and every command CI runs must already exist as a project-local
command developers can run themselves.

---

## 1. Required I/O Context Schemas & Natural Language Auto-Inference

The skill supports **two invocation modes**:

1. **Orchestrator / Technical Mode (JSON Manifest)**: Pass the JSON context
   manifest below.
2. **Non-Technical Mode (Plain English Prompts)**: If the user provides a
   natural language prompt (e.g. *"Set up CI that runs lint, typecheck, and
   unit tests on Node 18 and 20 for every pull request, then builds on
   merge"*), the agent **must automatically infer and populate**
   `pipeline_context`, `check_matrix`, and `security_context` from the
   user's text and the existing repository configuration.

### JSON Context Manifest Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "CiPipelineContextManifest",
  "type": "object",
  "required": ["pipeline_context", "check_matrix"],
  "properties": {
    "pipeline_context": {
      "type": "object",
      "required": ["provider", "triggers"],
      "properties": {
        "provider": { "type": "string", "enum": ["github_actions", "gitlab_ci", "circleci", "azure_pipelines"] },
        "workflow_name": { "type": "string", "pattern": "^[a-z0-9-]+$", "default": "ci" },
        "triggers": {
          "type": "array",
          "items": { "type": "string", "enum": ["pull_request", "push_main", "tag", "schedule", "workflow_dispatch"] },
          "minItems": 1
        }
      }
    },
    "check_matrix": {
      "type": "object",
      "required": ["runtimes", "platforms", "fast_jobs"],
      "properties": {
        "runtimes": { "type": "array", "items": { "type": "string", "pattern": "^[0-9]+(\\.[0-9]+)?$" }, "minItems": 1 },
        "platforms": {
          "type": "array",
          "items": { "type": "string", "enum": ["ubuntu-latest", "windows-latest", "macos-latest"] },
          "minItems": 1
        },
        "fast_jobs": {
          "type": "array",
          "items": { "type": "string", "enum": ["lint", "typecheck", "unit", "build"] },
          "minItems": 1
        },
        "slow_jobs": {
          "type": "array",
          "items": { "type": "string", "enum": ["integration", "e2e", "security_scan", "coverage"] },
          "default": []
        }
      }
    },
    "security_context": {
      "type": "object",
      "required": ["top_level_permissions", "action_pinning", "secret_scope"],
      "properties": {
        "top_level_permissions": {
          "type": "object",
          "additionalProperties": { "type": "string", "enum": ["read", "write", "none"] }
        },
        "action_pinning": { "type": "string", "enum": ["full_sha", "reviewed_major_tag"] },
        "secret_scope": { "type": "string", "enum": ["none", "job_scoped", "environment_protected"] },
        "cache_trust_boundary": { "type": "string", "enum": ["pr_isolated", "shared_read_only"], "default": "pr_isolated" }
      }
    }
  }
}
```

### Automatic Natural Language Inference & Safety Validation Rules

If no raw JSON payload is provided, apply these defaults and safety checks:

- **`provider`**: Detected from existing CI files (`.github/workflows/`
  implies `github_actions`, `.gitlab-ci.yml` implies `gitlab_ci`). Defaults
  to `github_actions` when no CI configuration exists yet.
- **`triggers`**: Defaults to `["pull_request", "push_main"]`. Add
  `schedule` only for explicitly requested nightly or periodic verification;
  add `tag` only when releases are built from tags.
- **`runtimes`**: Derived from the project's declared support policy
  (`engines` in `package.json`, `requires-python` in `pyproject.toml`,
  `.nvmrc`, `.tool-versions`). Never invent runtime versions the project
  does not support.
- **`platforms`**: Defaults to `["ubuntu-latest"]`. Add `windows-latest` or
  `macos-latest` only when the project ships platform-specific artifacts or
  the user requests multi-OS coverage.
- **`fast_jobs`**: Defaults to `["lint", "typecheck", "unit"]`, filtered to
  the commands that actually exist in the project's declared scripts. A job
  without a backing project-local command must not be created.
- **`security_context`**: Defaults to
  `top_level_permissions: { "contents": "read" }`,
  `action_pinning: "full_sha"`, `secret_scope: "none"`, and
  `cache_trust_boundary: "pr_isolated"`.
- **Safety validation**: ABORT execution immediately if the requested change
  would remove an existing required check, weaken branch protection, grant
  `write` or cloud permissions to a test-only job, print a secret, or run
  untrusted pull-request code with access to privileged tokens.

---

## 2. Deterministic State Machine Execution Flow

Follow this exact sequential protocol. Do not skip steps or alter execution
ordering.

### Step 1: Repository, Gate & Risk Discovery

1. Read `AGENTS.md`, every existing workflow file, package metadata,
   declared test/lint/build commands, and supported runtime versions.
2. Map every existing and proposed required check to a user-visible risk
   (broken types, failing tests, unreviewed code, vulnerable dependencies).
   A check that maps to no risk is noise; a risk with no check is a gap.
3. Record the current branch protection configuration so the change is
   evaluated against it instead of silently replacing it.

### Step 2: Fast/Slow Separation & Job Dependency Graph

1. Separate fast feedback jobs (lint, typecheck, unit tests; target under
   ten minutes) from slower integration, browser, security, and build jobs.
2. Wire explicit `needs:` dependencies so a skipped or failed prerequisite
   cannot look green: downstream jobs must assert upstream outcomes, not
   merely observe them.
3. Add a final aggregator job (for example `all-checks`) with
   `if: always()` that fails unless every required upstream job reports
   `success`. Require the aggregator in branch protection so renaming a
   matrix leg cannot silently drop a gate.

### Step 3: Minimal Matrix & Immutable Action Pinning

1. Define a minimal version and platform matrix derived from the project's
   support policy: the oldest supported runtime, the current runtime, and
   only the platforms the project actually ships on.
2. Use `fail-fast: false` on matrix jobs so one failing leg does not hide
   the results of the others.
3. Pin every third-party action to an immutable full commit SHA (record the
   reviewed version in a trailing comment) or, at minimum, to a reviewed
   major tag when project policy explicitly allows it.

### Step 4: Least-Privilege Permissions, Environments & Secrets

1. Set top-level `permissions:` to the smallest set that lets any job run —
   normally `contents: read` — and escalate per job only with a written
   justification.
2. Route deployments through protected environments with required
   reviewers; test-only jobs hold no write or cloud permissions at all.
3. Scope every secret reference to the narrowest job and environment that
   needs it. Never print secrets, never pass them through step outputs, and
   never trust unvalidated pull-request input (titles, branch names, comment
   bodies) inside privileged jobs or shell strings.
4. For pull requests from forks, ensure privileged jobs either do not run
   or run only after an explicit maintainer approval gate.

### Step 5: Dependency & Cache Key Design

1. Key dependency caches on the lockfile hash plus the runtime version (for
   example `os-runtime-hashFiles(lockfile)`) so a lockfile or runtime change
   cannot restore a stale cache.
2. Scope restore keys narrowly; a pull-request cache must not be writable
   into the default-branch cache namespace.
3. Ensure caches cannot cross trust boundaries: content cached by an
   untrusted ref must never be restored into a job that holds secrets,
   signing keys, or deployment credentials.

### Step 6: Artifact, Evidence & Diagnostic Uploads

1. Upload useful artifacts: test reports (JUnit), coverage output, build
   bundles, and diagnostic logs, with failure evidence uploaded under
   `if: failure()` so debugging never requires a lucky re-run.
2. Set `retention-days` proportionate to sensitivity — short for logs that
   may embed environment details, longer for coverage and build manifests.
3. Name artifacts per matrix leg (`unit-report-node20`) so uploads from
   parallel legs never overwrite each other.

### Step 7: Deterministic Required Checks

1. Fixed commands: required checks run the exact project-local commands
   with no flag drift between local and CI execution.
2. Explicit `timeout-minutes` on every job so a hung runner fails fast
   instead of blocking the merge queue for the provider default.
3. Cancellation of superseded runs via a `concurrency` group keyed on
   workflow and ref with `cancel-in-progress: true` for pull requests.
4. Clear failure summaries: use problem matchers, JUnit annotations, or
   step summaries so the failing assertion is visible without downloading
   raw logs.

### Step 8: Local Validation & Change Documentation

1. Validate workflow syntax with `actionlint` and dry-run representative
   jobs with `act` before considering the change done.
2. Run the exact fast-job commands locally on a clean checkout and confirm
   they pass.
3. Document changed gates, expected runtime per job, known flaky checks
   (with their tracking issues), and follow-up work in the completion
   report.

---

## 3. Reference Implementation: Hardened GitHub Actions Workflow

```yaml
name: ci

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]
  workflow_dispatch:

# Cancel superseded runs on the same ref so stale results never gate a merge.
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

# Least privilege: the default token reads repository contents only.
# Individual jobs escalate narrowly and only with justification.
permissions:
  contents: read

env:
  CI: true

jobs:
  lint:
    name: Lint
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - name: Checkout
        uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
      - name: Setup Node.js
        uses: actions/setup-node@49933ea5288caeca8642d1e84afbd3f7d6820020 # v4.4.0
        with:
          node-version: "20"
          cache: npm
          cache-dependency-path: package-lock.json
      - name: Install dependencies
        run: npm ci --no-audit --no-fund
      - name: Run linter
        run: npm run lint

  typecheck:
    name: Typecheck
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
      - uses: actions/setup-node@49933ea5288caeca8642d1e84afbd3f7d6820020 # v4.4.0
        with:
          node-version: "20"
          cache: npm
          cache-dependency-path: package-lock.json
      - run: npm ci --no-audit --no-fund
      - run: npx --no-install tsc --noEmit

  unit:
    name: Unit (${{ matrix.node }})
    runs-on: ${{ matrix.platform }}
    timeout-minutes: 15
    strategy:
      fail-fast: false
      matrix:
        node: ["18", "20"]
        platform: [ubuntu-latest]
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
      - uses: actions/setup-node@49933ea5288caeca8642d1e84afbd3f7d6820020 # v4.4.0
        with:
          node-version: ${{ matrix.node }}
          cache: npm
          cache-dependency-path: package-lock.json
      - run: npm ci --no-audit --no-fund
      - name: Run unit tests with coverage
        run: npm run test -- --coverage --reporter=default --reporter=junit
      - name: Upload test report
        if: always()
        uses: actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02 # v4.6.2
        with:
          name: unit-report-node${{ matrix.node }}
          path: reports/junit.xml
          retention-days: 7

  integration:
    name: Integration
    needs: [lint, typecheck, unit]
    # Forked pull requests carry no secrets; privileged services run only
    # for same-repository refs or after explicit maintainer approval.
    if: >-
      github.event_name != 'pull_request' ||
      github.event.pull_request.head.repo.full_name == github.repository
    runs-on: ubuntu-latest
    timeout-minutes: 25
    permissions:
      contents: read
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
      - uses: actions/setup-node@49933ea5288caeca8642d1e84afbd3f7d6820020 # v4.4.0
        with:
          node-version: "20"
          cache: npm
      - run: npm ci --no-audit --no-fund
      - name: Start services and run integration tests
        run: npm run test:integration
      - name: Upload failure diagnostics
        if: failure()
        uses: actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02 # v4.6.2
        with:
          name: integration-diagnostics
          path: |
            logs/
            reports/
          retention-days: 3

  build:
    name: Build
    needs: [lint, typecheck]
    runs-on: ubuntu-latest
    timeout-minutes: 20
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
      - uses: actions/setup-node@49933ea5288caeca8642d1e84afbd3f7d6820020 # v4.4.0
        with:
          node-version: "20"
          cache: npm
      - run: npm ci --no-audit --no-fund
      - run: npm run build
      - name: Upload build bundle
        uses: actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02 # v4.6.2
        with:
          name: dist-bundle
          path: dist/
          retention-days: 14

  all-checks:
    name: Required checks
    needs: [lint, typecheck, unit, integration, build]
    if: always()
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - name: Assert every required job succeeded
        env:
          NEEDS_JSON: ${{ toJSON(needs) }}
        run: |
          node -e '
            const needs = JSON.parse(process.env.NEEDS_JSON);
            const failed = Object.entries(needs).filter(([, v]) => v.result !== "success");
            if (failed.length > 0) {
              console.error("Required jobs not green:", failed.map(([k, v]) => k + "=" + v.result).join(", "));
              process.exit(1);
            }
            console.log("All required jobs succeeded.");
          '
```

---

## 4. Workflow Verification & Required-Check Policy Pattern

Validate the workflow locally before pushing, then confirm the branch
protection policy names the checks the workflow actually emits:

```bash
# 1. Static-check workflow syntax, expression injection, and permission drift
actionlint .github/workflows/ci.yml

# 2. Dry-run the fast jobs locally with the same commands CI executes
act pull_request -j lint --dry-run
act pull_request -j unit --matrix node:20 --dry-run

# 3. Run the exact fast-job commands on a clean checkout
npm ci --no-audit --no-fund
npm run lint
npx --no-install tsc --noEmit
npm run test
```

Required-check policy applied through the GitHub API (`strict: true`
requires branches to be up to date before merging):

```json
{
  "required_status_checks": {
    "strict": true,
    "contexts": [
      "Lint",
      "Typecheck",
      "Unit (18)",
      "Unit (20)",
      "Integration",
      "Build",
      "Required checks"
    ]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "required_approving_review_count": 1,
    "dismiss_stale_reviews": true
  },
  "allow_force_pushes": false,
  "allow_deletions": false
}
```

```bash
# Apply and then verify the protection policy matches the workflow job names
gh api repos/{owner}/{repo}/branches/main/protection \
  --method PUT --input branch-protection.json
gh api repos/{owner}/{repo}/branches/main/protection/required_status_checks --jq '.contexts[]'
```

---

## 5. Pipeline Invariants & Feedback-Time Mathematics

Fast feedback budget — the slowest merge-blocking job stays inside budget:

$$T_{\text{fast}} = \max_{j \in J_{\text{fast}}} \left( t_{\text{queue}}(j) + t_{\text{run}}(j) \right) \le 10 \text{ minutes}$$

Required-check determinism — identical commits yield identical verdicts:

$$\forall c \in \text{RequiredChecks},\ \forall r_1, r_2 \text{ runs on commit } s:\quad \text{result}(c, s, r_1) = \text{result}(c, s, r_2)$$

Cache trust boundary — a job may only restore cache content written by a ref
of equal or higher trust:

$$\text{restore}(c, j) \;\Rightarrow\; \text{trust}\big(\text{writer}(c)\big) \ge \text{trust}(j)$$

Fast/slow coverage — merge-blocking work stays a small fraction of total
pipeline cost, and every fast job is merge-blocking:

$$\frac{\sum_{j \in J_{\text{fast}}} t_{\text{run}}(j)}{\sum_{j \in J_{\text{all}}} t_{\text{run}}(j)} \le 0.25 \qquad \text{and} \qquad J_{\text{fast}} \subseteq \text{RequiredChecks}$$

Flake budget — verdict flips on identical code are pipeline defects, not
test problems to route around:

$$\text{flake-rate}(c) = \frac{\#\{\text{runs of } c \text{ flipping verdict on identical } s\}}{\#\{\text{runs of } c\}} < 0.5\%$$

---

## 6. Guardrails

### Operational Restrictions

- **Never Weaken a Required Check**: Do not weaken a required check, skip a
  failing test, loosen a coverage threshold, or bypass branch protection to
  make a build green. Identify and fix the underlying failure, or escalate
  with evidence.
- **No Write Permissions for Test-Only Jobs**: Do not grant
  `contents: write`, `id-token: write`, cloud roles, or deployment
  credentials to jobs that only lint, typecheck, or test code.
- **Project-Local Commands Only**: CI steps invoke declared project
  commands (`npm run test`, `make check`); do not inline ad-hoc logic that
  diverges from what developers run locally.
- **Single-Agent Executable**: Optional `ci-verifier` subagent delegation
  can inspect failures or review workflow diffs in parallel, but one agent
  must remain able to complete this workflow end to end.

### Security Invariants

- **Least-Privilege Tokens**: Top-level permissions are `contents: read`
  (or stricter). Every per-job escalation carries a justification comment.
- **No Secret Exposure**: Secrets are never printed, echoed into logs,
  written to step outputs, or embedded in artifact uploads. Reference them
  only through the provider's secret mechanism at the narrowest scope.
- **Untrusted Input Isolation**: Pull-request titles, branch names, and
  issue bodies are never interpolated into `run:` shell strings; pass them
  through environment variables and treat them as data.
- **Pinned Supply Chain**: Third-party actions are pinned to reviewed
  immutable references; caches never cross trust boundaries from untrusted
  refs into privileged jobs.

---

## 7. Atomic Failure Recovery & Rollback Handler

Before creating or modifying files, the agent must capture a baseline list
of modified and untracked files. If any verification command in Section 8
fails and cannot be resolved within 2 iterations, the agent **must execute
targeted rollback restricted ONLY to files created or modified during this
run**:

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
failure causes. Never revert workflow files or branch protection settings
that existed before this run and were not touched by it.

---

## 8. Verification Plan & CI Toolchain Commands

Execute the following commands using project-local runners; adapt to the
project's declared scripts and CI provider tooling:

```bash
# 1. Static-check every workflow file for syntax and injection risks
actionlint .github/workflows/*.yml

# 2. Dry-run representative jobs locally
act pull_request -j lint --dry-run
act pull_request -j unit --matrix node:20 --dry-run

# 3. Run the exact fast-job commands on a clean checkout
npm ci --no-audit --no-fund
npm run lint
npx --no-install tsc --noEmit
npm run test

# 4. Confirm required checks match the workflow job names
gh api repos/{owner}/{repo}/branches/main/protection/required_status_checks --jq '.contexts[]'
```

---

## 9. Completion Report

Report workflows changed, trigger and permission behavior (including the
top-level permission set and every per-job escalation with its
justification), matrix and cache choices with their key design, the mapping
of each required check to the user-visible risk it gates, commands run with
their results, artifacts produced with their retention windows, expected
runtime per job against the feedback budget, known flaky checks, and any
unverified provider behavior or follow-up work.
