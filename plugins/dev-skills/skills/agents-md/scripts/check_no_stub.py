#!/usr/bin/env python3
# dev-skills: agents-md __PLUGIN_VERSION__
"""Fail when unimplemented placeholders reach the shipped tree.

The rule: not implemented means not merged. A documented function whose body
is `pass`, a `raise NotImplementedError`, a `throw new Error("not implemented")`
are all promises that no test will catch.

Protocol and abstract declarations are exempt: `...` in a Protocol body,
`@abstractmethod`, and TypeScript interface/declare blocks are legitimate.

    check_no_stub.py backend/ frontend/src

Exit code 1 on any hit, 0 when clean.
"""

from __future__ import annotations

import argparse
import ast
import fnmatch
import re
import sys
from pathlib import Path

DEFAULT_EXCLUDES = [
    "*/node_modules/*",
    "*/.next/*",
    "*/.git/*",
    "*/dist/*",
    "*/build/*",
    "*/__pycache__/*",
    "*/venv/*",
    "*/.venv/*",
    "*/migrations/*",
    "*.lock",
    "*.min.js",
    "*.map",
    "*.d.ts",
]

JS_SUFFIXES = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".vue", ".svelte"}

JS_STUB = re.compile(
    r"""throw\s+new\s+Error\s*\(\s*['"`][^'"`]*\b(not\s+implemented|unimplemented|todo)\b""",
    re.IGNORECASE,
)


def excluded(path: Path, patterns: list[str]) -> bool:
    s = str(path)
    return any(fnmatch.fnmatch(s, pat) for pat in patterns)


def is_protocol_or_abstract(node: ast.ClassDef) -> bool:
    for base in node.bases:
        name = getattr(base, "id", None) or getattr(base, "attr", None)
        if name in {"Protocol", "ABC"}:
            return True
    return False


def has_decorator(
    node: ast.FunctionDef | ast.AsyncFunctionDef, names: set[str]
) -> bool:
    for d in node.decorator_list:
        n = getattr(d, "id", None) or getattr(d, "attr", None)
        if n in names:
            return True
    return False


def python_stubs(path: Path, text: str) -> list[str]:
    out: list[str] = []
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return out

    exempt_functions: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and is_protocol_or_abstract(node):
            for b in ast.walk(node):
                if isinstance(b, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    exempt_functions.add(id(b))

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if id(node) in exempt_functions or has_decorator(
                node, {"abstractmethod", "overload"}
            ):
                continue
            body = list(node.body)
            if (
                body
                and isinstance(body[0], ast.Expr)
                and isinstance(body[0].value, ast.Constant)
                and isinstance(body[0].value.value, str)
            ):
                docstring, body = True, body[1:]
            else:
                docstring = False
            if not body:
                continue
            # `pass` as the only statement of a *documented* function is the smell.
            if len(body) == 1 and isinstance(body[0], ast.Pass) and docstring:
                out.append(
                    f"{path}:{node.lineno}: `{node.name}` is documented but its body is `pass`"
                )
        if isinstance(node, ast.Raise):
            exc = node.exc
            name = None
            if isinstance(exc, ast.Call):
                name = getattr(exc.func, "id", None) or getattr(exc.func, "attr", None)
            elif isinstance(exc, ast.Name):
                name = exc.id
            if name == "NotImplementedError":
                out.append(f"{path}:{node.lineno}: raise NotImplementedError")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--exclude", action="append", default=[])
    args = ap.parse_args()

    patterns = DEFAULT_EXCLUDES + args.exclude
    hits: list[str] = []

    for root in args.paths:
        p = Path(root)
        files = (
            [p]
            if p.is_file()
            else [
                f
                for f in p.rglob("*")
                if f.is_file()
                and (f.suffix == ".py" or f.suffix in JS_SUFFIXES)
                and not excluded(f, patterns)
            ]
        )
        for f in files:
            try:
                text = f.read_text(encoding="utf-8", errors="strict")
            except (UnicodeDecodeError, OSError):
                continue
            if f.suffix == ".py":
                hits.extend(python_stubs(f, text))
            else:
                for lineno, line in enumerate(text.splitlines(), 1):
                    if JS_STUB.search(line):
                        hits.append(f"{f}:{lineno}: {line.strip()[:90]}")

    for h in hits:
        print(h)

    if hits:
        print(f"\nFAIL: {len(hits)} stub(s). Not implemented means not merged.")
        return 1

    print(f"OK: no stub in {', '.join(args.paths)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
