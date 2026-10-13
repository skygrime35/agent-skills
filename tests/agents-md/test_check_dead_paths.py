import shutil
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _helpers import make_repo, run_raw, run_script  # noqa: E402

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

    def test_scope_includes_agents_dir_and_prints_header(self):
        root = make_repo({**BASE, "AGENTS.md": "x\n", "CLAUDE.md": "x\n", "AGENTS/INDEX.md": "x\n",
                          "AGENTS/deep/NOTE.md": "See `docs/gone.md`.\n", "other/AGENTS.md": "x\n"})
        self.addCleanup(shutil.rmtree, root, True)
        code, lines = run_raw(SCRIPT, root)
        self.assertEqual(code, 1)
        self.assertTrue(lines[0].startswith("# scope: 5 files ("), lines[0])
        self.assertIn("AGENTS/deep/NOTE.md:1\tdocs/gone.md\tdead", lines)

    def test_archive_paths_from_config_and_flag_are_excluded(self):
        files = {**BASE, "AGENTS.md": "x\n", "AGENTS/adr/0001.md": "`docs/gone.md`\n",
                 "AGENTS/errors/e1.md": "`docs/gone.md`\n",
                 ".claude/agents-md.yml": "version: 1\narchives:\n  paths: [AGENTS/adr/, notes/]\n  policy: tolerate\n"}
        root = make_repo(files)
        self.addCleanup(shutil.rmtree, root, True)
        code, lines = run_raw(SCRIPT, root)
        self.assertTrue(lines[0].startswith("# scope: 2 files"), lines[0])  # AGENTS.md + errors/e1.md
        self.assertEqual(code, 1)
        code, lines = run_raw(SCRIPT, root, "--archive", "AGENTS/errors")
        self.assertTrue(lines[0].startswith("# scope: 1 files"), lines[0])
        self.assertEqual(code, 0)

    def test_directory_argument_recurses(self):
        root = make_repo({**BASE, "notes/a.md": "`docs/gone.md`\n", "notes/sub/b.md": "`docs/guide.md`\n",
                          "notes/skip.txt": "`docs/gone.md`\n"})
        self.addCleanup(shutil.rmtree, root, True)
        code, lines = run_raw(SCRIPT, root, str(root / "notes"))
        self.assertTrue(lines[0].startswith("# scope: 2 files"), lines[0])
        self.assertEqual(code, 1)

    def test_gitignored_missing_target_is_local_not_dead(self):
        root = make_repo({**BASE, "AGENTS.md": "`config/secrets.local.yml` and `docs/gone.md`\n",
                          ".gitignore": "*.local.yml\n"})
        self.addCleanup(shutil.rmtree, root, True)
        subprocess.run(["git", "init", "-q", str(root)], check=True)
        code, rows = run_script(SCRIPT, root)
        self.assertEqual(dict(rows), {"config/secrets.local.yml": "local", "docs/gone.md": "dead"})
        self.assertEqual(code, 1)

    def test_only_local_targets_exit_zero(self):
        root = make_repo({"AGENTS.md": "`config/secrets.local.yml`\n", ".gitignore": "*.local.yml\n"})
        self.addCleanup(shutil.rmtree, root, True)
        subprocess.run(["git", "init", "-q", str(root)], check=True)
        code, rows = run_script(SCRIPT, root)
        self.assertEqual((code, rows), (0, {("config/secrets.local.yml", "local")}))

    def test_moved_hint_stem_became_directory(self):
        root = make_repo({"x/services/a.py": "", "AGENTS.md": "`x/services.py`\n"})
        self.addCleanup(shutil.rmtree, root, True)
        code, lines = run_raw(SCRIPT, root)
        self.assertEqual(code, 1)
        self.assertIn("AGENTS.md:1\tx/services.py\tdead\thint: moved? x/services/", lines)

    def test_moved_hint_same_name_elsewhere_only_when_single(self):
        root = make_repo({"src/app/unique_mod.py": "", "AGENTS.md": "`old/unique_mod.py` `old/models.py`\n",
                          "a/models.py": "", "b/models.py": ""})
        self.addCleanup(shutil.rmtree, root, True)
        _, lines = run_raw(SCRIPT, root)
        self.assertIn("AGENTS.md:1\told/unique_mod.py\tdead\thint: moved? src/app/unique_mod.py", lines)
        self.assertIn("AGENTS.md:1\told/models.py\tdead", lines)  # two candidates: no hint


    def test_dependency_paths_are_external_not_dead(self):
        root = make_repo({"requirements.txt": "somelib==1.2\n", "src/app/views.py": "",
                          "AGENTS.md": "`somelib/views.py` `gone/views.py`\n"})
        self.addCleanup(shutil.rmtree, root, True)
        _, lines = run_raw(SCRIPT, root)
        self.assertIn("AGENTS.md:1\tsomelib/views.py\texternal", lines)
        self.assertTrue(any(l.startswith("AGENTS.md:1\tgone/views.py\tdead") for l in lines), lines)

    def test_abbreviated_unique_path_is_ok(self):
        root = make_repo({"backend/apps/users/migrations/0040_add_reason.py": "",
                          "AGENTS.md": "`users/0040_add_reason.py`\n"})
        self.addCleanup(shutil.rmtree, root, True)
        _, lines = run_raw(SCRIPT, root)
        self.assertIn("AGENTS.md:1\tusers/0040_add_reason.py\tok", lines)

    def test_name_templates_are_skipped(self):
        root = make_repo({"AGENTS.md": "`docs/postmortems/YYYY-MM-DD-short-title.md`\n"})
        self.addCleanup(shutil.rmtree, root, True)
        _, lines = run_raw(SCRIPT, root)
        self.assertFalse(any("YYYY" in l for l in lines), lines)

    def _git_repo(self, files: dict):
        root = make_repo(files)
        self.addCleanup(shutil.rmtree, root, True)
        subprocess.run(["git", "init", "-q", str(root)], check=True)
        subprocess.run(["git", "-C", str(root), "add", "-A"], check=True)
        return root

    def test_gitignored_missing_directory_is_local(self):
        root = self._git_repo({**BASE, "AGENTS.md": "`docs/logs/` and `docs/shots/` and `docs/gone/`\n",
                               ".gitignore": "logs/\ndocs/shots\n"})
        code, rows = run_script(SCRIPT, root)
        self.assertEqual(dict(rows), {"docs/logs/": "local", "docs/shots/": "local", "docs/gone/": "dead"})
        self.assertEqual(code, 1)

    def test_negated_ignore_pattern_is_not_local(self):
        root = self._git_repo({**BASE, "AGENTS.md": "`docs/keep/x.md`\n", ".gitignore": "docs/keep/*\n!docs/keep/x.md\n"})
        _, rows = run_script(SCRIPT, root)
        self.assertEqual(dict(rows), {"docs/keep/x.md": "dead"})

    def test_directory_argument_recurses(self):
        root = make_repo({"AGENTS.md": "`gone/a.md`\n", "docs/a.md": "`gone/b.md`\n", "docs/sub/c.md": "`gone/c.md`\n",
                          "docs/skip.txt": "`gone/d.md`\n"})
        self.addCleanup(shutil.rmtree, root, True)
        code, lines = run_raw(SCRIPT, root, str(root / "docs"))
        self.assertEqual(code, 1)
        self.assertEqual(sorted(l.split("\t")[0] for l in lines if not l.startswith("#")),
                         ["docs/a.md:1", "docs/sub/c.md:1"])

    def test_archives_excluded_by_default_and_scannable_by_directory(self):
        root = make_repo({"AGENTS.md": "ok\n", "AGENTS/errors/e.md": "`gone/e.md`\n"})
        self.addCleanup(shutil.rmtree, root, True)
        self.assertEqual(run_raw(SCRIPT, root)[0], 0)
        self.assertEqual(run_raw(SCRIPT, root, str(root / "AGENTS" / "errors"))[0], 1)


if __name__ == "__main__":
    unittest.main()
