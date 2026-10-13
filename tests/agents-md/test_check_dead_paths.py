import shutil
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _helpers import make_repo, run_script  # noqa: E402

SCRIPT = "check_dead_paths.py"

BASE = {
    "src/app/models.py": "",
    "src/app/migrations/0001_initial.py": "",
    "docs/guide.md": "# Guide\n",
    "svc/api/views.py": "",
    "svc/utils/helpers.py": "",
    "svc/other/helpers.py": "",
}


class DeadPathsTest(unittest.TestCase):
    def check(self, doc: str, extra: dict | None = None):
        root = make_repo({**BASE, **(extra or {}), "AGENTS.md": doc})
        self.addCleanup(shutil.rmtree, root, True)
        return run_script(SCRIPT, root)

    def statuses(self, doc: str, extra: dict | None = None) -> dict:
        return dict(self.check(doc, extra)[1])

    def test_ok_paths(self):
        code, rows = self.check("See `src/app/models.py`, `docs/guide.md`, [g](docs/guide.md), `src/app/`.\n")
        self.assertEqual(code, 0)
        self.assertEqual({s for _, s in rows}, {"ok"})

    def test_false_positive_categories_are_ignored(self):
        cases = [
            "users/0065", "app/0012_auto", "Foo.bar", "api/views.Class", "pkg/mod.func",
            "@scope/pkg", "@scope/pkg@1.2", "next/headers", "pkg/sub", "reports/summary/",
            "left-1/2", "origin/main", ".git/index.lock", "POST/PUT", "try/except",
            "try/except/finally", "1000/min", "10/hour", "live_started/ended",
            "node_modules/", "frontend/node_modules/", "media.example.com/ads/x.png",
            "apps/X/api.py", "path with space/x.py", "$HOME/x.py", "src/*.py",
            "migrations/0042", "ENV_VAR/users/",
        ]
        doc = "\n".join(f"- `{c}`" for c in cases) + "\n"
        code, rows = self.check(doc)
        self.assertEqual(rows, set(), rows)
        self.assertEqual(code, 0)

    def test_real_dead_file_paths_are_reported(self):
        doc = "`src/wrong/models.py` and `lib/missing.ts` and `docs/gone.md`, `scripts/deploy.sh`.\n"
        code, rows = self.check(doc)
        self.assertEqual(code, 1)
        self.assertEqual(rows, {("src/wrong/models.py", "dead"), ("lib/missing.ts", "dead"),
                                ("docs/gone.md", "dead"), ("scripts/deploy.sh", "dead")})

    def test_dead_directory_with_real_first_segment(self):
        st = self.statuses("`src/missing_dir/` and `src/app/`.\n")
        self.assertEqual(st["src/missing_dir/"], "dead")
        self.assertEqual(st["src/app/"], "ok")

    def test_dead_markdown_link_and_anchor(self):
        st = self.statuses("[a](docs/nope.md) [b](docs/guide.md#absent) [c](docs/guide.md#guide)\n")
        self.assertEqual(st["docs/nope.md"], "dead")
        self.assertEqual(st["docs/guide.md#absent"], "dead")
        self.assertEqual(st["docs/guide.md#guide"], "ok")

    def test_ambiguous_suffix_is_separate_from_dead(self):
        code, rows = self.check("`utils/helpers.py` `other/helpers.py` `helpers/x.py`\n")
        st = dict(rows)
        self.assertEqual(st["utils/helpers.py"], "ok")
        self.assertEqual(st["other/helpers.py"], "ok")
        code2, rows2 = self.check("`svc/utils/` `thing/helpers.py`\n",
                                  {"a/thing/helpers.py": "", "b/thing/helpers.py": ""})
        self.assertEqual(dict(rows2)["thing/helpers.py"], "ambiguous")
        self.assertEqual(code2, 0)

    def test_conditional_mentions_are_not_dead(self):
        doc = ("The old `src/legacy/old.py` has been deleted.\n"
               "Use `config/local.yml` if present.\n"
               "Il n'y a pas de `src/zzz/models.py`: supprime.\n"
               "There is no `src/app/` layer in `svc/`.\n"
               "The shim `src/shim/views.py`\nwas removed long ago.\n")
        code, rows = self.check(doc)
        self.assertEqual(code, 0)
        self.assertTrue(rows and all(s in ("conditional", "ok") for _, s in rows), rows)

    def test_conditional_does_not_hide_a_real_dead_on_another_line(self):
        doc = "Old thing was deleted.\n\n\n`src/wrong/models.py` is the entry point.\n"
        self.assertEqual(self.statuses(doc)["src/wrong/models.py"], "dead")

    def test_line_suffix_is_ignored(self):
        st = self.statuses("`src/app/models.py:12` `src/app/models.py::test_x` `src/none.py:3`\n")
        self.assertEqual(st["src/app/models.py"], "ok")
        self.assertEqual(st["src/none.py"], "dead")

    def test_fenced_code_is_skipped_and_quiet_ok(self):
        root = make_repo({**BASE, "AGENTS.md": "```\n`gone/x.py`\n```\n`src/app/models.py`\n"})
        self.addCleanup(shutil.rmtree, root, True)
        code, rows = run_script(SCRIPT, root, "--quiet-ok")
        self.assertEqual((code, rows), (0, set()))

    def test_usage_error_exit_code(self):
        code, _ = run_script(SCRIPT, make_repo({}), "/nonexistent/missing.md")
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
