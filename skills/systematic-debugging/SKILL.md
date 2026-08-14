---
name: systematic-debugging
description: "Investigate a bug, failing test, regression, unexpected output, or production issue through reproduction, evidence, hypotheses, root-cause analysis, and a regression test before fixing it."
---

# Systematic Debugging

Investigate a bug, failing test, regression, unexpected output, or production
issue through a disciplined evidence loop: observe, reproduce, trace,
hypothesize, root-cause, regression-test, fix minimally, and report. The
default stance is **evidence before patch** — no production code changes
until the failure is reproducible and at least one falsifiable hypothesis is
on record.

The workflow is stack-agnostic. Before forming theories, inspect the local
repository to inherit its runtime, test harness, logging conventions, and
debugging tooling, and adapt every command below to the project's declared
scripts instead of inventing new entry points.

---

## 1. Required I/O Context Schemas & Natural Language Auto-Inference

The skill supports **two invocation modes**:

1. **Orchestrator / Technical Mode (JSON Manifest)**: Pass the JSON context
   manifest below.
2. **Non-Technical Mode (Plain English Prompts)**: If the user provides a
   natural language report (e.g. *"The checkout endpoint intermittently
   returns 500 when two customers buy the same SKUs at once"*), the agent
   **must automatically infer and populate** `bug_spec`,
   `environment_context`, and `reproduction_context` from the user's text,
   any pasted stack traces, and the repository's runtime conventions.

### JSON Context Manifest Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "SystematicDebuggingContextManifest",
  "type": "object",
  "required": ["bug_spec"],
  "properties": {
    "bug_spec": {
      "type": "object",
      "required": ["observed_behavior", "expected_behavior", "severity"],
      "properties": {
        "observed_behavior": { "type": "string", "minLength": 1 },
        "expected_behavior": { "type": "string", "minLength": 1 },
        "severity": { "type": "string", "enum": ["blocker", "critical", "major", "minor", "trivial"] },
        "impact_scope": { "type": "string" },
        "first_seen": { "type": "string" }
      }
    },
    "environment_context": {
      "type": "object",
      "required": ["runtime", "version"],
      "properties": {
        "runtime": { "type": "string", "enum": ["node", "python", "browser", "go", "jvm", "dotnet", "mixed", "unknown"] },
        "version": { "type": "string" },
        "os": { "type": "string" },
        "inputs": { "type": "array", "items": { "type": "string" } },
        "config_flags": { "type": "array", "items": { "type": "string" } }
      }
    },
    "reproduction_context": {
      "type": "object",
      "required": ["command", "determinism"],
      "properties": {
        "command": { "type": "string" },
        "determinism": { "type": "string", "enum": ["always", "intermittent", "not_yet_reproduced"] },
        "failure_rate": { "type": "number", "minimum": 0, "maximum": 1 },
        "artifacts": { "type": "array", "items": { "type": "string" } }
      }
    }
  }
}
```

### Automatic Natural Language Inference & Safety Rules

If no raw JSON payload is provided, apply these defaults and safety checks:

- **`observed_behavior` / `expected_behavior`**: Extracted from the prompt's
  problem statement. If the user cannot state the expected behavior, record
  the documented contract (test assertions, API schema, spec text) as the
  expectation and flag the gap in the report.
- **`severity`**: Inferred from impact language ("production down",
  "customers blocked" maps to `critical` or `blocker`; cosmetic wording maps
  to `minor`). Defaults to `major` when ambiguous; never silently downgrade.
- **`environment_context.runtime` / `version`**: Detected from
  `package.json`, `pyproject.toml`, `go.mod`, lockfiles, or CI configuration
  before running anything.
- **`reproduction_context.command`**: Reuse the project's declared test or
  run scripts. If no reproduction exists yet, set `determinism` to
  `not_yet_reproduced` and build one in Step 2 before any fix attempt.
- **Secret Safety**: Redact credentials, tokens, session identifiers, and
  personal data from every pasted log, stack trace, or payload before storing
  it in notes, fixtures, or reports.
- **Scope Safety**: Investigate before editing. Do not refactor, upgrade
  dependencies, or "clean up" unrelated code while root-causing a bug.

---

## 2. Deterministic State Machine Execution Flow

Follow this exact sequential protocol. Do not skip steps or alter execution
ordering. Each step's output is the next step's input; if a step cannot
produce its output, record the gap explicitly instead of guessing.

### Step 1: Observe — State the Problem Precisely

1. State the observed behavior, the expected behavior, the business or user
   impact, and the severity in one short paragraph each.
2. Inventory the available evidence: error messages, stack traces, logs,
   metrics, screenshots, failing CI jobs, and user reports.
3. Redact secrets from all captured evidence before writing it anywhere.
4. Note what is **not** known yet; an honest unknown list prevents premature
   theorizing.

### Step 2: Reproduce — Build the Smallest Reliable Failing Signal

1. Build the smallest reliable reproduction or failing signal: a single test,
   a single request, a single script — not the whole production workload.
2. Record the exact command, inputs, environment assumptions (versions,
   flags, data fixtures), and the observed result.
3. Classify determinism: `always`, `intermittent`, or `not_yet_reproduced`.
   For intermittent failures, run the reproduction in a loop (10-100
   iterations) and record the measured failure rate before trusting any
   conclusion drawn from it.
4. If reproduction is impossible in the current environment, state exactly
   which environmental factor blocks it and what would unblock it.

### Step 3: Trace — Follow Data and Control Flow from the Failure

1. Read the relevant code path and trace data or control flow **backward**
   from the observable failure toward its source: stack frame by stack
   frame, log line by log line.
2. Add temporary, targeted instrumentation (log lines, breakpoints,
   assertions) only where the trace goes dark; remove it before finishing.
3. Redact secrets from any new logs produced during tracing.
4. Locate the divergence boundary: the earliest point where an actual value
   differs from the contract value. Every hypothesis in Step 4 must explain
   this boundary.

### Step 4: Hypothesize — Competing, Falsifiable Theories

1. Form at least two competing hypotheses that could each explain the
   divergence boundary, and write each in falsifiable form: "If H is true,
   then experiment E will show X; otherwise H is rejected."
2. Design the cheapest targeted experiment per hypothesis (a one-line probe,
   a forced input, a bisected commit) and run experiments in order of
   information gain per cost.
3. Prefer a targeted experiment over an intuitive patch. A patch applied
   before falsification destroys the evidence needed to confirm the cause.
4. Optional independent exploration (a subagent mapping the code path in
   parallel) is allowed **only** when it will accelerate evidence gathering;
   one agent must still be able to complete this workflow alone.

### Step 5: Root-Cause — Identify with Evidence

1. Identify the root cause with evidence: name the exact line, state,
   configuration value, or external input, and cite the experiment output
   that proves it.
2. Distinguish root cause from trigger: the input that provokes the bug is
   not the defect itself.
3. If evidence is insufficient, stop and say what is unknown, which
   hypotheses remain live, and what observation would discriminate between
   them. Do not patch on a hunch.

### Step 6: Regression Test — Lock the Failure at a Public Seam

1. Add or update a regression test at a public behavior seam (HTTP endpoint,
   exported function, CLI command) when the project has an applicable test
   harness.
2. The test must encode the **expected** behavior, so it fails against the
   unfixed code. Run it now and confirm it fails for the root-cause reason,
   not for a setup or fixture error. This is the red step of the red-green
   loop.
3. Keep the test minimal: one behavior, one assertion cluster, no fixtures
   beyond what the reproduction requires.

### Step 7: Minimal Fix — Smallest Change That Addresses the Cause

1. Implement the smallest fix that addresses the root cause. Stay within the
   diff budget in Section 5: no drive-by refactors, no unrelated cleanups,
   no speculative hardening of adjacent code.
2. Run the regression test and confirm it passes — the green step. Never
   edit the test to make it pass.
3. Re-run the original reproduction command from Step 2 and the relevant
   verification commands (type check, lint, focused tests, then the broader
   suite) and capture exact output.
4. Remove all temporary instrumentation added in Step 3.

### Step 8: Report — Cause, Change, Evidence, Uncertainty

1. Report the root cause, the changed behavior, the tests and commands run
   with their results, and the remaining uncertainty.
2. State honestly what was **not** verified: untested platforms, unexercised
   inputs, intermittent rates below measurement resolution.
3. If optional independent exploration was used, note which evidence came
   from it and how that evidence was independently confirmed.

---

## 3. Reference Implementation: Hypothesis Register & Evidence Log

Worked example: intermittent HTTP 500 on `POST /api/orders` — roughly 1 in 20
requests under concurrent load, never in single-user testing. The register
keeps every hypothesis falsifiable; the evidence log forces each conclusion
to cite a concrete observation.

```markdown
# Debug Case: ORD-500 — intermittent 500 on POST /api/orders

## Problem Statement
- Observed: ~5% of POST /api/orders requests return 500 with
  `deadlock detected` in the API error log during load test (50 rps, 10 min).
- Expected: all valid requests return 201; zero 5xx.
- Severity: critical (production checkout path). First seen: 2026-08-10.

## Reproduction
- Command: `python scripts/repro_ord500.py --rounds 100`
- Determinism: intermittent (4-6% of requests fail at 50 rps; 0% at 1 rps).
- Environment: Python 3.12, FastAPI 0.115, PostgreSQL 16, pool_size=5.

## Hypothesis Register
| ID | Hypothesis (falsifiable form)                                    | Experiment      | Status   |
|----|------------------------------------------------------------------|-----------------|----------|
| H1 | If concurrent requests lock inventory rows in opposite order,    | E1: inspect     | CONFIRMED|
|    | then pg_locks will show a blocked-wait cycle during failures.    | pg_locks        |          |
| H2 | If the pool exhausts connections, then failures correlate with   | E2: metric      | REJECTED |
|    | checkout-wait spikes above 500ms.                                | overlay         |          |
| H3 | If the retry middleware replays a consumed request body, then    | E3: replay      | REJECTED |
|    | failing requests carry body-hash mismatch warnings.              | trace           |          |

## Evidence Log
- E2 (10:12): pool checkout-wait p99 = 3ms during the failing window; no
  correlation with 500s. H2 rejected.
- E3 (10:31): zero body-hash warnings across 600 captured failures.
  H3 rejected.
- E1 (11:05): `SELECT * FROM pg_locks WHERE NOT granted` during a failure
  burst shows tx A holding `inventory id=7` while awaiting `inventory id=9`,
  and tx B holding the reverse. H1 confirmed: the single-item path locks in
  `ORDER BY sku` order while the batch path locks in request insertion order.

## Root Cause
`update_inventory_batch()` locks rows in insertion order instead of a
canonical sort order, creating a lock-ordering cycle under concurrency.
Trigger: concurrent carts sharing two or more SKUs. Defect: missing sort.

## Fix & Verification
- Fix: sort batch keys before `SELECT ... FOR UPDATE` (2-line diff).
- Regression test: `tests/test_orders_concurrency.py::test_no_deadlock_under_shared_skus`
  fails pre-fix (5 deadlocks in 100 rounds), passes post-fix (0 in 500).
- Remaining uncertainty: verified on PostgreSQL only, not on MySQL backends.
```

Minimal deterministic reproduction script that isolates the failure:

```python
"""Repro ORD-500: force concurrent /api/orders calls sharing two SKUs.

Deterministic isolation: workers always request the shared SKUs in opposite
order, so the missing canonical lock ordering surfaces within seconds.
Exit code 1 while the bug is live; 0 once fixed.
"""
import argparse
import concurrent.futures
import urllib.error
import urllib.request

ENDPOINT = "http://localhost:8000/api/orders"
SKU_A, SKU_B = "SKU-7", "SKU-9"


def place_order(skus: list) -> int:
    items = ",".join('{{"sku": "{0}", "qty": 1}}'.format(s) for s in skus)
    body = ('{{"items": [{0}]}}'.format(items)).encode()
    req = urllib.request.Request(
        ENDPOINT, data=body, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status
    except urllib.error.HTTPError as exc:
        return exc.code


def run_round() -> tuple:
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        forward = pool.submit(place_order, [SKU_A, SKU_B])
        reverse = pool.submit(place_order, [SKU_B, SKU_A])
        return forward.result(), reverse.result()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rounds", type=int, default=100)
    args = parser.parse_args()
    failures = 0
    for _ in range(args.rounds):
        failures += sum(1 for code in run_round() if code >= 500)
    total = 2 * args.rounds
    print("5xx rate: {0:.2%} ({1}/{2})".format(failures / total, failures, total))
    raise SystemExit(1 if failures else 0)


if __name__ == "__main__":
    main()
```

---

## 4. Regression Test at the Public Behavior Seam

The regression test encodes expected behavior at a public seam, so it must
**fail before the fix** (red) and **pass after** (green). Always run it
against the unfixed code first: a regression test that passes pre-fix proves
nothing and usually signals a harness mistake.

```python
import anyio
import pytest
from httpx import AsyncClient

SHARED_SKUS = ["SKU-7", "SKU-9"]
ROUNDS = 200


@pytest.mark.anyio
async def test_no_deadlock_under_shared_skus(client: AsyncClient, seed_inventory):
    """Public-seam regression for ORD-500.

    Red   (pre-fix):  ~5% of rounds return 500 (deadlock detected).
    Green (post-fix): 200 rounds complete with zero 5xx responses.
    """
    async def place(order: list) -> int:
        resp = await client.post(
            "/api/orders",
            json={"items": [{"sku": sku, "qty": 1} for sku in order]},
        )
        return resp.status_code

    for _ in range(ROUNDS):
        results: list = []

        async def run(order: list) -> None:
            results.append(await place(order))

        async with anyio.create_task_group() as tg:
            tg.start_soon(run, SHARED_SKUS)
            tg.start_soon(run, list(reversed(SHARED_SKUS)))

        assert all(code == 201 for code in results), (
            "expected 201 for both concurrent orders, got {0}".format(results)
        )
```

Red-green loop discipline:

1. **Red**: Run the new test against the unfixed code. Confirm it fails and
   that the failure message matches the root cause (deadlock), not a fixture
   or harness error. If it passes pre-fix, the test is wrong — fix the test.
2. **Green**: Apply the minimal fix and confirm the same unmodified test now
   passes. Never weaken the assertion to reach green.
3. **Hold**: Re-run the full focused suite plus the original reproduction
   command from Step 2. The fix must not trade one failure for another.

---

## 5. Debugging Invariants & Evidence Mathematics

**Reproduction determinism requirement**: a fix is only verifiable against a
failure whose measured rate exceeds zero with statistical confidence. For an
intermittent bug with observed rate $p$, $n$ clean post-fix runs bound the
probability of a missed failure:

$$P(\text{miss} \mid p) = (1 - p)^{n} \le 0.05 \;\Longrightarrow\; n \ge \frac{\ln 0.05}{\ln(1 - p)}$$

**Hypothesis falsifiability criterion**: every registered hypothesis must
admit at least one experiment whose outcome can reject it:

$$\forall h \in H:\; \exists\, e \in E:\; \text{outcome}(e) \in \{\text{confirms}(h),\ \text{rejects}(h)\}$$

**Evidence-before-patch rule**: a fix change may only reference a root cause
backed by at least one recorded observation in the evidence log:

$$\text{patch admitted} \iff \exists\, o \in \text{EvidenceLog}:\; o \vdash \text{rootCause}$$

**Fix minimality (diff budget)**: the change set is the smallest one that
flips the regression test from red to green, with a hard ceiling unless
explicitly justified in the report:

$$\lvert \text{diff} \rvert = \min \{ \lvert d \rvert : \text{test}_{\text{red}} \xrightarrow{d} \text{test}_{\text{green}} \}, \qquad \lvert \text{diff} \rvert \le 50 \text{ LOC}$$

---

## 6. Guardrails

### Operational Restrictions

- **Evidence Before Patch**: Do not modify production code before the
  failure is reproduced and at least one falsifiable hypothesis is recorded.
  Prefer a targeted experiment over an intuitive patch at every decision
  point.
- **Minimal Diff Discipline**: Implement the smallest fix that addresses the
  root cause. No drive-by refactors, dependency upgrades, formatting sweeps,
  or unrelated "improvements" inside a bug-fix change.
- **Temporary Instrumentation Is Temporary**: Remove probe logs, breakpoints,
  and debug flags before finishing; they must never reach the final diff.
- **Honest Uncertainty**: If evidence is insufficient, state what is unknown
  and what would discriminate between the remaining hypotheses instead of
  guessing. Never declare "fixed" against an unreproduced failure.
- **Single-Agent Executable**: Optional independent exploration (a subagent
  mapping a code path or scanning logs in parallel) is permitted only when it
  will accelerate evidence gathering; one agent must still be able to
  complete this workflow end to end.

### Security Invariants

- **Redact Secrets Everywhere**: Credentials, tokens, session identifiers,
  connection strings, and personal data must be redacted from logs, stack
  traces, reports, test fixtures, and subagent prompts before storage or
  transmission. Use `<placeholder>` tokens in fixtures.
- **No Production Mutation While Investigating**: Reproduce against staging,
  local, or replayed traffic. Never run experiments that write to production
  data stores to "see what happens".
- **Contain Exploit-Relevant Detail**: If the bug is a security defect,
  restrict reproduction artifacts and root-cause detail to the report; do not
  paste working payloads into shared logs or issue trackers.

---

## 7. Atomic Failure Recovery & Rollback Handler

Before creating or modifying files, capture a baseline list of modified and
untracked files. If any verification command in Section 8 fails after the fix
and cannot be resolved within 2 iterations, execute targeted rollback
restricted ONLY to files created or modified during this run:

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

Preserve the hypothesis register and evidence log across rollback — they are
investigation output, not code. After rollback, output the exact error trace,
the surviving register, and the current evidence log so the next attempt
resumes from evidence, not from scratch.

---

## 8. Verification Plan & Debugging Toolchain Commands

Execute the following commands using project-local runners; adapt to the
project's declared scripts and runtime:

```bash
# 1. Re-run the recorded reproduction command (must show 0 failures post-fix)
python scripts/repro_ord500.py --rounds 100

# 2. Type check the touched modules
npx --no-install tsc --noEmit          # TypeScript projects
# python -m mypy <changed_package>     # Python projects

# 3. Execute the code linter
npm run lint                           # or: python -m ruff check .

# 4. Run the new regression test alone (red-green proof)
npx --no-install vitest run <test_file>   # or: python -m pytest <test_file> -v

# 5. Run the focused suite around the changed module, then the full suite
npm run test                           # or: python -m pytest

# 6. Scan the diff for leftover instrumentation and secret-shaped strings
git diff | grep -nE "console\.log|print\(|debugger|breakpoint\(" && echo "CLEANUP REQUIRED"
git diff | grep -nE "(api[_-]?key|token|secret|password)\s*[:=]" && echo "SECRET SCAN HIT"
```

---

## 9. Completion Report

Report the following, in order:

1. **Problem statement**: observed vs. expected behavior, impact, severity.
2. **Reproduction**: exact command, determinism class, measured failure rate.
3. **Root cause**: the precise defect (file, line, state, or configuration
   value) and the evidence that proves it, citing the hypothesis register
   entries that were confirmed and rejected.
4. **Fix**: the minimal diff and why it addresses the cause, not the symptom.
5. **Regression test**: the public-seam test added, with its red and green
   runs quoted verbatim.
6. **Verification**: every command run with its result, plus the diff-budget
   accounting against Section 5.
7. **Remaining uncertainty**: what was not verified, which hypotheses remain
   open (if any), and recommended follow-up monitoring or tests.
