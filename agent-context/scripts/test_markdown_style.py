#!/usr/bin/env python3
"""Tests for lint_markdown_style.py — stdlib `unittest`, no tool install required.

The lint shells out to `dprint` and `rumdl`, so the suite puts stub executables
of those names on PATH and drives the script as a subprocess under the real
`winter lint` env contract. That exercises the parsing, the scope filtering, and
the degradation paths without either binary present.

Run from this directory:

    python3 -m unittest test_markdown_style
"""

from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "lint_markdown_style.py"


class MarkdownStyleLintTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.workspace = Path(self._tmp.name).resolve()
        self.repo = self.workspace / "repo"
        self.repo.mkdir()
        self.bin = self.workspace / "bin"
        self.bin.mkdir()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    # ── fixture helpers ───────────────────────────────────────────────────────

    def configure(self, *, dprint: bool = True, rumdl: bool = True) -> None:
        """Commit one or both tool configs — the opt-in the lint keys on."""
        if dprint:
            (self.repo / "dprint.json").write_text("{}\n")
        if rumdl:
            (self.repo / ".rumdl.toml").write_text("[global]\n")

    def stub(self, name: str, stdout: str, exit_code: int) -> None:
        path = self.bin / name
        path.write_text(f"#!/bin/sh\ncat <<'STUB_EOF'\n{stdout}STUB_EOF\nexit {exit_code}\n")
        path.chmod(path.stat().st_mode | stat.S_IEXEC)

    def doc(self, relpath: str) -> Path:
        file = self.repo / relpath
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text("# doc\n")
        return file

    def run_lint(self, paths: list[Path], *, with_stubs: bool = True) -> tuple[list[dict], int]:
        env = dict(os.environ)
        env["WINTER_WORKSPACE_DIR"] = str(self.workspace)
        env["WINTER_LINT_PATHS"] = "\n".join(str(p) for p in paths)
        env["WINTER_LINT_SCOPE"] = "repo"
        env["PATH"] = f"{self.bin}:/usr/bin:/bin" if with_stubs else "/usr/bin:/bin"
        proc = subprocess.run([sys.executable, str(SCRIPT)], env=env, capture_output=True, text=True)
        findings = [json.loads(line) for line in proc.stdout.splitlines() if line.strip()]
        return findings, proc.returncode

    # ── the checks ────────────────────────────────────────────────────────────

    def test_violations_from_both_tools_become_fail_findings(self) -> None:
        self.configure()
        doc = self.doc("doc.md")
        self.stub("dprint", f"{doc}\n", 20)
        self.stub("rumdl", "doc.md:12:1: [MD013] Line length 130 exceeds 120 characters [*]\n", 1)

        findings, code = self.run_lint([self.repo])

        self.assertEqual(code, 0)
        by_check = {f["check"]: f for f in findings}
        self.assertEqual(by_check["markdown-format"]["status"], "fail")
        self.assertEqual(by_check["markdown-format"]["file"], "repo/doc.md")
        self.assertEqual(by_check["markdown-lint"]["status"], "fail")
        self.assertEqual(by_check["markdown-lint"]["file"], "repo/doc.md")
        self.assertEqual(by_check["markdown-lint"]["line"], 12)
        self.assertIn("MD013", by_check["markdown-lint"]["message"])

    def test_clean_run_emits_nothing(self) -> None:
        self.configure()
        self.doc("doc.md")
        self.stub("dprint", "", 0)
        self.stub("rumdl", "Success: No issues found in 1 file\n", 0)

        findings, code = self.run_lint([self.repo])

        self.assertEqual(code, 0)
        self.assertEqual(findings, [])

    def test_repo_without_configs_is_out_of_scope(self) -> None:
        self.doc("doc.md")
        self.stub("dprint", "boom\n", 20)
        self.stub("rumdl", "doc.md:1:1: [MD013] nope\n", 1)

        findings, code = self.run_lint([self.repo])

        self.assertEqual(code, 0)
        self.assertEqual(findings, [])

    def test_one_config_runs_only_that_tool(self) -> None:
        self.configure(dprint=True, rumdl=False)
        doc = self.doc("doc.md")
        self.stub("dprint", f"{doc}\n", 20)
        self.stub("rumdl", "doc.md:1:1: [MD013] nope\n", 1)

        findings, _ = self.run_lint([self.repo])

        self.assertEqual([f["check"] for f in findings], ["markdown-format"])

    def test_missing_binaries_warn_once_per_repo(self) -> None:
        self.configure()
        self.doc("doc.md")

        findings, code = self.run_lint([self.repo], with_stubs=False)

        self.assertEqual(code, 0)
        self.assertEqual({f["status"] for f in findings}, {"warn"})
        self.assertEqual(sorted(f["check"] for f in findings), ["markdown-format", "markdown-lint"])
        self.assertIn("not on PATH", findings[0]["message"])

    def test_changed_scope_reports_only_selected_files(self) -> None:
        self.configure()
        selected = self.doc("selected.md")
        other = self.doc("other.md")
        self.stub("dprint", f"{selected}\n{other}\n", 20)
        self.stub(
            "rumdl",
            "selected.md:3:1: [MD040] Code block (```) missing language\nother.md:9:1: [MD040] Code block (```) missing language\n",
            1,
        )

        findings, _ = self.run_lint([selected])

        self.assertEqual({f["file"] for f in findings}, {"repo/selected.md"})

    def test_changed_scope_with_no_selected_violation_is_silent(self) -> None:
        self.configure()
        selected = self.doc("selected.md")
        other = self.doc("other.md")
        self.stub("dprint", f"{other}\n", 20)
        self.stub("rumdl", "other.md:9:1: [MD040] Code block (```) missing language\n", 1)

        findings, _ = self.run_lint([selected])

        self.assertEqual(findings, [])

    def test_tool_error_naming_no_file_is_one_fail(self) -> None:
        self.configure()
        self.doc("doc.md")
        self.stub("dprint", "Error: Had 1 config diagnostic(s) in dprint.json\n", 12)
        self.stub("rumdl", "Error: invalid rule name in .rumdl.toml\n", 2)

        findings, code = self.run_lint([self.repo])

        self.assertEqual(code, 0)
        self.assertEqual(len(findings), 2)
        self.assertEqual({f["status"] for f in findings}, {"fail"})
        self.assertIn("failed in repo", findings[0]["message"])
        self.assertNotIn("file", findings[0])

    def test_file_outside_any_governed_repo_is_ignored(self) -> None:
        loose = self.workspace / "loose.md"
        loose.write_text("# loose\n")
        self.stub("dprint", f"{loose}\n", 20)
        self.stub("rumdl", "loose.md:1:1: [MD013] nope\n", 1)

        findings, _ = self.run_lint([loose])

        self.assertEqual(findings, [])


if __name__ == "__main__":
    unittest.main()
