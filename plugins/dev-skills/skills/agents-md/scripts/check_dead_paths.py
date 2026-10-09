#!/usr/bin/env python3
"""Report paths and links cited in agent docs that resolve to nothing. Read-only.

    check_dead_paths.py                       # AGENTS.md, CLAUDE.md, domain AGENTS.md, docs index
    check_dead_paths.py AGENTS.md docs/a.md   # explicit files
    check_dead_paths.py --root /repo FILE...

Scans backtick spans that look like paths (they contain a "/"; a bare file name
is a convention name, not a pointer) and markdown links, with #anchors checked
against the target's headings. Fenced code blocks, URLs, placeholders and globs
are skipped. A target is resolved relative to the citing file, then to the repo
root, then by suffix against `git ls-files` (so a domain-relative path works).

Output, one line per citation: file:line<TAB>target<TAB>status
status: ok | dead | ambiguous (suffix matches several tracked files).
Exit 0 when nothing is dead, 1 when something is dead, 2 on usage error.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

EXIT_OK, EXIT_DEAD, EXIT_USAGE = 0, 1, 2

# Files scanned when none are given: the root docs, the docs index, every
# tracked domain AGENTS.md. Missing ones are skipped silently.
DEFAULT_FILES = ["AGENTS.md", "CLAUDE.md", "AGENTS/INDEX.md", "docs/INDEX.md", "docs/index.md"]
DOMAIN_FILE_NAME = "AGENTS.md"

# Directories never walked in the no-git fallback (vendored or generated).
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build"}

FENCE_RE = re.compile(r"^\s*(```|~~~)")
LINK_RE = re.compile(r"(?<!\!)\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
TICK_RE = re.compile(r"`([^`\n]+)`")
# A path-like backtick span: at least one "/" between name segments.
PATH_RE = re.compile(r"^(?:\.{1,2}/)?[\w@.+-]+(?:/[\w@.+-]+)+/?$")
URL_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
# Placeholders and globs: <x>, {x}, $VAR, *, ?, [x], "...", XXX, path/to/.
PLACEHOLDER_RE = re.compile(r"[<>{}$*?\[\]|]|\.\.\.|\bXXX\b|(^|/)(path/to|your|my)[-_/]", re.I)
HEADING_RE = re.compile(r"^\s{0,3}(#{1,6})\s+(.*?)\s*#*\s*$")


def git_files(root: Path) -> list[str]:
    try:
        out = subprocess.run(["git", "-C", str(root), "ls-files"], capture_output=True,
                             text=True, check=True).stdout
        return [line for line in out.splitlines() if line]
    except (OSError, subprocess.CalledProcessError):
        found = []
        for base, dirs, names in os.walk(root):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            found += [os.path.relpath(os.path.join(base, n), root) for n in names]
        return found


def slugify(heading: str) -> str:
    """GitHub-style anchor: lowercase, drop punctuation, spaces to hyphens."""
    text = re.sub(r"[`*_~]|\[([^\]]*)\]\([^)]*\)", lambda m: m.group(1) or "", heading).lower()
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
    return re.sub(r"\s", "-", text.strip())


def anchors_of(path: Path) -> set[str]:
    seen: dict[str, int] = {}
    result: set[str] = set()
    in_fence = False
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return result
    for line in lines:
        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        m = None if in_fence else HEADING_RE.match(line)
        if m:
            slug = slugify(m.group(2))
            n = seen.get(slug, 0)
            seen[slug] = n + 1
            result.add(slug if n == 0 else f"{slug}-{n}")
    return result


def citations(path: Path):
    """Yield (line_number, raw_target, is_link) for each citation outside fences."""
    in_fence = False
    for no, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        for m in LINK_RE.finditer(line):
            yield no, m.group(1), True
        for m in TICK_RE.finditer(LINK_RE.sub("", line)):
            yield no, m.group(1).strip(), False


def skippable(target: str, is_link: bool) -> bool:
    if URL_RE.match(target) or target.startswith(("/", "~")) or PLACEHOLDER_RE.search(target):
        return True
    return not is_link and not PATH_RE.match(target)


class Resolver:
    def __init__(self, root: Path):
        self.root = root
        self.tracked = git_files(root)

    def resolve(self, target: str, base: Path) -> tuple[str, Path | None]:
        for candidate in (base.parent / target, self.root / target):
            if candidate.exists():
                return "ok", candidate
        needle = target.strip("/")
        hits = {f for f in self.tracked if f == needle or f.endswith("/" + needle)}
        hits |= {f.split(needle + "/", 1)[0] + needle for f in self.tracked
                 if f.startswith(needle + "/") or ("/" + needle + "/") in f}
        if len(hits) == 1:
            return "ok", self.root / next(iter(hits))
        return ("ambiguous" if hits else "dead"), None


def default_files(root: Path) -> list[Path]:
    names = list(DEFAULT_FILES)
    names += [f for f in git_files(root) if f.endswith("/" + DOMAIN_FILE_NAME)]
    return [root / n for n in dict.fromkeys(names) if (root / n).is_file()]


def main() -> int:
    ap = argparse.ArgumentParser(description="Report dead paths and links in agent docs (read-only).",
                                 epilog="Output: file:line<TAB>target<TAB>status (ok|dead|ambiguous). "
                                        "Exit 0 none dead, 1 dead found, 2 usage error.")
    ap.add_argument("files", nargs="*", help="markdown files to scan (default: agent docs found in the repo)")
    ap.add_argument("--root", default=".", help="repository root (default: current directory)")
    ap.add_argument("--quiet-ok", action="store_true", help="print only dead and ambiguous lines")
    try:
        args = ap.parse_args()
    except SystemExit as e:
        return EXIT_OK if e.code == 0 else EXIT_USAGE
    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"error: root is not a directory: {args.root}", file=sys.stderr)
        return EXIT_USAGE
    files = [Path(f).resolve() for f in args.files] or default_files(root)
    missing = [str(f) for f in files if not f.is_file()]
    if missing:
        print("error: not a file: " + ", ".join(missing), file=sys.stderr)
        return EXIT_USAGE
    resolver = Resolver(root)
    dead = 0
    for f in files:
        rel = os.path.relpath(f, root)
        for no, raw, is_link in citations(f):
            if skippable(raw, is_link):
                continue
            path_part, _, anchor = raw.partition("#")
            path_part = path_part.split("?", 1)[0]
            if not path_part and not anchor:
                continue
            if path_part:
                status, found = resolver.resolve(path_part, f)
            else:
                status, found = "ok", f
            if status == "ok" and anchor and found is not None and found.suffix.lower() == ".md":
                if slugify(anchor) not in anchors_of(found):
                    status = "dead"
            dead += status == "dead"
            if status != "ok" or not args.quiet_ok:
                print(f"{rel}:{no}\t{raw}\t{status}")
    return EXIT_DEAD if dead else EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
