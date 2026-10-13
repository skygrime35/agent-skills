#!/usr/bin/env python3
"""Report paths and links cited in agent docs that resolve to nothing. Read-only.

    check_dead_paths.py                       # root AGENTS.md, CLAUDE.md, domain AGENTS.md, AGENTS/**/*.md, docs index
    check_dead_paths.py AGENTS.md docs/a.md   # explicit files
    check_dead_paths.py AGENTS/ docs/         # a directory argument recurses into its *.md
    check_dead_paths.py --root /repo FILE...
    check_dead_paths.py --archive errors/     # excluded from the default scope (repeatable)

Default scope excludes the `archives.paths` of `.claude/agents-md.yml` (read when
present) plus any --archive; archives are scanned in a separate pass by the skill.
The first output line is a comment: `# scope: N files (a, b, ...)`.

Scans backtick spans and markdown links, with #anchors checked against the
target's headings. A backtick span counts as a repo path only when it looks like
one (see looks_like_path): it ends in a known source/doc file extension, or it
ends with "/" and its first segment is a directory name of the repo. Everything
else is ignored: migration ids (app/0042), dotted symbols (pkg/mod.Class), npm
packages (@scope/pkg, next/headers), URL routes, CSS classes, HTTP verbs and
"a/b" word pairs, rates (10/min), git refs (origin/main, .git/...), generated
dirs (node_modules/), host names, placeholders, globs, spans with spaces.
Fenced code blocks and URLs are skipped. A target is resolved relative to the
citing file, then to the repo root, then by suffix against `git ls-files` (or a
directory walk outside git), so a domain-relative path works. A backtick mention
next to a negation or condition ("deleted", "no longer", "if present",
"supprime") is reported as `conditional` instead of `dead`.

Output, one line per citation: file:line<TAB>target<TAB>status
status: ok | dead | ambiguous (suffix matches several tracked files) |
        conditional (mentioned as absent or optional; never counted dead) |
        local (target missing but git-ignored: not dead, info only) |
        external (a source file inside a dependency declared in requirements*.txt,
        pyproject.toml, package.json or go.mod, e.g. `somelib/views.py`; info only).
An abbreviated path is `ok` when its file name is unique in the repo and its
cited directories appear in order in the real path.
A `dead` line may carry a fourth column `hint: moved? <path>` when the missing
file's stem exists as a directory (`x/services.py` -> `x/services/`) or a single
file of the same name exists elsewhere.
--quiet-ok prints only dead and ambiguous lines (and the scope comment).
Exit 0 when nothing is dead, 1 when something is dead, 2 on usage error.
"""

from __future__ import annotations

import argparse
import json
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
PLACEHOLDER_RE = re.compile(
    r"[<>{}$*?\[\]|]|\.\.\.|\bXXX\b|(^|/)(path/to|your|my)[-_/]|YYYY|\bMM-DD\b|short-title|\bfoo\b|\bexample\b", re.I)
# A lone capital-letter segment is a placeholder too (apps/X/api.py); case-sensitive.
LONE_CAPITAL_RE = re.compile(r"(^|/)[A-Z](/|$)")
# Source extensions: a missing path with one of these inside a declared dependency is a
# third-party package path (`external`), not a dead reference.
DEP_FILE_RE = re.compile(r"^(requirements[\w.-]*\.txt|pyproject\.toml|package\.json|go\.mod)$")
# Dependency-name-looking tokens in requirements/pyproject/go.mod (over-inclusive on purpose:
# a token only matters when it is also the first segment of a missing code path).
DEP_NAME_RE = re.compile(r"[A-Za-z][A-Za-z0-9_.-]*")


def norm_dep(name: str) -> str:
    return re.sub(r"[-_.]+", "_", name).lower()


CODE_EXTS = {"py", "pyi", "ts", "tsx", "js", "jsx", "mjs", "cjs", "go", "rs", "java", "kt", "rb", "php"}
# File extensions that make a "/"-containing span a file path.
KNOWN_EXTS = {
    "py", "pyi", "ts", "tsx", "js", "jsx", "mjs", "cjs", "vue", "svelte", "go", "rs", "java", "kt",
    "rb", "php", "cs", "swift", "c", "h", "cpp", "sh", "bash", "zsh", "sql", "md", "mdx", "rst",
    "txt", "json", "jsonc", "yml", "yaml", "toml", "ini", "cfg", "conf", "env", "lock", "xml",
    "html", "css", "scss", "sass", "less", "svg", "png", "jpg", "jpeg", "gif", "webp", "ico",
    "pdf", "csv", "tsv", "ipynb", "tf", "proto", "graphql", "example", "sample", "tpl", "j2",
}
# Extensionless file names that are still files.
KNOWN_BARE = {"Dockerfile", "Makefile", "Procfile", "Jenkinsfile", "Vagrantfile", "Gemfile",
              "Caddyfile", "LICENSE", "CODEOWNERS"}
# Generated, vendored or VCS content: never checked.
GENERATED_DIRS = {".git", "node_modules", ".next", ".nuxt", ".venv", "venv", "__pycache__", "dist",
                  "build", "coverage", ".cache", ".pytest_cache", ".mypy_cache", "target"}
GIT_REF_PREFIXES = ("origin/", "upstream/", "refs/")
# Migration-like segment: 0042 or 0042_add_field.
MIGRATION_RE = re.compile(r"^\d{3,}(?:_\w+)?$")
# Trailing line or test selector: file.py:12, file.py:12-20, file.py::test_x
LOCATOR_RE = re.compile(r"(?::\d+(?:-\d+)?|::\w+)$")
# Wording saying the path is absent, removed or optional, close to the mention.
CONDITIONAL_RE = re.compile(
    r"\b(?:delet\w*|remov\w*|no longer|does not exist|doesn't exist|do not exist|nor an?|neither|"
    r"if (?:it )?(?:is )?(?:present|exists?|any)|when present|impossible|dropped|"
    r"supprim\w*|retir\w*|n'existe (?:pas|plus)|si (?:pr[ée]sent|existant)|inexistant\w*)\b", re.I)
# A negating word right before the span: "no `x/`", "aucun `x/`".
NEGATED_BEFORE_RE = re.compile(r"\b(?:no|not|without|aucune?|pas de|sans)\s*[*_]*\s*$", re.I)
CONDITIONAL_WINDOW = 70  # characters of context kept on each side of the span
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
    """Yield (line_number, raw_target, is_link, context) for each citation outside fences.

    context is the text around a backtick span (the span itself removed); empty for links.
    """
    in_fence = False
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    for no, line in enumerate(lines, 1):
        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        for m in LINK_RE.finditer(line):
            yield no, m.group(1), True, ""
        plain = LINK_RE.sub(lambda m: " " * len(m.group(0)), line)
        before_lines = lines[no - 2] if no > 1 else ""
        after_lines = lines[no] if no < len(lines) else ""
        for m in TICK_RE.finditer(plain):
            before = (before_lines + " " + plain[:m.start()])[-CONDITIONAL_WINDOW:]
            after = (plain[m.end():] + " " + after_lines)[:CONDITIONAL_WINDOW]
            yield no, m.group(1).strip(), False, before + "\0" + after


def conditional(around: str) -> bool:
    before, _, after = around.partition("\0")
    return bool(CONDITIONAL_RE.search(before + " " + after) or NEGATED_BEFORE_RE.search(before))


def skippable(target: str, is_link: bool) -> bool:
    if URL_RE.match(target) or target.startswith(("/", "~")) or PLACEHOLDER_RE.search(target):
        return True
    if LONE_CAPITAL_RE.search(target):
        return True
    return not is_link and not PATH_RE.match(target)


def _ext(segment: str) -> str:
    body = segment.strip(".")
    return body.rsplit(".", 1)[1].lower() if "." in body else ""


def looks_like_path(target: str, repo_dirs: set[str]) -> bool:
    """True when a backtick span is plausibly a repo path (rules in the module docstring)."""
    if target.startswith(GIT_REF_PREFIXES) or "@" in target:
        return False
    segs = [s for s in target.strip("/").split("/") if s not in ("", ".", "..")]
    if not segs or (len(segs) < 2 and not target.endswith("/")):
        return False
    if any(s in GENERATED_DIRS for s in segs[:-1]) or segs[-1] in GENERATED_DIRS:
        return False
    if any(s.isdigit() for s in segs):  # 10/hour, 1000/min
        return False
    last = segs[-1]
    if target.endswith("/"):  # directory: the first segment must be a directory of the repo
        return segs[0] in repo_dirs and MIGRATION_RE.match(last) is None
    first_ext = _ext(segs[0])
    if first_ext and first_ext not in KNOWN_EXTS:
        return False  # host name such as media.example.com
    if _ext(last) in KNOWN_EXTS:
        return MIGRATION_RE.match(last) is None
    return last in KNOWN_BARE  # otherwise: dotted symbol, migration id, route, word pair


def _dir_prefixes(path: str):
    parts = path.split("/")[:-1]
    for n in range(1, len(parts) + 1):
        yield "/".join(parts[:n])


class Resolver:
    def __init__(self, root: Path):
        self.root = root
        self.tracked = git_files(root)
        self.repo_dirs = {seg for f in self.tracked for seg in f.split("/")[:-1]}
        self._deps: set[str] | None = None

    def strong_dir(self, target: str, base: Path) -> bool:
        """First segment of a directory span exists at the repo root or next to the citing file."""
        first = target.strip("/").split("/")[0]
        return (self.root / first).is_dir() or (base.parent / first).is_dir()

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
        if hits:
            return "ambiguous", None
        loose = self.loose_match(needle)
        if loose:
            return "ok", self.root / loose
        return "dead", None

    def external(self, target: str) -> bool:
        """A code path inside a declared dependency (`somelib/views.py` with somelib in the
        project's requirements, pyproject.toml, package.json or go.mod)."""
        needle = target.strip("/")
        if "/" not in needle or _ext(needle.rsplit("/", 1)[-1]) not in CODE_EXTS:
            return False
        first = needle.split("/", 1)[0]
        return first not in self.repo_dirs and norm_dep(first) in self.dependencies()

    def dependencies(self) -> set[str]:
        if self._deps is None:
            self._deps = set()
            for f in self.tracked:
                name = f.rsplit("/", 1)[-1]
                if not (DEP_FILE_RE.match(name)):
                    continue
                try:
                    text = (self.root / f).read_text(encoding="utf-8", errors="replace")
                except OSError:
                    continue
                if name == "package.json":
                    try:
                        data = json.loads(text)
                    except ValueError:
                        continue
                    for key in ("dependencies", "devDependencies", "peerDependencies"):
                        self._deps |= {norm_dep(k.split("/")[-1]) for k in (data.get(key) or {})}
                else:
                    self._deps |= {norm_dep(m) for m in DEP_NAME_RE.findall(text)}
        return self._deps

    def loose_match(self, needle: str) -> str:
        """Abbreviated path: the file name is unique in the repo and every cited directory
        appears, in order, in its real path (`users/0040_x.py` -> `.../users/migrations/0040_x.py`)."""
        parts = needle.split("/")
        same = [f for f in self.tracked if f.rsplit("/", 1)[-1] == parts[-1]]
        if len(same) != 1:
            return ""
        real_dirs, i = same[0].split("/")[:-1], 0
        for d in parts[:-1]:
            try:
                i = real_dirs.index(d, i) + 1
            except ValueError:
                return ""
        return same[0]

    def moved_hint(self, target: str) -> str:
        """Where a missing file probably went: same stem as a directory, or same name elsewhere."""
        needle = target.strip("/")
        stem = needle.rsplit(".", 1)[0] if "." in needle.rsplit("/", 1)[-1] else ""
        if stem:
            dirs = {d for f in self.tracked for d in _dir_prefixes(f)}
            cands = sorted(d for d in dirs if d == stem or d.endswith("/" + stem))
            if (self.root / stem).is_dir():
                cands.append(stem)
            if cands:
                return cands[0] + "/"
        name = needle.rsplit("/", 1)[-1]
        same = [f for f in self.tracked if f.rsplit("/", 1)[-1] == name]
        return same[0] if len(same) == 1 else ""


ARCHIVE_DIR = "AGENTS"
CONFIG_PATH = ".claude/agents-md.yml"
DEFAULT_ARCHIVES = ("errors/", "adr/", "postmortems/")  # config-schema.md default for archives.paths


def config_archive_paths(root: Path) -> list[str]:
    """`archives.paths` from the project config (flow list), without a YAML dependency."""
    try:
        text = (root / CONFIG_PATH).read_text(encoding="utf-8")
    except OSError:
        return list(DEFAULT_ARCHIVES)
    m = re.search(r"^archives:\s*\n((?:[ \t]+.*\n?)+)", text, re.M)
    pm = re.search(r"^[ \t]+paths:\s*\[([^\]]*)\]", m.group(1), re.M) if m else None
    if not pm:
        return list(DEFAULT_ARCHIVES)
    return [p.strip().strip("'\"") for p in pm.group(1).split(",") if p.strip()]


def under(rel: str, prefixes: list[str]) -> bool:
    """Whether rel lies in an archive dir; a relative archive path matches at any depth
    (`errors/` covers `AGENTS/errors/x.md`), a path starting with `/` only from the root."""
    for p in prefixes:
        if p.startswith("/"):
            if rel.startswith(p.strip("/") + "/"):
                return True
        elif ("/" + rel).find("/" + p.strip("/") + "/") != -1:
            return True
    return False


def default_files(root: Path, archives: list[str]) -> list[Path]:
    tracked = git_files(root)
    names = list(DEFAULT_FILES)
    names += [f for f in tracked if f.endswith("/" + DOMAIN_FILE_NAME)]
    names += sorted(f for f in tracked if f.startswith(ARCHIVE_DIR + "/") and f.endswith(".md"))
    base = root / ARCHIVE_DIR
    if base.is_dir():
        names += sorted(os.path.relpath(p, root) for p in base.rglob("*.md"))
    return [root / n for n in dict.fromkeys(names)
            if (root / n).is_file() and not under(n, archives)]


def expand(paths: list[str]) -> list[Path]:
    """Directory arguments recurse into their *.md files."""
    out: list[Path] = []
    for raw in paths:
        p = Path(raw).resolve()
        out += sorted(p.rglob("*.md")) if p.is_dir() else [p]
    return out


def is_ignored(root: Path, rel: str) -> bool:
    """True when git says the (possibly missing) path is ignored; False outside git.

    A directory-only pattern (`logs/`) never matches a missing path without its trailing
    slash, so both spellings are asked. A `!` negation match prints a line and exits 0
    with `-q` unset, so the verbose form is used and negated matches count as not ignored.
    """
    for spelling in dict.fromkeys((rel.rstrip("/"), rel.rstrip("/") + "/")):
        try:
            out = subprocess.run(["git", "-C", str(root), "check-ignore", "-v", "--", spelling],
                                 capture_output=True, text=True)
        except OSError:
            return False
        if out.returncode == 0 and out.stdout.strip() and "\t" in out.stdout:
            pattern = out.stdout.split("\t", 1)[0].split(":", 2)[-1]
            if not pattern.startswith("!"):
                return True
    return False


def main() -> int:
    ap = argparse.ArgumentParser(description="Report dead paths and links in agent docs (read-only).",
                                 epilog="Output: file:line<TAB>target<TAB>status "
                                        "(ok|dead|ambiguous|conditional). "
                                        "Exit 0 none dead, 1 dead found, 2 usage error.")
    ap.add_argument("files", nargs="*", help="markdown files to scan (default: agent docs found in the repo)")
    ap.add_argument("--root", default=".", help="repository root (default: current directory)")
    ap.add_argument("--quiet-ok", action="store_true", help="print only dead and ambiguous lines")
    ap.add_argument("--archive", action="append", default=[], metavar="PATH",
                    help="repo-relative archive path excluded from the default scope; repeatable "
                         "(adds to archives.paths of .claude/agents-md.yml)")
    try:
        args = ap.parse_args()
    except SystemExit as e:
        return EXIT_OK if e.code == 0 else EXIT_USAGE
    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"error: root is not a directory: {args.root}", file=sys.stderr)
        return EXIT_USAGE
    missing = [f for f in args.files if not Path(f).exists()]
    if missing:
        print("error: not a file: " + ", ".join(missing), file=sys.stderr)
        return EXIT_USAGE
    archives = config_archive_paths(root) + args.archive
    files = expand(args.files) if args.files else default_files(root, archives)
    names = [os.path.relpath(f, root) for f in files]
    shown = ", ".join(names[:5]) + (", ..." if len(names) > 5 else "")
    print(f"# scope: {len(files)} files ({shown})")
    resolver = Resolver(root)
    dead = 0
    for f in files:
        rel = os.path.relpath(f, root)
        for no, raw, is_link, around in citations(f):
            if not is_link:
                raw = LOCATOR_RE.sub("", raw)
            if skippable(raw, is_link):
                continue
            if not is_link:
                if not looks_like_path(raw, resolver.repo_dirs):
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
            if status == "dead" and not is_link and raw.endswith("/") \
                    and not resolver.strong_dir(raw, f):
                continue  # route-like: its first segment is a directory only somewhere deep
            if status in ("dead", "ambiguous") and not is_link and conditional(around):
                status = "conditional"
            hint = ""
            if status == "dead" and path_part:
                if is_ignored(root, path_part.strip("/")) or is_ignored(
                        root, os.path.relpath(f.parent / path_part, root)):
                    status = "local"
                elif resolver.external(path_part):
                    status = "external"
                else:
                    moved = resolver.moved_hint(path_part)
                    hint = f"\thint: moved? {moved}" if moved else ""
            dead += status == "dead"
            if status in ("dead", "ambiguous") or not args.quiet_ok:
                print(f"{rel}:{no}\t{raw}\t{status}{hint}")
    return EXIT_DEAD if dead else EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
