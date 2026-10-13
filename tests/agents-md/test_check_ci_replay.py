import shutil
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _helpers import make_repo, run_raw  # noqa: E402

SCRIPT = "check_ci_replay.py"

CI = """name: CI
on: [push]
jobs:
  lint:
    name: Lint
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: backend
    steps:
      - uses: actions/checkout@v4
      - run: pip install ruff
      - name: ruff
        run: |
          ruff check .
          ruff format --check .
  scripts-lint:
    runs-on: ubuntu-latest
    steps:
      - run: ruff check --isolated scripts
  types:
    runs-on: ubuntu-latest
    steps:
      - name: mypy
        env:
          KEY: "x: y"
        run: cd backend && mypy --strict apps config # trailing comment
  frontend:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: frontend
    steps:
      - run: npm ci
      - run: npm test
      - run: npx tsc --noEmit
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: aquasecurity/trivy-action@abc
        with:
          scan-type: image
  deploy:
    runs-on: self-hosted
    steps:
      - run: ./scripts/deploy.sh
  plumbing:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: echo hello
"""

FILES = {"backend/apps/a.py": "", "backend/config/s.py": "", "scripts/x.sh": "", "frontend/package.json": "{}",
         ".github/workflows/ci.yml": CI}

REPLAY_MD = """# Doc

## Vital commands

```bash
# comment line
docker compose exec backend ruff check . && docker compose exec backend ruff format --check .
cd backend && mypy apps config
ruff check --isolated scripts
cd frontend && npm run test && npx tsc --noEmit
trivy image app:latest
```

## Other

```bash
bash scripts/deploy.sh
```
"""


class CiReplayTest(unittest.TestCase):
    def run_check(self, files=None, *extra):
        root = make_repo({**FILES, **(files or {})})
        self.addCleanup(shutil.rmtree, root, True)
        code, lines = run_raw(SCRIPT, root, *extra)
        rows = {l.split("\t")[0].split(":", 1)[1]: l.split("\t")[1:] for l in lines if not l.startswith("#")}
        return code, rows, lines

    def test_markdown_block_covers_jobs(self):
        code, rows, _ = self.run_check({"AGENTS.md": REPLAY_MD}, "--replay", "AGENTS.md", "--heading", "vital commands")
        self.assertEqual({k: v[0] for k, v in rows.items()},
                         {"lint": "covered", "scripts-lint": "covered", "types": "covered", "frontend": "covered",
                          "scan": "covered", "deploy": "missing", "plumbing": "excluded"})
        self.assertEqual(code, 1)

    def test_heading_scope_ends_at_next_heading(self):
        _, rows, _ = self.run_check({"AGENTS.md": REPLAY_MD}, "--replay", "AGENTS.md", "--heading", "Vital")
        self.assertEqual(rows["deploy"][0], "missing")
        _, rows, _ = self.run_check({"AGENTS.md": REPLAY_MD}, "--replay", "AGENTS.md")  # every block
        self.assertEqual(rows["deploy"][0], "covered")

    def test_exclude_makes_exit_zero(self):
        code, rows, _ = self.run_check({"AGENTS.md": REPLAY_MD}, "--replay", "AGENTS.md", "--heading", "Vital",
                                       "--exclude", "deploy")
        self.assertEqual((code, rows["deploy"]), (0, ["excluded", "--exclude"]))

    def test_exclude_by_name_and_file(self):
        code, rows, _ = self.run_check({"AGENTS.md": REPLAY_MD}, "--replay", "AGENTS.md", "--heading", "Vital",
                                       "--exclude", ".github/workflows/ci.yml:deploy", "--exclude", "Lint")
        self.assertEqual(code, 0)
        self.assertEqual(rows["lint"][0], "excluded")

    def test_missing_path_scope_is_reported(self):
        # the replay lints `backend` but no longer `scripts`
        md = REPLAY_MD.replace("ruff check --isolated scripts\n", "")
        code, rows, _ = self.run_check({"AGENTS.md": md}, "--replay", "AGENTS.md", "--heading", "Vital")
        self.assertEqual(rows["scripts-lint"][0], "missing")
        self.assertIn("ruff check --isolated scripts", rows["scripts-lint"][1])

    def test_different_subcommand_is_missing(self):
        md = REPLAY_MD.replace("ruff format --check", "ruff check")
        _, rows, _ = self.run_check({"AGENTS.md": md}, "--replay", "AGENTS.md", "--heading", "Vital")
        self.assertEqual(rows["lint"][0], "missing")
        self.assertIn("ruff format", rows["lint"][1])

    def test_shell_script_step_lines_and_plain_lines(self):
        script = (
            "#!/usr/bin/env bash\n"
            "step backend ruff \"cd backend && ruff check . && ruff format --check .\"\n"
            "step scripts ruff-s \"ruff check --isolated scripts\"\n"
            "advisory backend types \"dx 'mypy --strict apps config'\"\n"
            "step frontend fe \"cd frontend && npm run test \\\n   && npx tsc --noEmit\"\n"
            "step security trivy \"trivy image x\"\n"
        )
        code, rows, _ = self.run_check({"scripts/ci_local.sh": script}, "--replay", "scripts/ci_local.sh",
                                       "--exclude", "deploy")
        self.assertEqual({k: v[0] for k, v in rows.items()},
                         {"lint": "covered", "scripts-lint": "covered", "types": "covered", "frontend": "covered",
                          "scan": "covered", "deploy": "excluded", "plumbing": "excluded"})
        self.assertEqual(code, 0)

    def test_plain_command_script(self):
        script = "set -e\nruff check backend\nruff format --check backend\nruff check --isolated scripts\n" \
                 "mypy backend/apps backend/config\nnpm test --prefix frontend\nnpx tsc --noEmit\n"
        _, rows, _ = self.run_check({"ci.sh": script}, "--replay", "ci.sh", "--exclude", "deploy")
        self.assertEqual(rows["lint"][0], "covered")
        self.assertEqual(rows["types"][0], "covered")

    def test_workflow_parsing_run_block_comments_and_expressions(self):
        wf = ("jobs:\n  a:\n    steps:\n      - name: x\n        run: >\n          ruff check\n          src # keep\n"
              "      - run: python3 ${{ github.workspace }}/tools/c.py --x ${{ matrix.v }}\n"
              "        working-directory: ${{ github.workspace }}\n")
        md = "```\nruff check src\npython3 tools/c.py\n```\n"
        code, rows, _ = self.run_check({".github/workflows/ci.yml": wf, "R.md": md, "src/a.py": "", "tools/c.py": ""},
                                       "--replay", "R.md")
        self.assertEqual((code, rows["a"][0]), (0, "covered"))

    def test_env_cd_flags_and_order_are_ignored(self):
        wf = "jobs:\n  a:\n    steps:\n      - run: FOO=1 pytest -q -x apps/a\n"
        md = "```\ncd /tmp && true\nBAR=2 pytest apps/a --tb=short -v\n```\n"
        code, rows, _ = self.run_check({".github/workflows/ci.yml": wf, "R.md": md, "apps/a/t.py": ""}, "--replay", "R.md")
        self.assertEqual((code, rows["a"][0]), (0, "covered"))

    def test_inline_python_is_missing_but_py_compile_matches_compileall(self):
        wf = ("jobs:\n  a:\n    steps:\n      - run: python -c \"print(1)\"\n  b:\n    steps:\n"
              "      - run: |\n          python -c \"\n          import py_compile\n          py_compile.compile('x')\n          \"\n")
        md = "```\npython -m compileall -q .\n```\n"
        code, rows, _ = self.run_check({".github/workflows/ci.yml": wf, "R.md": md}, "--replay", "R.md")
        self.assertEqual((rows["a"][0], rows["b"][0], code), ("missing", "covered", 1))

    def test_pipe_filter_and_command_substitution_are_not_checks(self):
        wf = ("jobs:\n  a:\n    steps:\n      - run: |\n          app=$(echo \"$d\" | cut -d/ -f2)\n"
              "          if npm run | grep -q \"lint\"; then npm run lint; fi\n          tar czf - . | gzip > out.tgz\n")
        md = "```\nnpm run lint\n```\n"
        code, rows, _ = self.run_check({".github/workflows/ci.yml": wf, "R.md": md}, "--replay", "R.md")
        self.assertEqual((code, rows["a"][0]), (0, "covered"))

    def test_placeholder_paths_compare_by_their_stable_prefix(self):
        wf = "jobs:\n  a:\n    steps:\n      - run: pytest \"apps/$app/tests/unit\" -p no:django\n"
        md = "```\npytest apps/<x>/tests/unit -p no:django\n```\n"
        code, rows, _ = self.run_check({".github/workflows/ci.yml": wf, "R.md": md, "apps/a.py": ""}, "--replay", "R.md")
        self.assertEqual(rows["a"][0], "covered")

    def test_compose_file_distinguishes_commands(self):
        wf = "jobs:\n  a:\n    steps:\n      - run: docker compose -f docker-compose.prod.yml config --quiet\n"
        md = "```\ndocker compose -f docker-compose.dev.yml config --quiet\n```\n"
        files = {".github/workflows/ci.yml": wf, "R.md": md, "docker-compose.prod.yml": "", "docker-compose.dev.yml": ""}
        self.assertEqual(self.run_check(files, "--replay", "R.md")[1]["a"][0], "missing")
        files["R.md"] = md.replace("dev", "prod")
        self.assertEqual(self.run_check(files, "--replay", "R.md")[1]["a"][0], "covered")

    def test_only_missing_hides_covered(self):
        _, _, lines = self.run_check({"AGENTS.md": REPLAY_MD}, "--replay", "AGENTS.md", "--heading", "Vital",
                                     "--only-missing")
        self.assertEqual([l.split("\t")[1] for l in lines if not l.startswith("#")], ["missing"])

    def test_usage_errors_exit_two(self):
        root = make_repo(FILES)
        self.addCleanup(shutil.rmtree, root, True)
        self.assertEqual(run_raw(SCRIPT, root)[0], 2)  # no --replay
        self.assertEqual(run_raw(SCRIPT, root, "--replay", "nope.sh")[0], 2)
        (root / "d.md").write_text("# T\n")
        self.assertEqual(run_raw(SCRIPT, root, "--replay", "d.md", "--heading", "absent")[0], 2)
        empty = make_repo({"R.md": "```\nls\n```\n"})
        self.addCleanup(shutil.rmtree, empty, True)
        self.assertEqual(run_raw(SCRIPT, empty, "--replay", "R.md")[0], 2)  # no workflows directory

    def test_help_documents_cli(self):
        code, lines = run_raw(SCRIPT, Path("."), "--help")
        text = "\n".join(lines)
        for flag in ("--replay", "--heading", "--exclude", "--workflows", "--only-missing"):
            self.assertIn(flag, text)
        self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
