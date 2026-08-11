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
    "local_model_path": "/mnt/models/Qwen2.5-Coder-7B-Instruct-Q4_K_M.gguf",
    "param_count_b": 7.61,
    "quant_type": "gguf | awq | gptq | fp16",
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

### Step 1: Hardware Discovery & GQA VRAM Proof

1. Execute exact CLI discovery command based on target architecture:
   - **Linux CUDA**: `nvidia-smi --query-gpu=memory.total,memory.free --format=csv,noheader,nounits`
   - **macOS Metal**: `sysctl -n hw.memsize`
   - **Linux CPU/RAM Fallback**: `free -m`

2. Compute deterministic VRAM consumption using Grouped-Query Attention (GQA):
   - $VRAM_{weights\_mb} = \frac{param\_count\_b \times 10^9 \times quant\_bytes\_per\_param}{1024^2}$
   - $VRAM_{kv\_cache\_mb} = \frac{2 \times layers \times kv\_heads \times head\_dim \times context\_length \times max\_batch\_size \times precision\_bytes}{1024^2}$
   - $VRAM_{total\_mb} = VRAM_{weights\_mb} + VRAM_{kv\_cache\_mb} + 2048$ (System safety buffer = 2048 MB)

3. **Pre-flight Gate Assertion**:
   - Evaluate $VRAM_{total\_mb} \le free\_vram\_mb$.
   - **If assertion fails**: Abort execution immediately, emit JSON error `{"status": "OOM_PREFLIGHT_FAIL", "required_mb": VRAM_total_mb, "available_mb": free_vram_mb}`, and exit without spawning processes.

### Step 2: Engine Selection & Process-Scoped Launch

1. Initialize execution environment variables dynamically:
   ```bash
   PORT=<port>
   PID_FILE="/tmp/indium_llm_${PORT}.pid"
   LOG_FILE="/tmp/indium_llm_${PORT}.log"
   ```

2. Construct quantization parameters dynamically:
   - If `quant_type` is `"fp16"`, set `QUANT_FLAG=""`.
   - Otherwise, set `QUANT_FLAG="--quantization <quant_type>"`.

3. Launch background daemon bound to `127.0.0.1:<port>`:
   - **Path A: Enterprise CUDA Multi-User Server (vLLM)**:
     ```bash
     vllm serve <model_id> \
       --port <port> \
       --host 127.0.0.1 \
       ${QUANT_FLAG} \
       --gpu-memory-utilization 0.85 \
       --max-model-len <context_length> \
       --max-num-seqs <max_batch_size> \
       --guided-decoding-backend outlines > "${LOG_FILE}" 2>&1 &
     echo $! > "${PID_FILE}"
     ```
   - **Path B: Edge / Desktop / Apple Silicon Metal (llama.cpp)**:
     ```bash
     llama-server \
       -m <local_model_path> \
       -c <context_length> \
       -np <max_batch_size> \
       --port <port> \
       --host 127.0.0.1 > "${LOG_FILE}" 2>&1 &
     echo $! > "${PID_FILE}"
     ```

### Step 3: OpenAI API Bridging & Sampler Safeguards

1. Verify loopback REST endpoint listener binding at `http://127.0.0.1:<port>/v1`.
2. Inject default request template configurations into the client layer to prevent decoding loops:
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

### Step 4: Health Check Polling & TTFT SLA Testing

1. **HTTP Health Check Polling**:
   Execute a bounded retry loop to allow weight loading into VRAM (timeout after 60s):
   ```bash
   PORT=<port>
   TIMEOUT=60
   ELAPSED=0
   until [ "$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:${PORT}/v1/models)" = "200" ]; do
     if [ $ELAPSED -ge $TIMEOUT ]; then
       echo "HEALTHCHECK_TIMEOUT"
       exit 1
     fi
     sleep 2
     ELAPSED=$((ELAPSED + 2))
   done
   ```

2. **TTFT SLA Benchmark**:
   ```bash
   PORT=<port>
   curl -s -w "\nTTFT: %{time_starttransfer}s\nTOTAL: %{time_total}s\nHTTP: %{http_code}\n" \
     -X POST http://127.0.0.1:${PORT}/v1/chat/completions \
     -H "Content-Type: application/json" \
     -d '{"model": "<model_id>", "messages": [{"role": "user", "content": "ping"}], "max_tokens": 10}'
   ```
   Assert `time_starttransfer < 0.200` (Time-To-First-Token < 200ms SLA) and HTTP status equals `200`.

### Step 5: Process-Scoped Failure Recovery & Rollback Handler

If health checks time out, assertions fail, or CUDA OOM is detected in `${LOG_FILE}`:
1. Capture diagnostic log snippet: `tail -n 50 "${LOG_FILE}"`
2. Terminate the scoped process hierarchy cleanly:
   ```bash
   PORT=<port>
   PID_FILE="/tmp/indium_llm_${PORT}.pid"
   if [ -f "${PID_FILE}" ]; then
     TARGET_PID=$(cat "${PID_FILE}")
     pkill -9 -P "${TARGET_PID}" 2>/dev/null
     kill -9 "${TARGET_PID}" 2>/dev/null
     rm -f "${PID_FILE}"
   fi
   ```
3. Return structured error JSON to the orchestrator.

## Guardrails

- Never execute model loading without verifying the GQA VRAM math proof.
- Do not bind serving endpoints to external interfaces (`0.0.0.0`) without explicit authentication proxies.
- Process cleanup must be scoped strictly to the target instance PID file; global `pkill` calls are prohibited.
- YAML frontmatter must contain strictly `name` and `description` fields to pass distribution validation.

## Completion Report

Report `hardware_manifest` metrics, `model_spec` parameters, computed $VRAM_{total\_mb}$ vs $free\_vram\_mb$, instance PID, active loopback endpoint URL, HTTP health polling duration, measured TTFT SLA timing, and structured JSON output validation proof.
