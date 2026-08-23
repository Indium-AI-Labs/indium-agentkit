# Changelog

All notable changes to this project are documented here.

## Unreleased

### Changed

- Refactored installation around explicit project/user scope, destination,
  target, and item selection so `add <name>` installs only the requested
  artifact and project installs never leak into user-level agent directories.
- Made npm installs durable copies by default, aligned project-context files
  with the selected agent architecture, and made target auto-detection fail
  closed when no agent directory exists.
- Consolidated validation and installer smoke tests into one cancellable CI
  workflow; the Windows smoke job now runs only for installer-related changes.

### Added

- Codex delegation guidance and a dependency-free delegation packet adapter.
- Deployment-safety, CI-pipeline, incident-triage, and infrastructure-review
  workflows.
- Release-engineer, CI-verifier, and incident-commander specialist agents.
- Frontend, backend API, and database-design implementation workflows.
- Specialist frontend-builder, backend-builder, and database-architect agents.
- Shared feature, API, migration, and verification handoff templates with
  structural validation.
- Per-item skill and subagent installation with installation diagnostics.
- Content scaffolding and catalog tooling.
- Planning, merge-conflict, migration, security-review, and release-note skills.
- Migration-planning, security-review, and performance-profiling subagents.
- Compatibility, security, and release guidance with installer smoke-test CI.
