#!/usr/bin/env python3
# dev-skills: agents-md __PLUGIN_VERSION__
"""Fail when forbidden characters appear in a configured scope.

Typical targets: em dash / en dash (the most recognisable tell of generated
prose) and emoji. Runs on any repository, no third-party dependency.

    check_forbidden_chars.py --chars em-dash,en-dash frontend/src
    check_forbidden_chars.py --chars emoji --exclude '*.min.js' docs/
    check_forbidden_chars.py --chars em-dash --comments-only src/

Exit code 1 on any hit, 0 when clean.
"""

from __future__ import annotations

import argparse
import fnmatch
import sys
import unicodedata
from pathlib import Path

# Named sets, so CI config stays readable instead of carrying raw codepoints.
NAMED_SETS: dict[str, list[str]] = {
    "em-dash": ["—"],
    "en-dash": ["–"],
    "dashes": ["—", "–"],
    "ellipsis": ["…"],
    "smart-quotes": ["“", "”", "‘", "’"],
}

EMOJI_RANGES = [
    (0x1F300, 0x1FAFF),
    (0x2600, 0x27BF),
    (0x2B00, 0x2BFF),
    (0xFE0F, 0xFE0F),
]

DEFAULT_EXCLUDES = [
    "*/node_modules/*",
    "*/.next/*",
    "*/.git/*",
    "*/dist/*",
    "*/build/*",
    "*/__pycache__/*",
    "*/venv/*",
    "*/.venv/*",
    "*.lock",
    "*.min.js",
    "*.map",
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
    ".md",
    ".mdx",
    ".json",
    ".yml",
    ".yaml",
    ".toml",
    ".html",
    ".css",
    ".scss",
    ".go",
    ".rs",
    ".rb",
    ".java",
    ".kt",
    ".php",
    ".sh",
    ".txt",
}

COMMENT_PREFIXES = ("//", "#", "*", "/*", "<!--", '"""', "'''")


def is_emoji(ch: str) -> bool:
    cp = ord(ch)
    return any(lo <= cp <= hi for lo, hi in EMOJI_RANGES)


def build_matcher(spec: str):
    """Return (predicate, human-readable label) for one --chars token."""
    if spec == "emoji":
        return is_emoji, "emoji"
    if spec in NAMED_SETS:
        chars = set(NAMED_SETS[spec])
        return (lambda ch: ch in chars), spec
    # Fall back to a literal character list, e.g. --chars '—,–'
    chars = {c for c in spec.split(",") if c}
    return (lambda ch: ch in chars), spec


def excluded(path: Path, patterns: list[str]) -> bool:
    s = str(path)
    return any(fnmatch.fnmatch(s, pat) for pat in patterns)


def iter_files(roots: list[str], patterns: list[str]):
    for root in roots:
        p = Path(root)
        if p.is_file():
            if not excluded(p, patterns):
                yield p
            continue
        for f in p.rglob("*"):
            if f.is_file() and f.suffix in TEXT_SUFFIXES and not excluded(f, patterns):
                yield f


def looks_like_comment(line: str) -> bool:
    return line.lstrip().startswith(COMMENT_PREFIXES)


def describe(ch: str) -> str:
    try:
        name = unicodedata.name(ch)
    except ValueError:
        name = "UNNAMED"
    return f"U+{ord(ch):04X} {name}"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("paths", nargs="+", help="files or directories to scan")
    ap.add_argument(
        "--chars",
        default="dashes",
        help="named set (%s, emoji) or a literal comma list" % ", ".join(NAMED_SETS),
    )
    ap.add_argument(
        "--exclude", action="append", default=[], help="extra glob to skip (repeatable)"
    )
    ap.add_argument(
        "--comments-only", action="store_true", help="only flag hits on comment lines"
    )
    ap.add_argument(
        "--code-only", action="store_true", help="only flag hits outside comment lines"
    )
    ap.add_argument(
        "--max-report", type=int, default=50, help="stop printing after N hits"
    )
    args = ap.parse_args(argv)

    matchers = (
        [build_matcher(tok) for tok in args.chars.split(",") if tok]
        if args.chars not in NAMED_SETS and args.chars != "emoji" and "," in args.chars
        else [build_matcher(args.chars)]
    )

    patterns = DEFAULT_EXCLUDES + args.exclude
    hits = 0
    shown = 0

    for path in iter_files(args.paths, patterns):
        try:
            lines = path.read_text(encoding="utf-8", errors="strict").splitlines()
        except (UnicodeDecodeError, OSError):
            continue  # binary or unreadable: not our business
        for lineno, line in enumerate(lines, 1):
            comment = looks_like_comment(line)
            if args.comments_only and not comment:
                continue
            if args.code_only and comment:
                continue
            for col, ch in enumerate(line, 1):
                if any(pred(ch) for pred, _ in matchers):
                    hits += 1
                    if shown < args.max_report:
                        shown += 1
                        print(
                            f"{path}:{lineno}:{col}: {describe(ch)}  |  {line.strip()[:90]}"
                        )

    if hits:
        if hits > shown:
            print(f"... {hits - shown} more")
        label = ", ".join(lbl for _, lbl in matchers)
        print(
            f"\nFAIL: {hits} forbidden character(s) [{label}] in {', '.join(args.paths)}"
        )
        return 1

    print(f"OK: no forbidden character in {', '.join(args.paths)}")
    return 0


def cli(argv: list[str] | None = None) -> int:
    """Entry point for tests: parse argv (default: sys.argv[1:]) and return the exit code."""
    return main(argv)


if __name__ == "__main__":
    sys.exit(main())
