#!/usr/bin/env python3
"""
analyze_token_telemetry.py

Analyze agent execution logs, transcripts, or telemetry JSON files to calculate
prompt/completion token budgets, identify context window spikes, and estimate costs.

Usage:
    python scripts/analyze_token_telemetry.py [--log-path <path>] [--json] [--threshold <tokens>]
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Standard LLM Pricing per 1M tokens ($ / 1,000,000)
MODEL_PRICING = {
    "claude-3-5-sonnet": {"input": 3.00, "output": 15.00},
    "gemini-1.5-pro": {"input": 1.25, "output": 5.00},
    "gemini-1.5-flash": {"input": 0.075, "output": 0.30},
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "default": {"input": 2.00, "output": 8.00},
}


def parse_telemetry_file(file_path: Path) -> List[Dict[str, Any]]:
    """Parse telemetry JSON or JSONL file and extract token events."""
    events = []
    content = file_path.read_text(encoding="utf-8")

    # Try standard JSON list
    try:
        data = json.loads(content)
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            return [data]
    except json.JSONDecodeError:
        pass

    # Fallback to JSON Lines (JSONL)
    for line_num, line in enumerate(content.splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            item = json.loads(line)
            if isinstance(item, dict):
                events.append(item)
        except json.JSONDecodeError:
            continue

    return events


def analyze_events(events: List[Dict[str, Any]], threshold: int, model_name: str) -> Dict[str, Any]:
    """Calculate token metrics, cost estimates, and budget breaches."""
    total_input = 0
    total_output = 0
    agent_breakdown: Dict[str, Dict[str, int]] = {}
    high_usage_steps = []

    pricing = MODEL_PRICING.get(model_name, MODEL_PRICING["default"])

    for idx, event in enumerate(events):
        agent = event.get("agent_name") or event.get("source") or "unknown_agent"
        input_t = event.get("input_tokens") or event.get("prompt_tokens") or 0
        output_t = event.get("output_tokens") or event.get("completion_tokens") or 0

        # Handle nested usage dict if present
        usage = event.get("usage", {})
        if isinstance(usage, dict):
            input_t = input_t or usage.get("input_tokens") or usage.get("prompt_tokens") or 0
            output_t = output_t or usage.get("output_tokens") or usage.get("completion_tokens") or 0

        step_total = input_t + output_t
        total_input += input_t
        total_output += output_t

        if agent not in agent_breakdown:
            agent_breakdown[agent] = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "steps": 0}

        agent_breakdown[agent]["input_tokens"] += input_t
        agent_breakdown[agent]["output_tokens"] += output_t
        agent_breakdown[agent]["total_tokens"] += step_total
        agent_breakdown[agent]["steps"] += 1

        if step_total >= threshold:
            high_usage_steps.append({
                "step_index": event.get("step_index", idx),
                "agent_name": agent,
                "input_tokens": input_t,
                "output_tokens": output_t,
                "total_tokens": step_total,
            })

    total_tokens = total_input + total_output
    estimated_cost = (
        (total_input / 1_000_000) * pricing["input"] +
        (total_output / 1_000_000) * pricing["output"]
    )

    return {
        "summary": {
            "total_events_processed": len(events),
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "total_tokens": total_tokens,
            "estimated_cost_usd": round(estimated_cost, 4),
            "model_pricing_tier": model_name,
            "threshold_tokens": threshold,
            "high_usage_breaches": len(high_usage_steps),
        },
        "agent_breakdown": agent_breakdown,
        "high_usage_steps": high_usage_steps,
    }


def format_table(analysis: Dict[str, Any]) -> str:
    """Format analysis into a clean text summary."""
    s = analysis["summary"]
    lines = [
        "=" * 65,
        "          TOKEN TELEMETRY & COST ANALYSIS REPORT          ",
        "=" * 65,
        f"Total Events Processed : {s['total_events_processed']}",
        f"Total Input Tokens     : {s['total_input_tokens']:,}",
        f"Total Output Tokens    : {s['total_output_tokens']:,}",
        f"Total Combined Tokens  : {s['total_tokens']:,}",
        f"Estimated Cost (USD)   : ${s['estimated_cost_usd']:.4f} ({s['model_pricing_tier']})",
        f"Budget Breaches (>{s['threshold_tokens']:,}t): {s['high_usage_breaches']}",
        "-" * 65,
        "AGENT BREAKDOWN:",
        f"{'Agent Name':<25} | {'Input':<10} | {'Output':<10} | {'Total':<10} | {'Steps':<5}",
        "-" * 65,
    ]

    for agent, d in analysis["agent_breakdown"].items():
        lines.append(
            f"{agent:<25} | {d['input_tokens']:<10,} | {d['output_tokens']:<10,} | {d['total_tokens']:<10,} | {d['steps']:<5}"
        )

    if analysis["high_usage_steps"]:
        lines.extend([
            "-" * 65,
            "CONTEXT SPIKE WARNINGS (Threshold Breaches):",
        ])
        for breach in analysis["high_usage_steps"]:
            lines.append(
                f" - Step #{breach['step_index']} [{breach['agent_name']}]: {breach['total_tokens']:,} tokens "
                f"({breach['input_tokens']:,} in / {breach['output_tokens']:,} out)"
            )

    lines.append("=" * 65)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Analyze agent execution logs for LLM token usage and cost.")
    parser.add_argument("--log-path", type=str, help="Path to telemetry JSON or JSONL file")
    parser.add_argument("--threshold", type=int, default=50000, help="Token threshold warning level (default 50,000)")
    parser.add_argument("--model", type=str, default="claude-3-5-sonnet", choices=list(MODEL_PRICING.keys()), help="LLM pricing tier")
    parser.add_argument("--json", action="store_true", help="Output raw JSON instead of text table")

    args = parser.parse_args()

    events = []
    if args.log_path:
        p = Path(args.log_path)
        if p.exists():
            events = parse_telemetry_file(p)
        else:
            print(f"Error: Log file not found at {args.log_path}", file=sys.stderr)
            sys.exit(1)
    else:
        # Default mock event if run standalone for demonstration
        events = [
            {"step_index": 1, "agent_name": "agent-orchestrator", "input_tokens": 12500, "output_tokens": 1200},
            {"step_index": 2, "agent_name": "backend-api", "input_tokens": 34000, "output_tokens": 4800},
            {"step_index": 3, "agent_name": "security-reviewer", "input_tokens": 58000, "output_tokens": 2100},
        ]

    analysis = analyze_events(events, args.threshold, args.model)

    if args.json:
        print(json.dumps(analysis, indent=2))
    else:
        print(format_table(analysis))


if __name__ == "__main__":
    main()
