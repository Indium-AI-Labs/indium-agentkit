"""Unit tests for scripts/validate_rbac_schema.py."""

from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.validate_rbac_schema import (
    extract_frontmatter_bounded,
    main,
    validate_file_rbac,
    validate_rbac_schema,
)

REPO_ROOT = Path(__file__).resolve().parent.parent


class ValidateRBACSchemaTests(unittest.TestCase):

    def test_current_repository_passes_rbac_validation(self) -> None:
        violations, scanned = validate_rbac_schema(REPO_ROOT)
        self.assertEqual(violations, [])
        self.assertGreater(scanned, 0)

    def test_extract_frontmatter_bounded(self) -> None:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as handle:
            handle.write("---\nname: test-agent\ndescription: test\n---\n\n# Header\n" + "line\n" * 200)
            temp_path = Path(handle.name)

        try:
            raw_yaml, error = extract_frontmatter_bounded(temp_path)
            self.assertIsNone(error)
            self.assertEqual(raw_yaml, "name: test-agent\ndescription: test\n")
        finally:
            temp_path.unlink(missing_ok=True)

    def test_skill_schema_routing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            skill_dir = temp_path / "skills" / "demo-skill"
            skill_dir.mkdir(parents=True)
            skill_file = skill_dir / "SKILL.md"
            skill_file.write_text(
                "---\nname: demo-skill\ndescription: A demo skill for testing.\n---\n\n# Demo Skill\n",
                encoding="utf-8",
            )

            violations, scanned = validate_rbac_schema(temp_path)
            self.assertEqual(scanned, 1)
            self.assertEqual(violations, [])

    def test_skill_directory_mismatch_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            skill_dir = temp_path / "skills" / "demo-skill"
            skill_dir.mkdir(parents=True)
            skill_file = skill_dir / "SKILL.md"
            skill_file.write_text(
                "---\nname: mismatched-name\ndescription: Mismatched skill name.\n---\n\n# Mismatched\n",
                encoding="utf-8",
            )

            violations, scanned = validate_rbac_schema(temp_path)
            self.assertEqual(scanned, 1)
            self.assertEqual(len(violations), 1)
            self.assertIn("must match directory name", violations[0]["message"])

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

    def test_known_readonly_subagent_with_write_tool_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            agents_dir = temp_path / "agents"
            agents_dir.mkdir()
            bad_agent = agents_dir / "agent-orchestrator.md"
            bad_agent.write_text(
                "---\nname: agent-orchestrator\ndescription: Topology inspector\npermission_mode: read-only\ntools:\n  - Read\n  - Grep\n  - Edit\nmodel: inherit\n---\n\n# Orchestrator\n",
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
                "---\nname: agent-orchestrator\ndescription: Topology inspector\npermission_mode: read-only\ntools:\n  - Read\n  - Grep\n  - Glob\n  - Bash\nmodel: inherit\n---\n\n# Good Agent\n",
                encoding="utf-8",
            )

            violations, scanned = validate_rbac_schema(temp_path)
            self.assertEqual(scanned, 1)
            self.assertEqual(violations, [])

    def test_malformed_yaml_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            agents_dir = temp_path / "agents"
            agents_dir.mkdir()
            bad_yaml = agents_dir / "bad-yaml.md"
            bad_yaml.write_text(
                "---\nname: bad-yaml\ntools: [Read, Grep: bad\n---\n\n# Bad YAML\n",
                encoding="utf-8",
            )

            violations, scanned = validate_rbac_schema(temp_path)
            self.assertEqual(scanned, 1)
            self.assertEqual(len(violations), 1)
            self.assertEqual(violations[0]["error_type"], "YAMLError")

    def test_pydantic_validation_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            agents_dir = temp_path / "agents"
            agents_dir.mkdir()
            invalid_agent = agents_dir / "invalid-agent.md"
            invalid_agent.write_text(
                "---\ndescription: missing name field\ntools: Read\n---\n\n# Invalid Agent\n",
                encoding="utf-8",
            )

            violations, scanned = validate_rbac_schema(temp_path)
            self.assertEqual(scanned, 1)
            self.assertEqual(len(violations), 1)
            self.assertEqual(violations[0]["error_type"], "SchemaValidationError")

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
