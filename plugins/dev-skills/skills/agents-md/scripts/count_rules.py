#!/usr/bin/env python3
"""Count normative statements and prohibitions in agent documentation files.

Read-only audit tool, run in place (never copied into a project). Canonical
counter for the instruction budget and the non-regression prohibition count;
the method is defined in references/structure.md (Instruction budget).

Unit, in a normative section: every list item and every table body row counts
as one statement (a rule list needs no modal word), plus every prose sentence
carrying a modal marker. Non-normative sections (heading matching stack,
architecture, structure, commands, references, index or the French
equivalents; see DEFAULT_SKIP, override with --skip-heading, disable with
--no-skip) and their subsections do not use the structural rule: only a unit
that carries an explicit modal marker counts there, so no stated prohibition
is ever lost. Prohibition: a counted statement carrying a negative marker.
Fenced code, HTML comments, front matter, headings and table header rows are
skipped. A heuristic, about +/-10%.

JSON: per file `statements`, `prohibitions`, `sections` (own units only, each
with `skipped`); top level `totals` {statements, prohibitions} over all files;
with --section-heading, `selected_totals` sums every selected section once
(a section matched by two patterns, or as a subsection of a matched parent, is
not counted twice).

Usage: count_rules.py FILE... [--section-heading TEXT]... [--lang auto|en|fr]
                      [--skip-heading REGEX]... [--no-skip]
Exit codes: 0 counted, 2 usage error or unreadable file.
"""

import argparse
import json
import re
import sys
import unicodedata

MODALS = {
    "en": ["must", "never", "always", "required", "forbidden", "shall", "do not"],
    "fr": [
        "doit",
        "doivent",
        "jamais",
        "toujours",
        "obligatoire",
        "obligatoires",
        "interdit",
        "interdite",
        "interdits",
        "interdites",
        "ne pas",
        "ne jamais",
        "aucun",
        "aucune",
        "il faut",
    ],
}
PROHIBITIONS = {
    "en": ["never", "must not", "forbidden", "do not", "don't"],
    "fr": [
        "jamais",
        "interdit",
        "interdite",
        "interdits",
        "interdites",
        "ne pas",
        "aucun",
        "aucune",
    ],
}
# Stopwords used only to guess the language of a file in --lang auto.
STOP = {
    "en": {"the", "is", "and", "for", "with", "that", "this", "are", "to", "of"},
    "fr": {
        "le",
        "la",
        "les",
        "des",
        "est",
        "une",
        "pour",
        "dans",
        "que",
        "qui",
        "avec",
        "sur",
        "du",
    },
}
# Headings (folded) whose sections hold facts, not rules: the every-item rule is off there.
DEFAULT_SKIP = [
    r"\b(?:stack|architecture|structure|commands?|references?|index)\b",
    r"\b(?:pile|arborescence|commandes?|sommaire|table of contents)\b",
]
HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
LIST_ITEM = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+(.*)$")
FENCE = re.compile(r"^\s*(```|~~~)")


def fold(text):
    """Lowercase and strip accents so matching is accent- and case-insensitive."""
    nfkd = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in nfkd if not unicodedata.combining(c)).replace("’", "'")


def compile_markers(words):
    alts = "|".join(re.escape(fold(w)).replace(r"\ ", r"\s+") for w in words)
    return re.compile(r"(?<![\w'])(?:%s)(?![\w])" % alts)


MODAL_RE = {k: compile_markers(v) for k, v in MODALS.items()}
PROHIB_RE = {k: compile_markers(v) for k, v in PROHIBITIONS.items()}


def detect_lang(text):
    words = re.findall(r"[a-z']+", fold(text))
    fr = sum(1 for w in words if w in STOP["fr"])
    en = sum(1 for w in words if w in STOP["en"])
    return "fr" if fr > en else "en"


def split_units(lines):
    """Return (sections, units); a unit is (heading_index, kind, text), kind item|row|prose."""
    section = -1
    para = []
    item = None
    in_fence = in_comment = False
    sections = []

    def flush_para():
        if para:
            for s in re.split(r"(?<=[.!?])\s+", " ".join(para)):
                if s.strip():
                    units.append((section, "prose", s))
            para.clear()

    def flush_item():
        nonlocal item
        if item is not None:
            units.append((section, "item", item))
            item = None

    units = []
    table_last = None
    for i, line in enumerate(lines):
        if i == 0 and line.strip() == "---":
            in_comment = "frontmatter"
            continue
        if in_comment == "frontmatter":
            if line.strip() == "---":
                in_comment = False
            continue
        if in_comment:
            if "-->" in line:
                in_comment = False
            continue
        if FENCE.match(line):
            flush_para()
            flush_item()
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if line.lstrip().startswith("<!--"):
            if "-->" not in line:
                in_comment = True
            continue
        m = HEADING.match(line)
        if m:
            flush_para()
            flush_item()
            sections.append({"level": len(m.group(1)), "heading": m.group(2)})
            section = len(sections) - 1
            continue
        if not line.strip():
            flush_para()
            flush_item()
            continue
        if line.lstrip().startswith("|"):
            flush_para()
            flush_item()
            if re.fullmatch(r"[\s|:-]+", line):
                if table_last is not None and table_last == len(units) - 1:
                    units.pop()  # the row above a separator is the header
                table_last = None
            else:
                units.append((section, "row", line))
                table_last = len(units) - 1
            continue
        li = LIST_ITEM.match(line)
        if li:
            flush_para()
            flush_item()
            item = li.group(1)
            continue
        if item is not None and line.startswith((" ", "\t")):
            item += " " + line.strip()
            continue
        flush_item()
        para.append(line.strip())
    flush_para()
    flush_item()
    return sections, units


def skipped_flags(sections, skip_res):
    """Per section: True when its heading, or an ancestor's, is non-normative."""
    flags, stack = [], []  # stack of (level, skipped)
    for sec in sections:
        while stack and stack[-1][0] >= sec["level"]:
            stack.pop()
        own = any(r.search(fold(sec["heading"])) for r in skip_res)
        flags.append(own or (bool(stack) and stack[-1][1]))
        stack.append((sec["level"], flags[-1]))
    return flags


def count_file(path, lang_opt, skip_res):
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    lang = detect_lang(text) if lang_opt == "auto" else lang_opt
    lines = text.splitlines()
    sections, units = split_units(lines)
    flags = skipped_flags(sections, skip_res)
    stats = [
        {
            "heading": s["heading"],
            "level": s["level"],
            "skipped": flags[n],
            "statements": 0,
            "prohibitions": 0,
        }
        for n, s in enumerate(sections)
    ]
    preamble = {
        "heading": "(before first heading)",
        "level": 0,
        "skipped": False,
        "statements": 0,
        "prohibitions": 0,
    }
    for idx, kind, unit in units:
        folded = fold(unit)
        target = stats[idx] if idx >= 0 else preamble
        structural = kind in ("item", "row") and not target["skipped"]
        if structural or MODAL_RE[lang].search(folded):
            target["statements"] += 1
            if PROHIB_RE[lang].search(folded):
                target["prohibitions"] += 1
    all_sections = ([preamble] if preamble["statements"] else []) + stats
    return {
        "path": path,
        "lang": lang,
        "statements": sum(s["statements"] for s in all_sections),
        "prohibitions": sum(s["prohibitions"] for s in all_sections),
        "sections": all_sections,
    }


def select(result, pattern):
    """Aggregate sections whose heading contains the pattern, plus their subsections.

    Returns the summary and the covered section objects (identity set for dedup).
    """
    needle = fold(pattern)
    secs = [s for s in result["sections"] if s["level"] > 0]
    matched, covered = [], []
    i = 0
    while i < len(secs):
        if needle in fold(secs[i]["heading"]):
            level = secs[i]["level"]
            matched.append(secs[i]["heading"])
            j = i
            while j < len(secs) and (j == i or secs[j]["level"] > level):
                covered.append(secs[j])
                j += 1
            i = j
        else:
            i += 1
    summary = {
        "pattern": pattern,
        "matched": matched,
        "statements": sum(s["statements"] for s in covered),
        "prohibitions": sum(s["prohibitions"] for s in covered),
    }
    return summary, covered


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Count normative statements and prohibitions (read-only, JSON on stdout)."
    )
    ap.add_argument("files", nargs="+", help="Markdown files to count")
    ap.add_argument(
        "--section-heading",
        action="append",
        default=[],
        metavar="TEXT",
        help="also total the section whose heading contains TEXT (accent- and "
        "case-insensitive, subsections included); repeatable",
    )
    ap.add_argument(
        "--lang",
        choices=["auto", "en", "fr"],
        default="auto",
        help="marker list: auto guesses per file (default)",
    )
    ap.add_argument(
        "--skip-heading",
        action="append",
        default=None,
        metavar="REGEX",
        help="regex on the folded heading marking a non-normative section "
        "(replaces the defaults; repeatable)",
    )
    ap.add_argument(
        "--no-skip", action="store_true", help="treat every section as normative"
    )
    args = ap.parse_args(argv)
    patterns = [] if args.no_skip else (args.skip_heading or DEFAULT_SKIP)
    try:
        skip_res = [re.compile(p) for p in patterns]
    except re.error as exc:
        print("count_rules.py: bad --skip-heading regex: %s" % exc, file=sys.stderr)
        return 2
    results, covered_ids, covered = [], set(), []
    for path in args.files:
        try:
            res = count_file(path, args.lang, skip_res)
        except (OSError, UnicodeDecodeError) as exc:
            print("count_rules.py: cannot read %s: %s" % (path, exc), file=sys.stderr)
            return 2
        if args.section_heading:
            res["selected"] = []
            for p in args.section_heading:
                summary, cov = select(res, p)
                res["selected"].append(summary)
                for sec in cov:
                    if id(sec) not in covered_ids:
                        covered_ids.add(id(sec))
                        covered.append(sec)
        results.append(res)
    out = {
        "files": results,
        "totals": {
            "statements": sum(r["statements"] for r in results),
            "prohibitions": sum(r["prohibitions"] for r in results),
        },
        "total_statements": sum(r["statements"] for r in results),
        "total_prohibitions": sum(r["prohibitions"] for r in results),
        "note": "heuristic, about +/-10%; harness share not included",
    }
    if args.section_heading:
        out["selected_totals"] = {
            "statements": sum(s["statements"] for s in covered),
            "prohibitions": sum(s["prohibitions"] for s in covered),
        }
    json.dump(out, sys.stdout, indent=2, ensure_ascii=False)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
