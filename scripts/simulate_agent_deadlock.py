#!/usr/bin/env python3
"""
simulate_agent_deadlock.py

Simulate multi-agent state machine handoffs, detect circular delegation loops,
and verify that delegation graphs enforce max-depth limits and deadlock breakers.

Usage:
    python scripts/simulate_agent_deadlock.py [--topology-file <path>] [--max-depth 5] [--json]
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple


class AgentDeadlockSimulator:
    """Simulator to test multi-agent handoffs for infinite loops and deadlocks."""

    def __init__(self, max_depth: int = 5, max_iterations: int = 10):
        self.max_depth = max_depth
        self.max_iterations = max_iterations

    def detect_graph_cycles(self, transition_graph: Dict[str, List[str]]) -> List[List[str]]:
        """Find cycles in agent transition graph using Depth First Search (DFS)."""
        cycles = []
        visited = set()
        rec_stack = []

        def dfs(node: str, path: List[str]):
            visited.add(node)
            rec_stack.append(node)
            path.append(node)

            for neighbor in transition_graph.get(node, []):
                if neighbor not in visited:
                    dfs(neighbor, list(path))
                elif neighbor in rec_stack:
                    # Found a cycle
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    if cycle not in cycles:
                        cycles.append(cycle)

            rec_stack.pop()

        for agent in list(transition_graph.keys()):
            if agent not in visited:
                dfs(agent, [])

        return cycles

    def simulate_execution(self, initial_agent: str, transition_rules: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate step-by-step state machine execution across agents."""
        current_agent = initial_agent
        visited_agents: List[str] = [current_agent]
        history: List[Dict[str, Any]] = []
        status = "COMPLETED"
        error_message = None

        state = {
            "version": "1.0.0",
            "active_agent": current_agent,
            "delegation_depth": 0,
            "artifacts": {},
            "visited_agents": visited_agents,
        }

        for step in range(1, self.max_iterations + 1):
            history.append({
                "step": step,
                "agent": current_agent,
                "depth": state["delegation_depth"],
                "visited": list(state["visited_agents"]),
            })

            # Check Delegation Depth Limit
            if state["delegation_depth"] >= self.max_depth:
                status = "DEADLOCK_PREVENTED"
                error_message = f"MAX_DELEGATION_DEPTH_EXCEEDED (depth={state['delegation_depth']})"
                break

            # Resolve Next Agent Hand-off
            rules = transition_rules.get(current_agent, {})
            next_agent = rules.get("next_agent")

            if not next_agent or next_agent == "done":
                status = "COMPLETED"
                break

            # Cycle Check Without State Progress
            has_progress = rules.get("progress_check", False)
            if next_agent in state["visited_agents"] and not has_progress:
                status = "DEADLOCK_PREVENTED"
                error_message = f"CIRCULAR_HANDOFF_DETECTED: {current_agent} -> {next_agent} without progress"
                break

            # Perform Handoff
            current_agent = next_agent
            state["active_agent"] = current_agent
            state["delegation_depth"] += 1
            state["visited_agents"].append(current_agent)

        else:
            if status != "DEADLOCK_PREVENTED":
                status = "DEADLOCK_PREVENTED"
                error_message = f"MAX_ITERATIONS_EXCEEDED (steps={self.max_iterations})"

        return {
            "status": status,
            "error_message": error_message,
            "total_steps": len(history),
            "final_depth": state["delegation_depth"],
            "visited_path": state["visited_agents"],
            "execution_history": history,
        }


def main():
    parser = argparse.ArgumentParser(description="Simulate multi-agent handoffs and test for deadlock prevention.")
    parser.add_argument("--topology-file", type=str, help="Path to JSON file containing transition graph")
    parser.add_argument("--max-depth", type=int, default=5, help="Maximum allowed delegation depth (default: 5)")
    parser.add_argument("--max-iterations", type=int, default=10, help="Maximum allowed iteration steps (default: 10)")
    parser.add_argument("--json", action="store_true", help="Output JSON results")

    args = parser.parse_args()

    simulator = AgentDeadlockSimulator(max_depth=args.max_depth, max_iterations=args.max_iterations)

    if args.topology_file:
        p = Path(args.topology_file)
        if not p.exists():
            print(f"Error: Topology file not found at {args.topology_file}", file=sys.stderr)
            sys.exit(1)
        topology = json.loads(p.read_text(encoding="utf-8"))
    else:
        # Default mock multi-agent topology with potential cycle:
        # Orchestrator -> Coder -> Reviewer -> Coder (Cycle without progress)
        topology = {
            "initial_agent": "agent-orchestrator",
            "transition_graph": {
                "agent-orchestrator": ["backend-builder"],
                "backend-builder": ["security-reviewer"],
                "security-reviewer": ["backend-builder"],
            },
            "transition_rules": {
                "agent-orchestrator": {"next_agent": "backend-builder"},
                "backend-builder": {"next_agent": "security-reviewer"},
                "security-reviewer": {"next_agent": "backend-builder", "progress_check": False},
            },
        }

    cycles = simulator.detect_graph_cycles(topology.get("transition_graph", {}))
    simulation = simulator.simulate_execution(
        topology.get("initial_agent", "agent-orchestrator"),
        topology.get("transition_rules", {}),
    )

    result = {
        "detected_cycles": cycles,
        "simulation": simulation,
    }

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("=" * 65)
        print("        MULTI-AGENT DEADLOCK & HANDOFF SIMULATION REPORT        ")
        print("=" * 65)
        print(f"Initial Agent          : {topology.get('initial_agent')}")
        print(f"Graph Cycles Detected  : {len(cycles)}")
        for idx, cycle in enumerate(cycles, start=1):
            print(f"  Cycle #{idx}: {' -> '.join(cycle)}")
        print("-" * 65)
        print(f"Simulation Status      : {simulation['status']}")
        if simulation["error_message"]:
            print(f"Protection Verdict     : PASS ({simulation['error_message']})")
        else:
            print("Protection Verdict     : PASS (Completed cleanly)")
        print(f"Total Steps            : {simulation['total_steps']}")
        print(f"Final Delegation Depth : {simulation['final_depth']} (Max SLA: {args.max_depth})")
        print(f"Delegation Path        : {' -> '.join(simulation['visited_path'])}")
        print("=" * 65)


if __name__ == "__main__":
    main()
