from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = REPO_ROOT / "scripts" / "validate_content.py"


class ValidateContentTests(unittest.TestCase):
    def run_validator(self, root: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(VALIDATOR), "--repo-root", str(root)],
            check=False,
            capture_output=True,
            text=True,
        )

    def create_minimum_repository(self, root: Path) -> None:
        (root / "templates").mkdir()
        (root / "skills").mkdir()
        (root / "agents").mkdir()
        (root / "scripts").mkdir()
        (root / "AGENTS.md").write_text("# Repo\n", encoding="utf-8")
        (root / "templates" / "AGENTS.md").write_text("# Template\n", encoding="utf-8")
        (root / "scripts" / "build_cursor_rules.py").write_text("", encoding="utf-8")

    def test_current_repository_is_valid(self) -> None:
        result = self.run_validator(REPO_ROOT)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("content validation passed", result.stdout)

    def test_rejects_invalid_skill_and_secret(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self.create_minimum_repository(root)
            skill_file = root / "skills" / "different-name" / "SKILL.md"
            skill_file.parent.mkdir()
            fake_token = "gh" + "p_" + "abcdefghijklmnopqrstuvwxyz123456"
            skill_file.write_text(
                f"---\nname: wrong-name\ndescription: test\n---\nToken: {fake_token}\n",
                encoding="utf-8",
            )
            result = self.run_validator(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("match the skill directory name", result.stderr)
            self.assertIn("possible GitHub token", result.stderr)


if __name__ == "__main__":
    unittest.main()
