---
name: llm-eval-harness
description: Design and execute evaluation benchmarks for prompts, RAG retrieval pipelines, and agent tools to measure cost, latency, accuracy, and guardrails.
---

# LLM Eval Harness

Design, execute, and analyze quantitative evaluation suites for Large Language Model (LLM) prompts, Retrieval-Augmented Generation (RAG) pipelines, function-calling agent tools, and safety guardrails across latency distributions, token costs, accuracy metrics, and RAG Triad benchmarks.

The skill is **quantitative and benchmark-validated**: golden evaluation datasets, deterministic schema assertions, semantic embedding similarity, RAG precision/recall, LLM-as-a-judge pairwise comparisons, and Statistical F1 Scores ($F1 = 2 \cdot \frac{P \cdot R}{P + R}$) are calculated and verified before reporting candidate model or prompt deployment readiness.

---

## 1. Required I/O Context Schemas & Natural Language Auto-Inference

The skill supports **two invocation modes**:

1. **🤖 Orchestrator / Technical Mode (JSON Manifest)**: Pass the JSON context manifest below.
2. **💬 Non-Technical Mode (Plain English Prompts)**: If the user provides a natural language prompt (e.g. *"Run a RAG evaluation benchmark comparing gpt-4o vs claude-3-5-sonnet on 100 customer support questions measuring faithfulness, relevance, and latency"*), the agent **must automatically infer and populate** `eval_type`, `candidate_models`, `golden_dataset_path`, and `target_metrics` from the user's text.

### JSON Context Manifest Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "LlmEvalHarnessContextManifest",
  "type": "object",
  "required": ["eval_spec", "dataset_config"],
  "properties": {
    "eval_spec": {
      "type": "object",
      "required": ["eval_type", "candidate_models"],
      "properties": {
        "eval_type": { 
          "type": "string", 
          "enum": ["prompt_regression", "rag_triad", "tool_calling_accuracy", "guardrail_safety", "model_comparison"],
          "default": "rag_triad"
        },
        "candidate_models": { "type": "array", "items": { "type": "string" }, "minItems": 1 },
        "judge_model": { "type": "string", "default": "claude-3-5-sonnet" },
        "sample_size": { "type": "integer", "default": 100 }
      }
    },
    "dataset_config": {
      "type": "object",
      "required": ["golden_dataset_path"],
      "properties": {
        "golden_dataset_path": { "type": "string" },
        "ground_truth_key": { "type": "string", "default": "expected_output" },
        "input_key": { "type": "string", "default": "user_query" }
      }
    },
    "target_metrics": {
      "type": "object",
      "properties": {
        "min_faithfulness_score": { "type": "number", "default": 0.85 },
        "min_answer_relevance_score": { "type": "number", "default": 0.85 },
        "max_p95_latency_ms": { "type": "integer", "default": 2500 },
        "max_cost_per_query_usd": { "type": "number", "default": 0.02 }
      }
    }
  }
}
```

### Automatic Natural Language Inference & Evaluation Safety Rules

If no raw JSON payload is provided, apply these defaults and strict evaluation safety rules:

- **No Secret/PII Leakage**: Golden evaluation datasets MUST NOT contain production API keys, passwords, or unmasked PII.
- **Statistical Significance**: Model comparison benchmarks MUST evaluate a minimum sample size of 50+ test cases to avoid prompt variance noise.
- **Judge Isolation**: When using LLM-as-a-judge, position swap inputs (A/B and B/A) to eliminate positional bias in judge evaluations.

---

## 2. Deterministic State Machine Execution Flow

Follow this exact sequential protocol. Do not skip steps or alter execution ordering.

### Step 1: Golden Dataset & Ground Truth Specification

1. Inspect dataset file (`evals/golden_dataset.json`, `.jsonl`, `.csv`).
2. Verify test sample schema: `user_query`, `reference_context` (for RAG), `expected_output` (ground truth), `allowed_tools` (for agents).

### Step 2: Evaluation Metric & Assertion Definition

Define evaluation metrics across three categories:
1. **Deterministic Assertions**: JSON schema validation, regex pattern matching, exact string match.
2. **RAG Triad Metrics**:
   - **Context Precision & Recall**: $P = \frac{|R \cap E|}{|R|}, R = \frac{|R \cap E|}{|E|}$.
   - **Faithfulness / Groundedness**: Ratio of claims in generated output supported by retrieved context.
   - **Answer Relevance**: Semantic embedding similarity between query and answer.
3. **Operational Telemetry**: Token consumption cost (Input + Output USD), $P_{50} / P_{95} / P_{99}$ latency distributions.

### Step 3: Benchmark Execution & Concurrent Invocation

1. Run candidate models against golden dataset samples concurrently.
2. Record model responses, token counts (`prompt_tokens`, `completion_tokens`), and response latencies ($t_{\text{response}} - t_{\text{request}}$).

### Step 4: LLM-as-a-Judge Pairwise Scoring & Position Swap

1. Prompt judge model with structured evaluation rubric (score 1–5).
2. Perform Position Swap (run Candidate A vs B, then Candidate B vs A) to neutralize LLM judge ordering bias.

---

## 3. Reference Implementation: Python RAG Triad Evaluation Harness

```python
import json
import math
import time
from typing import List, Dict, Any

def compute_cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """Calculate Cosine Similarity between two embedding vectors."""
    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot_product / (norm_a * norm_b)

class RagEvaluator:
    """Quantitative RAG Evaluation Harness measuring Faithfulness & Latency."""
    
    def __init__(self, target_faithfulness: float = 0.85):
        self.target_faithfulness = target_faithfulness

    def evaluate_sample(
        self, query: str, context: str, response: str, ground_truth: str
    ) -> Dict[str, Any]:
        t0 = time.time()
        
        # 1. Simple Token Overlap Faithfulness Approximation (Grounding Check)
        context_words = set(context.lower().split())
        response_words = response.lower().split()
        
        if not response_words:
            faithfulness = 0.0
        else:
            supported_words = sum(1 for w in response_words if w in context_words)
            faithfulness = min(1.0, supported_words / len(response_words))
            
        latency_ms = (time.time() - t0) * 1000.0
        
        return {
            "query": query,
            "faithfulness_score": round(faithfulness, 4),
            "latency_ms": round(latency_ms, 2),
            "pass_faithfulness": faithfulness >= self.target_faithfulness
        }

if __name__ == "__main__":
    evaluator = RagEvaluator(target_faithfulness=0.80)
    res = evaluator.evaluate_sample(
        query="What is the port for Redis?",
        context="Redis default port is 6379 for standard connections.",
        response="The default port for Redis is 6379.",
        ground_truth="6379"
    )
    print(f"Evaluation Result: {json.dumps(res, indent=2)}")
```

---

## 4. Evaluation Formulas & RAG Triad Invariants

### 1. Retrieval Precision ($P$) & Recall ($R$)

$$P = \frac{|\text{Relevant Context} \cap \text{Retrieved Context}|}{|\text{Retrieved Context}|}$$

$$R = \frac{|\text{Relevant Context} \cap \text{Retrieved Context}|}{|\text{Relevant Context}|}$$

### 2. Statistical F1 Score

$$F1 = 2 \cdot \frac{\text{Precision} \cdot \text{Recall}}{\text{Precision} + \text{Recall}}$$

### 3. Cosine Semantic Similarity

$$\text{Sim}(A, B) = \frac{A \cdot B}{\|A\| \|B\|} = \frac{\sum_{i=1}^n A_i B_i}{\sqrt{\sum_{i=1}^n A_i^2} \sqrt{\sum_{i=1}^n B_i^2}}$$

---

## 5. Guardrails

### Operational Restrictions

- **Judge Bias Neutralization**: Always run position swap (A/B and B/A) when using LLM-as-a-judge scoring.
- **No Production Token Waste**: Use mock embeddings or local cached responses for rapid local evaluation loop testing before running full cloud LLM benchmark passes.
- **No Secret Leakage**: Sanitise all evaluation dataset inputs to ensure zero API keys or credentials are present.

---

## 6. Atomic Failure Recovery & Rollback Handler

If an evaluation run encounters API timeouts or network errors:

```bash
# Clean up temporary eval results and partial JSON reports
rm -f temp_eval_run_*.json 2>/dev/null
```

---

## 7. Verification Plan & Toolchain Commands

Execute evaluation harness:

```bash
# 1. Run custom RAG eval harness script
python3 evals/run_rag_eval.py --dataset evals/golden_dataset.json

# 2. Run token telemetry and cost analyzer on eval logs
python3 scripts/analyze_token_telemetry.py --log-path evals/telemetry.json
```

---

## 8. Completion Report

Report evaluation scope, dataset sample size, candidate models evaluated, average Faithfulness, Context Precision/Recall, F1 score, $P_{50} / P_{95}$ latencies, total token costs (USD), and final model deployment recommendations.
