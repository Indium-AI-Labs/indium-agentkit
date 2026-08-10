# Content catalog

Generated from `SKILL.md` and subagent frontmatter with:

```bash
python scripts/list_content.py --format markdown
```


| Kind | Name | Description |
| --- | --- | --- |
| skill | `accessibility-audit` | Audit a user interface for WCAG conformance, keyboard operability, screen reader compatibility, color contrast, and inclusive design, reporting findings with severity and remediation. |
| skill | `api-design` | Design an API contract — resources, operations, schemas, errors, versioning, and pagination — from requirements before implementation, producing a completed api-contract handoff. |
| skill | `author-agentkit-content` | Create or update indium-agentkit skills, subagents, templates, validation, and documentation. Use when adding, revising, validating, or publishing content in this distribution repository. |
| skill | `backend-api` | Build robust typed API endpoints with safe contracts. |
| skill | `ci-pipeline` | Design reliable CI pipelines with useful required checks. |
| skill | `delegate-work` | Plan bounded Codex subagent delegation with structured handoffs. |
| skill | `compliance-audit` | Audit code, configuration, and data flows against GDPR, SOC 2, HIPAA, and PCI-DSS compliance controls including PII redaction and audit logging. |
| skill | `contract-testing` | Design and implement consumer-driven contract tests (Pact, MSW, Playwright) to verify interface compatibility between microservices and frontend/backend boundaries. |
| skill | `data-pipeline-design` | Design safe ETL/ELT pipelines, data warehouse schemas, partition strategies, idempotency controls, and data quality assertions before implementation. |
| skill | `database-design` | Design safe PostgreSQL schemas and staged migrations. |
| skill | `dependency-audit` | Audit project dependencies for vulnerabilities, staleness, license risk, unused packages, and version-policy compliance using manifests, lockfiles, and available scanning tools. |
| skill | `deployment-safety` | Plan and verify staged deployments with safe rollback. |
| skill | `estimate-work` | Break down a feature, fix, or change into estimated effort with scope, risk factors, assumptions, and sequencing before prioritization. |
| skill | `frontend-ship` | Build accessible, typed frontend features end to end. |
| skill | `incident-triage` | Triage incidents with evidence, mitigation, and follow-up. |
| skill | `infrastructure-review` | Review infrastructure for security, reliability, and cost risks. |
| skill | `llm-eval-harness` | Design and execute evaluation benchmarks for prompts, RAG retrieval pipelines, and agent tools to measure token cost, latency, accuracy, and guardrail compliance. |
| skill | `load-testing-suite` | Design, configure, and execute load and stress testing suites (k6, Locust) with target latency SLAs, throughput targets, and tear-down verification. |
| skill | `mobile-release-safety` | Plan and audit mobile application releases (iOS/Android/React Native/Flutter) covering app store submission requirements, code signing, feature flags, OTA updates, and crash reporting. |
| skill | `observability-setup` | Instrument code with structured logging, metrics, distributed tracing, or alerting following existing observability patterns and avoiding credential exposure. |
| skill | `onboard-to-codebase` | Generate a developer onboarding guide or codebase orientation by analyzing architecture, conventions, dependencies, workflows, and common tasks from the existing project. |
| skill | `performance-optimization` | Measure, analyze, and optimize a specific performance bottleneck through profiling, targeted change, and comparative re-measurement with evidence. |
| skill | `plan-change` | Turn a feature request, bug report, refactor, or technical proposal into an implementation-ready plan with scope, acceptance criteria, affected areas, test seams, risks, and ordered steps. |
| skill | `prototype-spike` | Investigate a technical approach through a time-boxed, throwaway spike that produces evidence and a go-or-no-go recommendation before committing to a design. |
| skill | `refactor-code` | Restructure, rename, extract, inline, or simplify code to improve clarity, cohesion, or maintainability while preserving observable behavior, verified by the existing test suite. |
| skill | `release-notes` | Create accurate user-facing release notes or changelog entries from a commit range, tags, issues, and repository history, including breaking changes, migrations, and known limitations. |
| skill | `resolve-merge-conflicts` | Resolve Git merge or rebase conflicts by recovering each side's intent, preserving compatible behavior, validating the result, and documenting unavoidable trade-offs. |
| skill | `review-change` | Review a local diff, branch, commit range, or pull request for correctness, regressions, security concerns, project conventions, and missing tests. Use when asked for a code review; report findings without editing by default. |
| skill | `safe-migration` | Plan and implement safe schema, API, configuration, storage, or file-format migrations with compatibility analysis, staged rollout, rollback, and evidence-based verification. |
| skill | `security-review` | Review a scoped code change, endpoint, integration, configuration, or infrastructure definition for security risks by tracing assets, trust boundaries, authorization, input handling, and exploit paths. |
| skill | `systematic-debugging` | Investigate a bug, failing test, regression, unexpected output, or production issue through reproduction, evidence, hypotheses, root-cause analysis, and a regression test before fixing it. |
| skill | `test-first-change` | Plan and implement a behavior change, bug fix, or refactor with focused behavior-level tests, public seams, and incremental red-green-refactor cycles. Use when writing or changing production code. |
| skill | `threat-modeling` | Perform structured threat modeling (STRIDE/PASTA) on architecture diagrams, system interfaces, and data flow graphs before implementation. |
| skill | `verify-and-ship` | Verify a completed repository change, run declared tests and lint, inspect the diff for generated artifacts or secrets, and commit and publish only when repository policy or the user authorizes it. Use before finishing or shipping work. |
| skill | `write-documentation` | Author, update, or audit project documentation — READMEs, architecture decisions, API references, onboarding guides, and inline doc — from code evidence without inventing behavior. |
| skill | `write-runbook` | Create or update an operational runbook for a service, feature, or failure mode with detection, diagnosis, mitigation, recovery, and escalation procedures. |
| subagent | `accessibility-checker` | Read-only accessibility specialist that evaluates markup, ARIA usage, color contrast, keyboard flow, and screen reader compatibility. |
| subagent | `api-designer` | Read-only API design specialist that analyzes requirements, existing conventions, and data models to propose typed contract designs. |
| subagent | `backend-builder` | Implement scoped typed API behavior with server-side safeguards. |
| subagent | `ci-verifier` | Diagnose CI workflows and report exact verification evidence. |
| subagent | `compliance-auditor` | Read-only compliance specialist that audits code, data flows, PII redaction, encryption, and audit logs against compliance control standards. |
| subagent | `data-engineer` | Read-only data engineering specialist that inspects schemas, pipeline transformations, partitioning strategies, and query performance. |
| subagent | `database-architect` | Analyze schemas and propose safe, verified migration plans. |
| subagent | `dependency-auditor` | Read-only dependency specialist that scans manifests, lockfiles, and advisory databases for vulnerabilities, staleness, and license risks. |
| subagent | `doc-writer` | Read-only documentation specialist that analyzes code, tests, and history to draft accurate project documentation. |
| subagent | `estimator` | Read-only estimation specialist that analyzes scope, complexity, dependencies, and risk to produce effort assessments. |
| subagent | `explorer` | Read-only codebase explorer that maps relevant files, control flow, conventions, and uncertainties for a focused task. |
| subagent | `frontend-builder` | Implement scoped accessible UI features from agreed contracts. |
| subagent | `incident-commander` | Coordinate evidence-based incident response without production edits. |
| subagent | `llm-evaluator` | Read-only LLM evaluation specialist that inspects prompt definitions, RAG retrieval logic, benchmark datasets, and guardrails. |
| subagent | `migration-planner` | Read-only migration planner that inventories compatibility impact, rollout stages, rollback paths, and verification for schema, API, configuration, or file-format changes. |
| subagent | `mobile-specialist` | Read-only mobile specialist that inspects build configurations, permission manifests, native bridges, bundle sizes, and store submission readiness. |
| subagent | `performance-profiler` | Read-only performance specialist that chooses approved profiling methods, compares evidence against a baseline, and reports bottlenecks. |
| subagent | `release-engineer` | Prepare release plans and assess deployment readiness. |
| subagent | `resilience-reviewer` | Read-only resilience specialist that analyzes circuit breakers, retry backoffs, timeout configurations, connection pools, and fallbacks. |
| subagent | `reviewer` | Read-only independent reviewer for a completed diff, branch, or pull request who reports actionable findings with evidence. |
| subagent | `runbook-writer` | Read-only specialist that analyzes infrastructure, code, monitoring, and failure modes to draft operational runbooks. |
| subagent | `security-reviewer` | Read-only security reviewer that traces trust boundaries, sensitive data, authorization, and exploit paths in a scoped change. |
| subagent | `verifier` | Read-only verification specialist that runs declared tests, lint, builds, and focused reproductions and reports exact results. |
