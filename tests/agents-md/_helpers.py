"""Shared fixture helpers for the agents-md checker tests (stdlib only)."""

import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[2] / "plugins" / "dev-skills" / "skills" / "agents-md" / "scripts"


def make_repo(files: dict[str, str]) -> Path:
    root = Path(tempfile.mkdtemp(prefix="agents-md-test-"))
    for rel, content in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return root


def run_raw(name: str, root: Path, *extra: str):
    """Return (exit code, stdout lines) of a checker run."""
    proc = subprocess.run([sys.executable, str(SCRIPTS / name), "--root", str(root), *extra],
                          capture_output=True, text=True)
    return proc.returncode, proc.stdout.splitlines()


def run_script(name: str, root: Path, *extra: str):
    """Return (exit code, {(target, status)}), parsed from the TSV output.

    Comment lines (`# ...`) are skipped; an optional fourth column (hint) is ignored.
    """
    code, lines = run_raw(name, root, *extra)
    rows = set()
    for line in lines:
        if line.startswith("#"):
            continue
        _, target, status, *_ = line.split("\t")
        rows.add((target, status))
    return code, rows
