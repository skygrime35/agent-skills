#!/usr/bin/env python3
"""Check that a section cited in agent docs exists in the file it points to. Read-only.

    check_sections.py                          # same default files as check_dead_paths.py
    check_sections.py AGENTS.md AGENTS/INDEX.md
    check_sections.py --root /repo FILE...

Recognised citations (outside fenced code blocks):
  `FILE.md` § Section name        FILE.md §3.2        see FILE.md section "Name"
  [text](FILE.md#anchor)          [text](#anchor)     (anchor checked against headings)

Matching is folded (case, accents, punctuation). A label is `ok` when it equals
the heading text after its number prefix is stripped (`6bis. Client scopes` ->
`Client scopes`) or before its subtitle (` (note)`, ` - sub`, ` : sub`), or the heading's number/label token (`6bis`; `3c` checks
section 3), or the heading with prose running on after it. A label equal to the
bold lead of a list item (`- **Label** ...`) is `ok-bullet`. A label that is only
a part of a heading ("Guardrails" against "Absolute guardrails") is `partial`:
reported with the full heading as suggestion, never `ok`. `§ A / B` (also `&`)
cites two sections, each checked on its own line.
A bare `AGENTS.md` resolves to the root AGENTS.md; a path citation is resolved
relative to the repo root, then to the citing file, then by suffix via `git ls-files`
(a bare name other than AGENTS.md: citing file first).

Output, one line per citation: file:line<TAB>target<TAB>status
status: ok | ok-bullet (found as a bold bullet lead only) | partial (only a part of
a heading; a fourth column gives `suggest: <full heading>`) | dead (file or section
missing) | ambiguous (several files match).
Exit 0 when nothing is dead, 1 when something is dead (partial is not dead), 2 on
usage error.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import unicodedata
import sys
from pathlib import Path

EXIT_OK, EXIT_DEAD, EXIT_USAGE = 0, 1, 2

DEFAULT_FILES = ["AGENTS.md", "CLAUDE.md", "AGENTS/INDEX.md", "docs/INDEX.md", "docs/index.md"]
DOMAIN_FILE_NAME = "AGENTS.md"
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build"}

# Shortest leading word run accepted as a section name when the captured text
# runs on into prose ("section Setup and then run it"). One word is too lax.
MIN_WORDS = 2

FENCE_RE = re.compile(r"^\s*(```|~~~)")
HEADING_RE = re.compile(r"^\s{0,3}(#{1,6})\s+(.*?)\s*#*\s*$")
LINK_RE = re.compile(r"(?<!\!)\[[^\]]*\]\(([^)\s#]*)#([^)\s]+)\)")
FILE_PAT = r"`?([\w@.+/-]+\.md)`?"
BULLET_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+\*\*(.+?)\*\*")
LABEL_SPLIT_RE = re.compile(r"\s+[/&+]\s+")
# "FILE § Section", "FILE section Section", "FILE, section Section"
CITE_RE = re.compile(FILE_PAT + r"[\s,:]*(?:§+|\bsections?\b)\s*(?:\"([^\"]+)\"|«\s*([^»]+?)\s*»|“([^”]+)”|`([^`]+)`|([^.;,)\n]+?)(?=\s+(?:and|or|but|see)\s|[.;,)]|$))", re.I)


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
    text = re.sub(r"[`*_~]|\[([^\]]*)\]\([^)]*\)", lambda m: m.group(1) or "", heading).lower()
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
    return re.sub(r"\s", "-", text.strip())


def fold(text: str) -> str:
    """Lowercase and strip accents."""
    return "".join(c for c in unicodedata.normalize("NFKD", text.lower()) if not unicodedata.combining(c))


def words(text: str) -> list[str]:
    plain = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    return re.findall(r"[\w.]+", fold(re.sub(r"[`*_~]", "", plain)))


def lines_outside_fences(path: Path):
    in_fence = False
    for no, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if not in_fence:
            yield no, line


HEADINGS: dict[Path, list[str]] = {}
BULLETS: dict[Path, list[str]] = {}


def headings_of(path: Path) -> list[str]:
    cache = HEADINGS.get(path)
    if cache is None:
        cache = [m.group(2) for _, line in lines_outside_fences(path) if (m := HEADING_RE.match(line))]
        HEADINGS[path] = cache
    return cache


def bullet_leads_of(path: Path) -> list[str]:
    cache = BULLETS.get(path)
    if cache is None:
        cache = [m.group(1) for _, line in lines_outside_fences(path) if (m := BULLET_RE.match(line))]
        BULLETS[path] = cache
    return cache


def norm(text: str) -> str:
    """Folded comparison key: words joined by single spaces."""
    return " ".join(words(text))


SUBTITLE_RE = re.compile(r"\s+[(\u2014\u2013-]|\s*:\s")  # " (note)", " - sub", " : sub"


def title_forms(heading: str) -> list[list[str]]:
    """Word lists a label may equal: full, number-stripped, and each without its subtitle."""
    forms = []
    for text in (heading, SUBTITLE_RE.split(heading, 1)[0]):
        hw = words(text)
        forms += [hw, strip_number(hw)]
    return [f for f in forms if f]


def strip_number(heading_words: list[str]) -> list[str]:
    """Drop a leading number/label token (digit-bearing: 6bis, 3.2, W4)."""
    if len(heading_words) > 1 and re.search(r"\d", heading_words[0]):
        return heading_words[1:]
    return heading_words


def label_match(titles: list[str], cited: str) -> tuple[str, str]:
    """('ok'|'partial'|'dead', matching title) for a cited label against heading titles."""
    cited_words = words(cited)
    if not cited_words:
        return "ok", ""  # nothing checkable was captured
    # "3c" cites lettered item (c) of section 3: check that section 3 exists.
    m = re.fullmatch(r"(\d+(?:\.\d+)*)[a-z]?\.?", cited_words[0])
    number = m.group(1) if m else None
    partial = ""
    for h in titles:
        hw = words(h)
        if not hw:
            continue
        if number and hw[0].rstrip(".") == number.rstrip("."):
            return "ok", h
        # label token: "6bis" -> "6bis. Client scopes"
        if len(cited_words) == 1 and re.search(r"\d", hw[0]) and hw[0].rstrip(".:") == cited_words[0].rstrip(".:"):
            return "ok", h
        for full in title_forms(h):
            if cited_words == full:
                return "ok", h
            # heading followed by prose that ran into the capture ("Setup steps - then run")
            if len(full) >= MIN_WORDS and cited_words[:len(full)] == full:
                return "ok", h
        # a contiguous run of the cited words (or its leading run) inside the heading
        for n in range(len(cited_words), 0, -1):
            run = cited_words[:n]
            if (n >= MIN_WORDS or len(cited_words) == 1) and any(
                    hw[i:i + n] == run for i in range(len(hw) - n + 1)):
                partial = partial or h
                break
    return ("partial", partial) if partial else ("dead", "")


def section_status(path: Path, cited: str) -> tuple[str, str]:
    """(status, suggestion): ok | ok-bullet | partial | dead for one section label."""
    status, title = label_match(headings_of(path), cited)
    if status == "ok":
        return "ok", ""
    b_status, b_title = label_match(bullet_leads_of(path), cited)
    if b_status == "ok":
        return "ok-bullet", ""
    if status == "partial":
        return "partial", title
    return ("partial", b_title) if b_status == "partial" else ("dead", "")


def anchor_exists(path: Path, anchor: str) -> bool:
    seen: dict[str, int] = {}
    slugs = set()
    for h in headings_of(path):
        s = slugify(h)
        n = seen.get(s, 0)
        seen[s] = n + 1
        slugs.add(s if n == 0 else f"{s}-{n}")
    return slugify(anchor) in slugs


def resolve(target: str, base: Path, root: Path, tracked: list[str]) -> tuple[str, Path | None]:
    if "/" in target.strip("/") or target == DOMAIN_FILE_NAME:
        order = (root / target, base.parent / target)  # repo-root citation first
    else:
        order = (base.parent / target, root / target)
    for candidate in order:
        if candidate.is_file():
            return "ok", candidate
    needle = target.strip("/")
    hits = [f for f in tracked if f == needle or f.endswith("/" + needle)]
    if len(hits) == 1:
        return "ok", root / hits[0]
    return ("ambiguous" if hits else "dead"), None


def default_files(root: Path, tracked: list[str]) -> list[Path]:
    names = list(DEFAULT_FILES) + [f for f in tracked if f.endswith("/" + DOMAIN_FILE_NAME)]
    return [root / n for n in dict.fromkeys(names) if (root / n).is_file()]


def main() -> int:
    ap = argparse.ArgumentParser(description="Check that cited sections and anchors exist in their target (read-only).",
                                 epilog="Output: file:line<TAB>target<TAB>status (ok|ok-bullet|dead|ambiguous). "
                                        "Exit 0 none dead, 1 dead found, 2 usage error.")
    ap.add_argument("files", nargs="*", help="markdown files to scan (default: agent docs found in the repo)")
    ap.add_argument("--root", default=".", help="repository root (default: current directory)")
    ap.add_argument("--quiet-ok", action="store_true", help="print only dead and ambiguous lines (hides ok and ok-bullet; partial stays)")
    try:
        args = ap.parse_args()
    except SystemExit as e:
        return EXIT_OK if e.code == 0 else EXIT_USAGE
    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"error: root is not a directory: {args.root}", file=sys.stderr)
        return EXIT_USAGE
    tracked = git_files(root)
    files = [Path(f).resolve() for f in args.files] or default_files(root, tracked)
    missing = [str(f) for f in files if not f.is_file()]
    if missing:
        print("error: not a file: " + ", ".join(missing), file=sys.stderr)
        return EXIT_USAGE
    dead = 0
    for f in files:
        rel = os.path.relpath(f, root)
        for no, line in lines_outside_fences(f):
            found: list[tuple[str, str, str]] = []  # (label, file target, section|anchor)
            for m in LINK_RE.finditer(line):
                if not re.match(r"[A-Za-z][A-Za-z0-9+.-]*:", m.group(1)):
                    found.append((f"{m.group(1)}#{m.group(2)}", m.group(1), "#" + m.group(2)))
            stripped = LINK_RE.sub("", line)
            for m in CITE_RE.finditer(stripped):
                sec = next((g for g in m.groups()[1:] if g), "").strip()
                for label in LABEL_SPLIT_RE.split(sec) if sec else [sec]:
                    found.append((f"{m.group(1)} § {label}", m.group(1), label.strip()))
            for label, target, sec in found:
                status, path = ("ok", f) if not target else resolve(target, f, root, tracked)
                suggestion = ""
                if status == "ok" and path is not None:
                    if sec.startswith("#"):
                        status = "ok" if anchor_exists(path, sec[1:]) else "dead"
                    else:
                        status, suggestion = section_status(path, sec)
                dead += status == "dead"
                if status not in ("ok", "ok-bullet") or not args.quiet_ok:
                    extra = f"\tsuggest: {suggestion}" if suggestion else ""
                    print(f"{rel}:{no}\t{label}\t{status}{extra}")
    return EXIT_DEAD if dead else EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
