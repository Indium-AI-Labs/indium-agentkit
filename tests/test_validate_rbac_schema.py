"""Unit tests for scripts/validate_rbac_schema.py."""

from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.validate_rbac_schema import (
    main,
    parse_frontmatter,
    parse_tools_list,
    validate_file_rbac,
    validate_rbac_schema,
)

REPO_ROOT = Path(__file__).resolve().parent.parent


class ValidateRBACSchemaTests(unittest.TestCase):

    def test_current_repository_passes_rbac_validation(self) -> None:
        violations, scanned = validate_rbac_schema(REPO_ROOT)
        self.assertEqual(violations, [])
        self.assertGreater(scanned, 0)

    def test_parse_tools_list(self) -> None:
        self.assertEqual(parse_tools_list("Read, Grep, Glob, Bash"), ["Read", "Grep", "Glob", "Bash"])
        self.assertEqual(parse_tools_list("Read; Edit; Write"), ["Read", "Edit", "Write"])
        self.assertEqual(parse_tools_list(""), [])

    def test_readonly_agent_with_write_tool_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            agents_dir = temp_path / "agents"
            agents_dir.mkdir()
            bad_agent = agents_dir / "bad-agent.md"
            bad_agent.write_text(
                "---\nname: bad-agent\ndescription: test agent\npermission_mode: read-only\ntools: Read, Grep, Edit, Write\nmodel: inherit\n---\n\n# Bad Agent\n",
                encoding="utf-8",
            )

            violations, scanned = validate_rbac_schema(temp_path)
            self.assertEqual(scanned, 1)
            self.assertEqual(len(violations), 1)
            self.assertEqual(violations[0]["error_type"], "PrivilegeEscalationError")
            self.assertIn("edit", violations[0]["prohibited_tools"])
            self.assertIn("write", violations[0]["prohibited_tools"])

    def test_readonly_description_with_write_tool_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            agents_dir = temp_path / "agents"
            agents_dir.mkdir()
            bad_agent = agents_dir / "custom-auditor.md"
            bad_agent.write_text(
                "---\nname: custom-auditor\ndescription: Read-only compliance auditor\ntools: Read, Patch\nmodel: inherit\n---\n\n# Auditor\n",
                encoding="utf-8",
            )

            violations, scanned = validate_rbac_schema(temp_path)
            self.assertEqual(scanned, 1)
            self.assertEqual(len(violations), 1)
            self.assertEqual(violations[0]["error_type"], "PrivilegeEscalationError")
            self.assertEqual(violations[0]["prohibited_tools"], ["patch"])

    def test_known_readonly_subagent_with_write_tool_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            agents_dir = temp_path / "agents"
            agents_dir.mkdir()
            bad_agent = agents_dir / "agent-orchestrator.md"
            bad_agent.write_text(
                "---\nname: agent-orchestrator\ndescription: Topology inspector\ntools: Read, Grep, Edit\nmodel: inherit\n---\n\n# Orchestrator\n",
                encoding="utf-8",
            )

            violations, scanned = validate_rbac_schema(temp_path)
            self.assertEqual(scanned, 1)
            self.assertEqual(len(violations), 1)
            self.assertEqual(violations[0]["error_type"], "PrivilegeEscalationError")
            self.assertIn("edit", violations[0]["prohibited_tools"])

    def test_valid_readonly_agent_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            agents_dir = temp_path / "agents"
            agents_dir.mkdir()
            good_agent = agents_dir / "agent-orchestrator.md"
            good_agent.write_text(
                "---\nname: agent-orchestrator\ndescription: Read-only topology inspector\ntools: Read, Grep, Glob, Bash\nmodel: inherit\n---\n\n# Good Agent\n",
                encoding="utf-8",
            )

            violations, scanned = validate_rbac_schema(temp_path)
            self.assertEqual(scanned, 1)
            self.assertEqual(violations, [])

    def test_invalid_target_dir_returns_error(self) -> None:
        non_existent = REPO_ROOT / "non_existent_directory_12345"
        violations, scanned = validate_rbac_schema(non_existent)
        self.assertEqual(scanned, 0)
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0]["error_type"], "SchemaValidationError")

    def test_cli_main_success(self) -> None:
        old_argv = sys.argv
        sys.argv = ["validate_rbac_schema.py", "--target-dir", str(REPO_ROOT)]
        captured_out = io.StringIO()
        try:
            sys.stdout = captured_out
            exit_code = main()
            self.assertEqual(exit_code, 0)
            output = json.loads(captured_out.getvalue().strip())
            self.assertEqual(output["status"], "PASSED")
        finally:
            sys.argv = old_argv
            sys.stdout = sys.__stdout__


if __name__ == "__main__":
    unittest.main()
