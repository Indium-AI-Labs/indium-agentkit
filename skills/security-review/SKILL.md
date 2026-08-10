---
name: security-review
description: "Review a scoped code change, endpoint, integration, configuration, or infrastructure definition for security risks by tracing assets, trust boundaries, authorization, input handling, and exploit paths."
---

# Security review

1. Define the scope, assets, attackers, trust boundaries, and security-relevant assumptions.
2. Trace untrusted input to sensitive sinks, and trace authorization from identity to protected action.
3. Check secrets handling, authentication, authorization, logging, error disclosure, cryptography, dependency use, and infrastructure permissions as relevant to the scope.
4. Prioritize exploitable, evidenced issues over generic advice. Do not claim compliance or absence of vulnerabilities.
5. Report each finding with severity, affected location, exploit conditions, impact, remediation direction, and verification needed.
6. Keep review mode read-only unless the user explicitly asks for remediation. Use an independent security reviewer as an optional second pass for high-risk changes.
