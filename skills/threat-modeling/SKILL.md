---
name: threat-modeling
description: "Perform structured threat modeling (STRIDE/PASTA) on architecture diagrams, system interfaces, and data flow graphs before implementation."
---

# Threat modeling

Identify security threats, attack vectors, trust boundaries, and mitigation controls
prior to feature development or architectural overhaul. Use STRIDE (Spoofing, Tampering,
Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege) as the
baseline taxonomy.

## Workflow

1. Read `AGENTS.md`, system architecture documentation, data flow diagrams, API specs,
   and auth models. Map key assets, data stores, external dependencies, and trust boundaries.
2. Identify trust boundaries: boundaries where data passes between different levels of
   trust (e.g. browser to web server, web server to DB, internal service to third-party API).
3. Enumerate threats across each trust boundary using STRIDE:
   - **Spoofing**: Can an attacker impersonate a user or service?
   - **Tampering**: Can data in transit or at rest be modified unauthorized?
   - **Repudiation**: Can a user perform an action without audit trail proof?
   - **Information Disclosure**: Can sensitive data be leaked or exposed?
   - **Denial of Service**: Can resources be exhausted or rendered unavailable?
   - **Elevation of Privilege**: Can an unprivileged user gain admin control?
4. Rate threat likelihood and impact using CVSS or DREAD scoring to prioritize risk.
5. Formulate concrete mitigation controls for each threat (e.g. mTLS, request signing,
   rate limiting, role-based access control, input sanitization).
6. Document residual risk and required follow-up verification tests.
7. Record findings in `templates/handoffs/threat-model.md` or equivalent project artifact.

## Guardrails

- Focus on actionable threats backed by architectural evidence; avoid speculative
  or irrelevant vulnerability scenarios.
- Do not execute penetration tests or exploits against live systems.
- An optional security-reviewer subagent can inspect data flow graphs, but one agent can
  complete this workflow independently.

## Completion report

Report assets mapped, trust boundaries evaluated, threats enumerated by STRIDE category,
risk ratings, proposed mitigations, and residual risks.
