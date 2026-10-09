#!/usr/bin/env python3
"""Fail when a file, function or class exceeds its size threshold.

Python is measured by AST (exact). Other languages fall back to file-level
line counts only, because brace-counting heuristics produce false positives
that erode trust in the check.

    check_monolith.py --file 400 --function 75 --class 200 backend/
    check_monolith.py --file 150 --allowlist scripts/monolith_allowlist.txt frontend/src

Exit code 1 on any violation, 0 when clean.
"""

from __future__ import annotations

import argparse
import ast
import fnmatch
import sys
from pathlib import Path

DEFAULT_EXCLUDES = [
    "*/node_modules/*", "*/.next/*", "*/.git/*", "*/dist/*", "*/build/*",
    "*/__pycache__/*", "*/venv/*", "*/.venv/*", "*/migrations/*",
    "*.lock", "*.min.js", "*.map", "*.snap",
]

COUNTED_SUFFIXES = {
    ".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".vue", ".svelte",
    ".go", ".rs", ".rb", ".java", ".kt", ".php",
}


def excluded(path: Path, patterns: list[str]) -> bool:
    s = str(path)
    return any(fnmatch.fnmatch(s, pat) for pat in patterns)


def load_allowlist(path: str | None) -> set[str]:
    if not path:
        return set()
    p = Path(path)
    if not p.exists():
        return set()
    return {
        line.strip() for line in p.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }


def allowed(path: Path, allowlist: set[str]) -> bool:
    s = str(path)
    return any(s == entry or s.endswith("/" + entry) or fnmatch.fnmatch(s, entry)
               for entry in allowlist)


def significant_lines(text: str) -> int:
    """Lines that are neither blank nor a lone comment marker."""
    n = 0
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith(("#", "//", "*", "/*")):
            continue
        n += 1
    return n


def python_violations(path: Path, text: str, fn_max: int, cls_max: int) -> list[str]:
    out: list[str] = []
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return out  # not our job to report syntax errors
    for node in ast.walk(tree):
        if not hasattr(node, "end_lineno") or node.end_lineno is None:
            continue
        span = node.end_lineno - node.lineno + 1
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and span > fn_max:
            out.append(f"{path}:{node.lineno}: function `{node.name}` is {span} lines (max {fn_max})")
        elif isinstance(node, ast.ClassDef):
            if span > cls_max:
                out.append(f"{path}:{node.lineno}: class `{node.name}` is {span} lines (max {cls_max})")
            public = [
                b.name for b in node.body
                if isinstance(b, (ast.FunctionDef, ast.AsyncFunctionDef)) and not b.name.startswith("_")
            ]
            if len(public) > 10:
                out.append(f"{path}:{node.lineno}: class `{node.name}` has {len(public)} public methods (max 10)")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--file", type=int, default=400, help="max significant lines per file")
    ap.add_argument("--function", type=int, default=75, help="max lines per function (Python only)")
    ap.add_argument("--class", dest="cls", type=int, default=200, help="max lines per class (Python only)")
    ap.add_argument("--allowlist", help="file of tolerated paths, one per line, # comments allowed")
    ap.add_argument("--exclude", action="append", default=[])
    args = ap.parse_args()

    allowlist = load_allowlist(args.allowlist)
    patterns = DEFAULT_EXCLUDES + args.exclude
    violations: list[str] = []
    tolerated = 0

    for root in args.paths:
        p = Path(root)
        files = [p] if p.is_file() else [
            f for f in p.rglob("*")
            if f.is_file() and f.suffix in COUNTED_SUFFIXES and not excluded(f, patterns)
        ]
        for f in files:
            if allowed(f, allowlist):
                tolerated += 1
                continue
            try:
                text = f.read_text(encoding="utf-8", errors="strict")
            except (UnicodeDecodeError, OSError):
                continue
            n = significant_lines(text)
            if n > args.file:
                violations.append(f"{f}: {n} significant lines (max {args.file})")
            if f.suffix == ".py":
                violations.extend(python_violations(f, text, args.function, args.cls))

    for v in violations:
        print(v)

    if tolerated:
        print(f"\n({tolerated} file(s) tolerated by the allowlist)")

    if violations:
        print(f"\nFAIL: {len(violations)} size violation(s)")
        return 1

    print(f"OK: no size violation in {', '.join(args.paths)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
