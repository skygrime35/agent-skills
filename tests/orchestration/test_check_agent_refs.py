"""Tests for skills/orchestration/scripts/check_agent_refs.py (exit codes and output)."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = (Path(__file__).resolve().parents[2]
          / "plugins/dev-skills/skills/orchestration/scripts/check_agent_refs.py")

GOOD_AGENT = """---
name: {name}
description: "Use when a test needs it."
model: haiku
effort: medium
---
Do the task. Report findings.
"""
BAD_AGENT = """---
name: {name}
description: "Use when a test needs it."
model: haiku
---
Do the task. Report findings.
"""
CONFIG = """agents:
  location: {location}
  types:
    - {{name: owned-one, model: haiku, effort: medium}}
"""


def run(*args):
    proc = subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True)
    return proc.returncode, proc.stdout + proc.stderr


class CheckAgentRefsTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.agents = self.root / "agents"
        self.agents.mkdir()
        self.doc = self.root / "AGENTS.md"
        self.doc.write_text("# Title\n\n## Orchestration\nUse `owned-one`.\n")

    def write_agent(self, name, bad=False):
        template = BAD_AGENT if bad else GOOD_AGENT
        (self.agents / f"{name}.md").write_text(template.format(name=name))

    def write_config(self, location="project"):
        path = self.root / "orchestration.yml"
        path.write_text(CONFIG.format(location=location))
        return str(path)

    def test_clean_run_exits_0(self):
        self.write_agent("owned-one")
        code, _ = run("--doc", str(self.doc), "--agents-dir", str(self.agents))
        self.assertEqual(code, 0)

    def test_owned_broken_exits_1(self):
        self.write_agent("owned-one", bad=True)
        code, out = run("--doc", str(self.doc), "--agents-dir", str(self.agents),
                        "--config", self.write_config(), "--only-owned")
        self.assertEqual(code, 1, out)
        self.assertIn("missing required key: effort", out)

    def test_non_owned_broken_with_only_owned_exits_0(self):
        self.write_agent("owned-one")
        self.write_agent("someone-elses", bad=True)
        code, out = run("--doc", str(self.doc), "--agents-dir", str(self.agents),
                        "--config", self.write_config(), "--only-owned")
        self.assertEqual(code, 0, out)
        self.assertIn("warning:", out)

    def test_non_owned_broken_without_only_owned_exits_1(self):
        self.write_agent("owned-one")
        self.write_agent("someone-elses", bad=True)
        code, _ = run("--doc", str(self.doc), "--agents-dir", str(self.agents))
        self.assertEqual(code, 1)

    def test_absent_dir_is_a_warning(self):
        code, out = run("--doc", str(self.doc), "--agents-dir", str(self.root / "nope"))
        self.assertEqual(code, 0, out)
        self.assertIn("warning:", out)
        self.assertIn("does not exist", out)

    def test_absent_dir_strict_exits_1(self):
        code, out = run("--doc", str(self.doc), "--agents-dir", str(self.root / "nope"),
                        "--strict")
        self.assertEqual(code, 1, out)
        self.assertIn("does not exist", out)

    def test_multiple_section_headings(self):
        self.write_agent("owned-one")
        self.doc.write_text("# T\n\n## Alpha\nUse `owned-one`.\n\n## Beta\nUse `haiku-ghost`.\n\n"
                            "## Other\nUse `sonnet-unrelated`.\n")
        args = ("--doc", str(self.doc), "--agents-dir", str(self.agents))
        code, out = run(*args, "--section-heading", "## Alpha", "--section-heading", "## Beta")
        self.assertEqual(code, 1, out)
        self.assertIn("haiku-ghost", out)
        self.assertNotIn("sonnet-unrelated", out)  # outside both spans
        code, out = run(*args, "--section-heading", "## Alpha")
        self.assertEqual(code, 0, out)  # Beta's ghost is outside the only span


if __name__ == "__main__":
    unittest.main()
