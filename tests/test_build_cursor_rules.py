from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
BUILDER = REPO_ROOT / "scripts" / "build_cursor_rules.py"


class BuildCursorRulesTests(unittest.TestCase):
    def run_builder(
        self, skills_dir: Path, out_dir: Path, *arguments: str
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(BUILDER),
                "--skills-dir",
                str(skills_dir),
                "--out-dir",
                str(out_dir),
                *arguments,
            ],
            check=False,
            capture_output=True,
            text=True,
        )

    def test_empty_directory_is_successful(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            skills_dir = root / "skills"
            skills_dir.mkdir()
            result = self.run_builder(skills_dir, root / "rules")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), "no skills found")

    def test_converts_description_and_body(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            skill_file = root / "skills" / "demo" / "SKILL.md"
            skill_file.parent.mkdir(parents=True)
            skill_file.write_text(
                '---\nname: demo\ndescription: "Demo rule"\n---\n# Demo\n\nBody.\n',
                encoding="utf-8",
            )
            rules_dir = root / "rules"
            result = self.run_builder(root / "skills", rules_dir)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(
                (rules_dir / "demo.mdc").read_text(encoding="utf-8"),
                '---\ndescription: "Demo rule"\nalwaysApply: false\n---\n# Demo\n\nBody.\n',
            )

    def test_converts_only_the_selected_skill(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            for name in ("alpha", "beta"):
                skill_file = root / "skills" / name / "SKILL.md"
                skill_file.parent.mkdir(parents=True)
                skill_file.write_text(
                    f'---\nname: {name}\ndescription: "{name}"\n---\n# {name}\n',
                    encoding="utf-8",
                )

            rules_dir = root / "rules"
            result = self.run_builder(
                root / "skills", rules_dir, "--skill", "beta"
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(
                sorted(path.name for path in rules_dir.iterdir()), ["beta.mdc"]
            )


if __name__ == "__main__":
    unittest.main()
