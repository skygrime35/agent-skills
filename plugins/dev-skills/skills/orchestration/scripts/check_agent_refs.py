#!/usr/bin/env python3
"""Verify that a doc's orchestration section, the installed agent type files,
and the orchestration config agree with each other.

Mechanizes checks O1.1 (cited agent type installed nowhere), O6.1/O6.2/O6.4
(frontmatter hygiene), O8.1 (xhigh/max effort, reported for a quirks check)
and O1.4/O2.1 (config vs reality) of the /orchestration skill. Stdlib only. Exit 1 on any finding, findings printed as
`file:line: message`.

Usage:
  check_agent_refs.py --doc AGENTS.md [--section-heading "..."]...
                      --agents-dir ~/.claude/agents [--agents-dir .claude/agents]
                      [--config .claude/orchestration.yml]
"""

import argparse
import re
import sys
from pathlib import Path

EFFORTS = {"low", "medium", "high", "xhigh", "max"}
COLORS = {"red", "blue", "green", "yellow", "purple", "orange", "pink", "cyan"}
KNOWN_MODELS = {"fable", "opus", "sonnet", "haiku"}
KEBAB = re.compile(r"`([a-z0-9]+(?:-[a-z0-9]+)+)`")

findings = []
QUIRKS = ""  # text of the config's quirks block; a type named there may run at xhigh/max


def finding(path, line, message):
    findings.append(f"{path}:{line}: {message}")


def parse_frontmatter(path):
    """Return (dict, first_body_line_index) or (None, 0) when malformed."""
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return None, 0
    fm = {}
    for i, raw in enumerate(lines[1:], start=2):
        if raw.strip() == "---":
            return fm, i
        m = re.match(r"^([A-Za-z_-]+)\s*:\s*(.*)$", raw)
        if m:
            fm[m.group(1)] = m.group(2).strip()
    return None, 0


def section_span(doc_lines, heading):
    """Lines of the owned section: from the heading to the next same-level heading."""
    if heading is None:
        return list(enumerate(doc_lines, start=1))
    level = None
    start = None
    for i, line in enumerate(doc_lines, start=1):
        if line.strip() == heading.strip() or heading.strip() in line:
            m = re.match(r"^(#+)", line)
            if m:
                level, start = len(m.group(1)), i
                break
    if start is None:
        finding(ARGS.doc, 1, f"section heading not found: {heading!r}")
        return []
    span = []
    for i, line in enumerate(doc_lines[start:], start=start + 1):
        m = re.match(r"^(#+)\s", line)
        if m and len(m.group(1)) <= level:
            break
        span.append((i, line))
    return span


def collect_agent_files(dirs):
    files = {}
    for d in dirs:
        d = Path(d).expanduser()
        if not d.is_dir():
            continue
        for f in sorted(d.glob("*.md")):
            files.setdefault(f.stem, []).append(f)
    return files


def check_frontmatter(name, path):
    fm, body_start = parse_frontmatter(path)
    if fm is None:
        finding(path, 1, "malformed or missing frontmatter")
        return None
    for key, value in fm.items():
        if ": " in value and value[:1] not in ("\"", "'"):
            finding(path, 1, f"unquoted {key} value contains ': ', invalid YAML: quote it")
    for key in ("name", "description", "model", "effort"):
        if not fm.get(key):
            finding(path, 1, f"frontmatter missing required key: {key}")
    if fm.get("name") and fm["name"] != name:
        finding(path, 2, f"frontmatter name {fm['name']!r} != filename stem {name!r}")
    if fm.get("effort") and fm["effort"] not in EFFORTS:
        finding(path, 1, f"effort {fm['effort']!r} not in {sorted(EFFORTS)}")
    if fm.get("effort") in ("xhigh", "max") and name not in QUIRKS:
        finding(path, 1, f"effort {fm['effort']!r} with no quirks entry naming {name!r} (O8.1)")
    if "maxTurns" in fm and not re.fullmatch(r"[1-9][0-9]*", fm["maxTurns"]):
        finding(path, 1, f"maxTurns {fm['maxTurns']!r} is not a positive integer")
    if fm.get("color") and fm["color"] not in COLORS:
        finding(path, 1, f"color {fm['color']!r} not in {sorted(COLORS)}")
    body = path.read_text(encoding="utf-8").splitlines()[body_start:]
    if not any(line.strip() for line in body):
        finding(path, body_start + 1, "empty body: a type needs a system prompt")
    return fm


def config_types(config_path):
    """Minimal YAML scrape of agents.types entries: name/model/effort."""
    types = {}
    in_types = False
    for i, raw in enumerate(config_path.read_text(encoding="utf-8").splitlines(), 1):
        stripped = raw.strip()
        if re.match(r"^types\s*:", stripped):
            in_types = True
            continue
        if in_types:
            if stripped.startswith("- ") or stripped.startswith("-{") or stripped.startswith("- {"):
                entry = dict(re.findall(r"\b(name|model|effort|maxTurns)\s*:\s*([A-Za-z0-9-]+)", stripped))
                if entry.get("name"):
                    types[entry["name"]] = (entry, i)
            elif stripped and not raw.startswith((" ", "\t")):
                in_types = False
    return types


def quirks_text(config_path):
    """Raw text of the top-level `quirks:` block, up to the next top-level key."""
    out, inside = [], False
    for raw in config_path.read_text(encoding="utf-8").splitlines():
        if re.match(r"^quirks\s*:", raw):
            inside = True
            out.append(raw)
        elif inside and raw.strip() and not raw.startswith((" ", "\t", "-")):
            break
        elif inside:
            out.append(raw)
    return "\n".join(out)


def main():
    global QUIRKS
    if ARGS.config and Path(ARGS.config).is_file():
        QUIRKS = quirks_text(Path(ARGS.config))
    doc_path = Path(ARGS.doc)
    installed = collect_agent_files(ARGS.agents_dir)

    # Step 2: frontmatter hygiene on every installed type (O6.1 / O6.2)
    parsed = {}
    for name, paths in installed.items():
        for p in paths:
            fm = check_frontmatter(name, p)
            if fm:
                parsed[name] = fm

    # Step 1: cited types resolve against the installed set (O1.1)
    if doc_path.is_file():
        doc_lines = doc_path.read_text(encoding="utf-8").splitlines()
        headings = ARGS.section_heading or [None]
        spans = [item for h in headings for item in section_span(doc_lines, h)]
        for lineno, line in spans:
            for token in KEBAB.findall(line):
                model_prefix = token.split("-", 1)[0]
                looks_like_type = token in parsed or model_prefix in KNOWN_MODELS
                if looks_like_type and token not in installed:
                    finding(doc_path, lineno,
                            f"cited agent type `{token}` installed in none of: "
                            + ", ".join(ARGS.agents_dir))
    else:
        finding(doc_path, 1, "doc file not found")

    # Step 3: config vs reality (O1.4 / O2.1)
    if ARGS.config:
        config_path = Path(ARGS.config)
        if config_path.is_file():
            for name, (entry, lineno) in config_types(config_path).items():
                if name not in parsed:
                    finding(config_path, lineno,
                            f"config lists type {name!r} but no parseable file exists")
                    continue
                for key in ("model", "effort", "maxTurns"):
                    if entry.get(key) and parsed[name].get(key) != entry[key]:
                        finding(config_path, lineno,
                                f"config says {name}.{key}={entry[key]!r}, "
                                f"file says {parsed[name].get(key)!r}")
        else:
            finding(config_path, 1, "config file not found")

    for f in findings:
        print(f)
    return 1 if findings else 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--doc", required=True, help="base doc file (AGENTS.md / CLAUDE.md)")
    parser.add_argument("--section-heading", action="append", default=None,
                        help="heading of an owned section; repeat once per span "
                             "(config section_spans); whole doc if omitted")
    parser.add_argument("--agents-dir", action="append", required=True,
                        help="directory of agent type .md files (repeatable)")
    parser.add_argument("--config", default=None, help=".claude/orchestration.yml")
    ARGS = parser.parse_args()
    sys.exit(main())
