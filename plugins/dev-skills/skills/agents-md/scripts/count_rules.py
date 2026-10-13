#!/usr/bin/env python3
"""Count normative statements and prohibitions in agent documentation files.

Read-only audit tool, run in place (never copied into a project). Canonical
counter for the instruction budget and the non-regression prohibition count;
the method is defined in references/structure.md (Instruction budget).

Unit: one list item, table row or prose sentence carrying a modal marker counts
once, however many markers it holds. Prohibition: a statement carrying a
negative marker. Fenced code, HTML comments, front matter and headings are
skipped. The count is a lower-bound heuristic (modal-based), about +/-10%.

Usage: count_rules.py FILE... [--section-heading TEXT]... [--lang auto|en|fr]
Exit codes: 0 counted, 2 usage error or unreadable file.
"""
import argparse
import json
import re
import sys
import unicodedata

MODALS = {
    "en": ["must", "never", "always", "required", "forbidden", "shall", "do not"],
    "fr": ["doit", "doivent", "jamais", "toujours", "obligatoire", "obligatoires",
           "interdit", "interdite", "interdits", "interdites", "ne pas",
           "ne jamais", "aucun", "aucune", "il faut"],
}
PROHIBITIONS = {
    "en": ["never", "must not", "forbidden", "do not", "don't"],
    "fr": ["jamais", "interdit", "interdite", "interdits", "interdites", "ne pas", "aucun", "aucune"],
}
# Stopwords used only to guess the language of a file in --lang auto.
STOP = {
    "en": {"the", "is", "and", "for", "with", "that", "this", "are", "to", "of"},
    "fr": {"le", "la", "les", "des", "est", "une", "pour", "dans", "que", "qui", "avec", "sur", "du"},
}
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
    """Yield (heading_index, unit_text): list items, table rows, prose sentences."""
    section = -1
    para = []
    item = None
    in_fence = in_comment = False
    sections = []

    def flush_para():
        if para:
            for s in re.split(r"(?<=[.!?])\s+", " ".join(para)):
                if s.strip():
                    units.append((section, s))
            para.clear()

    def flush_item():
        nonlocal item
        if item is not None:
            units.append((section, item))
            item = None

    units = []
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
            flush_para(); flush_item()
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
            flush_para(); flush_item()
            sections.append({"level": len(m.group(1)), "heading": m.group(2)})
            section = len(sections) - 1
            continue
        if not line.strip():
            flush_para(); flush_item()
            continue
        if line.lstrip().startswith("|"):
            flush_para(); flush_item()
            if not re.fullmatch(r"[\s|:-]+", line):
                units.append((section, line))
            continue
        li = LIST_ITEM.match(line)
        if li:
            flush_para(); flush_item()
            item = li.group(1)
            continue
        if item is not None and line.startswith((" ", "\t")):
            item += " " + line.strip()
            continue
        flush_item()
        para.append(line.strip())
    flush_para(); flush_item()
    return sections, units


def count_file(path, lang_opt):
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    lang = detect_lang(text) if lang_opt == "auto" else lang_opt
    lines = text.splitlines()
    sections, units = split_units(lines)
    stats = [{"heading": s["heading"], "level": s["level"], "statements": 0, "prohibitions": 0}
             for s in sections]
    preamble = {"heading": "(before first heading)", "level": 0, "statements": 0, "prohibitions": 0}
    for idx, unit in units:
        folded = fold(unit)
        if MODAL_RE[lang].search(folded):
            target = stats[idx] if idx >= 0 else preamble
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
    """Aggregate sections whose heading contains the pattern, plus their subsections."""
    needle = fold(pattern)
    secs = [s for s in result["sections"] if s["level"] > 0]
    matched, stm, pro = [], 0, 0
    i = 0
    while i < len(secs):
        if needle in fold(secs[i]["heading"]):
            level = secs[i]["level"]
            matched.append(secs[i]["heading"])
            j = i
            while j < len(secs) and (j == i or secs[j]["level"] > level):
                stm += secs[j]["statements"]
                pro += secs[j]["prohibitions"]
                j += 1
            i = j
        else:
            i += 1
    return {"pattern": pattern, "matched": matched, "statements": stm, "prohibitions": pro}


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Count normative statements and prohibitions (read-only, JSON on stdout).")
    ap.add_argument("files", nargs="+", help="Markdown files to count")
    ap.add_argument("--section-heading", action="append", default=[], metavar="TEXT",
                    help="also total the section whose heading contains TEXT (accent- and "
                         "case-insensitive, subsections included); repeatable")
    ap.add_argument("--lang", choices=["auto", "en", "fr"], default="auto",
                    help="marker list: auto guesses per file (default)")
    args = ap.parse_args(argv)
    results = []
    for path in args.files:
        try:
            res = count_file(path, args.lang)
        except (OSError, UnicodeDecodeError) as exc:
            print("count_rules.py: cannot read %s: %s" % (path, exc), file=sys.stderr)
            return 2
        if args.section_heading:
            res["selected"] = [select(res, p) for p in args.section_heading]
        results.append(res)
    out = {
        "files": results,
        "total_statements": sum(r["statements"] for r in results),
        "total_prohibitions": sum(r["prohibitions"] for r in results),
        "note": "modal-based lower bound, about +/-10%; harness share not included",
    }
    json.dump(out, sys.stdout, indent=2, ensure_ascii=False)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
