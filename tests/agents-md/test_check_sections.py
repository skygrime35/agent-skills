import shutil
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _helpers import make_repo, run_raw, run_script  # noqa: E402

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

    def test_substring_of_heading_is_partial_with_suggestion(self):
        root = make_repo({"AGENTS.md": ROOT_DOC, "docs/x.md": "AGENTS.md § Guardrails\n"})
        self.addCleanup(shutil.rmtree, root, True)
        code, lines = run_raw(SCRIPT, root, str(root / "docs/x.md"))
        self.assertEqual(code, 0)  # partial is reported, not dead
        self.assertEqual(lines, ["docs/x.md:1\tAGENTS.md § Guardrails\tpartial\tsuggest: Absolute guardrails"])

    def test_full_heading_text_is_ok_even_with_number_prefix(self):
        self.assertEqual(self.status("AGENTS.md § Absolute guardrails\n", "AGENTS.md § Absolute guardrails",
                                     citing_path="docs/x.md"), "ok")
        self.assertEqual(self.status("AGENTS.md § Client message scopes\n", "AGENTS.md § Client message scopes",
                                     citing_path="docs/x.md"), "ok")

    def test_partial_multiword_run_inside_heading(self):
        self.assertEqual(self.status("AGENTS.md § message scopes\n", "AGENTS.md § message scopes",
                                     citing_path="docs/x.md"), "partial")

    def test_partial_is_shown_by_quiet_ok(self):
        root = make_repo({"AGENTS.md": ROOT_DOC, "docs/x.md": "AGENTS.md § Guardrails\n"})
        self.addCleanup(shutil.rmtree, root, True)
        _, rows = run_script(SCRIPT, root, "--quiet-ok", str(root / "docs/x.md"))
        self.assertEqual(rows, {("AGENTS.md § Guardrails", "partial")})

    def test_label_token_needs_a_digit(self):
        # "Absolute" is the first word of a heading, not a number/label token.
        self.assertEqual(self.status("AGENTS.md § Absolute\n", "AGENTS.md § Absolute",
                                     citing_path="docs/x.md"), "partial")

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

    VIDEO_DOC = "# Videos\n\n## Thumbnail origin and cuts\n\n## `ready` gate on the essentials + local sync\n\n## Setup\n"

    def test_label_with_and_is_not_cut(self):
        extra = {"docs/V.md": self.VIDEO_DOC}
        for text in ("see `docs/V.md` § Thumbnail origin and cuts.\n", "docs/V.md § Thumbnail origin and cuts\n"):
            code, rows = self.check(text, extra=extra, citing_path="docs/x.md")
            self.assertEqual(rows, {"docs/V.md § Thumbnail origin and cuts": "ok"}, text)
            self.assertEqual(code, 0)

    def test_prose_after_a_short_name_still_resolves(self):
        extra = {"docs/V.md": self.VIDEO_DOC}
        _, rows = self.check("docs/V.md § Setup and then run it\n", extra=extra, citing_path="docs/x.md")
        self.assertEqual(rows, {"docs/V.md § Setup": "ok"})

    def test_part_of_a_heading_before_and_stays_partial(self):
        extra = {"docs/V.md": self.VIDEO_DOC}
        _, rows = self.check("docs/V.md § Thumbnail origin\n", extra=extra, citing_path="docs/x.md")
        self.assertEqual(rows, {"docs/V.md § Thumbnail origin": "partial"})

    def test_backticked_label_with_trailing_word(self):
        extra = {"docs/V.md": self.VIDEO_DOC}
        for text in ("`docs/V.md` § `ready` gate.\n", "see docs/V.md § `ready` gate, then stop\n"):
            code, rows = self.check(text, extra=extra, citing_path="docs/x.md")
            self.assertEqual(rows, {"docs/V.md § ready gate": "ok"}, text)

    def test_backticked_label_alone_keeps_partial_when_only_a_part(self):
        extra = {"docs/V.md": self.VIDEO_DOC}
        _, rows = self.check("docs/V.md § `ready`\n", extra=extra, citing_path="docs/x.md")
        self.assertEqual(rows, {"docs/V.md § ready": "partial"})

    def test_exact_backticked_heading_is_ok(self):
        extra = {"docs/V.md": "# V\n\n## `ready`\n"}
        _, rows = self.check("docs/V.md § `ready`\n", extra=extra, citing_path="docs/x.md")
        self.assertEqual(rows, {"docs/V.md § ready": "ok"})

    def test_directory_argument_recurses(self):
        root = make_repo({"AGENTS.md": ROOT_DOC, "docs/a.md": "AGENTS.md § 6bis\n",
                          "docs/sub/b.md": "AGENTS.md § Nowhere\n", "docs/note.txt": "AGENTS.md § Nowhere\n"})
        self.addCleanup(shutil.rmtree, root, True)
        code, lines = run_raw(SCRIPT, root, str(root / "docs"))
        self.assertEqual(code, 1)
        self.assertEqual(sorted(l.split("\t")[0] for l in lines), ["docs/a.md:1", "docs/sub/b.md:1"])

    def test_archives_flag_scans_default_archive_dirs_only(self):
        root = make_repo({"AGENTS.md": "AGENTS.md § Nowhere\n", "AGENTS/errors/e.md": "AGENTS.md § Absolute guardrails\n",
                          "adr/0001.md": "AGENTS.md § Missing\n"})
        self.addCleanup(shutil.rmtree, root, True)
        code, lines = run_raw(SCRIPT, root, "--archives")
        self.assertEqual(sorted(l.split("\t")[0] for l in lines), ["AGENTS/errors/e.md:1", "adr/0001.md:1"])
        self.assertEqual(code, 1)

    def test_archives_flag_uses_config_paths(self):
        root = make_repo({"AGENTS.md": ROOT_DOC, ".claude/agents-md.yml": "archives:\n  paths: [old/]\n",
                          "old/x.md": "AGENTS.md § Missing\n", "adr/y.md": "AGENTS.md § Missing\n"})
        self.addCleanup(shutil.rmtree, root, True)
        _, lines = run_raw(SCRIPT, root, "--archives")
        self.assertEqual([l.split("\t")[0] for l in lines], ["old/x.md:1"])

    def test_usage_error_exit_code(self):
        code, _ = run_script(SCRIPT, make_repo({}), "/nonexistent/missing.md")
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
