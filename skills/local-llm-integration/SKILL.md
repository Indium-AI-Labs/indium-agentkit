---
name: local-llm-integration
description: "Deploy, optimize, and serve quantized open-weight local LLMs (vLLM/Ollama/llama.cpp) with GQA-aware VRAM pre-flight validation, process-scoped cleanup, and healthcheck polling."
---

# Local LLM Integration

Deploy, optimize, and serve open-weight local LLMs as a deterministic state machine using production serving engines (vLLM, Ollama, llama.cpp). Enforce strict I/O gatekeeping, GQA-aware pre-flight VRAM verification, process-scoped launches, OpenAI REST API bridging, constrained decoding, and TTFT SLA validation.

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
    "quant_bytes_per_param": 0.55,
    "context_length": 8192,
    "layers": 28,
    "kv_heads": 8,
    "head_dim": 128
  },
  "deployment_config": {
    "engine": "vLLM | Ollama | llama.cpp",
    "port": 8000,
    "max_batch_size": 4,
    "precision_bytes": 2
  }
}
```

## State Machine Execution Protocol

### Step 1: Hardware Discovery & GQA-Aware VRAM Verification Proof

1. Execute exact CLI discovery command for the target host platform:
   - **Linux CUDA**: `nvidia-smi --query-gpu=memory.total,memory.free --format=csv,noheader,nounits`
   - **macOS Metal**: `sysctl -n hw.memsize`
   - **Linux CPU/RAM Fallback**: `free -m`

2. Compute GQA-Aware (Grouped-Query Attention) VRAM Consumption:
   - `Weight_RAM_MB = (param_count_b * quant_bytes_per_param * 1024)`
   - `KV_Cache_MB = (2 * layers * kv_heads * head_dim * context_length * max_batch_size * precision_bytes) / (1024 * 1024)`
   - `Total_Required_MB = Weight_RAM_MB + KV_Cache_MB + 2048` (System safety buffer = 2048 MB)

3. **Pre-flight Gate Assertion**:
   - Evaluate `Total_Required_MB <= free_vram_mb`.
   - **If assertion fails**: Immediately abort execution, emit JSON error `{"status": "OOM_PREFLIGHT_FAIL", "required_mb": Total_Required_MB, "available_mb": free_vram_mb}`, and exit without spawning processes.

### Step 2: Process-Scoped Engine Launch

1. Launch background serving process bound to `127.0.0.1:<port>`:
   - **vLLM (Enterprise CUDA Server)**:
     ```bash
     vllm serve <model_id> \
       --port <port> \
       --host 127.0.0.1 \
       --gpu-memory-utilization 0.90 \
       --max-model-len <context_length> \
       --dtype float16 > /tmp/vllm_<port>.log 2>&1 &
     ```
   - **Ollama / llama.cpp (Edge / Desktop / Apple Silicon Metal)**:
     ```bash
     llama-server \
       -m <gguf_path> \
       -c <context_length> \
       --port <port> \
       --host 127.0.0.1 > /tmp/llama_<port>.log 2>&1 &
     ```

2. Capture process-scoped PID: `echo $! > /tmp/local_llm_<port>.pid`

### Step 3: OpenAI REST API Bridging & Constrained Decoding

1. Confirm loopback REST endpoint availability at `http://127.0.0.1:<port>/v1`.
2. Inject decoding sampler constraints into request payloads to prevent infinite token loops:
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

### Step 4: Healthcheck Polling & TTFT SLA Testing

1. **Healthcheck Readiness Polling Loop**:
   ```bash
   for i in $(seq 1 30); do
     status=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:<port>/v1/models)
     if [ "$status" -eq 200 ]; then break; fi
     sleep 1
   done
   ```
   Assert final `$status` equals `200`.

2. **TTFT SLA Benchmark**:
   ```bash
   curl -s -w "\nTTFT: %{time_starttransfer}s\nTOTAL: %{time_total}s\nHTTP: %{http_code}\n" \
     -X POST http://127.0.0.1:<port>/v1/chat/completions \
     -H "Content-Type: application/json" \
     -d '{"model": "<model_id>", "messages": [{"role": "user", "content": "ping"}], "max_tokens": 10}'
   ```
   Assert `time_starttransfer < 0.200` (Time-To-First-Token < 200ms SLA) and HTTP status == `200`.

### Step 5: Process-Scoped Failure Recovery & Rollback

If healthcheck polling times out, TTFT SLA fails, or CUDA OOM occurs:
1. Inspect tail of log file: `tail -n 50 /tmp/vllm_<port>.log`
2. Perform process-scoped termination:
   ```bash
   if [ -f /tmp/local_llm_<port>.pid ]; then kill -9 $(cat /tmp/local_llm_<port>.pid); fi
   pkill -9 -f "vllm.*<port>" || pkill -9 -f "llama-server.*<port>"
   ```
3. Remove stale PID file: `rm -f /tmp/local_llm_<port>.pid`
4. Return structured error object to the orchestrator.

## Guardrails

- Never launch engine processes without validating GQA-aware VRAM pre-flight math.
- Do not expose endpoints to public IP interfaces without authentication proxies.
- YAML frontmatter must contain strictly `name` and `description` fields to pass distribution validation.
- Optional `local-model-specialist` subagent can assist with quantization tuning, but single-agent execution must execute all steps end-to-end.

## Completion Report

Report `hardware_manifest` metrics, `model_spec` parameters, `deployment_config` choices, computed `Total_Required_MB` vs `free_vram_mb`, PID file location, loopback endpoint URL, healthcheck polling latency, TTFT SLA test metrics, and JSON output schema verification.
