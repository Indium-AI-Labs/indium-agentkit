# Indium Agentkit Architecture Map

Auto-generated architecture diagram depicting subagents, execution skills, and zero-trust RBAC boundaries.

```mermaid
flowchart TD
    classDef orchestrator fill:#2b3a4a,stroke:#4a90e2,stroke-width:2px,color:#ffffff;
    classDef subagent fill:#1e293b,stroke:#38bdf8,stroke-width:1.5px,color:#f8fafc;
    classDef skill fill:#0f172a,stroke:#34d399,stroke-width:1.5px,color:#f8fafc;
    classDef validator fill:#312e81,stroke:#818cf8,stroke-width:1.5px,color:#ffffff;

    subgraph CLI [User & Cursor / Claude IDE Layer]
        USER([Developer / Agent Client]):::orchestrator
        CLI_TOOLS[npm / cli.js / Cursor Rules]:::orchestrator
    end

    subgraph Subagents [Zero-Trust Read-Only Subagents (agents/)]
        AGENT_accessibility_checker["🤖 accessibility-checker<br/><i>Read-only accessibility specialist that evaluates markup, ARIA usage, color contrast, keyboard flow, and screen reader compatibility.</i><br/><small>Tools: Read, Grep, Glob, Bash</small>"]:::subagent
        AGENT_agent_orchestrator["🤖 agent-orchestrator<br/><i>Read-only specialist that inspects multi-agent system states, JSON-RPC routing boundaries, context window growth, and delegation chains to prevent execution loops and payload bloat.</i><br/><small>Tools: Read, Grep, Glob, Bash</small>"]:::subagent
        AGENT_api_designer["🤖 api-designer<br/><i>Design typed API contracts from requirements without editing code.</i><br/><small>Tools: Read, Grep, Glob, Bash</small>"]:::subagent
        AGENT_backend_builder["🤖 backend-builder<br/><i>Implement scoped typed API behavior with server-side safeguards.</i><br/><small>Tools: Read, Grep, Glob, Bash</small>"]:::subagent
        AGENT_ci_verifier["🤖 ci-verifier<br/><i>Diagnose CI workflows and report exact verification evidence.</i><br/><small>Tools: Read, Grep, Glob, Bash</small>"]:::subagent
        AGENT_compliance_auditor["🤖 compliance-auditor<br/><i>Read-only compliance specialist that audits code, data flows, PII redaction, encryption, and audit logs against compliance control standards.</i><br/><small>Tools: Read, Grep, Glob, Bash</small>"]:::subagent
        AGENT_data_engineer["🤖 data-engineer<br/><i>Audit data pipelines, models, quality, and governance read-only.</i><br/><small>Tools: Read, Grep, Glob, Bash</small>"]:::subagent
        AGENT_database_architect["🤖 database-architect<br/><i>Analyze schemas and propose safe, verified migration plans.</i><br/><small>Tools: Read, Grep, Glob, Bash</small>"]:::subagent
        AGENT_dependency_auditor["🤖 dependency-auditor<br/><i>Audit dependency vulnerabilities, staleness, and license risk read-only.</i><br/><small>Tools: Read, Grep, Glob, Bash</small>"]:::subagent
        AGENT_doc_writer["🤖 doc-writer<br/><i>Read-only documentation specialist that analyzes code, tests, and history to draft accurate project documentation.</i><br/><small>Tools: Read, Grep, Glob, Bash</small>"]:::subagent
        AGENT_ebpf_specialist["🤖 ebpf-specialist<br/><i>Audit eBPF bytecode, XDP packet processing programs, eBPF maps, and kernel-level tracing probes for safety, side effects, and verifier bounds read-only.</i><br/><small>Tools: Read, Grep, Glob, Bash</small>"]:::subagent
        AGENT_estimator["🤖 estimator<br/><i>Read-only estimation specialist that analyzes scope, complexity, dependencies, and risk to produce effort assessments.</i><br/><small>Tools: Read, Grep, Glob, Bash</small>"]:::subagent
        AGENT_explorer["🤖 explorer<br/><i>Read-only codebase explorer that maps relevant files, control flow, conventions, and uncertainties for a focused task.</i><br/><small>Tools: Read, Grep, Glob, Bash</small>"]:::subagent
        AGENT_formal_verifier["🤖 formal-verifier<br/><i>Evaluate formal specifications (TLA+, Alloy, Dafny), state space invariants, temporal logic properties, and mathematical proofs read-only.</i><br/><small>Tools: Read, Grep, Glob, Bash</small>"]:::subagent
        AGENT_frontend_builder["🤖 frontend-builder<br/><i>Implement scoped accessible UI features from agreed contracts.</i><br/><small>Tools: Read, Grep, Glob, Bash</small>"]:::subagent
        AGENT_incident_commander["🤖 incident-commander<br/><i>Coordinate evidence-based incident response without production edits.</i><br/><small>Tools: Read, Grep, Glob, Bash</small>"]:::subagent
        AGENT_iot_embedded_auditor["🤖 iot-embedded-auditor<br/><i>Audit RTOS task scheduling, firmware update routines, memory layout, and peripheral hardware interfaces read-only.</i><br/><small>Tools: Read, Grep, Glob, Bash</small>"]:::subagent
        AGENT_llm_evaluator["🤖 llm-evaluator<br/><i>Read-only LLM evaluation specialist that inspects prompt definitions, RAG retrieval logic, benchmark datasets, and guardrails.</i><br/><small>Tools: Read, Grep, Glob, Bash</small>"]:::subagent
        AGENT_local_model_specialist["🤖 local-model-specialist<br/><i>Evaluate on-device LLM integration, GGUF quantization levels, and KV cache memory constraints read-only.</i><br/><small>Tools: Read, Grep, Glob, Bash</small>"]:::subagent
        AGENT_migration_planner["🤖 migration-planner<br/><i>Read-only migration planner that inventories compatibility impact, rollout stages, rollback paths, and verification for schema, API, configuration, or file-format changes.</i><br/><small>Tools: Read, Grep, Glob, Bash</small>"]:::subagent
        AGENT_mobile_specialist["🤖 mobile-specialist<br/><i>Read-only mobile specialist that inspects build configurations, permission manifests, native bridges, bundle sizes, and store submission readiness.</i><br/><small>Tools: Read, Grep, Glob, Bash</small>"]:::subagent
        AGENT_performance_profiler["🤖 performance-profiler<br/><i>Measure performance bottlenecks against a reproducible baseline.</i><br/><small>Tools: Read, Grep, Glob, Bash</small>"]:::subagent
        AGENT_release_engineer["🤖 release-engineer<br/><i>Prepare release plans and assess deployment readiness.</i><br/><small>Tools: Read, Grep, Glob, Bash</small>"]:::subagent
        AGENT_resilience_reviewer["🤖 resilience-reviewer<br/><i>Review failure handling, retries, limits, and recovery paths read-only.</i><br/><small>Tools: Read, Grep, Glob, Bash</small>"]:::subagent
        AGENT_reviewer["🤖 reviewer<br/><i>Read-only independent reviewer for a completed diff, branch, or pull request who reports actionable findings with evidence.</i><br/><small>Tools: Read, Grep, Glob, Bash</small>"]:::subagent
        AGENT_runbook_writer["🤖 runbook-writer<br/><i>Draft evidence-backed operational runbooks from system behavior.</i><br/><small>Tools: Read, Grep, Glob, Bash</small>"]:::subagent
        AGENT_security_reviewer["🤖 security-reviewer<br/><i>Review scoped changes for trust-boundary and exploit-path risks.</i><br/><small>Tools: Read, Grep, Glob, Bash</small>"]:::subagent
        AGENT_synthetic_data_architect["🤖 synthetic-data-architect<br/><i>Audit relational database topologies, foreign key constraints, and statistical distributions to design referentially intact, PII-free synthetic data schemas read-only.</i><br/><small>Tools: Read, Grep, Glob, Bash</small>"]:::subagent
        AGENT_verifier["🤖 verifier<br/><i>Read-only verification specialist that runs declared tests, lint, builds, and focused reproductions and reports exact results.</i><br/><small>Tools: Read, Grep, Glob, Bash</small>"]:::subagent
    end

    subgraph Skills [Contract-First Execution Skills (skills/)]
        SKILL_accessibility_audit["⚡ accessibility-audit<br/><i>Audit a user interface for WCAG conformance, keyboard operability, screen reader compatibility, color contrast, and inclusive design, reporting findings with severity and remediation.</i>"]:::skill
        SKILL_api_design["⚡ api-design<br/><i>Design an API contract — resources, operations, schemas, errors, versioning, and pagination — from requirements before implementation, producing a completed api-contract handoff.</i>"]:::skill
        SKILL_ast_manipulation_codemods["⚡ ast-manipulation-codemods<br/><i>Write Abstract Syntax Tree (AST) transformers to automate large-scale, syntax-aware codebase migrations.</i>"]:::skill
        SKILL_author_agentkit_content["⚡ author-agentkit-content<br/><i>Create or update indium-agentkit skills, subagents, templates, validation, and documentation. Use when adding, revising, validating, or publishing content in this distribution repository.</i>"]:::skill
        SKILL_backend_api["⚡ backend-api<br/><i>Build robust typed API endpoints with safe contracts.</i>"]:::skill
        SKILL_ci_pipeline["⚡ ci-pipeline<br/><i>Design reliable CI pipelines with useful required checks.</i>"]:::skill
        SKILL_compliance_audit["⚡ compliance-audit<br/><i>Audit code, configuration, and data flows against GDPR, SOC 2, HIPAA, and PCI-DSS compliance controls including PII redaction and audit logging.</i>"]:::skill
        SKILL_contract_testing["⚡ contract-testing<br/><i>Design and implement consumer-driven contract tests (Pact, MSW, Playwright) to verify interface compatibility between microservices and frontend/backend boundaries.</i>"]:::skill
        SKILL_cryptographic_protocol_implementation["⚡ cryptographic-protocol-implementation<br/><i>Implement modern authenticated encryption, secure key exchange, mTLS, and post-quantum cryptographic primitives.</i>"]:::skill
        SKILL_data_pipeline_design["⚡ data-pipeline-design<br/><i>Design safe ETL/ELT pipelines, data warehouse schemas, partition strategies, idempotency controls, and data quality assertions before implementation.</i>"]:::skill
        SKILL_database_design["⚡ database-design<br/><i>Design safe PostgreSQL schemas and staged migrations.</i>"]:::skill
        SKILL_delegate_work["⚡ delegate-work<br/><i>Plan bounded Codex subagent delegation with structured handoffs.</i>"]:::skill
        SKILL_dependency_audit["⚡ dependency-audit<br/><i>Audit project dependencies for vulnerabilities, staleness, license risk, unused packages, and version-policy compliance using manifests, lockfiles, and available scanning tools.</i>"]:::skill
        SKILL_deployment_safety["⚡ deployment-safety<br/><i>Plan and verify staged deployments with safe rollback.</i>"]:::skill
        SKILL_estimate_work["⚡ estimate-work<br/><i>Break down a feature, fix, or change into estimated effort with scope, risk factors, assumptions, and sequencing before prioritization.</i>"]:::skill
        SKILL_event_sourcing_architecture["⚡ event-sourcing-architecture<br/><i>Design immutable event logs, CQRS command/query models, and materialized view projections.</i>"]:::skill
        SKILL_frontend_ship["⚡ frontend-ship<br/><i>Build accessible, typed, expressive, glassmorphic, and 3D frontend features end to end.</i>"]:::skill
        SKILL_hardware_in_loop_testing["⚡ hardware-in-loop-testing<br/><i>Interface hardware-in-the-loop (HIL) simulation testbeds with embedded firmware endpoints under noise and faults.</i>"]:::skill
        SKILL_incident_triage["⚡ incident-triage<br/><i>Triage incidents with evidence, mitigation, and follow-up.</i>"]:::skill
        SKILL_infrastructure_review["⚡ infrastructure-review<br/><i>Review infrastructure for security, reliability, and cost risks.</i>"]:::skill
        SKILL_llm_eval_harness["⚡ llm-eval-harness<br/><i>Design and execute evaluation benchmarks for prompts, RAG retrieval pipelines, and agent tools to measure token cost, latency, accuracy, and guardrail compliance.</i>"]:::skill
        SKILL_load_testing_suite["⚡ load-testing-suite<br/><i>Design, configure, and execute load and stress testing suites (k6, Locust) with target latency SLAs, throughput targets, and tear-down verification.</i>"]:::skill
        SKILL_local_llm_integration["⚡ local-llm-integration<br/><i>Deploy, optimize, and serve quantized open-weight local LLMs (vLLM/Ollama/llama.cpp) with GQA-aware VRAM pre-flight validation, process-scoped cleanup, and healthcheck polling.</i>"]:::skill
        SKILL_mobile_release_safety["⚡ mobile-release-safety<br/><i>Plan and audit mobile application releases (iOS/Android/React Native/Flutter) covering app store submission requirements, code signing, feature flags, OTA updates, and crash reporting.</i>"]:::skill
        SKILL_multi_agent_workflow_design["⚡ multi-agent-workflow-design<br/><i>Design typed state machines, JSON-RPC handoff protocols, and delegation topologies for multi-agent execution.</i>"]:::skill
        SKILL_observability_setup["⚡ observability-setup<br/><i>Instrument code with structured logging, metrics, distributed tracing, or alerting following existing observability patterns and avoiding credential exposure.</i>"]:::skill
        SKILL_onboard_to_codebase["⚡ onboard-to-codebase<br/><i>Generate a developer onboarding guide or codebase orientation by analyzing architecture, conventions, dependencies, workflows, and common tasks from the existing project.</i>"]:::skill
        SKILL_performance_optimization["⚡ performance-optimization<br/><i>Measure, analyze, and optimize a specific performance bottleneck through profiling, targeted change, and comparative re-measurement with evidence.</i>"]:::skill
        SKILL_plan_change["⚡ plan-change<br/><i>Turn a feature request, bug report, refactor, or technical proposal into an implementation-ready plan with scope, acceptance criteria, affected areas, test seams, risks, and ordered steps.</i>"]:::skill
        SKILL_prototype_spike["⚡ prototype-spike<br/><i>Investigate a technical approach through a time-boxed, throwaway spike that produces evidence and a go-or-no-go recommendation before committing to a design.</i>"]:::skill
        SKILL_refactor_code["⚡ refactor-code<br/><i>Restructure, rename, extract, inline, or simplify code to improve clarity, cohesion, or maintainability while preserving observable behavior, verified by the existing test suite.</i>"]:::skill
        SKILL_release_notes["⚡ release-notes<br/><i>Create accurate user-facing release notes or changelog entries from a commit range, tags, issues, and repository history, including breaking changes, migrations, and known limitations.</i>"]:::skill
        SKILL_resolve_merge_conflicts["⚡ resolve-merge-conflicts<br/><i>Resolve Git merge or rebase conflicts by recovering each side's intent, preserving compatible behavior, validating the result, and documenting unavoidable trade-offs.</i>"]:::skill
        SKILL_review_change["⚡ review-change<br/><i>Review a local diff, branch, commit range, or pull request for correctness, regressions, security concerns, project conventions, and missing tests. Use when asked for a code review; report findings without editing by default.</i>"]:::skill
        SKILL_rtos_firmware_development["⚡ rtos-firmware-development<br/><i>Write deterministic, low-latency task schedulers and peripheral drivers for embedded FreeRTOS/Zephyr devices.</i>"]:::skill
        SKILL_safe_migration["⚡ safe-migration<br/><i>Plan and implement safe schema, API, configuration, storage, or file-format migrations with compatibility analysis, staged rollout, rollback, and evidence-based verification.</i>"]:::skill
        SKILL_security_review["⚡ security-review<br/><i>Review a scoped code change, endpoint, integration, configuration, or infrastructure definition for security risks by tracing assets, trust boundaries, authorization, input handling, and exploit paths.</i>"]:::skill
        SKILL_synthetic_data_generation["⚡ synthetic-data-generation<br/><i>Implement deterministic scripts to populate databases with referentially solid, PII-free data.</i>"]:::skill
        SKILL_systematic_debugging["⚡ systematic-debugging<br/><i>Investigate a bug, failing test, regression, unexpected output, or production issue through reproduction, evidence, hypotheses, root-cause analysis, and a regression test before fixing it.</i>"]:::skill
        SKILL_test_first_change["⚡ test-first-change<br/><i>Plan and implement a behavior change, bug fix, or refactor with focused behavior-level tests, public seams, and incremental red-green-refactor cycles. Use when writing or changing production code.</i>"]:::skill
        SKILL_threat_modeling["⚡ threat-modeling<br/><i>Perform structured threat modeling (STRIDE/PASTA) on architecture diagrams, system interfaces, and data flow graphs before implementation.</i>"]:::skill
        SKILL_verify_and_ship["⚡ verify-and-ship<br/><i>Verify a completed repository change, run declared tests and lint, inspect the diff for generated artifacts or secrets, and commit and publish only when repository policy or the user authorizes it. Use before finishing or shipping work.</i>"]:::skill
        SKILL_write_documentation["⚡ write-documentation<br/><i>Author, update, or audit project documentation — READMEs, architecture decisions, API references, onboarding guides, and inline doc — from code evidence without inventing behavior.</i>"]:::skill
        SKILL_write_runbook["⚡ write-runbook<br/><i>Create or update an operational runbook for a service, feature, or failure mode with detection, diagnosis, mitigation, recovery, and escalation procedures.</i>"]:::skill
    end

    subgraph Validation [Validation & Catalog Pipeline]
        V_CONTENT["validate_content.py"]:::validator
        V_RBAC["validate_rbac_schema.py"]:::validator
        V_CATALOG["generate_catalog.py"]:::validator
    end

    USER --> CLI_TOOLS
    CLI_TOOLS --> Subagents
    CLI_TOOLS --> Skills
    Subagents -. Delegate Context .-> Skills
    Skills --> Validation
    Subagents --> Validation
```
