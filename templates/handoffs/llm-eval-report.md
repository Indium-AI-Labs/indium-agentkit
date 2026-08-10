# LLM evaluation report

## Scope

State the evaluation target (model, prompt version, RAG pipeline, or agent tool),
test dataset size, and environment configuration.

## Evaluation metrics

| Metric | Target | Baseline | Candidate | Status |
| --- | --- | --- | --- | --- |
| `metric name` | threshold | score | score | pass / fail |

## Test dataset performance

| Category | Sample count | Pass rate | Common failure modes |
| --- | --- | --- | --- |
| `category` | count | percentage | Failure summary |

## Cost and latency comparison

| Metric | Baseline | Candidate | Delta |
| --- | --- | --- | --- |
| Average latency | ms | ms | delta |
| p95 latency | ms | ms | delta |
| Cost per 1k requests | currency | currency | delta |

## Safety and guardrails

Report safety evaluation results: injection resilience, PII leakage, hallucination checks,
and toxic output filtering.

## Handoff

**Changed contract:** Describe any prompt, API, or behavioral output changes or state `none`.

**Files / systems affected:** List prompt templates, evaluation scripts, and model configs.

**Evidence and tests:** Summarize benchmark execution logs and evaluation results.

**Risks / rollback:** State risks of deploying the candidate model or prompt.

**What the next agent needs:** Recommended deployment parameters or follow-up iterations.
