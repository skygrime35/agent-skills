#!/usr/bin/env python3
"""Measure what each subagent type actually costs, from local Claude Code transcripts.

Probe D12 of the /orchestration skill; feeds audit family O8 and the maxTurns
calibration. Read-only, stdlib only, nothing leaves the machine.

The last section lists, per type, every resolved `message.model` and Claude Code
CLI `version` seen (alias resolution audit, check O8.10).

Costs are estimates at API list prices (PRICES below, a mirror of
references/models.md: update both in the same batch). On a subscription, read
them as relative quota consumption. Assistant messages are de-duplicated by
message id, since a transcript writes one line per content block.

Scope. By default only the current repository's transcripts are read: Claude
Code stores them in ~/.claude/projects/<cwd with every non-alphanumeric
character replaced by "-">/. The repository is the git repo of the cwd: its main
checkout, every listed worktree, and any folder named after the main checkout
followed by "-" (sibling worktrees `<repo>-<task>`, including removed ones, and
Claude Code's `<repo>--claude-worktrees-<name>`). Outside a git repo, the cwd alone. `--all-projects` widens to every project, `--project SUBSTR`
keeps the folders whose name contains SUBSTR.

Window. A transcript counts when its session started on or after the start
date. Start date, first match wins: `--since YYYY-MM-DD`; `--days N`; the oldest
mtime of the installed agent type files (~/.claude/agents/*.md and
./.claude/agents/*.md), i.e. the install date of the current types, since older
sessions could not use them; 30 days when no type file exists. The date used is
always printed. The header line also prints `window_days` (whole days from the
start date to now) and `too_short: true|false` (true below MIN_WINDOW_DAYS = 7):
audit reports spend and run-share findings from a too-short window as P3
observations only.

Model ids. Models are grouped by exact id: `claude-opus-5` and `claude-opus-5-5`
are different models and are reported separately, never merged.

Usage:
  usage_by_agent_type.py [--since YYYY-MM-DD | --days N] [--all-projects]
                         [--project SUBSTR] [--projects-dir ~/.claude/projects]
"""

import argparse
import collections
import datetime
import glob
import json
import os
import re
import subprocess
import sys
import time

# Per MTok: (input, output, cache read, 5m cache write). Matched by substring
# of the model ID, most specific first. Haiku 5.5 uses its <=100k-prompt rates
# here; long prompts cost 5x more, so Haiku figures are a lower bound.
PRICES = [
    ("fable-5-1", (10.0, 50.0, 0.25, 12.5)),
    ("fable", (10.0, 50.0, 1.0, 12.5)),
    ("opus-5-5", (4.0, 20.0, 0.20, 5.0)),
    ("opus", (5.0, 25.0, 0.50, 6.25)),
    ("sonnet-5", (2.0, 10.0, 0.20, 2.5)),
    ("sonnet", (3.0, 15.0, 0.30, 3.75)),
    ("haiku-5-5", (0.10, 0.50, 0.01, 0.125)),
    ("haiku", (1.0, 5.0, 0.10, 1.25)),
]


def price_for(model):
    for key, price in PRICES:
        if key in model:
            return price
    return None


def usage_cost(usage, price):
    return (usage.get("input_tokens", 0) * price[0]
            + usage.get("output_tokens", 0) * price[1]
            + usage.get("cache_read_input_tokens", 0) * price[2]
            + usage.get("cache_creation_input_tokens", 0) * price[3]) / 1e6


def assistant_messages(path):
    """Yield (model, usage, cli_version) once per assistant message id."""
    seen = set()
    with open(path, errors="ignore") as fh:
        for line in fh:
            try:
                entry = json.loads(line)
            except ValueError:
                continue
            if entry.get("type") != "assistant":
                continue
            msg = entry.get("message") or {}
            mid = msg.get("id")
            if not mid or mid in seen:
                continue
            seen.add(mid)
            yield msg.get("model", ""), msg.get("usage") or {}, entry.get("version", "")


DEFAULT_DAYS = 30  # window when neither --since/--days nor an installed type file gives a start
MIN_WINDOW_DAYS = 7  # a shorter window is too short to judge spend or run shares (audit O8 rule)


def encode_cwd(path):
    """Claude Code's project folder name for a working directory."""
    return re.sub(r"[^A-Za-z0-9]", "-", path)


def in_scope(folder):
    """Whether a project folder name belongs to the selected scope."""
    if ARGS.project and ARGS.project not in folder:
        return False
    if ARGS.all_projects or ARGS.project:
        return True
    return any(folder == root or folder.startswith(root + "-") for root in repo_roots())


_ROOTS = None


def repo_roots():
    """Encoded folder names of the current repository: its main checkout and every worktree.

    Sibling worktrees are usually named `<repo>-<task>` and removed once merged, so a
    prefix match on the main checkout name (`<main>-...`) also keeps the sessions of
    worktrees that no longer exist; this covers Claude Code's own
    `<repo>--claude-worktrees-<name>` folders too.
    """
    global _ROOTS
    if _ROOTS is None:
        paths = {os.getcwd()}
        try:
            common = subprocess.run(["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
                                    capture_output=True, text=True, check=True).stdout.strip()
            paths.add(os.path.dirname(common.rstrip("/")))
            listing = subprocess.run(["git", "worktree", "list", "--porcelain"],
                                     capture_output=True, text=True, check=True).stdout
            paths.update(line[len("worktree "):] for line in listing.splitlines() if line.startswith("worktree "))
        except (OSError, subprocess.CalledProcessError):
            pass  # not a git repo: the cwd alone
        _ROOTS = {encode_cwd(p) for p in paths}
    return _ROOTS


def installed_type_files():
    dirs = [os.path.expanduser("~/.claude/agents"), os.path.join(os.getcwd(), ".claude", "agents")]
    return [f for d in dirs for f in glob.glob(os.path.join(d, "*.md"))]


def window_start():
    """Return (epoch seconds, human label of where the start came from)."""
    if ARGS.since:
        try:
            day = datetime.datetime.strptime(ARGS.since, "%Y-%m-%d")
        except ValueError:
            sys.exit(f"error: --since expects YYYY-MM-DD, got {ARGS.since!r}")
        return day.timestamp(), "--since"
    if ARGS.days is not None:
        return time.time() - ARGS.days * 86400, f"--days {ARGS.days}"
    files = installed_type_files()
    if files:
        return min(os.path.getmtime(f) for f in files), "oldest installed agent type file"
    return time.time() - DEFAULT_DAYS * 86400, f"no installed type file: last {DEFAULT_DAYS} days"


def started_at(path):
    """Session start: first timestamp in the transcript, else the file mtime."""
    try:
        with open(path, errors="ignore") as fh:
            for line in fh:
                try:
                    stamp = json.loads(line).get("timestamp")
                except ValueError:
                    continue
                if stamp:
                    return datetime.datetime.fromisoformat(stamp.replace("Z", "+00:00")).timestamp()
                break
    except (OSError, ValueError):
        pass
    return os.path.getmtime(path)


def main():
    root = os.path.expanduser(ARGS.projects_dir)
    cutoff, cutoff_label = window_start()
    scope = "all projects" if ARGS.all_projects else (
        f"projects matching {ARGS.project!r}" if ARGS.project else f"current repo ({os.getcwd()})")
    window_days = (time.time() - cutoff) / 86400
    too_short = window_days < MIN_WINDOW_DAYS
    print(f"Scope: {scope}; since {datetime.datetime.fromtimestamp(cutoff):%Y-%m-%d} ({cutoff_label}); "
          f"window_days {int(window_days)}; too_short: {'true' if too_short else 'false'}\n")

    by_type = collections.defaultdict(lambda: {"runs": 0, "calls": 0, "ctx": 0, "cost": 0.0,
                                               "models": collections.Counter(),
                                               "versions": collections.Counter()})
    for path in glob.glob(os.path.join(root, "*", "*", "subagents", "*.jsonl")):
        if not in_scope(os.path.relpath(path, root).split(os.sep)[0]):
            continue
        if started_at(path) < cutoff:
            continue
        try:
            with open(path[:-len(".jsonl")] + ".meta.json") as fh:
                agent_type = json.load(fh).get("agentType") or "?"
        except (OSError, ValueError):
            agent_type = "?"
        row = by_type[agent_type]
        row["runs"] += 1
        for model, usage, version in assistant_messages(path):
            price = price_for(model)
            if price is None:
                continue
            row["versions"][version or "?"] += 1
            row["calls"] += 1
            row["ctx"] += (usage.get("input_tokens", 0) + usage.get("cache_read_input_tokens", 0)
                           + usage.get("cache_creation_input_tokens", 0))
            row["cost"] += usage_cost(usage, price)
            row["models"][model] += 1

    main_by_model = collections.Counter()
    for path in glob.glob(os.path.join(root, "*", "*.jsonl")):
        if not in_scope(os.path.relpath(path, root).split(os.sep)[0]):
            continue
        if started_at(path) < cutoff:
            continue
        for model, usage, _version in assistant_messages(path):
            price = price_for(model)
            if price is not None:
                main_by_model[model] += usage_cost(usage, price)

    sub_total = sum(r["cost"] for r in by_type.values())
    if not by_type:
        print(f"no subagent transcripts in scope since that date under {root}")
        return 1

    print("Subagents (estimated, API list prices)")
    print(f"{'type':20} {'runs':>5} {'calls/run':>9} {'ctx/call':>9} {'$/run':>7} {'$ total':>8} {'share':>6}  model ids (exact)")
    for agent_type, r in sorted(by_type.items(), key=lambda kv: -kv[1]["cost"]):
        runs = max(r["runs"], 1)
        calls = max(r["calls"], 1)
        top_model = ",".join(m for m, _ in r["models"].most_common()) or "-"
        share = 100 * r["cost"] / sub_total if sub_total else 0
        print(f"{agent_type:20} {r['runs']:5} {r['calls'] / runs:9.0f} {r['ctx'] / calls / 1e3:8.0f}k "
              f"{r['cost'] / runs:7.2f} {r['cost']:8.0f} {share:5.1f}%  {top_model}")

    main_total = sum(main_by_model.values())
    print(f"\nMain sessions: ${main_total:.0f}   subagents: ${sub_total:.0f}")
    for model, cost in main_by_model.most_common():
        print(f"  {model:24} ${cost:8.0f}")

    # Appended after the legacy output (existing consumers keep parsing the table above).
    print("\nResolved models and CLI versions per type (probe O8.10; different ids = different models)")
    for agent_type, r in sorted(by_type.items()):
        models = ", ".join(f"{m} x{n}" for m, n in r["models"].most_common()) or "-"
        versions = ", ".join(f"{v} x{n}" for v, n in r["versions"].most_common()) or "-"
        print(f"  {agent_type}: models [{models}] cli [{versions}]")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--since", default=None, metavar="YYYY-MM-DD",
                        help="only sessions started on or after this date "
                             "(default: oldest mtime of the installed agent type files)")
    parser.add_argument("--days", type=int, default=None, help="window in days instead of --since")
    parser.add_argument("--all-projects", action="store_true",
                        help="read the transcripts of every project, not only the current repo")
    parser.add_argument("--project", default=None,
                        help="only transcript folders whose name contains this substring")
    parser.add_argument("--projects-dir", default="~/.claude/projects",
                        help="Claude Code transcripts root")
    ARGS = parser.parse_args()
    if ARGS.since and ARGS.days is not None:
        parser.error("--since and --days are exclusive")
    sys.exit(main())
