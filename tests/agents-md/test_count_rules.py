"""Unit tests for agents-md/scripts/count_rules.py (neutral fixtures)."""
import contextlib
import io
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(HERE, "..", "..", "plugins", "dev-skills", "skills", "agents-md", "scripts")
sys.path.insert(0, SCRIPTS)
import count_rules  # noqa: E402

EN = """# Demo

Intro sentence without any rule.

## Rules

- Never commit to the main branch.
- Run the tests before pushing.
- You must use the wrapper; always check the exit code.
- A plain bullet.

```
never counted inside a fence
```

<!-- must never be counted -->

## Other

You must read this. Do not skip it.

### Nested

- Forbidden: editing generated files.
"""

FR = """# Demo

## Regles

- Il ne faut jamais pousser sur la branche principale.
- Le build doit passer avant la fusion.
- Aucun secret dans le depot.
- Une ligne neutre.

## Listes paginées

- Toujours paginer les listes.
"""


def run(files, *extra):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = count_rules.main(list(files) + list(extra))
    return code, (json.loads(out.getvalue()) if code == 0 else None)


class CountRulesTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)

    def write(self, name, text):
        path = os.path.join(self.dir.name, name)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        return path

    def test_english_counts(self):
        code, data = run([self.write("en.md", EN)])
        self.assertEqual(code, 0)
        f = data["files"][0]
        self.assertEqual(f["lang"], "en")
        # never, must/always (one bullet), must, do not, forbidden = 5
        self.assertEqual(f["statements"], 5)
        # never, do not, forbidden
        self.assertEqual(f["prohibitions"], 3)

    def test_french_counts_accent_insensitive(self):
        code, data = run([self.write("fr.md", FR)], "--section-heading", "listes paginees")
        self.assertEqual(code, 0)
        f = data["files"][0]
        self.assertEqual(f["lang"], "fr")
        self.assertEqual(f["statements"], 4)
        self.assertEqual(f["prohibitions"], 2)
        sel = f["selected"][0]
        self.assertEqual(sel["matched"], ["Listes paginées"])
        self.assertEqual(sel["statements"], 1)

    def test_section_includes_subsections(self):
        _, data = run([self.write("en.md", EN)], "--section-heading", "other")
        sel = data["files"][0]["selected"][0]
        self.assertEqual(sel["statements"], 3)
        self.assertEqual(sel["prohibitions"], 2)

    def test_forced_lang_ignores_other_markers(self):
        _, data = run([self.write("en.md", EN)], "--lang", "fr")
        self.assertEqual(data["files"][0]["statements"], 0)

    def test_totals_over_several_files(self):
        a = self.write("a.md", "- Never do X.\n")
        b = self.write("b.md", "- Always do Y.\n")
        _, data = run([a, b], "--lang", "en")
        self.assertEqual(data["total_statements"], 2)
        self.assertEqual(data["total_prohibitions"], 1)

    def test_missing_file_exits_2(self):
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            code = count_rules.main([os.path.join(self.dir.name, "absent.md")])
        self.assertEqual(code, 2)

    def test_help_exits_0(self):
        with contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(SystemExit) as cm:
                count_rules.main(["--help"])
        self.assertEqual(cm.exception.code, 0)


if __name__ == "__main__":
    unittest.main()
