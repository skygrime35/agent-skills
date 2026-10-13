#!/usr/bin/env python3
# dev-skills: agents-md __PLUGIN_VERSION__
"""Fail when deferral markers are left in shipped code.

The rule this enforces: either do it now, or record it in the debt register.
A TODO in the code is a decision nobody scheduled.

    check_no_todo.py backend/ frontend/src
    check_no_todo.py --markers TODO,FIXME,HACK --allow tests/ src/

Exit code 1 on any hit, 0 when clean.
"""

from __future__ import annotations

import argparse
import fnmatch
import re
import sys
from pathlib import Path

DEFAULT_MARKERS = ["TODO", "FIXME", "XXX", "HACK", "OPTIMIZE", "REVIEW"]

DEFAULT_EXCLUDES = [
    "*/node_modules/*",
    "*/.next/*",
    "*/.git/*",
    "*/dist/*",
    "*/build/*",
    "*/__pycache__/*",
    "*/venv/*",
    "*/.venv/*",
    "*/migrations/*",
    "*.lock",
    "*.min.js",
    "*.map",
    "*/TODO.md",
]

TEXT_SUFFIXES = {
    ".py",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".mjs",
    ".cjs",
    ".vue",
    ".svelte",
    ".go",
    ".rs",
    ".rb",
    ".java",
    ".kt",
    ".php",
    ".sh",
    ".css",
    ".scss",
    ".sql",
}


def excluded(path: Path, patterns: list[str]) -> bool:
    s = str(path)
    return any(fnmatch.fnmatch(s, pat) for pat in patterns)


def iter_files(roots: list[str], patterns: list[str], suffixes: set[str]):
    for root in roots:
        p = Path(root)
        if p.is_file():
            if not excluded(p, patterns):
                yield p
            continue
        for f in p.rglob("*"):
            if f.is_file() and f.suffix in suffixes and not excluded(f, patterns):
                yield f


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--markers", default=",".join(DEFAULT_MARKERS))
    ap.add_argument(
        "--allow", action="append", default=[], help="extra glob to skip (repeatable)"
    )
    ap.add_argument(
        "--suffixes", default="", help="comma list overriding the default code suffixes"
    )
    ap.add_argument(
        "--strict",
        action="store_true",
        help="flag every occurrence, including prose citing the debt register",
    )
    args = ap.parse_args(argv)

    markers = [m.strip() for m in args.markers.split(",") if m.strip()]
    alt = "|".join(re.escape(m) for m in markers)

    if args.strict:
        # Any standalone occurrence. Noisy: flags prose that merely cites TODO.md.
        pattern = re.compile(r"\b(" + alt + r")\b")
    else:
        # Only the conventional deferral forms: the marker opens a comment, or is
        # followed by `:` / `(owner)`. This is what distinguishes an actual debt
        # marker from a sentence pointing at the debt register ("cf. DOCS/TODO.md").
        pattern = re.compile(
            r"(?:^\s*(?:#|//|\*|/\*|<!--)?\s*(?:" + alt + r")\b(?!\.\w)"
            r"|\b(?:" + alt + r")\s*(?:\([^)]*\))?\s*:)"
        )
    patterns = DEFAULT_EXCLUDES + args.allow
    suffixes = {
        s if s.startswith(".") else "." + s for s in args.suffixes.split(",") if s
    } or TEXT_SUFFIXES

    hits = 0
    for path in iter_files(args.paths, patterns, suffixes):
        try:
            lines = path.read_text(encoding="utf-8", errors="strict").splitlines()
        except (UnicodeDecodeError, OSError):
            continue
        for lineno, line in enumerate(lines, 1):
            if pattern.search(line):
                hits += 1
                print(f"{path}:{lineno}: {line.strip()[:100]}")

    if hits:
        print(f"\nFAIL: {hits} deferral marker(s) [{', '.join(markers)}]")
        print("Do it now, or move it to the debt register.")
        return 1

    print(f"OK: no deferral marker in {', '.join(args.paths)}")
    return 0


def cli(argv: list[str] | None = None) -> int:
    """Entry point for tests: parse argv (default: sys.argv[1:]) and return the exit code."""
    return main(argv)


if __name__ == "__main__":
    sys.exit(main())
