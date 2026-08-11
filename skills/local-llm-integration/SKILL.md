---
name: local-llm-integration
description: "Deploy, optimize, and serve quantized local LLMs using vLLM or Ollama runtimes. Use when a project requires on-premise inference, zero data egress, offline air-gapped security, or predictable local inference performance."
---

# Local LLM Integration

Deploy, optimize, and serve quantized open-weight local LLMs (e.g., Llama, Qwen, DeepSeek) using production inference engines (vLLM, Ollama, llama.cpp). Enforce deterministic pre-flight VRAM bounds, OpenAI-compatible API bridging, constrained output decoding, and performance SLA validation.

## Workflow

1. **Environment Pre-flight & VRAM Math**:
   - Inspect target system hardware (total VRAM, unified RAM for Apple Silicon, CUDA compute capability).
   - Calculate total memory requirement: `VRAM_Required = Model_Weights_GB + (2 * Layers * Heads * Head_Dim * Context_Len * Batch_Size * Precision_Bytes) + System_Buffer_GB`.
   - **Fail-safe Abort**: If `VRAM_Required` exceeds `hardware_manifest` capacity, stop execution immediately, dump memory breakdown, and exit without launching processes.

2. **Inference Engine Selection**:
   - **vLLM Engine (Enterprise / High-Throughput)**: Mandated for multi-user CUDA server deployments requiring PagedAttention, continuous batching, and high request concurrency (P99 latency < 100ms).
   - **Ollama / llama.cpp Engine (Edge / Desktop / Apple Silicon)**: Selected for single-user pilots, workstation development, or Metal-accelerated unified memory architectures.

3. **Engine Memory & Runtime Bounds**:
   - Set explicit GPU memory fraction (e.g., `gpu_memory_utilization=0.90` for vLLM).
   - Clamp context window length (`max_model_len` / `n_ctx`) to prevent KV cache exhaustion during long generations.
   - Enable tensor parallelism (`tensor_parallel_size`) across multi-GPU setups if model weight size exceeds single-GPU VRAM.

4. **OpenAI-Compatible REST API Bridging**:
   - Configure serving daemon to bind to local loopback (e.g., `http://localhost:8000/v1` or `http://localhost:11434/v1`).
   - Standardize endpoint routing to expose `/v1/models` and `/v1/chat/completions`, enabling drop-in replacement for cloud API clients without codebase rewrites.

5. **Constrained Decoding & Sampler Protection**:
   - Enforce GBNF (GGML Backus-Naur Form) or JSON Schema grammars directly at the engine sampler level for structured outputs.
   - Configure decoding safety limits (temperature, top_p, repetition penalty, max tokens) to prevent infinite token loops and hallucination cascades.

6. **Validation Invariants & SLA Verification**:
   - Execute HTTP health check against `/v1/models` (must return HTTP 200).
   - Run synthetic test prompt to measure Time-To-First-Token (TTFT < 200ms SLA) and output schema conformance.

7. **Atomic Fail-Safe & Rollback Handling**:
   - If port binding fails or startup triggers CUDA OOM errors, capture diagnostic logs, terminate all spawned background daemons, and restore pre-execution system configurations.

## Guardrails

- Never bypass VRAM pre-flight calculations or attempt unbuffered model loading.
- Do not expose local model endpoints beyond loopback (`127.0.0.1`) without explicit mTLS or RBAC authentication.
- An optional `local-model-specialist` subagent can assist with GGUF quantization selection or KV cache tuning, but single-agent execution must complete all workflow steps.

## Completion Report

Report target hardware manifest, engine selected (vLLM vs Ollama), model parameters & quantization level, VRAM headroom, loopback API endpoint, TTFT SLA test results, and schema adherence verification.
