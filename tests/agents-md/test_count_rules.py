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
        # 4 list items in "Rules" + 2 modal sentences + 1 nested item = 7
        self.assertEqual(f["statements"], 7)
        # never, do not, forbidden
        self.assertEqual(f["prohibitions"], 3)

    def test_french_counts_accent_insensitive(self):
        code, data = run([self.write("fr.md", FR)], "--section-heading", "listes paginees")
        self.assertEqual(code, 0)
        f = data["files"][0]
        self.assertEqual(f["lang"], "fr")
        self.assertEqual(f["statements"], 5)
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
        # list items still count structurally; prose sentences need a modal of the forced language
        _, data = run([self.write("en.md", EN)], "--lang", "fr")
        self.assertEqual(data["files"][0]["statements"], 5)
        self.assertEqual(data["files"][0]["prohibitions"], 0)

    def test_imperative_list_without_modal_counts_per_item(self):
        text = "# Doc\n\n## Rules\n\n- Run the tests.\n- Keep commits small.\n  - Nested one.\n\n"
        _, data = run([self.write("a.md", text)])
        self.assertEqual(data["files"][0]["statements"], 3)
        self.assertEqual(data["files"][0]["prohibitions"], 0)

    def test_table_rows_count_not_header_or_separator(self):
        text = "# Doc\n\n## Rules\n\n| Rule | Why |\n|---|---|\n| Do A | x |\n| Never B | y |\n"
        _, data = run([self.write("a.md", text)])
        self.assertEqual(data["files"][0]["statements"], 2)
        self.assertEqual(data["files"][0]["prohibitions"], 1)

    def test_plain_prose_without_modal_does_not_count(self):
        _, data = run([self.write("a.md", "# Doc\n\n## Rules\n\nThis is background. It explains things.\n")])
        self.assertEqual(data["files"][0]["statements"], 0)

    def test_non_normative_sections_skip_structural_rule_but_keep_modals(self):
        text = ("# Doc\n\n## Tech stack\n\n- Python\n- Postgres\n- Never edit the lockfile.\n\n"
                "### Layout\n\n- src/\n\n## Commands\n\n| cmd | what |\n|--|--|\n| make | build |\n\n"
                "## Rules\n\n- Be kind.\n")
        _, data = run([self.write("a.md", text)])
        f = data["files"][0]
        self.assertEqual(f["statements"], 2)  # the modal bullet in stack + the Rules item
        self.assertEqual(f["prohibitions"], 1)
        skipped = {s["heading"]: s["skipped"] for s in f["sections"]}
        self.assertEqual(skipped, {"Doc": False, "Tech stack": True, "Layout": True,
                                   "Commands": True, "Rules": False})

    def test_french_non_normative_headings_and_overrides(self):
        text = "# Doc\n\n## Arborescence\n\n- src/\n\n## Regles\n\n- Une regle.\n"
        _, data = run([self.write("a.md", text)])
        self.assertEqual(data["files"][0]["statements"], 1)
        _, data = run([self.write("b.md", text)], "--no-skip")
        self.assertEqual(data["files"][0]["statements"], 2)
        _, data = run([self.write("c.md", text)], "--skip-heading", "^regles$")
        self.assertEqual(data["files"][0]["statements"], 1)  # only Arborescence now counts

    def test_bad_skip_regex_exits_2(self):
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            code = count_rules.main([self.write("a.md", "# x\n"), "--skip-heading", "("])
        self.assertEqual(code, 2)

    def test_totals_and_selected_totals_have_no_double_count(self):
        text = "# Doc\n\n## Guardrails\n\n- Never A.\n\n### Sub\n\n- Do B.\n\n## Other\n\n- C.\n"
        _, data = run([self.write("a.md", text)], "--section-heading", "guardrails",
                      "--section-heading", "sub", "--section-heading", "guard")
        self.assertEqual(data["totals"], {"statements": 3, "prohibitions": 1})
        self.assertEqual(data["selected_totals"], {"statements": 2, "prohibitions": 1})
        self.assertEqual(data["total_statements"], 3)
        sel = data["files"][0]["selected"]
        self.assertEqual([x["statements"] for x in sel], [2, 1, 2])  # per pattern, overlap kept

    def test_no_selected_totals_without_section_heading(self):
        _, data = run([self.write("a.md", "- Never A.\n")])
        self.assertNotIn("selected_totals", data)

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
