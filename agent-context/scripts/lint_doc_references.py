#!/usr/bin/env python3
"""Reference-integrity lint for agent-facing markdown.

The routing tables in `workspace:/CLAUDE.md` and repository indexes are how an
agent navigates the docs via progressive disclosure. Two failure modes silently
degrade that:

1. **Broken links.** A relative markdown link whose target no longer exists is
   a dead end — `fail`.
2. **Orphans.** A markdown file under a `context/` or `methodology/` root that
   exists but is unreachable from any routing table or skill (no
   AGENTS.md/AGENTS.winter.md/CLAUDE.md/index.md/README.md or SKILL.md link chain
   leads to it) is content an agent will never be routed to — `warn` (raise or
   silence per consumer).

Reachability and orphan detection are whole-repo properties. Standalone
`--repo` scans that root. Under `winter lint`, orphan detection scans each
selected repository directory root; a changed-file-only scope runs direct
broken-link checks but skips orphan detection rather than widening scope.

Link targets that carry a scheme or a path-notation prefix (`https:`,
`mailto:`, `workspace:/…`, `winter-<name>:/…`) are skipped for broken-link
checking — a single-repo lint can't resolve cross-context references.  For
orphan reachability, path-notation targets in `SKILL.md` files are resolved
against `repo_root` so that docs linked from a skill are not falsely orphaned.

This is a `winter lint` check following the standard script contract: NDJSON
findings on stdout, exit 0. It is also runnable standalone:

    python3 lint_doc_references.py --repo /path/to/checkout
    python3 lint_doc_references.py --repo /path/to/checkout --allow 'context/scratch/*'
"""

from __future__ import annotations

import fnmatch
import re
import sys
import tomllib
from collections import deque
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _doclint as dl  # noqa: E402

CHECK = "doc-references"

# Root files that anchor the repository routing graph. A nested index or README
# is reached through that graph; its filename alone does not make it an entrypoint.
SEED_NAMES = frozenset({"index.md", "AGENTS.md", "AGENTS.winter.md", "CLAUDE.md", "README.md"})

# Skills are a second class of reachability entrypoint: the BFS also seeds from
# any SKILL.md found in the repo and follows their outbound links transitively.
SKILL_NAME = "SKILL.md"

# Agent-facing roots whose markdown must be reachable through progressive
# disclosure. A component may own either root or both.
ROUTED_DOC_ROOTS = frozenset({"context", "methodology"})

# Routing files whose outbound links are checked for breakage. Scoped to the
# routing tables (per the issue): a broken link in a navigation table strands an
# agent mid-disclosure. Links in body docs (skills, agents) often use a
# workspace-root-relative convention this single-repo lint can't model, so they
# are out of scope here.
LINK_CHECK_NAMES = frozenset({"index.md", "AGENTS.md", "AGENTS.winter.md", "CLAUDE.md"})

# Captures a path-notation identity and path, such as
# `winter-harness:/architecture/index.md`.
_PATHNOTATION_RE = re.compile(r"^([a-z][a-z0-9+.-]*):/(.+)$")

# A target with a scheme or path-notation prefix: `https:`, `mailto:`,
# `workspace:/…`, `winter-harness:/…`. Not resolvable in a single-repo lint.
_PREFIXED_RE = re.compile(r"^[a-z][a-z0-9+.-]*:")


class DocReferenceLint:
    """Checks routing-table integrity: broken links and orphaned docs.

    Constructor injection: `scanner` provides file collection and line parsing;
    `orphan_severity` is the finding level for orphans (`warn`, `fail`, or
    `off`); `allow` is a list of repo-relative glob patterns that exempt files
    from orphan detection.
    """

    def __init__(
        self,
        scanner: dl.MarkdownScanner,
        orphan_severity: str,
        allow: list[str],
        workspace_root: Path | None = None,
    ) -> None:
        self._scanner = scanner
        self._orphan_severity = orphan_severity
        self._allow = allow
        self._workspace_root = workspace_root

    def check(self, repo_root: Path, base: Path) -> list[dl.Finding]:
        files = self._scanner.collect_markdown([repo_root])
        findings = self._broken_link_findings(files, base)
        findings += self._orphan_findings(files, repo_root, base)
        return findings

    def check_scope(
        self,
        paths: list[Path],
        repository_roots: list[Path],
        base: Path,
    ) -> list[dl.Finding]:
        """Check direct references in scope and reachability for selected repos."""
        findings = self._broken_link_findings(self._scanner.collect_markdown(paths), base)
        for repo_root in repository_roots:
            files = self._scanner.collect_markdown([repo_root])
            findings += self._orphan_findings(files, repo_root, base)
        return findings

    def _is_local_relative(self, target: str) -> bool:
        """True for a link this lint should resolve on the local filesystem."""
        if not target or target.startswith("#"):
            return False
        if set(target) <= {".", "…"}:  # `…` / `...` ellipsis placeholder, not a path
            return False
        if target.startswith("/"):  # root-relative — ambiguous, out of scope
            return False
        if _PREFIXED_RE.match(target):  # scheme or path-notation prefix
            return False
        return True

    def _resolve(self, target: str, from_file: Path) -> Path:
        return (from_file.parent / target).resolve()

    def _local_link_targets(self, file: Path) -> list[str]:
        """Relative link and `@import` targets — the edges reachability follows."""
        lines = self._scanner.read_lines(file)
        if lines is None:
            return []
        out: list[str] = []
        for _, line in self._scanner.iter_content_lines("\n".join(lines)):
            for target in self._scanner.link_targets(line) + self._scanner.import_targets(line):
                if self._is_local_relative(target):
                    out.append(target)
        return out

    def _skill_pathnotation_targets(self, file: Path, repo_root: Path) -> list[Path]:
        """Repo-local paths referenced via path-notation in a skill file.

        Only identities that can denote this root are followed: its extension
        name from `winter-ext.toml`, `local`, and `workspace` when this root is
        itself the workspace (or no external workspace is configured). Arbitrary
        extension prefixes must not make same-named local files reachable.
        """
        lines = self._scanner.read_lines(file)
        if lines is None:
            return []
        root = repo_root.resolve()
        local_identities = self._local_pathnotation_identities(root)
        out: list[Path] = []
        seen: set[Path] = set()
        for _, line in self._scanner.iter_content_lines("\n".join(lines)):
            candidates = (
                self._scanner.link_targets(line)
                + self._scanner.import_targets(line)
                + self._scanner.code_spans(line)
            )
            for target in candidates:
                file_target = target.split("#", 1)[0]
                m = _PATHNOTATION_RE.match(file_target)
                if not m or m.group(1) not in local_identities:
                    continue
                candidate = (root / m.group(2)).resolve()
                try:
                    candidate.relative_to(root)
                except ValueError:
                    continue  # resolves outside the repo — skip
                if candidate.suffix == ".md" and candidate.exists() and candidate not in seen:
                    seen.add(candidate)
                    out.append(candidate)
        return out

    def _local_pathnotation_identities(self, repo_root: Path) -> set[str]:
        identities = {"local"}
        if self._workspace_root is None or repo_root == self._workspace_root.resolve():
            identities.add("workspace")
        manifest = repo_root / "winter-ext.toml"
        try:
            name = tomllib.loads(manifest.read_text()).get("name")
        except (OSError, tomllib.TOMLDecodeError):
            name = None
        if isinstance(name, str) and name:
            identities.add(name)
        return identities

    def _broken_link_findings(self, files: list[Path], base: Path) -> list[dl.Finding]:
        findings: list[dl.Finding] = []
        for file in files:
            if file.name not in LINK_CHECK_NAMES:
                continue
            lines = self._scanner.read_lines(file)
            if lines is None:
                continue
            for lineno, line in self._scanner.iter_content_lines("\n".join(lines)):
                if self._scanner.has_example_marker(line):
                    continue
                for target in self._scanner.link_targets(line):
                    if not self._is_local_relative(target):
                        continue
                    resolved = self._resolve(target, file)
                    if not resolved.exists():
                        findings.append(
                            dl.Finding(
                                check=CHECK,
                                status="fail",
                                message=f"broken link `{target}` — target does not exist",
                                file=self._scanner.relpath(file, base),
                                line=lineno,
                                remediation="Fix the path, or remove the link if the target is gone.",
                            )
                        )
        return findings

    def _reachable_markdown(self, files: list[Path], repo_root: Path) -> set[Path]:
        """Resolved `.md` paths reachable from the routing seeds by link-following.

        Seeds from both routing-table files (`SEED_NAMES`) and skill entrypoints
        (`SKILL_NAME`).  Skill files additionally contribute path-notation targets
        (e.g. `workspace:/context/foo.md`) resolved against `repo_root`.
        """
        by_path = {f.resolve(): f for f in files}
        root = repo_root.resolve()
        visited: set[Path] = set()
        queue: deque[Path] = deque()
        for resolved, _ in by_path.items():
            is_root_seed = resolved.parent == root and resolved.name in SEED_NAMES
            if is_root_seed or resolved.name == SKILL_NAME:
                visited.add(resolved)
                queue.append(resolved)
        while queue:
            current = queue.popleft()
            for target in self._local_link_targets(current):
                resolved = self._resolve(target, current)
                if resolved.suffix != ".md" or resolved in visited:
                    continue
                try:
                    resolved.relative_to(root)
                except ValueError:
                    continue  # link escaping the repo — not our orphan question
                if resolved.exists():
                    visited.add(resolved)
                    queue.append(resolved)
            if current.name == SKILL_NAME:
                for resolved in self._skill_pathnotation_targets(current, repo_root):
                    if resolved not in visited:
                        visited.add(resolved)
                        queue.append(resolved)
        return visited

    def _under_routed_doc_root(self, file: Path, repo_root: Path) -> bool:
        """Whether `file` is beneath a context or methodology root."""
        try:
            rel = file.resolve().relative_to(repo_root.resolve())
        except ValueError:
            return False
        return bool(ROUTED_DOC_ROOTS.intersection(rel.parts[:-1]))

    def _orphan_findings(self, files: list[Path], repo_root: Path, base: Path) -> list[dl.Finding]:
        if self._orphan_severity == "off":
            return []
        visited = self._reachable_markdown(files, repo_root)
        findings: list[dl.Finding] = []
        for file in files:
            if not self._under_routed_doc_root(file, repo_root):
                continue
            resolved = file.resolve()
            if resolved in visited:
                continue
            rel = self._scanner.relpath(file, base)
            repo_rel = self._scanner.relpath(file, repo_root)
            if any(fnmatch.fnmatch(repo_rel, pat) for pat in self._allow):
                continue
            findings.append(
                dl.Finding(
                    check=CHECK,
                    status=self._orphan_severity,
                    message=f"orphaned doc — `{repo_rel}` exists but no routing table or skill links to it",
                    file=rel,
                    remediation="Link it from an index/routing table (`index.md`, `README.md`, `AGENTS.md`, "
                    "`AGENTS.winter.md`, or `CLAUDE.md`) or from a `SKILL.md`, or allow-list it with `--allow` if it is intentionally unrouted.",
                )
            )
        return findings


def main(argv: list[str]) -> int:
    orphan_severity = "warn"
    allow: list[str] = []
    rest: list[str] = []
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == "--orphan-severity":
            if i + 1 >= len(argv) or argv[i + 1] not in {"warn", "fail", "off"}:
                sys.stderr.write("--orphan-severity requires warn|fail|off\n")
                return 2
            orphan_severity = argv[i + 1]
            i += 2
            continue
        if arg == "--allow":
            if i + 1 >= len(argv):
                sys.stderr.write("--allow requires a glob argument\n")
                return 2
            allow.append(argv[i + 1])
            i += 2
            continue
        rest.append(arg)
        i += 1

    cli = dl.LintCli()
    repo_root, paths_args = cli.parse_repo_arg(rest)
    scope = cli.resolve_scope(paths_args, repo_root)

    scanner = dl.MarkdownScanner()
    workspace_root = cli.base_dir(repo_root) if cli.has_contributed_scope() else None
    lint = DocReferenceLint(scanner, orphan_severity, allow, workspace_root)
    reporter = dl.NdjsonReporter()
    if cli.has_contributed_scope():
        roots = cli.selected_repository_roots(scope)
        findings = lint.check_scope(scope, roots, cli.base_dir(repo_root))
    else:
        findings = lint.check(repo_root, cli.base_dir(repo_root))
    return reporter.emit(findings)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
