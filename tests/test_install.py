from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
INSTALLER = REPO_ROOT / "scripts" / "install.py"
CHECKER = REPO_ROOT / "scripts" / "check_install.py"


class InstallTests(unittest.TestCase):
    def run_installer(
        self, *arguments: str, home: Path
    ) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        environment["HOME"] = str(home)
        environment["USERPROFILE"] = str(home)
        return subprocess.run(
            [sys.executable, str(INSTALLER), *arguments, "--home", str(home)],
            check=False,
            capture_output=True,
            text=True,
            env=environment,
        )

    def test_project_scope_installs_only_selected_skill_and_target(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            project = root / "project"
            home = root / "home"
            project.mkdir()
            home.mkdir()

            result = self.run_installer(
                "--scope",
                "project",
                "--project-dir",
                str(project),
                "--target",
                "codex",
                "--item",
                "systematic-debugging",
                "--mode",
                "copy",
                home=home,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            installed = project / ".codex" / "skills"
            self.assertEqual(
                sorted(path.name for path in installed.iterdir()),
                ["systematic-debugging"],
            )
            self.assertFalse((project / ".claude").exists())
            self.assertFalse((home / ".codex").exists())
            self.assertFalse((home / ".claude").exists())

            diagnostic = subprocess.run(
                [
                    sys.executable,
                    str(CHECKER),
                    "--project",
                    str(project),
                    "--target",
                    "codex",
                    "--item",
                    "systematic-debugging",
                    "--mode",
                    "copy",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(diagnostic.returncode, 0, diagnostic.stdout)

    def test_cursor_add_generates_only_the_selected_rule(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            project = root / "project"
            home = root / "home"
            project.mkdir()
            home.mkdir()

            result = self.run_installer(
                "--scope",
                "project",
                "--project-dir",
                str(project),
                "--target",
                "cursor",
                "--item",
                "systematic-debugging",
                "--mode",
                "copy",
                home=home,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            rules = project / ".cursor" / "rules"
            self.assertEqual(
                sorted(path.name for path in rules.iterdir()),
                ["systematic-debugging.mdc"],
            )

    def test_project_context_follows_the_selected_architecture(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            project = root / "project"
            home = root / "home"
            project.mkdir()
            home.mkdir()

            result = self.run_installer(
                "--scope",
                "project",
                "--project-dir",
                str(project),
                "--target",
                "claude",
                "--item",
                "all",
                "--mode",
                "copy",
                "--include-context",
                home=home,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((project / "CLAUDE.md").is_file())
            self.assertFalse((project / "AGENTS.md").exists())
            self.assertTrue((project / ".claude" / "skills").is_dir())
            self.assertTrue((project / ".claude" / "agents").is_dir())
            self.assertFalse((home / ".claude").exists())

    def test_user_scope_honors_target_without_project_writes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            home = root / "home"
            home.mkdir()

            result = self.run_installer(
                "--scope",
                "user",
                "--target",
                "codex",
                "--item",
                "systematic-debugging",
                "--mode",
                "copy",
                home=home,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(
                (home / ".codex" / "skills" / "systematic-debugging" / "SKILL.md").is_file()
            )
            self.assertFalse((home / ".claude").exists())
            self.assertFalse((home / ".gemini").exists())

    def test_unknown_item_fails_without_creating_destinations(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            project = root / "project"
            home = root / "home"
            project.mkdir()
            home.mkdir()

            result = self.run_installer(
                "--scope",
                "project",
                "--project-dir",
                str(project),
                "--target",
                "codex",
                "--item",
                "does-not-exist",
                home=home,
            )

            self.assertEqual(result.returncode, 2)
            self.assertIn("unknown skill or subagent", result.stderr)
            self.assertEqual(list(project.iterdir()), [])

    def test_subagent_fails_for_target_without_native_agent_support(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            project = root / "project"
            home = root / "home"
            project.mkdir()
            home.mkdir()

            result = self.run_installer(
                "--scope",
                "project",
                "--project-dir",
                str(project),
                "--target",
                "codex",
                "--item",
                "reviewer",
                home=home,
            )

            self.assertEqual(result.returncode, 2)
            self.assertIn("no native installation path", result.stderr)
            self.assertEqual(list(project.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
