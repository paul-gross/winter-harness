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
import lint_link_anchors as anchors
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
                ".winter/ext/codeberg/context/issue-format.md",
                "projects/winter-cli/README.md",
                "../winter-product/context/todos.md",
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
        self.assertIsNotNone(self.lint.classify_span("winter-product/context/todos.md"))

    def test_multi_level_sibling_is_flagged(self) -> None:
        self.assertIsNotNone(self.lint.classify_span("../../winter-product/context/todos.md"))


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
        lint = self._make_lint(allow=["context/orphan.md"])
        orphans = lint._orphan_findings(self.files, self.root, self.root)
        self.assertEqual(orphans, [])

    def test_orphan_severity_off(self) -> None:
        lint = self._make_lint(orphan_severity="off")
        self.assertEqual(lint._orphan_findings(self.files, self.root, self.root), [])


class DocReferencesSkillsTest(unittest.TestCase):
    """Skills (`SKILL.md`) are reachability entrypoints alongside routing tables."""

    def setUp(self) -> None:
        self.root = FIXTURES / "doc_references_skills"
        self.scanner = dl.MarkdownScanner()
        self.files = self.scanner.collect_markdown([self.root])

    def _make_lint(self) -> docs.DocReferenceLint:
        return docs.DocReferenceLint(self.scanner, "warn", [])

    def test_skill_relative_link_not_orphaned(self) -> None:
        # context/via-relative.md is linked only from SKILL.md via a relative path —
        # it must not be reported as an orphan.
        lint = self._make_lint()
        orphans = lint._orphan_findings(self.files, self.root, self.root)
        messages = " ".join(f.message for f in orphans)
        self.assertNotIn("via-relative.md", messages)

    def test_skill_pathnotation_link_not_orphaned(self) -> None:
        # context/via-pathnotation.md is linked only from SKILL.md via
        # `workspace:/context/via-pathnotation.md` path-notation — it must not be
        # reported as an orphan.
        lint = self._make_lint()
        orphans = lint._orphan_findings(self.files, self.root, self.root)
        messages = " ".join(f.message for f in orphans)
        self.assertNotIn("via-pathnotation.md", messages)

    def test_unreachable_doc_still_orphaned(self) -> None:
        # context/skill-orphan.md is linked from neither a routing table nor any
        # skill — it must still be reported as an orphan.
        lint = self._make_lint()
        orphans = lint._orphan_findings(self.files, self.root, self.root)
        messages = " ".join(f.message for f in orphans)
        self.assertIn("skill-orphan.md", messages)


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


class LinkAnchorSlugTest(unittest.TestCase):
    """Unit tests for the GitHub-style slug helper."""

    def test_basic_heading(self) -> None:
        self.assertEqual(anchors._compute_slug("Hello World"), "hello-world")

    def test_punctuation_stripped(self) -> None:
        self.assertEqual(anchors._compute_slug("Type (Scope): Description"), "type-scope-description")

    def test_backtick_spans_inlined(self) -> None:
        self.assertEqual(anchors._compute_slug("With `Code` Span"), "with-code-span")

    def test_multi_space_produces_multiple_hyphens(self) -> None:
        # GitHub slugger replaces each space individually — two spaces → two hyphens.
        self.assertEqual(anchors._compute_slug("Hello,  World"), "hello--world")

    def test_leading_emoji_keeps_leading_hyphen(self) -> None:
        # The emoji is stripped (non-word), leaving a leading space → leading hyphen.
        # GitHub does not strip leading/trailing hyphens from the result.
        self.assertEqual(anchors._compute_slug("🎉 Celebrate"), "-celebrate")

    def test_duplicate_disambiguation(self) -> None:
        target = FIXTURES / "link_anchors" / "target.md"
        slugs = anchors.file_heading_slugs(target)
        self.assertIn("alpha", slugs)
        self.assertIn("beta", slugs)
        self.assertIn("beta-1", slugs)
        self.assertIn("with-code-span", slugs)

    def test_fenced_headings_not_counted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "fenced.md"
            f.write_text("```\n# Not A Heading\n```\n\n# Real Heading\n")
            slugs = anchors.file_heading_slugs(f)
            self.assertIn("real-heading", slugs)
            self.assertNotIn("not-a-heading", slugs)


class LinkAnchorLintFixtureTest(unittest.TestCase):
    """Tests against the link_anchors fixture directory."""

    def setUp(self) -> None:
        self.root = FIXTURES / "link_anchors"
        self.scanner = dl.MarkdownScanner()
        self.lint = anchors.LinkAnchorLint(self.scanner)

    def test_target_file_has_expected_slugs(self) -> None:
        target = self.root / "target.md"
        slugs = anchors.file_heading_slugs(target)
        self.assertIn("alpha", slugs)
        self.assertIn("beta", slugs)

    def test_dangling_same_file_anchor_is_flagged(self) -> None:
        check = self.root / "check.md"
        findings = self.lint.check([check], self.root)
        messages = [f.message for f in findings]
        # #nonexistent-heading is in check.md which has no such slug
        self.assertTrue(any("nonexistent-heading" in m for m in messages))

    def test_dangling_other_file_anchor_is_flagged(self) -> None:
        check = self.root / "check.md"
        findings = self.lint.check([check], self.root)
        messages = [f.message for f in findings]
        self.assertTrue(any("nonexistent" in m for m in messages))

    def test_dead_file_target_is_flagged(self) -> None:
        check = self.root / "check.md"
        findings = self.lint.check([check], self.root)
        messages = [f.message for f in findings]
        self.assertTrue(any("nonexistent.md" in m for m in messages))

    def test_valid_links_produce_no_findings(self) -> None:
        check = self.root / "check.md"
        findings = self.lint.check([check], self.root)
        for f in findings:
            # Valid anchors (alpha, beta-1, with-code-span) must not be flagged
            self.assertNotIn("#alpha", f.message)
            self.assertNotIn("#beta-1", f.message)
            self.assertNotIn("#with-code-span", f.message)
            self.assertNotIn("#check-fixture", f.message)

    def test_example_marked_line_is_skipped(self) -> None:
        check = self.root / "check.md"
        findings = self.lint.check([check], self.root)
        # The bad-anchor link is example-marked and must not produce a finding
        self.assertFalse(any("bad-anchor" in f.message for f in findings))

    def test_all_findings_are_fail(self) -> None:
        check = self.root / "check.md"
        findings = self.lint.check([check], self.root)
        self.assertTrue(findings)
        self.assertTrue(all(f.status == "fail" for f in findings))

    def test_exact_finding_count(self) -> None:
        # Expect exactly three failures: same-file dangling, other-file dangling,
        # and the dead relative link.
        check = self.root / "check.md"
        findings = self.lint.check([check], self.root)
        self.assertEqual(len(findings), 3)


class LinkAnchorCrossRepoTest(unittest.TestCase):
    """Tests for cross-repo `winter-<name>:/` and `workspace:/` anchor resolution."""

    def _make_lint(self, ws: Path) -> anchors.LinkAnchorLint:
        return anchors.LinkAnchorLint(dl.MarkdownScanner(), workspace_dir=ws)

    def test_cross_repo_valid_anchor(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            ext = ws / ".winter" / "ext" / "foo"
            ext.mkdir(parents=True)
            (ext / "topic.md").write_text("# Real Heading\n\nContent.\n")
            src = ws / "myrepo"
            src.mkdir()
            doc = src / "doc.md"
            doc.write_text("[link](winter-foo:/topic.md#real-heading)\n")
            findings = self._make_lint(ws).check([doc], ws)
            self.assertEqual(findings, [])

    def test_cross_repo_dangling_anchor(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            ext = ws / ".winter" / "ext" / "foo"
            ext.mkdir(parents=True)
            (ext / "topic.md").write_text("# Real Heading\n\nContent.\n")
            src = ws / "myrepo"
            src.mkdir()
            doc = src / "doc.md"
            doc.write_text("[link](winter-foo:/topic.md#nope)\n")
            findings = self._make_lint(ws).check([doc], ws)
            self.assertEqual(len(findings), 1)
            self.assertIn("nope", findings[0].message)

    def test_cross_repo_workspace_prefix(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            (ws / "context").mkdir()
            (ws / "context" / "guide.md").write_text("# Guide Heading\n")
            src = ws / "myrepo"
            src.mkdir()
            doc = src / "doc.md"
            doc.write_text("[link](workspace:/context/guide.md#guide-heading)\n")
            findings = self._make_lint(ws).check([doc], ws)
            self.assertEqual(findings, [])

    def test_cross_repo_unknown_context_skipped_without_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            doc = Path(tmp) / "doc.md"
            doc.write_text("[link](winter-foo:/topic.md#heading)\n")
            lint = anchors.LinkAnchorLint(dl.MarkdownScanner(), workspace_dir=None)
            findings = lint.check([doc], Path(tmp))
            self.assertEqual(findings, [])


class RawLinkTargetsTest(unittest.TestCase):
    """Tests for the new MarkdownScanner.raw_link_targets method."""

    def setUp(self) -> None:
        self.scanner = dl.MarkdownScanner()

    def test_preserves_fragment(self) -> None:
        targets = self.scanner.raw_link_targets("[text](path/to/file.md#heading)")
        self.assertEqual(targets, ["path/to/file.md#heading"])

    def test_same_file_anchor(self) -> None:
        targets = self.scanner.raw_link_targets("[text](#anchor)")
        self.assertEqual(targets, ["#anchor"])

    def test_no_fragment_unchanged(self) -> None:
        targets = self.scanner.raw_link_targets("[text](path/to/file.md)")
        self.assertEqual(targets, ["path/to/file.md"])

    def test_title_stripped_fragment_kept(self) -> None:
        targets = self.scanner.raw_link_targets('[text](path#frag "Title")')
        self.assertEqual(targets, ["path#frag"])

    def test_angle_bracket_form(self) -> None:
        targets = self.scanner.raw_link_targets("[text](<path#frag>)")
        self.assertEqual(targets, ["path#frag"])


if __name__ == "__main__":
    unittest.main()
