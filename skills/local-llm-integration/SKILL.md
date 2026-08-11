---
name: local-llm-integration
description: "Deploy, optimize, and serve quantized local LLMs using vLLM or Ollama runtimes. Use when a project requires on-premise inference, zero data egress, offline air-gapped security, or predictable local inference performance."
---

# Local LLM Integration

Deploy, optimize, and serve open-weight local LLMs (Llama, Qwen, DeepSeek) as a deterministic state machine using production serving engines (vLLM, Ollama, llama.cpp). Enforce strict I/O gatekeeping, mathematical pre-flight VRAM verification, exact CLI commands, OpenAI REST API bridging, constrained decoding, and TTFT SLA validation.

## Required I/O Context Schemas

Before execution, inspect and populate the following context objects:

```json
{
  "hardware_manifest": {
    "platform": "cuda | metal | cpu",
    "total_vram_mb": 24576,
    "free_vram_mb": 22000,
    "cuda_compute_capability": "8.9"
  },
  "model_spec": {
    "model_id": "Qwen/Qwen2.5-Coder-7B-Instruct-GGUF",
    "param_count_b": 7.61,
    "quant_type": "Q4_K_M",
    "context_length": 8192,
    "layers": 28,
    "heads": 28,
    "head_dim": 128
  }
}
```

## State Machine Execution Protocol

### Step 1: Hardware Discovery & Deterministic VRAM Proof

1. Run exact CLI discovery command based on host architecture:
   - **Linux CUDA**: `nvidia-smi --query-gpu=memory.total,memory.free --format=csv,noheader,nounits`
   - **macOS Metal**: `sysctl -n hw.memsize`
   - **Linux CPU/RAM Fallback**: `free -m`

2. Compute deterministic VRAM consumption:
   - `Weight_RAM_MB = (param_count_b * quant_bytes_per_param * 1024)` (e.g. Q4_K_M = 0.55 bytes/param -> 7.61 * 0.55 * 1024 = 4286 MB)
   - `KV_Cache_MB = (2 * layers * heads * head_dim * context_length * batch_size * precision_bytes) / (1024 * 1024)` (Precision = 2 for FP16)
   - `Total_Required_MB = Weight_RAM_MB + KV_Cache_MB + 2048` (System safety buffer = 2048 MB)

3. **Pre-flight Gate Assertion**:
   - Evaluate `Total_Required_MB <= free_vram_mb`.
   - **If assertion fails**: Immediately abort execution, emit JSON error `{"status": "OOM_PREFLIGHT_FAIL", "required_mb": Total_Required_MB, "available_mb": free_vram_mb}`, and exit without spawning processes.

### Step 2: Engine Selection & Daemon Launch

1. Select execution binary based on hardware and concurrency targets:
   - **Path A: Enterprise CUDA Multi-User Server (vLLM)**:
     ```bash
     vllm serve <model_id> \
       --port 8000 \
       --host 127.0.0.1 \
       --gpu-memory-utilization 0.90 \
       --max-model-len <context_length> \
       --dtype float16 > /tmp/vllm_daemon.log 2>&1 &
     ```
   - **Path B: Edge / Desktop / Apple Silicon Metal (Ollama or llama.cpp)**:
     ```bash
     llama-server \
       -m <gguf_path> \
       -c <context_length> \
       --port 11434 \
       --host 127.0.0.1 > /tmp/llama_daemon.log 2>&1 &
     ```

2. Capture process PID: `echo $! > /tmp/local_llm_daemon.pid`

### Step 3: OpenAI API Bridging & Constrained Decoding Setup

1. Verify loopback API listener binding: `http://127.0.0.1:8000/v1` or `http://127.0.0.1:11434/v1`.
2. Configure sampler constraints in request templates to eliminate token repetition loops:
   ```json
   {
     "model": "<model_id>",
     "temperature": 0.2,
     "top_p": 0.9,
     "repetition_penalty": 1.1,
     "max_tokens": 2048,
     "response_format": {
       "type": "json_object"
     }
   }
   ```

### Step 4: Validation Invariants & TTFT SLA Testing

1. **HTTP Health Check**:
   ```bash
   curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/v1/models
   ```
   Assert returned status code equals `200`.

2. **TTFT SLA Benchmark**:
   ```bash
   curl -s -w "\nTTFT: %{time_starttransfer}s\nTOTAL: %{time_total}s\nHTTP: %{http_code}\n" \
     -X POST http://127.0.0.1:8000/v1/chat/completions \
     -H "Content-Type: application/json" \
     -d '{"model": "<model_id>", "messages": [{"role": "user", "content": "ping"}], "max_tokens": 10}'
   ```
   Assert `time_starttransfer < 0.200` (Time-To-First-Token < 200ms SLA) and HTTP status == `200`.

### Step 5: Atomic Failure Recovery & Rollback Handler

If any verification assertion fails or CUDA OOM is detected in `/tmp/vllm_daemon.log`:
1. Read diagnostic tail: `tail -n 50 /tmp/vllm_daemon.log`
2. Terminate daemon process:
   ```bash
   if [ -f /tmp/local_llm_daemon.pid ]; then kill -9 $(cat /tmp/local_llm_daemon.pid); fi
   pkill -9 -f "vllm" || pkill -9 -f "llama-server"
   ```
3. Remove temporary PID files: `rm -f /tmp/local_llm_daemon.pid`
4. Return structured error summary to the orchestrator.

## Guardrails

- Never execute model loading without verifying the deterministic VRAM math proof.
- Do not bind serving endpoints to external interfaces (`0.0.0.0`) without explicit auth proxies.
- Frontmatter must contain strictly `name` and `description` fields to preserve distribution compatibility.
- An optional `local-model-specialist` subagent may assist with quantization choice, but single-agent execution must execute all steps end-to-end.

## Completion Report

Report `hardware_manifest` metrics, `model_spec` parameters, computed `Total_Required_MB` vs `free_vram_mb`, launched daemon PID, active loopback endpoint URL, HTTP health status, measured TTFT SLA timing, and structured JSON output validation proof.
