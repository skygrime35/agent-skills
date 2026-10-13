"""Tests for skills/orchestration/scripts/usage_by_agent_type.py (window header fields)."""

import datetime
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

SCRIPT = (Path(__file__).resolve().parents[2]
          / "plugins/dev-skills/skills/orchestration/scripts/usage_by_agent_type.py")

DAY = 86400


def encode_cwd(path):
    """Claude Code's project folder name for a working directory (same rule as the script)."""
    return re.sub(r"[^A-Za-z0-9]", "-", path)


def iso(epoch):
    return datetime.datetime.fromtimestamp(epoch, datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


class UsageByAgentTypeTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.home = Path(tmp.name, "home")
        self.work = Path(tmp.name, "work")  # the cwd: a plain directory, not a git repo
        self.work.mkdir(parents=True)
        self.work_real = os.path.realpath(self.work)

    def write_type_file(self, age_days):
        """Installed agent type in the temp HOME, with an mtime `age_days` in the past."""
        agents = self.home / ".claude" / "agents"
        agents.mkdir(parents=True, exist_ok=True)
        path = agents / "haiku-standard.md"
        path.write_text("---\nname: haiku-standard\ndescription: \"Use for briefed edits.\"\n"
                        "model: haiku\neffort: medium\n---\nReport findings.\n")
        stamp = time.time() - age_days * DAY
        os.utime(path, (stamp, stamp))

    def write_transcript(self, age_days):
        """One subagent run of type haiku-standard, started `age_days` ago."""
        sub = (self.home / ".claude" / "projects" / encode_cwd(self.work_real)
               / "session-1" / "subagents")
        sub.mkdir(parents=True)
        started = time.time() - age_days * DAY
        line = {
            "type": "assistant",
            "timestamp": iso(started),
            "version": "2.1.0",
            "message": {
                "id": "msg-1",
                "model": "claude-haiku-5-5",
                "usage": {"input_tokens": 1000, "output_tokens": 200,
                          "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0},
            },
        }
        (sub / "agent-a1.jsonl").write_text(json.dumps(line) + "\n")
        (sub / "agent-a1.meta.json").write_text(json.dumps({"agentType": "haiku-standard"}))

    def run_script(self, *args):
        env = dict(os.environ, HOME=str(self.home))
        result = subprocess.run([sys.executable, str(SCRIPT), *args], cwd=self.work_real,
                                env=env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def test_short_window_is_flagged(self):
        self.write_type_file(age_days=3)
        self.write_transcript(age_days=1)
        out = self.run_script()
        header = out.splitlines()[0]
        self.assertIn("window_days 3;", header)
        self.assertIn("too_short: true", header)

    def test_window_of_seven_days_or_more_is_not_flagged(self):
        self.write_type_file(age_days=10)
        self.write_transcript(age_days=2)
        out = self.run_script()
        header = out.splitlines()[0]
        self.assertIn("window_days 10;", header)
        self.assertIn("too_short: false", header)

    def test_run_is_counted_for_its_type(self):
        self.write_type_file(age_days=10)
        self.write_transcript(age_days=2)
        out = self.run_script()
        row = next(line for line in out.splitlines() if line.startswith("haiku-standard"))
        self.assertEqual(row.split()[1], "1")  # runs


if __name__ == "__main__":
    unittest.main()
