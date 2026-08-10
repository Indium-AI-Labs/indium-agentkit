"""Tests for the handoff-document validator."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "validate_handoff.py"


class ValidateHandoffTests(unittest.TestCase):
    def run_validator(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args], cwd=ROOT, capture_output=True, text=True, check=False)

    def test_canonical_templates_validate(self) -> None:
        result = self.run_validator("--templates-dir", "templates/handoffs")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("handoff validation passed", result.stdout)

    def test_missing_required_heading_fails(self) -> None:
        content = """# Feature brief

## Goal

Example.

## Handoff

**Changed contract:** none

**Files / systems affected:** none

**Evidence and tests:** none

**Risks / rollback:** none

**What the next agent needs:** none
"""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "brief.md"
            path.write_text(content, encoding="utf-8")
            result = self.run_validator(str(path), "--kind", "feature-brief")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing required heading: acceptance criteria", result.stderr)
