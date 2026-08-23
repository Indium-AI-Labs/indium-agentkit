#!/usr/bin/env python3
"""
generate_mermaid_architecture.py

Scan `agents/` and `skills/` in the repository, parse metadata/frontmatter,
and generate a comprehensive Mermaid flowchart diagram of the system architecture,
subagent roles, RBAC boundaries, and skill catalog.

Usage:
    python scripts/generate_mermaid_architecture.py [--out-file ARCHITECTURE.md] [--stdout]
"""

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple


def parse_frontmatter(file_path: Path) -> Dict[str, str]:
    """Extract YAML frontmatter fields from a markdown file."""
    content = file_path.read_text(encoding="utf-8")
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    fields = {}
    if match:
        raw_yaml = match.group(1)
        for line in raw_yaml.splitlines():
            line = line.strip()
            if ":" in line and not line.startswith("#"):
                key, val = line.split(":", 1)
                fields[key.strip()] = val.strip().strip('"\'')
    return fields


def get_agents(agents_dir: Path) -> List[Tuple[str, str, str]]:
    """Return list of (name, description, tools) for all agents."""
    agents = []
    if not agents_dir.exists():
        return agents
    for p in sorted(agents_dir.glob("*.md")):
        fm = parse_frontmatter(p)
        name = fm.get("name", p.stem)
        desc = fm.get("description", "Subagent")
        tools = fm.get("tools", "Read-only")
        agents.append((name, desc, tools))
    return agents


def get_skills(skills_dir: Path) -> List[Tuple[str, str]]:
    """Return list of (name, description) for all skills."""
    skills = []
    if not skills_dir.exists():
        return skills
    for p in sorted(skills_dir.glob("*/SKILL.md")):
        fm = parse_frontmatter(p)
        name = fm.get("name", p.parent.name)
        desc = fm.get("description", "Skill")
        skills.append((name, desc))
    return skills


def generate_mermaid(root_dir: Path) -> str:
    """Generate Mermaid Markdown content."""
    agents = get_agents(root_dir / "agents")
    skills = get_skills(root_dir / "skills")

    lines = [
        "# Indium Agentkit Architecture Map",
        "",
        "Auto-generated architecture diagram depicting subagents, execution skills, and zero-trust RBAC boundaries.",
        "",
        "```mermaid",
        "flowchart TD",
        "    classDef orchestrator fill:#2b3a4a,stroke:#4a90e2,stroke-width:2px,color:#ffffff;",
        "    classDef subagent fill:#1e293b,stroke:#38bdf8,stroke-width:1.5px,color:#f8fafc;",
        "    classDef skill fill:#0f172a,stroke:#34d399,stroke-width:1.5px,color:#f8fafc;",
        "    classDef validator fill:#312e81,stroke:#818cf8,stroke-width:1.5px,color:#ffffff;",
        "",
        "    subgraph CLI [User & Cursor / Claude IDE Layer]",
        "        USER([Developer / Agent Client]):::orchestrator",
        "        CLI_TOOLS[npm / cli.js / Cursor Rules]:::orchestrator",
        "    end",
        "",
        "    subgraph Subagents [Zero-Trust Read-Only Subagents (agents/)]",
    ]

    for name, desc, tools in agents:
        safe_id = f"AGENT_{name.replace('-', '_')}"
        clean_desc = desc.replace('"', "'")
        lines.append(f'        {safe_id}["🤖 {name}<br/><i>{clean_desc}</i><br/><small>Tools: {tools}</small>"]:::subagent')

    lines.append("    end")
    lines.append("")
    lines.append("    subgraph Skills [Contract-First Execution Skills (skills/)]")

    for name, desc in skills:
        safe_id = f"SKILL_{name.replace('-', '_')}"
        clean_desc = desc.replace('"', "'")
        lines.append(f'        {safe_id}["⚡ {name}<br/><i>{clean_desc}</i>"]:::skill')

    lines.append("    end")
    lines.append("")
    lines.append("    subgraph Validation [Validation & Catalog Pipeline]")
    lines.append('        V_CONTENT["validate_content.py"]:::validator')
    lines.append('        V_RBAC["validate_rbac_schema.py"]:::validator')
    lines.append('        V_CATALOG["generate_catalog.py"]:::validator')
    lines.append("    end")
    lines.append("")
    lines.append("    USER --> CLI_TOOLS")
    lines.append("    CLI_TOOLS --> Subagents")
    lines.append("    CLI_TOOLS --> Skills")
    lines.append("    Subagents -. Delegate Context .-> Skills")
    lines.append("    Skills --> Validation")
    lines.append("    Subagents --> Validation")
    lines.append("```")
    lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Generate Mermaid architecture diagram for indium-agentkit.")
    parser.add_argument("--out-file", type=str, default="ARCHITECTURE.md", help="Output file path")
    parser.add_argument("--stdout", action="store_true", help="Print output to stdout instead of writing file")
    args = parser.parse_args()

    root_dir = Path(__file__).parent.parent.resolve()
    mermaid_content = generate_mermaid(root_dir)

    if args.stdout:
        print(mermaid_content)
    else:
        out_path = root_dir / args.out_file
        out_path.write_text(mermaid_content, encoding="utf-8")
        print(f"Generated architecture diagram at: {out_path}")


if __name__ == "__main__":
    main()
