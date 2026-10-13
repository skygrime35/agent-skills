#!/usr/bin/env python3
"""Check that the local replay of a CI pipeline covers every CI job. Read-only.

    check_ci_replay.py --replay AGENTS.md --heading "Vital commands"
    check_ci_replay.py --replay scripts/ci_local.sh --exclude deploy --exclude docker-scan
    check_ci_replay.py --replay AGENTS.md --replay scripts/ci_local.sh --workflows .github/workflows

CI side: every `.github/workflows/*.y*ml` is read line by line (no YAML dependency).
For each job the `run:` commands are extracted, including `run: |` / `run: >` blocks,
with `working-directory` (job `defaults.run` or step) applied. A step with only
`uses:` counts as a command named after the action (`aquasecurity/trivy-action` ->
`trivy`) unless it is plumbing (`actions/*`, `*/setup-*`, cache, login, upload...).

Replay side (repeatable `--replay FILE`):
  *.md      the fenced code blocks under the heading containing `--heading` (case-
            insensitive; down to the next heading of the same or a higher level);
            without `--heading`, every fenced block of the file.
  other     a shell script: `step|advisory <group> <name> "<cmd>"` lines (the quoted
            command is parsed) and, at column 0, plain command lines. In a script
            with no `step` line, every line is a plain command line.

Normalisation, applied to both sides: split on `&&`, `||`, `;`, `|` and newlines;
drop env assignments, `cd` (tracked as the working directory), `sudo`, `time`, shell
keywords and non-check plumbing (`echo`, `pip install`, `npm ci`, `docker save`...);
unwrap `docker compose exec|run SERVICE cmd`, `uvx|npx|pipx run|uv run|poetry run`,
`python -m tool`, `bash|sh|./script`, `dx '...'` (quoted payload). A command becomes
`tool + subcommand + path arguments`: flags, flag order and values that are not paths
are ignored; `npm|pnpm|yarn` are one tool; `npm test` equals `npm run test`; paths are
joined with the working directory (`cd backend && ruff check .` = `ruff check backend`).
A CI command is covered by a replay command with the same tool and subcommand whose
paths cover it (equal, a parent directory, or `.`), or when either side has no path.
A `python -c` inline script cannot be normalised and is reported as missing.

Output, a `# ci:` comment line then one line per job:
file:job<TAB>status<TAB>detail
status: covered | missing (detail lists the uncovered commands) | excluded (`--exclude`,
or a job with no checkable command: detail says which).
--exclude JOB (repeatable) matches the job id, its `name:` or `file:job`.
Exit 0 when no job is missing, 1 when a job is missing, 2 on usage error.
"""

from __future__ import annotations

import argparse
import os
import posixpath
import re
import shlex
import sys
from pathlib import Path

EXIT_OK, EXIT_MISSING, EXIT_USAGE = 0, 1, 2

WORKFLOW_GLOBS = ("*.yml", "*.yaml")
SHELL_KEYWORDS = {"if", "then", "else", "elif", "do", "while", "until", "time", "!", "{", "(", "sudo", "exec", "command"}
SHELL_DROP = {"for", "case", "done", "fi", "esac", "}", ")", "[", "[[", "echo", "printf", "cat", "exit", "export",
              "set", "unset", "test", "true", "false", ":", "read", "trap", "source", ".", "return", "local",
              "shift", "sleep", "mkdir", "rm", "cp", "mv", "ln", "touch", "chmod", "tee", "wc", "env", "declare",
              "function", "readonly", "wait", "kill", "pwd", "ls", "tail", "head", "date", "basename", "dirname",
              "gzip", "gunzip", "tar", "zip", "unzip", "cut", "sort", "uniq", "awk", "sed", "xargs", "tr", "find", "diff", "jq"}
# (tool, first word of the subcommand) that only prepare the environment.
SETUP = {("pip", "install"), ("pip3", "install"), ("pip", "download"), ("npm", "ci"), ("npm", "install"),
         ("npm", "i"), ("yarn", "install"), ("pnpm", "install"), ("apt-get", "install"), ("apt-get", "update"),
         ("apt", "install"), ("apt", "update"), ("docker", "load"), ("docker", "save"), ("docker", "login"),
         ("docker", "rm"), ("docker", "pull"), ("docker", "push"), ("docker", "info"), ("docker", "ps"),
         ("docker", "logout"), ("docker compose", "down"), ("docker compose", "up"), ("docker compose", "pull"),
         ("docker compose", "logs"), ("docker compose", "ps"), ("brew", "install"), ("gem", "install"),
         ("go", "mod"), ("corepack", "enable"), ("uv", "sync"), ("uv", "pip"), ("poetry", "install"),
         ("python", "-m pip"), ("pip", ""), ("docker", "image"), ("docker", "images"), ("docker", "inspect"),
         ("docker", "builder"), ("docker", "system"), ("docker", "volume"), ("docker", "network"),
         ("docker", "rmi"), ("docker", "version"), ("playwright", "install"), ("playwright", "install-deps"),
         ("df", ""), ("du", ""), ("free", ""), ("git", "fetch"), ("git", "checkout"), ("git", "config"),
         ("git", "clone"), ("git", "init")}
# Flags whose next token is a value to skip when looking for the subcommand.
VALUE_FLAGS = {"-f", "-p", "--file", "--project-name", "--env-file", "--profile", "--project-directory", "-C",
               "--prefix", "--cwd", "--workdir", "-w", "-e", "--env", "-u", "--user"}
RUNNER_PREFIXES = {("uvx",), ("npx",), ("bunx",), ("pipx", "run"), ("uv", "run"), ("poetry", "run"),
                   ("pnpm", "dlx"), ("pnpm", "exec"), ("yarn", "dlx"), ("npm", "exec"), ("pipenv", "run"),
                   ("python", "-m"), ("python3", "-m")}
SKIP_ACTIONS = re.compile(r"^(actions|docker|github|astral-sh|peaceiris|codecov)/|/setup-|cache|login|buildx|qemu|"
                          r"upload|download|checkout|artifact|configure-", re.I)
NODE_LIKE = {"python", "node", "bash", "sh", "zsh", "ruby", "perl", "deno", "bun", "php"}
TOOL_ALIAS = {"python3": "python", "py": "python", "pip3": "pip", "pnpm": "npm", "yarn": "npm", "bunx": "npx"}
ENV_ASSIGN_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
SUBLIKE_RE = re.compile(r"^[a-z][\w:-]*$")
PIPE_MARK = "\x00"
EXPR_RE = re.compile(r"\$\{\{.*?\}\}")


# ------------------------------------------------------------------ shell splitting

def split_commands(text: str) -> list[str]:
    """Split a shell snippet into simple commands on unquoted newlines, `;`, `&&`, `||`, `|`.

    Quotes and backslash-newline continuations are honoured; `#` comments are dropped.
    """
    parts: list[str] = []
    buf: list[str] = []
    quote = ""
    depth = 0  # nesting of $( ... ) and ( ... ): never split inside
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if quote:
            buf.append(c)
            if c == "\\" and quote == '"' and i + 1 < n:
                buf.append(text[i + 1])
                i += 1
            elif c == quote:
                quote = ""
        elif c == "\\" and i + 1 < n and text[i + 1] == "\n":
            buf.append(" ")
            i += 1
        elif c == "\\" and i + 1 < n:
            buf.append(c + text[i + 1])
            i += 1
        elif c in "\"'":
            quote = c
            buf.append(c)
        elif c == "#" and (not buf or buf[-1] in " \t\n"):
            while i < n and text[i] != "\n":
                i += 1
            continue
        elif c == "(" and buf and buf[-1] == "$":
            depth += 1
            buf.append(c)
        elif c == ")" and depth:
            depth -= 1
            buf.append(c)
        elif depth or (c == "&" and buf and buf[-1] == ">") or (c == "&" and text[i + 1:i + 2] == ">"):
            buf.append(c)
        elif c in "\n;|&":
            parts.append("".join(buf))
            buf = []
            if c == "|" and text[i + 1:i + 2] not in ("|",):
                buf.append(PIPE_MARK)  # right side of a pipe: a filter, not a check
            while i + 1 < n and text[i + 1] in "|&" and c in "|&":
                i += 1
        else:
            buf.append(c)
        i += 1
    parts.append("".join(buf))
    return [p.strip(" \t") for p in parts if p.strip(" \t\x00")]


def strip_substitutions(text: str) -> str:
    """Replace each balanced `$( ... )` by SUBST: commands inside are not checks."""
    out, depth, i = [], 0, 0
    while i < len(text):
        if text.startswith("$(", i):
            depth += 1
            i += 2
            if depth == 1:
                out.append("SUBST")
        elif depth and text[i] == "(":
            depth += 1
            i += 1
        elif depth and text[i] == ")":
            depth -= 1
            i += 1
        else:
            if not depth:
                out.append(text[i])
            i += 1
    return "".join(out)


REDIRECT_RE = re.compile(r"^\d*[<>]{1,2}(&\d+|&-)?$")


def strip_redirects(words: list[str]) -> list[str]:
    """Drop `> file`, `2>&1`, `>>file`, `< file` redirections."""
    out, skip = [], False
    for w in words:
        if skip:
            skip = False
        elif REDIRECT_RE.match(w):
            skip = not re.search(r"&[\d-]$", w)
        elif re.match(r"^\d*[<>]{1,2}\S", w):
            continue
        else:
            out.append(w)
    return out


def words_of(command: str) -> list[str]:
    try:
        return shlex.split(command)
    except ValueError:
        return command.split()


# ------------------------------------------------------------------ normalisation

class Cmd:
    """One normalised command: tool, subcommand, absolute-ish paths, display text."""

    def __init__(self, tool: str, sub: str, paths: frozenset[str], text: str, wildcard_sub: bool = False,
                 inline: bool = False, wd_known: bool = True):
        self.tool, self.sub, self.paths, self.text = tool, sub, paths, text
        self.wildcard_sub, self.inline, self.wd_known = wildcard_sub, inline, wd_known


def pathlike(token: str, root: Path, wd: str, loose: bool = False) -> bool:
    """Whether a token is a path argument; loose: the working directory is unknown, so a name
    existing one level below the root counts."""
    if not token or token.startswith(("-", "$", "~", "/")) or "=" in token or "://" in token:
        return False
    if re.fullmatch(r"[\d.:]+", token) and token != ".":
        return False
    if token in (".", "./", ".."):
        return True
    clean = token.rstrip("/")
    if "*" in clean or "{" in clean:
        clean = re.split(r"[*{]", clean)[0].rstrip("/")
        return bool(clean)
    if "/" in token or (root / wd / clean).exists() or (root / clean).exists() or re.search(r"\.\w{1,5}$", token):
        return True
    return loose and any((d / clean).exists() for d in root.iterdir() if d.is_dir() and not d.name.startswith("."))


def join_path(wd: str, token: str) -> str:
    """Working directory + path argument, cut before the first placeholder or glob segment."""
    m = re.search(r"[*{$<\[]", token)
    if m:
        token = token[:m.start()]
        if not token.endswith("/"):
            token = token.rsplit("/", 1)[0] if "/" in token else ""
    token = token or "."
    return posixpath.normpath(posixpath.join(wd, token)) if wd or token != "." else "."


def unwrap(words: list[str], root: Path, wd: str) -> tuple[list[str], str | None]:
    """Strip wrappers (env, sudo, runners, docker compose exec, dx, bash -c) down to the tool."""
    while words:
        w = words[0]
        if ENV_ASSIGN_RE.match(w) or w in SHELL_KEYWORDS:
            words = words[1:]
        elif w == "env":
            words = words[1:]
            while words and (ENV_ASSIGN_RE.match(words[0]) or words[0].startswith(("-", "$"))):
                words = words[1:]
        elif w == "dx" and len(words) > 1:
            return unwrap_text(words[1], root, wd), None  # container working directory unknown
        elif w in ("bash", "sh") and len(words) > 2 and words[1] == "-c":
            return unwrap_text(words[2], root, wd), wd
        elif w == "docker" and len(words) > 2 and words[1] == "compose" or w == "docker-compose":
            rest = words[2:] if w == "docker" else words[1:]
            i = 0
            while i < len(rest) and rest[i] not in ("exec", "run", "build", "config", "up", "down", "pull"):
                i += 2 if rest[i] in VALUE_FLAGS else 1
            if i < len(rest) and rest[i] in ("exec", "run"):
                j = i + 1
                while j < len(rest) and rest[j].startswith("-"):
                    j += 2 if rest[j] in VALUE_FLAGS else 1
                if j < len(rest):
                    service = rest[j]
                    if (root / service).is_dir():
                        wd = posixpath.normpath(posixpath.join(wd, service)) if not wd else wd
                    return words_after(rest[j + 1:], root, wd)
            return ["docker compose"] + rest, wd
        else:
            break
    if words and "/" in words[0] and not words[0].startswith("-"):
        words = ["bash"] + words  # an executable path is a script: `./scripts/x.sh` == `bash scripts/x.sh`
    if words:
        tool = posixpath.basename(words[0])
        for prefix in RUNNER_PREFIXES:
            if tuple(words[:len(prefix)]) == prefix and len(words) > len(prefix):
                return words[len(prefix):], wd
        words = [tool] + words[1:]
        words[0] = TOOL_ALIAS.get(words[0], words[0])
        if words[0] == "npx":
            words = words[1:]
    return words, wd


def words_after(words: list[str], root: Path, wd: str) -> tuple[list[str], str]:
    return unwrap(words, root, wd)


def unwrap_text(text: str, root: Path, wd: str) -> list[str]:
    inner = split_commands(text)
    return unwrap(words_of(inner[-1]), root, wd)[0] if inner else []


def normalise(text: str, root: Path, wd: str) -> tuple[Cmd | None, str]:
    """(Cmd or None when plumbing, working directory after this command)."""
    if text.startswith(PIPE_MARK):
        return None, wd
    words = strip_redirects(words_of(strip_substitutions(text)))
    while words and (ENV_ASSIGN_RE.match(words[0]) or words[0] in SHELL_KEYWORDS):
        words = words[1:]
    if not words:
        return None, wd
    if words[0] == "cd":
        target = next((w for w in words[1:] if not w.startswith("-")), "")
        if not target or target.startswith(("$", "~")):
            return None, wd
        if target.startswith("/"):
            return None, ""
        return None, posixpath.normpath(posixpath.join(wd, target)).lstrip("./") if target != ".." or wd else ""
    words, wd2 = unwrap(words, root, wd)
    known = wd2 is not None
    wd2 = wd2 or ""
    if not words or words[0] in SHELL_DROP or ENV_ASSIGN_RE.match(words[0]) or words[0].endswith(":") \
            or words[0].endswith((")", ";;")) or words[0].startswith("*") or "://" in words[0]:
        return None, wd
    tool = TOOL_ALIAS.get(words[0], words[0])
    args = words[1:]
    # subcommand
    i = 0
    while i < len(args) and args[i].startswith("-"):
        i += 2 if args[i] in VALUE_FLAGS else 1
    first = args[i] if i < len(args) else ""
    sub, rest = "", args
    if tool in NODE_LIKE:
        if args and args[0] == "-c":
            if "py_compile" in " ".join(args) or "compileall" in " ".join(args):
                return Cmd("compileall", "", frozenset(), text), wd  # documented alias
            return Cmd(tool, "-c", frozenset(), text, inline=True), wd
        if args and args[0] == "-n" and tool in ("bash", "sh"):
            return Cmd("bash", "-n", frozenset(join_path(wd2, a) for a in args[1:] if pathlike(a, root, wd2, not known)), text), wd
        if first:
            sub = join_path(wd2, first)
            rest = args[i + 1:]
    elif tool == "npm" and first:
        if first == "run" or first == "run-script":
            second = next((a for a in args[i + 1:] if not a.startswith("-")), "")
            if not second:
                return None, wd  # bare `npm run` lists scripts
            sub = f"run {second}"
        elif first in ("test", "t", "tst", "start", "build"):
            sub = f"run {first}"
        else:
            sub = first
        rest = args[i + 1:]
    elif first and SUBLIKE_RE.match(first) and not pathlike(first, root, wd2, not known) and (
            not (root / wd2 / first).exists()):
        sub, rest = first, args[i + 1:]
    if (tool, sub.split(" ")[0] if tool != "python" else sub) in SETUP or (tool, sub) in SETUP:
        return None, wd
    if tool == "pip" and sub == "install":
        return None, wd
    paths = frozenset(join_path(wd2, a) for a in rest if pathlike(a, root, wd2, not known))
    if tool == "docker compose":
        # keep the compose file (`-f x`): it tells prod from preprod
        paths = frozenset(join_path(wd2, a) for a in args if pathlike(a, root, wd2, not known))
    return Cmd(tool, sub, paths, text, wd_known=known), wd


def commands_of(text: str, root: Path, wd: str = "") -> list[Cmd]:
    """Commands of a snippet run as one script: a `cd` carries over to the following commands."""
    out: list[Cmd] = []
    for simple in split_commands(text):
        cmd, wd = normalise(simple, root, wd)
        if cmd is not None:
            out.append(cmd)
    return out


def list_commands(text: str, root: Path) -> list[Cmd]:
    """Commands of a replay list: every line stands alone, so a `cd` never leaks to the next line."""
    out: list[Cmd] = []
    for line in re.sub(r"\\\n", " ", text).splitlines():
        out += commands_of(line, root)
    return out


def covers(replay: Cmd, ci: Cmd) -> bool:
    """Whether a replay command covers a CI command (rules in the module docstring)."""
    if ci.tool == "coverage" and ci.sub in ("report", "xml", "html") and "--cov" in replay.text:
        return True  # `coverage report --fail-under` is the gate `pytest --cov-fail-under` applies
    if replay.tool != ci.tool or (replay.sub != ci.sub and not ci.wildcard_sub):
        return False
    if ci.inline or replay.inline:
        return False
    if not ci.paths or not replay.paths:
        return True
    def within(p: str, q: str) -> bool:
        if p == q or q == "." or p.startswith(q.rstrip("/") + "/"):
            return True
        # replay run in an unknown directory (container): its paths may be relative to a subdirectory
        return not replay.wd_known and ("/" + q.strip("/") + "/") in ("/" + p + "/")

    return all(any(within(p, q) for q in replay.paths) for p in ci.paths)


# ------------------------------------------------------------------ CI side

def indent_of(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def clean_scalar(value: str) -> str:
    value = value.strip()
    if value[:1] in "\"'" and value[-1:] == value[:1] and len(value) > 1:
        return value[1:-1]
    return re.sub(r"\s+#\s.*$", "", value)


def clean_wd(value: str) -> str:
    """Working directory of a step: an expression (`${{ github.workspace }}`) means the root."""
    value = clean_scalar(value)
    return "" if "${{" in value else value.lstrip("./") if value != "." else ""


class Job:
    def __init__(self, file: str, jid: str):
        self.file, self.jid, self.name = file, jid, jid
        self.commands: list[Cmd] = []


def parse_workflow(path: Path, rel: str, root: Path) -> list[Job]:
    """Jobs of one workflow file, read line by line (see the module docstring)."""
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    jobs: list[Job] = []
    start = next((i for i, ln in enumerate(lines) if re.match(r"^jobs:\s*(#.*)?$", ln)), None)
    if start is None:
        return jobs
    job_indent = next((indent_of(ln) for ln in lines[start + 1:] if ln.strip() and not ln.lstrip().startswith("#")), 2)
    blocks: list[tuple[str, list[str]]] = []
    for ln in lines[start + 1:]:
        if ln.strip() and not ln.lstrip().startswith("#") and indent_of(ln) < job_indent:
            break
        m = re.match(r"^(\s*)([\w.-]+|\"[^\"]+\"):\s*(#.*)?$", ln)
        if m and indent_of(ln) == job_indent:
            blocks.append((m.group(2).strip('"'), []))
        elif blocks:
            blocks[-1][1].append(ln)
    for jid, body in blocks:
        job = Job(rel, jid)
        job_wd = ""
        step_indent = None
        i = 0
        steps: list[list[str]] = []
        while i < len(body):
            ln = body[i]
            m = re.match(r"^\s*name:\s*(.+)$", ln)
            if m and step_indent is None and indent_of(ln) == job_indent + 2:
                job.name = clean_scalar(m.group(1))
            m = re.match(r"^\s*working-directory:\s*(\S.*)$", ln)
            if m and step_indent is None:
                job_wd = clean_wd(m.group(1))
            if re.match(r"^\s*steps:\s*(#.*)?$", ln):
                step_indent = -1
            elif step_indent == -1 and ln.strip() and not ln.lstrip().startswith("#"):
                step_indent = indent_of(ln)
            if step_indent not in (None, -1) and ln.strip():
                if indent_of(ln) == step_indent and ln.lstrip().startswith("- "):
                    steps.append([ln])
                elif steps:
                    steps[-1].append(ln)
            elif step_indent not in (None, -1) and steps:
                steps[-1].append(ln)
            i += 1
        for step in steps:
            job.commands += step_commands(step, root, job_wd)
        jobs.append(job)
    return jobs


def step_commands(step: list[str], root: Path, job_wd: str) -> list[Cmd]:
    """Commands of one workflow step: its `run:` text and, for a bare action, the action."""
    wd, run_text, uses = job_wd, "", ""
    first = step[0].replace("- ", "  ", 1)
    lines = [first] + step[1:]
    key_indent = indent_of(first)
    i = 0
    while i < len(lines):
        ln = lines[i]
        m = re.match(r"^(\s*)(run|uses|working-directory):\s*(.*)$", ln)
        if m and indent_of(ln) == key_indent:
            key, value = m.group(2), m.group(3)
            if key == "working-directory":
                wd = clean_wd(value)
            elif key == "uses":
                uses = clean_scalar(value)
            elif re.match(r"^[|>][+-]?\s*(#.*)?$", value.strip()):
                block: list[str] = []
                i += 1
                while i < len(lines) and (not lines[i].strip() or indent_of(lines[i]) > key_indent):
                    block.append(lines[i])
                    i += 1
                body_indent = min((indent_of(b) for b in block if b.strip()), default=0)
                text = "\n".join(b[body_indent:] for b in block)
                run_text = text.replace("\n", " ") if value.strip().startswith(">") else text
                continue
            else:
                run_text = clean_scalar(value)
        i += 1
    run_text = re.sub(r"\$\{\{\s*github\.workspace\s*\}\}/?", "", run_text)  # the repo root
    run_text = EXPR_RE.sub("EXPR", run_text)
    if run_text:
        return commands_of(run_text, root, wd)
    if uses and not SKIP_ACTIONS.search(uses):
        name = uses.split("@")[0].rsplit("/", 1)[-1]
        name = re.sub(r"-action$", "", name)
        return [Cmd(name, "", frozenset(), f"uses: {uses.split('@')[0]}", wildcard_sub=True)]
    return []


# ------------------------------------------------------------------ replay side

def md_blocks(path: Path, heading: str) -> list[str]:
    """Fenced code blocks of `path` under the first heading containing `heading`."""
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    blocks: list[str] = []
    level, inside, fence, buf = 0, not heading, False, []
    for ln in lines:
        if re.match(r"^\s*(```|~~~)", ln):
            if fence and inside:
                blocks.append("\n".join(buf))
                buf = []
            fence = not fence
            continue
        if fence:
            buf.append(ln)
            continue
        m = re.match(r"^\s{0,3}(#{1,6})\s+(.*?)\s*#*\s*$", ln)
        if m and heading:
            if inside and len(m.group(1)) <= level:
                inside = False
            if not inside and heading.lower() in m.group(2).lower() and not level:
                inside, level = True, len(m.group(1))
    if heading and not level:
        raise ValueError(f"heading containing '{heading}' not found in {path}")
    return blocks


def script_commands(path: Path, root: Path) -> list[Cmd]:
    """Commands of a shell script: `step|advisory g n "cmd"` lines and plain column-0 lines."""
    text = path.read_text(encoding="utf-8", errors="replace")
    logical = re.sub(r"\\\n", " ", text).splitlines()
    has_steps = any(re.match(r"^\s*(step|advisory)\s", ln) for ln in logical)
    out: list[Cmd] = []
    for ln in logical:
        if re.match(r"^\s*(step|advisory)\s", ln):
            words = words_of(ln)
            if len(words) >= 4:
                out += commands_of(words[3].replace("\\$", "$"), root)
        elif (not has_steps or indent_of(ln) == 0) and ln.strip() and not re.match(r"^\s*[\w-]+\(\)", ln):
            out += commands_of(ln, root)
    return out


def replay_commands(spec: str, heading: str, root: Path) -> list[Cmd]:
    path = (root / spec) if not os.path.isabs(spec) else Path(spec)
    if not path.is_file():
        raise ValueError(f"replay file not found: {spec}")
    if path.suffix.lower() in (".md", ".mdx"):
        out: list[Cmd] = []
        for block in md_blocks(path, heading):
            out += list_commands(block, root)
        return out
    return script_commands(path, root)


# ------------------------------------------------------------------ main

def main() -> int:
    ap = argparse.ArgumentParser(
        description="Check that a local replay list covers every CI job (read-only).",
        epilog="Output: file:job<TAB>status<TAB>detail, status covered|missing|excluded. "
               "Exit 0 none missing, 1 missing, 2 usage error.")
    ap.add_argument("--root", default=".", help="repository root (default: current directory)")
    ap.add_argument("--workflows", default=".github/workflows", help="workflow directory, relative to the root")
    ap.add_argument("--replay", action="append", default=[], metavar="FILE",
                    help="replay list: a markdown file (fenced blocks under --heading) or a shell script; repeatable")
    ap.add_argument("--heading", default="", help="text of the markdown heading holding the replay block "
                                                  "(default: every fenced block of the file)")
    ap.add_argument("--exclude", action="append", default=[], metavar="JOB",
                    help="job id, job name or file:job to report as excluded; repeatable")
    ap.add_argument("--only-missing", action="store_true", help="print only missing jobs (and the comment line)")
    try:
        args = ap.parse_args()
    except SystemExit as e:
        return EXIT_OK if e.code == 0 else EXIT_USAGE
    root = Path(args.root).resolve()
    wf_dir = root / args.workflows
    if not root.is_dir() or not wf_dir.is_dir():
        print(f"error: workflow directory not found: {wf_dir}", file=sys.stderr)
        return EXIT_USAGE
    if not args.replay:
        print("error: at least one --replay FILE is required", file=sys.stderr)
        return EXIT_USAGE
    replay: list[Cmd] = []
    try:
        for spec in args.replay:
            replay += replay_commands(spec, args.heading, root)
    except (ValueError, OSError) as e:
        print(f"error: {e}", file=sys.stderr)
        return EXIT_USAGE
    files = sorted({p for g in WORKFLOW_GLOBS for p in wf_dir.glob(g)})
    jobs: list[Job] = []
    for f in files:
        jobs += parse_workflow(f, os.path.relpath(f, root), root)
    print(f"# ci: {len(jobs)} jobs in {len(files)} workflows; replay: {len(replay)} commands from {', '.join(args.replay)}")
    missing = 0
    for job in jobs:
        label = f"{job.file}:{job.jid}"
        if {job.jid, job.name, label} & set(args.exclude):
            status, detail = "excluded", "--exclude"
        elif not job.commands:
            status, detail = "excluded", "no checkable command"
        else:
            gaps = [c.text.strip().replace("\n", " ")[:90] for c in job.commands
                    if not any(covers(r, c) for r in replay)]
            status, detail = ("missing", " ; ".join(gaps)) if gaps else ("covered", f"{len(job.commands)} commands")
        missing += status == "missing"
        if status == "missing" or not args.only_missing:
            print(f"{label}\t{status}\t{detail}")
    return EXIT_MISSING if missing else EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
