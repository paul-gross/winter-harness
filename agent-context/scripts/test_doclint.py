"""Tests for the agent-facing markdown lints.

Stdlib `unittest` only — no third-party dependency, so the whole `scripts/`
directory can be invoked from any consumer checkout intact. Run with:

    python3 -m unittest test_doclint

The style lint's own suite is `test_markdown_style`; `python3 -m unittest
discover` runs both.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import _doclint as dl
import lint_doc_references as docs
import lint_link_anchors as anchors
import lint_path_notation as paths

FIXTURES = Path(__file__).resolve().parent / "fixtures"
DOC_REFERENCE_SCRIPT = Path(__file__).resolve().parent / "lint_doc_references.py"
LINK_ANCHOR_SCRIPT = Path(__file__).resolve().parent / "lint_link_anchors.py"


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
            "winter-context:/agent-context/index.md",
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
        self.assertIsNone(self.lint.classify_span("workspace:/.winter/ext/context/index.md"))

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
        self.assertIn("context/orphan.md", messages)
        self.assertNotIn("context/linked.md", messages)
        self.assertTrue(all(f.status == "warn" for f in orphans))

    def test_routed_methodology_not_orphaned(self) -> None:
        lint = self._make_lint()
        orphans = lint._orphan_findings(self.files, self.root, self.root)
        messages = " ".join(f.message for f in orphans)
        self.assertNotIn("methodology/index.md", messages)
        self.assertNotIn("methodology/routed.md", messages)

    def test_unrouted_methodology_is_orphaned(self) -> None:
        lint = self._make_lint()
        orphans = lint._orphan_findings(self.files, self.root, self.root)
        self.assertIn("methodology/orphan.md", " ".join(f.message for f in orphans))

    def test_detached_nested_routing_files_do_not_seed_themselves(self) -> None:
        lint = self._make_lint()
        orphans = lint._orphan_findings(self.files, self.root, self.root)
        messages = " ".join(f.message for f in orphans)
        for path in (
            "methodology/hidden/index.md",
            "methodology/hidden/README.md",
            "methodology/hidden/child.md",
        ):
            self.assertIn(path, messages)

    def test_reachability_is_multi_hop(self) -> None:
        # deep.md is reached only via linked.md (a non-seed doc), so it must be
        # reachable — orphan detection follows the full link chain, not one hop.
        lint = self._make_lint()
        orphans = lint._orphan_findings(self.files, self.root, self.root)
        self.assertNotIn("deep.md", " ".join(f.message for f in orphans))

    def test_orphan_allow_list_silences(self) -> None:
        lint = self._make_lint(
            allow=["context/orphan.md", "methodology/orphan.md", "methodology/hidden/*"]
        )
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


class SkillPathNotationIdentityTest(unittest.TestCase):
    def test_only_local_identities_are_resolved_and_fragments_are_stripped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "winter-ext.toml").write_text('name = "winter-current"\n')
            context = root / "context"
            context.mkdir()
            for name in ("extension.md", "workspace.md", "local.md", "other-only.md"):
                (context / name).write_text(f"# {name}\n")
            skill = root / "SKILL.md"
            skill.write_text(
                "`winter-current:/context/extension.md#section`\n"
                "`workspace:/context/workspace.md#section`\n"
                "`local:/context/local.md#section`\n"
                "`winter-other:/context/other-only.md#section`\n"
            )

            lint = docs.DocReferenceLint(dl.MarkdownScanner(), "warn", [])
            targets = {
                path.relative_to(root).as_posix()
                for path in lint._skill_pathnotation_targets(skill, root)
            }

            self.assertEqual(
                targets,
                {"context/extension.md", "context/workspace.md", "context/local.md"},
            )

    def test_workspace_identity_is_not_local_inside_a_selected_repo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            root = workspace / "alpha" / "winter-current"
            context = root / "context"
            context.mkdir(parents=True)
            (root / "winter-ext.toml").write_text('name = "winter-current"\n')
            (context / "extension.md").write_text("# Extension\n")
            (context / "workspace-only.md").write_text("# Workspace\n")
            skill = root / "SKILL.md"
            skill.write_text(
                "`winter-current:/context/extension.md`\n"
                "`workspace:/context/workspace-only.md`\n"
            )

            lint = docs.DocReferenceLint(
                dl.MarkdownScanner(), "warn", [], workspace_root=workspace
            )
            targets = {
                path.relative_to(root).as_posix()
                for path in lint._skill_pathnotation_targets(skill, root)
            }

            self.assertEqual(targets, {"context/extension.md"})


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


class ExemptLinesTest(unittest.TestCase):
    """The `<!-- winter-lint:example -->` marker exempts its block, not its line.

    A formatter owns where lines break, so a marker parked at the end of a
    wrapped paragraph has to cover the reference reflow pushed further up.
    """

    def setUp(self) -> None:
        self.scanner = dl.MarkdownScanner()

    def test_marker_covers_the_whole_paragraph_it_sits_in(self) -> None:
        text = "# Doc\n\nfirst\nsecond\nthird <!-- winter-lint:example -->\n"
        self.assertEqual(self.scanner.exempt_lines(text), {3, 4, 5})

    def test_unmarked_blocks_are_untouched(self) -> None:
        text = "marked <!-- winter-lint:example -->\n\nunmarked\n"
        self.assertEqual(self.scanner.exempt_lines(text), {1})

    def test_marker_alone_in_a_block_exempts_only_itself(self) -> None:
        # A formatter puts a blank line between a table and an adjacent comment,
        # which is exactly why a table's marker belongs inside a cell.
        text = "<!-- winter-lint:example -->\n\n| a | b |\n| - | - |\n"
        self.assertEqual(self.scanner.exempt_lines(text), {1})

    def test_marker_in_a_table_cell_exempts_the_table(self) -> None:
        text = "| a | b <!-- winter-lint:example --> |\n| - | - |\n"
        self.assertEqual(self.scanner.exempt_lines(text), {1, 2})

    def test_reflowed_reference_stays_exempt(self) -> None:
        body = "Do not write sibling-relative paths (`../winter-product/...`) when crossing a\nboundary. <!-- winter-lint:example -->\n"
        lint = paths.PathNotationLint(self.scanner, "warn")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "doc.md").write_text(body)
            self.assertEqual(lint.check([root], root), [])


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

    def test_empty_winter_lint_paths_does_not_fall_back_to_workspace(self) -> None:
        cli = dl.LintCli(env={"WINTER_LINT_PATHS": ""})
        self.assertEqual(cli.resolve_scope([], Path("/ws")), [])

    def test_scope_falls_back_to_argv_then_repo_root(self) -> None:
        cli = dl.LintCli(env={})
        self.assertEqual(cli.resolve_scope(["x.md"], Path("/ws")), [Path("x.md")])
        self.assertEqual(cli.resolve_scope([], Path("/ws")), [Path("/ws")])

    def test_base_dir_prefers_workspace_dir(self) -> None:
        self.assertEqual(dl.LintCli(env={"WINTER_WORKSPACE_DIR": "/ws"}).base_dir(Path("/repo")), Path("/ws"))
        self.assertEqual(dl.LintCli(env={}).base_dir(Path("/repo")), Path("/repo"))

    def test_selected_repository_roots_omit_files_and_non_repositories(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "repo"
            (repo / ".git").mkdir(parents=True)
            file = repo / "changed.md"
            file.write_text("# Changed\n")
            plain = root / "plain"
            plain.mkdir()

            roots = dl.LintCli(env={}).selected_repository_roots([file, plain, repo])

            self.assertEqual(roots, [repo.resolve()])


class DocReferenceSubprocessScopeTest(unittest.TestCase):
    def _run(self, workspace: Path, lint_paths: list[Path]) -> list[dict[str, object]]:
        env = os.environ.copy()
        env.update(
            {
                "WINTER_WORKSPACE_DIR": str(workspace),
                "WINTER_LINT_SCOPE": "changed" if all(p.is_file() for p in lint_paths) else "env",
                "WINTER_LINT_PATHS": "\n".join(str(path) for path in lint_paths),
            }
        )
        result = subprocess.run(
            [sys.executable, str(DOC_REFERENCE_SCRIPT)],
            cwd=workspace,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return [json.loads(line) for line in result.stdout.splitlines() if line]

    def test_each_selected_repo_root_is_checked_without_scanning_unrelated_repos(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            selected = workspace / "alpha" / "selected"
            also_selected = workspace / "alpha" / "also-selected"
            unrelated = workspace / "alpha" / "unrelated"
            for repo in (selected, also_selected, unrelated):
                (repo / ".git").mkdir(parents=True)
                (repo / "context").mkdir()
                (repo / "context" / "orphan.md").write_text("# Orphan\n")
            (selected / "index.md").write_text("# Selected\n")
            (also_selected / "index.md").write_text("# Also selected\n")
            (unrelated / "index.md").write_text("[broken](./missing.md)\n")

            findings = self._run(workspace, [selected, also_selected])
            files = {str(finding.get("file")) for finding in findings}

            self.assertEqual(
                files,
                {
                    "alpha/selected/context/orphan.md",
                    "alpha/also-selected/context/orphan.md",
                },
            )
            self.assertTrue(all("unrelated" not in str(finding) for finding in findings))

    def test_changed_file_scope_checks_direct_links_but_skips_whole_repo_orphans(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            repo = workspace / "alpha" / "selected"
            (repo / ".git").mkdir(parents=True)
            (repo / "context").mkdir()
            (repo / "context" / "orphan.md").write_text("# Orphan\n")
            changed = repo / "index.md"
            changed.write_text("[broken](./missing.md)\n")

            findings = self._run(workspace, [changed])

            self.assertEqual(len(findings), 1)
            self.assertIn("broken link", str(findings[0]["message"]))
            self.assertNotIn("orphaned doc", str(findings))


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

    def test_explicit_heading_id_is_the_anchor(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "explicit.md"
            f.write_text("## Capability registry {#capability-registry}\n")
            slugs = anchors.file_heading_slugs(f)
            self.assertEqual(slugs, {"capability-registry"})

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


class LinkAnchorSubprocessScopeTest(unittest.TestCase):
    def _run(
        self,
        repo: Path,
        workspace: Path | None = None,
    ) -> list[dict[str, object]]:
        env = os.environ.copy()
        for key in ("WINTER_WORKSPACE_DIR", "WINTER_LINT_PATHS", "WINTER_LINT_SCOPE"):
            env.pop(key, None)
        if workspace is not None:
            env.update(
                {
                    "WINTER_WORKSPACE_DIR": str(workspace),
                    "WINTER_LINT_PATHS": str(repo),
                    "WINTER_LINT_SCOPE": "env",
                }
            )
            command = [sys.executable, str(LINK_ANCHOR_SCRIPT)]
            cwd = workspace
        else:
            command = [sys.executable, str(LINK_ANCHOR_SCRIPT), "--repo", str(repo)]
            cwd = repo
        result = subprocess.run(
            command,
            cwd=cwd,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return [json.loads(line) for line in result.stdout.splitlines() if line]

    def test_selected_module_wins_dual_install_and_foreign_extension_stays_installed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            installed_workflow = workspace / ".winter" / "ext" / "workflow"
            installed_workflow.mkdir(parents=True)
            (installed_workflow / "topic.md").write_text("# Installed Heading\n")
            installed_canon = workspace / ".winter" / "ext" / "canon"
            installed_canon.mkdir(parents=True)
            (installed_canon / "rule.md").write_text("# Canon Heading\n")

            selected = workspace / "alpha" / "winter-workflow"
            (selected / ".git").mkdir(parents=True)
            (selected / "winter-ext.toml").write_text('name = "winter-workflow"\n')
            (selected / "topic.md").write_text("# Selected Heading\n")
            (selected / "index.md").write_text(
                "[selected](winter-workflow:/topic.md#selected-heading)\n"
                "[stale-only](winter-workflow:/topic.md#installed-heading)\n"
                "[foreign](winter-canon:/rule.md#canon-heading)\n"
            )

            findings = self._run(selected, workspace)

            self.assertEqual(len(findings), 1)
            self.assertIn("installed-heading", str(findings[0]["message"]))

    def test_standalone_repo_resolves_its_own_canonical_identity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "winter-workflow"
            (repo / ".git").mkdir(parents=True)
            (repo / "winter-ext.toml").write_text('name = "winter-workflow"\n')
            (repo / "topic.md").write_text("# Selected Heading\n")
            (repo / "index.md").write_text(
                "[valid](winter-workflow:/topic.md#selected-heading)\n"
                "[invalid](winter-workflow:/topic.md#missing-heading)\n"
            )

            findings = self._run(repo)

            self.assertEqual(len(findings), 1)
            self.assertIn("missing-heading", str(findings[0]["message"]))


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
