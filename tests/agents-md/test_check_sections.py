import shutil
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _helpers import make_repo, run_script  # noqa: E402

SCRIPT = "check_sections.py"

ROOT_DOC = """# Root

## Absolute guardrails

## 6bis. Client message scopes

### W4 - Payments

### V0-Q1 - Owner question

## Listes paginées

- **Rituel de release** : do the thing.
"""


class SectionsTest(unittest.TestCase):
    def check(self, citing: str, extra: dict | None = None, citing_path: str = "AGENTS.md"):
        files = {"AGENTS.md": ROOT_DOC, "docs/OTHER.md": "# Other\n\n## Setup steps\n", **(extra or {})}
        files[citing_path] = citing
        root = make_repo(files)
        self.addCleanup(shutil.rmtree, root, True)
        code, rows = run_script(SCRIPT, root, str(root / citing_path))
        return code, dict(rows)

    def status(self, citing, label, **kw):
        code, rows = self.check(citing, **kw)
        return rows[label]

    def test_prefix_label_matches_numbered_heading(self):
        self.assertEqual(self.status("`AGENTS.md` § 6bis\n", "AGENTS.md § 6bis", citing_path="docs/x.md"), "ok")

    def test_accent_and_case_insensitive(self):
        self.assertEqual(self.status("see AGENTS.md § listes paginees\n", "AGENTS.md § listes paginees",
                                     citing_path="docs/x.md"), "ok")

    def test_two_sections_are_both_checked(self):
        _, rows = self.check("AGENTS.md § W4 / V0\n", citing_path="docs/x.md")
        self.assertEqual(rows, {"AGENTS.md § W4": "ok", "AGENTS.md § V0": "ok"})
        code, rows = self.check("AGENTS.md § W4 / Missing part\n", citing_path="docs/x.md")
        self.assertEqual(rows["AGENTS.md § Missing part"], "dead")
        self.assertEqual(code, 1)

    def test_bold_bullet_lead_is_ok_bullet(self):
        self.assertEqual(self.status("AGENTS.md § Rituel de release\n", "AGENTS.md § Rituel de release",
                                     citing_path="docs/x.md"), "ok-bullet")

    def test_guillemets_quoted_label_with_trailing_prose(self):
        doc = "AGENTS.md § « Rituel de release » - une version = un texte (`A`/`B`\n"
        self.assertEqual(self.status(doc, "AGENTS.md § Rituel de release", citing_path="docs/x.md"), "ok-bullet")

    def test_bare_agents_md_resolves_to_root_not_citing_dir(self):
        # The citing directory has its own AGENTS.md without the section.
        extra = {"docs/AGENTS.md": "# Domain\n\n## Local only\n"}
        code, rows = self.check("AGENTS.md § Absolute guardrails\n", extra, citing_path="docs/x.md")
        self.assertEqual((code, rows["AGENTS.md § Absolute guardrails"]), (0, "ok"))

    def test_one_word_label_matches_whole_word_in_heading(self):
        self.assertEqual(self.status("AGENTS.md § Guardrails\n", "AGENTS.md § Guardrails",
                                     citing_path="docs/x.md"), "ok")

    def test_real_missing_section_and_missing_file(self):
        code, rows = self.check("AGENTS.md § Nonexistent chapter\ndocs/GONE.md § Setup steps\n",
                                citing_path="docs/x.md")
        self.assertEqual(rows["AGENTS.md § Nonexistent chapter"], "dead")
        self.assertEqual(rows["docs/GONE.md § Setup steps"], "dead")
        self.assertEqual(code, 1)

    def test_path_citation_relative_to_root(self):
        self.assertEqual(self.status("docs/OTHER.md § Setup steps\n", "docs/OTHER.md § Setup steps",
                                     citing_path="docs/x.md"), "ok")

    def test_anchor_links(self):
        code, rows = self.check("[a](docs/OTHER.md#setup-steps) [b](docs/OTHER.md#nope) [c](#root)\n",
                                citing_path="AGENTS.md")
        self.assertEqual(rows["docs/OTHER.md#setup-steps"], "ok")
        self.assertEqual(rows["docs/OTHER.md#nope"], "dead")

    def test_quiet_ok_hides_ok_and_bullets(self):
        root = make_repo({"AGENTS.md": ROOT_DOC, "docs/x.md": "AGENTS.md § 6bis\nAGENTS.md § Rituel de release\n"})
        self.addCleanup(shutil.rmtree, root, True)
        self.assertEqual(run_script(SCRIPT, root, "--quiet-ok", str(root / "docs/x.md")), (0, set()))

    def test_usage_error_exit_code(self):
        code, _ = run_script(SCRIPT, make_repo({}), "/nonexistent/missing.md")
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
