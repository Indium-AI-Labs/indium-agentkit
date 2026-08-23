---
name: multi-agent-workflow-design
description: Design typed state machines, JSON-RPC handoff protocols, and delegation topologies for multi-agent execution.
---

# Multi-Agent Workflow Design

Design typed state machines, JSON-RPC schema contracts, token-budgeted context windows, dynamic routing graphs, and idempotent handoff protocols for coordinated execution across multiple autonomous AI agents (LangGraph, AutoGen, CrewAI, OpenAI Swarm, custom JSON-RPC routers).

The skill is **contract-first and deadlock-free**: agent interaction graphs, tool permissions, state payload schemas, delegation depth limits, and context window pruning rules are verified before implementation.

---

## 1. Required I/O Context Schemas & Natural Language Auto-Inference

The skill supports **two invocation modes**:

1. **🤖 Orchestrator / Technical Mode (JSON Manifest)**: Pass the JSON context manifest below.
2. **💬 Non-Technical Mode (Plain English Prompts)**: If the user provides a natural language prompt (e.g. *"Design a multi-agent workflow where an Architect delegates to a Coder and a Reviewer verifies the code in a loop"*), the agent **must automatically infer and populate** `orchestration_pattern`, `agent_roles`, `handoff_contract`, and `token_budget` from the user's text.

### JSON Context Manifest Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "MultiAgentWorkflowContextManifest",
  "type": "object",
  "required": ["topology_spec", "handoff_contract"],
  "properties": {
    "topology_spec": {
      "type": "object",
      "required": ["orchestration_pattern", "primary_orchestrator"],
      "properties": {
        "orchestration_pattern": { 
          "type": "string", 
          "enum": ["hierarchical_hub_spoke", "sequential_pipeline", "consensus_mesh", "state_machine_dag"] 
        },
        "primary_orchestrator": { "type": "string", "pattern": "^[a-z0-9-]+$" },
        "max_delegation_depth": { "type": "integer", "default": 5 }
      }
    },
    "agent_roles": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["agent_name", "domain", "permission_mode"],
        "properties": {
          "agent_name": { "type": "string" },
          "domain": { "type": "string", "enum": ["core_engineering", "security_compliance", "cloud_devops", "frontend_design", "ai_ml"] },
          "permission_mode": { "type": "string", "enum": ["read-only", "write-scoped"] },
          "allowed_tools": { "type": "array", "items": { "type": "string" } }
        }
      }
    },
    "handoff_contract": {
      "type": "object",
      "required": ["schema_version", "payload_format"],
      "properties": {
        "schema_version": { "type": "string", "default": "1.0.0" },
        "payload_format": { "type": "string", "enum": ["json_rpc_2", "typed_pydantic", "langgraph_state"] },
        "strict_validation": { "type": "boolean", "default": true }
      }
    },
    "token_budget": {
      "type": "object",
      "properties": {
        "max_context_tokens": { "type": "integer", "default": 128000 },
        "max_step_iterations": { "type": "integer", "default": 10 },
        "context_pruning_strategy": { "type": "string", "enum": ["sliding_window", "summarized_history", "selective_handoff"] }
      }
    }
  }
}
```

---

## 2. Deterministic State Machine Execution Flow

Follow this exact sequential protocol. Do not skip steps or alter execution ordering.

### Step 1: Context Ingestion & Topology Mapping

1. Read `AGENTS.md`, subagent prompt definitions in `agents/`, and existing multi-agent manifests.
2. Build the Directed Acyclic Graph (DAG) or finite state machine mapping all agent states, transition events, and delegation routes.
3. Validate that read-only specialist subagents (`permission_mode: read-only`) are never assigned mutating tools.

### Step 2: JSON-RPC Handoff Protocol & Schema Design

1. Define standardized JSON-RPC 2.0 or typed state handoff structures (`v1.0.0`):
   ```json
   {
     "jsonrpc": "2.0",
     "method": "agent_handoff",
     "params": {
       "version": "1.0.0",
       "source_agent": "agent-orchestrator",
       "target_agent": "backend-builder",
       "task_context": {
         "feature_name": "user-auth",
         "api_contract": { "endpoint": "/api/v1/auth" }
       },
       "visited_agents": ["agent-orchestrator"],
       "delegation_depth": 1
     },
     "id": "req-12345"
   }
   ```
2. Ensure every state transition explicitly validates input payloads against the agreed schema before invoking the target agent.

### Step 3: Deadlock & Circular Loop Prevention

1. Analyze the state transition matrix for potential infinite execution loops (e.g. `Coder` $\rightarrow$ `Reviewer` $\rightarrow$ `Coder` $\rightarrow$ `Reviewer` repeating indefinitely).
2. Enforce a hard `max_delegation_depth` ($\le 5$) and `max_step_iterations` ($\le 10$).
3. Maintain an immutable `visited_agents` tracking array in the shared context object. Abort with a `DEADLOCK_PREVENTED` error if a cyclic loop is detected without progress.

### Step 4: Token Budget & Context Window Optimization

1. Implement context window pruning: pass **only relevant state key-values** to target subagents instead of dumping full conversation logs.
2. Apply `selective_handoff` or `summarized_history` strategies to restrict token overhead per step.

---

## 3. Reference Implementation: Typed LangGraph State Machine

```typescript
import { z } from 'zod';

// 1. Shared State Schema
const AgentStateSchema = z.object({
  version: z.literal('1.0.0'),
  taskDescription: z.string(),
  activeAgent: z.string(),
  visitedAgents: z.array(z.string()),
  delegationDepth: z.number().max(5),
  artifacts: z.record(z.string(), z.unknown()),
  status: z.enum(['PENDING', 'IN_PROGRESS', 'NEEDS_REVIEW', 'COMPLETED', 'FAILED']),
  errorMessage: z.string().optional(),
});

type AgentState = z.infer<typeof AgentStateSchema>;

// 2. State Machine Node: Orchestrator
export async function orchestratorNode(state: AgentState): Promise<Partial<AgentState>> {
  if (state.delegationDepth >= 5) {
    return {
      status: 'FAILED',
      errorMessage: 'MAX_DELEGATION_DEPTH_EXCEEDED: Aborting to prevent infinite loop.',
    };
  }

  // Check if target is verified
  if (state.artifacts.verificationResult === 'PASSED') {
    return { status: 'COMPLETED', activeAgent: 'done' };
  }

  // Delegate to builder
  return {
    activeAgent: 'backend-builder',
    visitedAgents: [...state.visitedAgents, 'agent-orchestrator'],
    delegationDepth: state.delegationDepth + 1,
    status: 'IN_PROGRESS',
  };
}

// 3. State Machine Node: Verifier / Reviewer
export async function verifierNode(state: AgentState): Promise<Partial<AgentState>> {
  const isCodeValid = state.artifacts.codeContent !== undefined;

  if (isCodeValid) {
    return {
      activeAgent: 'agent-orchestrator',
      artifacts: { ...state.artifacts, verificationResult: 'PASSED' },
    };
  }

  return {
    activeAgent: 'backend-builder',
    visitedAgents: [...state.visitedAgents, 'verifier'],
    delegationDepth: state.delegationDepth + 1,
    artifacts: { ...state.artifacts, verificationResult: 'FAILED' },
  };
}
```

---

## 4. Deadlock, Token Consumption & State Invariants

$$\text{Delegation Depth: } \text{Depth}(step) \le \text{MaxDepth} \quad (\text{default } 5)$$

$$\text{Token Budget Utilization: } Tokens_{current} \le 0.80 \times ContextWindow_{max}$$

$$\text{Handoff Schema Invariant: } \forall \text{ handoff } h: \quad h.\text{version} = \text{"1.0.0"} \land h.\text{target\_agent} \in \text{AllowedAgents}$$

---

## 5. Guardrails

### Operational Restrictions

- **Deadlock Guardrail**: Never design a workflow without a hard iteration ceiling (`max_step_iterations`) and delegation depth counter.
- **RBAC Tool Scoping**: Subagents with `permission_mode: read-only` must NEVER be granted mutating execution tools (`Write`, `Edit`, `Patch`).
- **Context Isolation**: Never pass unpruned, full conversation context logs to subagents; pass scoped, structured JSON state payloads.

---

## 6. Atomic Failure Recovery & Rollback Handler

Before executing multi-agent workflows, record initial file system and state baselines. If a workflow fails or hits a deadlock:

```bash
# Revert modified files
if [ -n "${MODIFIED_FILES:-}" ]; then
  git checkout -- ${MODIFIED_FILES} 2>/dev/null
fi

# Remove newly created untracked files
if [ -n "${CREATED_FILES:-}" ]; then
  rm -rf ${CREATED_FILES} 2>/dev/null
fi
```

---

## 7. Verification Plan & Toolchain Commands

Run multi-agent simulation tests:

```bash
# 1. Run agent deadlock simulator script
python3 scripts/simulate_agent_deadlock.py

# 2. Run unit tests for state handoffs
python3 -m unittest discover -s tests -v
```

---

## 8. Completion Report

Report workflow topology, agent role inventory, JSON-RPC handoff schema version, delegation depth bounds, token window budget, simulation results, and deadlock-freedom proofs.
