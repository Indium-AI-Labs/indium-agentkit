---
name: systematic-debugging
description: "Investigate a bug, failing test, regression, unexpected output, or production issue through reproduction, evidence, hypotheses, root-cause analysis, and a regression test before fixing it."
---

# Systematic debugging

1. State the observed behavior, expected behavior, impact, and available evidence.
2. Build the smallest reliable reproduction or failing signal. Record the exact command, inputs, environment assumptions, and result.
3. Read the relevant code path and trace data or control flow from the observable failure toward its source. Redact secrets from logs and reports.
4. Form competing, falsifiable hypotheses. Prefer a targeted experiment over an intuitive patch.
5. Identify the root cause with evidence. If evidence is insufficient, say what is unknown and what would discriminate between hypotheses.
6. Add or update a regression test at a public behavior seam when the project has an applicable test harness.
7. Implement the smallest fix that addresses the cause, then run the reproduction and relevant verification commands again.
8. Report the cause, changed behavior, tests run, and remaining uncertainty. Use optional independent exploration only when it will accelerate evidence gathering.
