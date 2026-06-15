"""Tests for the agent-facing markdown lints.

Stdlib `unittest` only — no third-party dependency, so the whole `scripts/`
directory can be invoked from any consumer checkout intact. Run with:

    python3 -m unittest test_doclint
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import _doclint as dl
import lint_doc_references as docs
import lint_path_notation as paths

FIXTURES = Path(__file__).resolve().parent / "fixtures"


class PathNotationTest(unittest.TestCase):
    def setUp(self) -> None:
        root = FIXTURES / "path_notation"
        scanner = dl.MarkdownScanner()
        lint = paths.PathNotationLint(scanner, "warn")
        self.findings = lint.check([root], root)
        self.spans = [f.message.split("`")[1] for f in self.findings]

    def test_flags_every_raw_cross_context_path(self) -> None:
        self.assertCountEqual(
            self.spans,
            [
                ".winter/ext/codeberg/ai/issue-format.md",
                "projects/winter-cli/README.md",
                "../winter-product/ai/todos.md",
                "winter-service-tmux/index.md",
                "/home/alice/notes.md",
            ],
        )

    def test_leaves_legitimate_references_alone(self) -> None:
        joined = " ".join(self.spans)
        for ok in (
            "architecture/error-handling.md",
            "pyproject.toml",
            "workspace:/CLAUDE.md",
            "winter-harness:/harness/index.md",
            "foo/bar.md",  # the example-marked line
        ):
            self.assertNotIn(ok, joined)

    def test_default_severity_is_warn(self) -> None:
        self.assertTrue(all(f.status == "warn" for f in self.findings))

    def test_severity_is_configurable(self) -> None:
        root = FIXTURES / "path_notation"
        scanner = dl.MarkdownScanner()
        lint = paths.PathNotationLint(scanner, "fail")
        failing = lint.check([root], root)
        self.assertTrue(failing and all(f.status == "fail" for f in failing))


class ClassifySpanTest(unittest.TestCase):
    def setUp(self) -> None:
        self.lint = paths.PathNotationLint(dl.MarkdownScanner(), "warn")

    def test_canonical_prefix_exempts_nested_segments(self) -> None:
        # A canonical reference that happens to contain `.winter/ext/…` deeper in
        # the path is already addressed and must not be flagged.
        self.assertIsNone(self.lint.classify_span("workspace:/.winter/ext/harness/index.md"))

    def test_winter_ext_filename_is_not_a_repo_path(self) -> None:
        self.assertIsNone(self.lint.classify_span("winter-ext.toml"))

    def test_non_repo_winter_tokens_are_exempt(self) -> None:
        # The git-exclude sentinel and the in-`winter` tool dir are not repos.
        self.assertIsNone(self.lint.classify_span("# >>> winter-dir/<name>"))
        self.assertIsNone(self.lint.classify_span("winter-lint/extractability.py"))

    def test_bare_repo_name_is_flagged(self) -> None:
        self.assertIsNotNone(self.lint.classify_span("winter-product/ai/todos.md"))

    def test_multi_level_sibling_is_flagged(self) -> None:
        self.assertIsNotNone(self.lint.classify_span("../../winter-product/ai/todos.md"))


class DocReferencesTest(unittest.TestCase):
    def setUp(self) -> None:
        self.root = FIXTURES / "doc_references"
        self.scanner = dl.MarkdownScanner()
        self.files = self.scanner.collect_markdown([self.root])

    def _make_lint(self, orphan_severity: str = "warn", allow: list[str] | None = None) -> docs.DocReferenceLint:
        return docs.DocReferenceLint(self.scanner, orphan_severity, allow or [])

    def test_flags_broken_link_only(self) -> None:
        lint = self._make_lint()
        broken = lint._broken_link_findings(self.files, self.root)
        self.assertEqual(len(broken), 1)
        self.assertEqual(broken[0].status, "fail")
        self.assertIn("nope.md", broken[0].message)

    def test_flags_orphan_not_routed_doc(self) -> None:
        lint = self._make_lint()
        orphans = lint._orphan_findings(self.files, self.root, self.root)
        messages = " ".join(f.message for f in orphans)
        self.assertIn("orphan.md", messages)
        self.assertNotIn("linked.md", messages)
        self.assertTrue(all(f.status == "warn" for f in orphans))

    def test_reachability_is_multi_hop(self) -> None:
        # deep.md is reached only via linked.md (a non-seed doc), so it must be
        # reachable — orphan detection follows the full link chain, not one hop.
        lint = self._make_lint()
        orphans = lint._orphan_findings(self.files, self.root, self.root)
        self.assertNotIn("deep.md", " ".join(f.message for f in orphans))

    def test_orphan_allow_list_silences(self) -> None:
        lint = self._make_lint(allow=["ai/orphan.md"])
        orphans = lint._orphan_findings(self.files, self.root, self.root)
        self.assertEqual(orphans, [])

    def test_orphan_severity_off(self) -> None:
        lint = self._make_lint(orphan_severity="off")
        self.assertEqual(lint._orphan_findings(self.files, self.root, self.root), [])


class CollectMarkdownTest(unittest.TestCase):
    def test_prunes_nested_checkouts(self) -> None:
        # A subdirectory carrying its own `.git` (clone dir or worktree file) is
        # a separate repo and must not be walked into; the root is never pruned.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "own.md").write_text("# own")
            clone = root / "nested-clone"
            (clone / ".git").mkdir(parents=True)
            (clone / "buried.md").write_text("# buried")
            worktree = root / "nested-worktree"
            worktree.mkdir()
            (worktree / ".git").write_text("gitdir: /elsewhere")
            (worktree / "also-buried.md").write_text("# also buried")

            scanner = dl.MarkdownScanner()
            names = {p.name for p in scanner.collect_markdown([root])}
            self.assertIn("own.md", names)
            self.assertNotIn("buried.md", names)
            self.assertNotIn("also-buried.md", names)


class LintCliTest(unittest.TestCase):
    def test_repo_arg_overrides_env_default(self) -> None:
        cli = dl.LintCli(env={"WINTER_WORKSPACE_DIR": "/ws"})
        repo_root, rest = cli.parse_repo_arg(["--repo", "/elsewhere", "--severity", "fail"])
        self.assertEqual(repo_root, Path("/elsewhere"))
        self.assertEqual(rest, ["--severity", "fail"])

    def test_repo_arg_defaults_to_workspace_dir(self) -> None:
        cli = dl.LintCli(env={"WINTER_WORKSPACE_DIR": "/ws"})
        repo_root, _ = cli.parse_repo_arg([])
        self.assertEqual(repo_root, Path("/ws"))

    def test_scope_prefers_winter_lint_paths(self) -> None:
        cli = dl.LintCli(env={"WINTER_LINT_PATHS": "/a\n/b\n"})
        self.assertEqual(cli.resolve_scope([], Path("/ws")), [Path("/a"), Path("/b")])

    def test_scope_falls_back_to_argv_then_repo_root(self) -> None:
        cli = dl.LintCli(env={})
        self.assertEqual(cli.resolve_scope(["x.md"], Path("/ws")), [Path("x.md")])
        self.assertEqual(cli.resolve_scope([], Path("/ws")), [Path("/ws")])

    def test_base_dir_prefers_workspace_dir(self) -> None:
        self.assertEqual(dl.LintCli(env={"WINTER_WORKSPACE_DIR": "/ws"}).base_dir(Path("/repo")), Path("/ws"))
        self.assertEqual(dl.LintCli(env={}).base_dir(Path("/repo")), Path("/repo"))


if __name__ == "__main__":
    unittest.main()
