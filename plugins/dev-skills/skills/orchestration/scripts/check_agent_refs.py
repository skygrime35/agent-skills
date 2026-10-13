#!/usr/bin/env python3
# dev-skills: orchestration __PLUGIN_VERSION__
"""Verify that a doc's orchestration section, the installed agent type files,
and the orchestration config agree with each other.

Mechanizes checks O1.1 (cited agent type installed nowhere), O6.1/O6.2/O6.4
(frontmatter hygiene), O8.1 (xhigh/max effort, reported for a quirks check)
and O1.4/O2.1 (config vs reality) of the /orchestration skill. Stdlib only. Exit 1 on any finding, findings printed as
`file:line: message`.

Absent --agents-dir: a directory that does not exist is reported as a
`warning:` line and leaves the exit code alone (nothing can be verified against
it, e.g. a CI runner without the global agents dir); when every given dir is
absent, a cited or listed type that cannot be found is a warning too. With
`--strict` an absent dir is an error, and so is every unresolved type. In 1.5.0
an absent dir failed the check (exit 1); since 1.6.0 it only warns. Pass
`--strict` where a missing dir must fail the build.

--only-owned (CI / pre-commit mode, needs --config): frontmatter checks are
errors only for the types the project owns: those listed in `agents.types` or
`agents.overrides` of the config AND installed in a project-scope dir. A type
whose only file sits in a global dir (`~/.claude/agents` or any
--global-agents-dir) is never owned, even if a legacy config lists it. Frontmatter issues of any other installed
file (hand-written, machine-local agents) are printed as `warning:` lines and
leave the exit code alone. When the config says `agents.location: global` and
an --agents-dir does not exist (CI runner), a cited or listed type that cannot
be found is also a `warning:`, not an error (unless `--strict`). Without the
flag, frontmatter checks cover every installed file.

Global types (machine-local): the committed config lists only project-scope
types. The global types the doctrine relies on are recorded with their values
in `.claude/orchestration.local.yml` (gitignored), under `local.global_types`
(`--local-config`, default: `orchestration.local.yml` next to --config, when
it exists). A recorded global type that is installed is compared with its
local entry (model/effort/maxTurns): a mismatch is a `warning:`; one that is
absent is a `warning:`. With --only-owned, a cited type that is not in the
config is also only a warning when absent. `--strict` makes all of these
errors.

Usage:
  check_agent_refs.py --doc AGENTS.md [--section-heading "..."]...
                      --agents-dir ~/.claude/agents [--agents-dir .claude/agents]
                      [--config .claude/orchestration.yml] [--only-owned] [--strict]
                      [--local-config .claude/orchestration.local.yml]
                      [--global-agents-dir ~/.claude/agents]
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
warnings = []
QUIRKS = ""  # text of the config's quirks block; a type named there may run at xhigh/max


def finding(path, line, message):
    findings.append(f"{path}:{line}: {message}")


def warning(path, line, message):
    warnings.append(f"warning: {path}:{line}: {message}")


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


def check_frontmatter(name, path, finding=finding):
    """`finding` is the sink: errors by default, `warning` for non-owned files."""
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


def config_entries(config_path):
    """Minimal YAML scrape of agents.types and agents.overrides entries.

    Returns {name: (entry, line, section)} with section in {"types", "overrides"}.
    """
    entries = {}
    section = None
    for i, raw in enumerate(config_path.read_text(encoding="utf-8").splitlines(), 1):
        stripped = raw.strip()
        m = re.match(r"^(types|overrides)\s*:", stripped)
        if m:
            section = m.group(1)
            continue
        if section:
            if stripped.startswith("- ") or stripped.startswith("-{") or stripped.startswith("- {"):
                entry = dict(re.findall(r"\b(name|model|effort|maxTurns)\s*:\s*([A-Za-z0-9-]+)", stripped))
                if entry.get("name"):
                    entries[entry["name"]] = (entry, i, section)
            elif stripped and not raw.startswith((" ", "\t")):
                section = None
    return entries


def config_types(config_path):
    """Owned types and overrides as {name: (entry, line)}."""
    return {n: (e, i) for n, (e, i, _) in config_entries(config_path).items()}


def config_location(config_path):
    """Value of `agents.location` (global | project), or None when absent."""
    in_agents = False
    for raw in config_path.read_text(encoding="utf-8").splitlines():
        if re.match(r"^agents\s*:", raw):
            in_agents = True
        elif in_agents and raw.strip() and not raw.startswith((" ", "\t")):
            in_agents = False
        elif in_agents:
            m = re.match(r"^\s+location\s*:\s*([A-Za-z]+)", raw)
            if m:
                return m.group(1)
    return None


def local_global_types(local_path):
    """Entries of `global_types:` in the local file as {name: (entry, line)}."""
    entries, inside = {}, False
    for i, raw in enumerate(local_path.read_text(encoding="utf-8").splitlines(), 1):
        stripped = raw.strip()
        if re.match(r"^global_types\s*:", stripped):
            inside = True
            continue
        if inside:
            if stripped.startswith("-"):
                entry = dict(re.findall(r"\b(name|model|effort|maxTurns)\s*:\s*([A-Za-z0-9.-]+)", stripped))
                if entry.get("name"):
                    entries[entry["name"]] = (entry, i)
            elif stripped and not stripped.startswith("#"):
                inside = False
    return entries


def is_global_dir(path):
    """True for the user-level agents dir or a dir passed as --global-agents-dir."""
    resolved = Path(path).expanduser().resolve()
    globals_ = [Path("~/.claude/agents").expanduser().resolve()]
    globals_ += [Path(g).expanduser().resolve() for g in (ARGS.global_agents_dir or [])]
    return resolved in globals_


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

    owned = set()
    config_names = set()
    degraded = False  # global types expected, but an agents dir is absent (CI)
    config_ok = bool(ARGS.config) and Path(ARGS.config).is_file()
    if ARGS.only_owned and config_ok:
        config_names = set(config_types(Path(ARGS.config)))
        # Owned = listed in the config AND installed in a project-scope dir.
        owned = {n for n in config_names
                 if any(not is_global_dir(p.parent) for p in installed.get(n, []))}
        missing_dirs = [d for d in ARGS.agents_dir if not Path(d).expanduser().is_dir()]
        if missing_dirs and config_location(Path(ARGS.config)) == "global":
            degraded = True
            warning(ARGS.config, 1, "agents.location is global and agents dir missing ("
                    + ", ".join(missing_dirs) + "): global types cannot be verified here")
    missing_dirs = [d for d in ARGS.agents_dir if not Path(d).expanduser().is_dir()]
    for d in missing_dirs:
        (finding if ARGS.strict else warning)(d, 1, "agents dir does not exist")
    if ARGS.strict:
        degraded = False
    # Sink for "type not found": nothing to verify against when every dir is absent.
    all_absent = len(missing_dirs) == len(ARGS.agents_dir)
    miss = warning if (degraded or (all_absent and not ARGS.strict)) else finding

    # Step 2: frontmatter hygiene on every installed type (O6.1 / O6.2)
    parsed = {}
    for name, paths in installed.items():
        sink = warning if ARGS.only_owned and name not in owned else finding
        for p in paths:
            fm = check_frontmatter(name, p, sink)
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
                    # Under --only-owned a cited type the config does not list is a
                    # global (machine-local) type: absent is a warning, not an error.
                    sink = miss
                    if (ARGS.only_owned and config_ok and not ARGS.strict
                            and token not in config_names):
                        sink = warning
                    sink(doc_path, lineno,
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
                    miss(config_path, lineno,
                         f"config lists type {name!r} but no parseable file exists")
                    continue
                legacy_global = ARGS.only_owned and name not in owned
                sink3 = warning if legacy_global and not ARGS.strict else finding
                for key in ("model", "effort", "maxTurns"):
                    if entry.get(key) and parsed[name].get(key) != entry[key]:
                        sink3(config_path, lineno,
                                f"config says {name}.{key}={entry[key]!r}, "
                                f"file says {parsed[name].get(key)!r}")
        else:
            finding(config_path, 1, "config file not found")

    # Step 4: global types recorded in the local file (D1 design: machine-local)
    local_path = Path(ARGS.local_config) if ARGS.local_config else (
        Path(ARGS.config).with_name("orchestration.local.yml") if ARGS.config else None)
    if local_path and local_path.is_file():
        sink4 = finding if ARGS.strict else warning
        for name, (entry, lineno) in local_global_types(local_path).items():
            if name not in parsed:
                sink4(local_path, lineno,
                      f"local file records global type {name!r} but no parseable file is installed")
                continue
            for key in ("model", "effort", "maxTurns"):
                if entry.get(key) and parsed[name].get(key) != entry[key]:
                    sink4(local_path, lineno,
                          f"local file says {name}.{key}={entry[key]!r}, "
                          f"installed file says {parsed[name].get(key)!r}")

    for f in findings + warnings:
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
    parser.add_argument("--only-owned", action="store_true",
                        help="errors only for types listed in the config's agents.types / "
                             "agents.overrides; other files and missing global dirs only warn")
    parser.add_argument("--local-config", default=None,
                        help=".claude/orchestration.local.yml (default: next to --config); "
                             "its local.global_types are compared with the installed files "
                             "(mismatch or absence: warning, error with --strict)")
    parser.add_argument("--global-agents-dir", action="append", default=None,
                        help="agents dir holding machine-local (global) types, besides "
                             "~/.claude/agents; its types are never owned (repeatable)")
    parser.add_argument("--strict", action="store_true",
                        help="an absent --agents-dir (and every unresolved type) is an error, "
                             "not a warning")
    ARGS = parser.parse_args()
    if ARGS.only_owned and not ARGS.config:
        parser.error("--only-owned requires --config")
    sys.exit(main())
