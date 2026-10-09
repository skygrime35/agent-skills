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

Usage:
  usage_by_agent_type.py [--days 30] [--project SUBSTR] [--projects-dir ~/.claude/projects]
"""

import argparse
import collections
import glob
import json
import os
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


def main():
    root = os.path.expanduser(ARGS.projects_dir)
    cutoff = time.time() - ARGS.days * 86400

    by_type = collections.defaultdict(lambda: {"runs": 0, "calls": 0, "ctx": 0, "cost": 0.0,
                                               "models": collections.Counter(),
                                               "versions": collections.Counter()})
    for path in glob.glob(os.path.join(root, "*", "*", "subagents", "*.jsonl")):
        if ARGS.project and ARGS.project not in os.path.relpath(path, root).split(os.sep)[0]:
            continue
        if os.path.getmtime(path) < cutoff:
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
        if ARGS.project and ARGS.project not in os.path.relpath(path, root).split(os.sep)[0]:
            continue
        if os.path.getmtime(path) < cutoff:
            continue
        for model, usage, _version in assistant_messages(path):
            price = price_for(model)
            if price is not None:
                main_by_model[model] += usage_cost(usage, price)

    sub_total = sum(r["cost"] for r in by_type.values())
    if not by_type:
        print(f"no subagent transcripts in the last {ARGS.days} days under {root}")
        return 1

    print(f"Subagents, last {ARGS.days} days (estimated, API list prices)")
    print(f"{'type':20} {'runs':>5} {'calls/run':>9} {'ctx/call':>9} {'$/run':>7} {'$ total':>8} {'share':>6}  main model")
    for agent_type, r in sorted(by_type.items(), key=lambda kv: -kv[1]["cost"]):
        runs = max(r["runs"], 1)
        calls = max(r["calls"], 1)
        top_model = r["models"].most_common(1)[0][0] if r["models"] else "-"
        share = 100 * r["cost"] / sub_total if sub_total else 0
        print(f"{agent_type:20} {r['runs']:5} {r['calls'] / runs:9.0f} {r['ctx'] / calls / 1e3:8.0f}k "
              f"{r['cost'] / runs:7.2f} {r['cost']:8.0f} {share:5.1f}%  {top_model}")

    main_total = sum(main_by_model.values())
    print(f"\nMain sessions: ${main_total:.0f}   subagents: ${sub_total:.0f}")
    for model, cost in main_by_model.most_common():
        print(f"  {model:24} ${cost:8.0f}")

    # Appended after the legacy output (existing consumers keep parsing the table above).
    print("\nResolved models and CLI versions per type (probe O8.10)")
    for agent_type, r in sorted(by_type.items()):
        models = ", ".join(f"{m} x{n}" for m, n in r["models"].most_common()) or "-"
        versions = ", ".join(f"{v} x{n}" for v, n in r["versions"].most_common()) or "-"
        print(f"  {agent_type}: models [{models}] cli [{versions}]")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--days", type=int, default=30, help="window in days (default 30)")
    parser.add_argument("--project", default=None,
                        help="only transcript folders whose name contains this substring")
    parser.add_argument("--projects-dir", default="~/.claude/projects",
                        help="Claude Code transcripts root")
    ARGS = parser.parse_args()
    sys.exit(main())
