#!/usr/bin/env python3
"""Check that a section cited in agent docs exists in the file it points to. Read-only.

    check_sections.py                          # same default files as check_dead_paths.py
    check_sections.py AGENTS.md AGENTS/INDEX.md
    check_sections.py AGENTS/ docs/            # a directory argument recurses into its *.md
    check_sections.py --archives               # scan only the archive dirs (errors/, adr/, postmortems/
                                               # or archives.paths of .claude/agents-md.yml)
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
cites two sections, each checked on its own line. A label may contain " and " / " or "
("Thumbnail origin and cuts"): the full text is tried first, then each cut before
" and " / " or " (prose running on after a short name). A backticked label may be
followed by plain words (`ready` gate): the span alone and span plus words are
both tried, and span plus words that is a leading run of a heading counts as `ok`.
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

DEFAULT_FILES = [
    "AGENTS.md",
    "CLAUDE.md",
    "AGENTS/INDEX.md",
    "docs/INDEX.md",
    "docs/index.md",
]
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
# "FILE § Section", "FILE section Section", "FILE, section Section". Groups 2-4: quoted
# forms; 5/6: a backticked span and the plain words right after it; 7: bare text (runs to
# punctuation; " and "/" or " are handled as cut candidates, "but"/"see" end it).
CITE_RE = re.compile(
    FILE_PAT
    + r"[\s,:]*(?:§+|\bsections?\b)\s*(?:\"([^\"]+)\"|«\s*([^»]+?)\s*»|“([^”]+)”|`([^`]+)`([^.;,)\n`]*?)(?=\s+(?:but|see)\s|[.;,)`]|$)|([^.;,)\n`]+?)(?=\s+(?:but|see)\s|[.;,)]|$))",
    re.I,
)
CUT_RE = re.compile(r"\s+(?:and|or)\s+", re.I)


def git_files(root: Path) -> list[str]:
    try:
        out = subprocess.run(
            ["git", "-C", str(root), "ls-files"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        return [line for line in out.splitlines() if line]
    except (OSError, subprocess.CalledProcessError):
        found = []
        for base, dirs, names in os.walk(root):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            found += [os.path.relpath(os.path.join(base, n), root) for n in names]
        return found


def slugify(heading: str) -> str:
    text = re.sub(
        r"[`*_~]|\[([^\]]*)\]\([^)]*\)", lambda m: m.group(1) or "", heading
    ).lower()
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
    return re.sub(r"\s", "-", text.strip())


def fold(text: str) -> str:
    """Lowercase and strip accents."""
    return "".join(
        c
        for c in unicodedata.normalize("NFKD", text.lower())
        if not unicodedata.combining(c)
    )


def words(text: str) -> list[str]:
    plain = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    return re.findall(r"[\w.]+", fold(re.sub(r"[`*_~]", "", plain)))


def lines_outside_fences(path: Path):
    in_fence = False
    for no, line in enumerate(
        path.read_text(encoding="utf-8", errors="replace").splitlines(), 1
    ):
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
        cache = [
            m.group(2)
            for _, line in lines_outside_fences(path)
            if (m := HEADING_RE.match(line))
        ]
        HEADINGS[path] = cache
    return cache


def bullet_leads_of(path: Path) -> list[str]:
    cache = BULLETS.get(path)
    if cache is None:
        cache = [
            m.group(1)
            for _, line in lines_outside_fences(path)
            if (m := BULLET_RE.match(line))
        ]
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


def label_match(
    titles: list[str], cited: str, lead_ok: bool = False
) -> tuple[str, str]:
    """('ok'|'partial'|'dead', matching title) for a cited label against heading titles.

    lead_ok: the label starts with a backticked span, so a leading run of a heading is `ok`.
    """
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
        if (
            len(cited_words) == 1
            and re.search(r"\d", hw[0])
            and hw[0].rstrip(".:") == cited_words[0].rstrip(".:")
        ):
            return "ok", h
        for full in title_forms(h):
            if cited_words == full:
                return "ok", h
            # heading followed by prose that ran into the capture ("Setup steps - then run")
            if len(full) >= MIN_WORDS and cited_words[: len(full)] == full:
                return "ok", h
            if (
                lead_ok
                and len(full) > len(cited_words) >= MIN_WORDS
                and full[: len(cited_words)] == cited_words
            ):
                return "ok", h
        # a contiguous run of the cited words (or its leading run) inside the heading
        for n in range(len(cited_words), 0, -1):
            run = cited_words[:n]
            if (n >= MIN_WORDS or len(cited_words) == 1) and any(
                hw[i : i + n] == run for i in range(len(hw) - n + 1)
            ):
                partial = partial or h
                break
    return ("partial", partial) if partial else ("dead", "")


def section_status(path: Path, cited: str, lead_ok: bool = False) -> tuple[str, str]:
    """(status, suggestion): ok | ok-bullet | partial | dead for one section label."""
    status, title = label_match(headings_of(path), cited, lead_ok)
    if status == "ok":
        return "ok", ""
    b_status, b_title = label_match(bullet_leads_of(path), cited, lead_ok)
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


def resolve(
    target: str, base: Path, root: Path, tracked: list[str]
) -> tuple[str, Path | None]:
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


RANK = {"ok": 3, "ok-bullet": 2, "partial": 1, "dead": 0}


def label_readings(match: re.Match) -> list[list[tuple[str, bool]]]:
    """One reading list per cited label (a `A / B` citation has two); each reading is
    (label, lead_ok), most complete first (see the module docstring)."""
    quoted = next((g for g in match.groups()[1:4] if g), "")
    span, tail, bare = match.group(5), match.group(6) or "", match.group(7) or ""
    text = (quoted or (span + tail if span else bare)).strip()
    lead = bool(span and tail.strip())
    pieces = [p for p in LABEL_SPLIT_RE.split(text)] if text else [text]
    result = []
    for piece in pieces:
        piece = piece.strip()
        readings = [(piece, lead and len(pieces) == 1)]
        if not quoted:
            readings += [
                (piece[: c.start()].strip(), False) for c in CUT_RE.finditer(piece)
            ]
            if lead and len(pieces) == 1:
                readings.append((span.strip(), False))
        result.append([r for r in readings if r[0] or r is readings[0]])
    return result


def best_reading(path: Path, readings: list[tuple[str, bool]]) -> tuple[str, str, str]:
    """(label, status, suggestion) of the best-scoring reading; among `ok` readings the shortest
    label wins, otherwise the first."""
    best = None
    for label, lead_ok in readings:
        status, suggestion = section_status(path, label, lead_ok)
        if (
            best is None
            or RANK[status] > RANK[best[1]]
            or (
                RANK[status] == RANK[best[1]] == RANK["ok"]
                and len(label) < len(best[0])
            )
        ):
            best = (label, status, suggestion)
    return best


CONFIG_PATH = ".claude/agents-md.yml"
DEFAULT_ARCHIVES = (
    "errors/",
    "adr/",
    "postmortems/",
)  # config-schema.md default for archives.paths


def archive_paths(root: Path) -> list[str]:
    """`archives.paths` from the project config (flow list), else the default archive dirs."""
    try:
        text = (root / CONFIG_PATH).read_text(encoding="utf-8")
    except OSError:
        return list(DEFAULT_ARCHIVES)
    m = re.search(r"^archives:\s*\n((?:[ \t]+.*\n?)+)", text, re.M)
    pm = re.search(r"^[ \t]+paths:\s*\[([^\]]*)\]", m.group(1), re.M) if m else None
    if not pm:
        return list(DEFAULT_ARCHIVES)
    return [p.strip().strip("'\"") for p in pm.group(1).split(",") if p.strip()]


def archive_files(root: Path, tracked: list[str]) -> list[Path]:
    """Every *.md under an archive dir (a relative archive path matches at any depth)."""
    prefixes = [p.strip("/") for p in archive_paths(root)]
    found = []
    for name in tracked or [os.path.relpath(p, root) for p in root.rglob("*.md")]:
        wrapped = "/" + name
        if (
            name.endswith(".md")
            and any(("/" + p + "/") in wrapped for p in prefixes)
            and (root / name).is_file()
        ):
            found.append(root / name)
    return sorted(set(found))


def expand(paths: list[str]) -> list[Path]:
    """Directory arguments recurse into their *.md files."""
    out: list[Path] = []
    for raw in paths:
        p = Path(raw).resolve()
        out += sorted(p.rglob("*.md")) if p.is_dir() else [p]
    return out


def default_files(root: Path, tracked: list[str]) -> list[Path]:
    names = list(DEFAULT_FILES) + [
        f for f in tracked if f.endswith("/" + DOMAIN_FILE_NAME)
    ]
    return [root / n for n in dict.fromkeys(names) if (root / n).is_file()]


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Check that cited sections and anchors exist in their target (read-only).",
        epilog="Output: file:line<TAB>target<TAB>status (ok|ok-bullet|partial|dead|ambiguous). "
        "Exit 0 none dead, 1 dead found, 2 usage error.",
    )
    ap.add_argument(
        "files",
        nargs="*",
        help="markdown files or directories (recursed) to scan (default: agent docs found in the repo)",
    )
    ap.add_argument(
        "--root", default=".", help="repository root (default: current directory)"
    )
    ap.add_argument(
        "--quiet-ok",
        action="store_true",
        help="print only dead and ambiguous lines (hides ok and ok-bullet; partial stays)",
    )
    ap.add_argument(
        "--archives",
        action="store_true",
        help="scan only the archive dirs (archives.paths of .claude/agents-md.yml, else errors/, adr/, postmortems/)",
    )
    try:
        args = ap.parse_args()
    except SystemExit as e:
        return EXIT_OK if e.code == 0 else EXIT_USAGE
    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"error: root is not a directory: {args.root}", file=sys.stderr)
        return EXIT_USAGE
    tracked = git_files(root)
    missing = [f for f in args.files if not Path(f).exists()]
    files = (
        expand(args.files)
        if args.files
        else (
            archive_files(root, tracked)
            if args.archives
            else default_files(root, tracked)
        )
    )
    missing += [str(f) for f in files if not f.is_file()]
    if missing:
        print("error: not a file: " + ", ".join(missing), file=sys.stderr)
        return EXIT_USAGE
    dead = 0
    for f in files:
        rel = os.path.relpath(f, root)
        for no, line in lines_outside_fences(f):
            found: list[
                tuple[str, list, str]
            ] = []  # (file target, section readings, link label)
            for m in LINK_RE.finditer(line):
                if not re.match(r"[A-Za-z][A-Za-z0-9+.-]*:", m.group(1)):
                    found.append(
                        (
                            m.group(1),
                            [("#" + m.group(2), False)],
                            f"{m.group(1)}#{m.group(2)}",
                        )
                    )
            stripped = LINK_RE.sub("", line)
            for m in CITE_RE.finditer(stripped):
                for readings in label_readings(m):
                    found.append((m.group(1), readings, ""))
            for target, readings, link_label in found:
                status, path = (
                    ("ok", f) if not target else resolve(target, f, root, tracked)
                )
                suggestion = ""
                label = link_label or f"{target} § {readings[0][0]}"
                if status == "ok" and path is not None:
                    if readings[0][0].startswith("#"):
                        status = (
                            "ok" if anchor_exists(path, readings[0][0][1:]) else "dead"
                        )
                    else:
                        chosen, status, suggestion = best_reading(path, readings)
                        if status != "dead":
                            label = f"{target} § {chosen}"
                dead += status == "dead"
                if status not in ("ok", "ok-bullet") or not args.quiet_ok:
                    extra = f"\tsuggest: {suggestion}" if suggestion else ""
                    print(f"{rel}:{no}\t{label}\t{status}{extra}")
    return EXIT_DEAD if dead else EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
