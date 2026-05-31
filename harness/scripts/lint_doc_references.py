#!/usr/bin/env python3
"""Reference-integrity lint for agent-facing markdown.

The routing tables in `workspace:/CLAUDE.md` and every `index.md` are how an
agent navigates the docs via progressive disclosure. Two failure modes silently
degrade that:

1. **Broken links.** A relative markdown link whose target no longer exists is
   a dead end — `fail`.
2. **Orphans.** An `ai/**/*.md` file that exists but is unreachable from any
   routing table (no index/README/CLAUDE.md link chain leads to it) is content
   an agent will never be routed to — `warn` (raise or silence per consumer).

Reachability and orphan detection are whole-repo properties, so this lint always
operates over the full repo (the `--repo` root), not a changed-file subset.

Link targets that carry a scheme or a path-notation prefix (`https:`,
`mailto:`, `workspace:/…`, `winter-<name>:/…`) are skipped here — a single-repo
lint can't resolve a cross-context reference, and the extractability lint
already validates `<context>:/…` targets against the dependency graph.

This is a `winter lint` check following the standard script contract: NDJSON
findings on stdout, exit 0. It is also runnable standalone:

    python3 lint_doc_references.py --repo /path/to/checkout
    python3 lint_doc_references.py --repo /path/to/checkout --allow 'ai/scratch/*'
"""

from __future__ import annotations

import fnmatch
import re
import sys
from collections import deque
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _doclint as dl  # noqa: E402

CHECK = "doc-references"

# Files that anchor the routing graph — reachability BFS starts from these.
SEED_NAMES = frozenset({"index.md", "CLAUDE.md", "CLAUDE.winter.md", "README.md"})

# Routing files whose outbound links are checked for breakage. Scoped to the
# routing tables (per the issue): a broken link in a navigation table strands an
# agent mid-disclosure. Links in body docs (skills, agents) often use a
# workspace-root-relative convention this single-repo lint can't model, so they
# are out of scope here.
LINK_CHECK_NAMES = frozenset({"index.md", "CLAUDE.md", "CLAUDE.winter.md"})

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
    ) -> None:
        self._scanner = scanner
        self._orphan_severity = orphan_severity
        self._allow = allow

    def check(self, repo_root: Path, base: Path) -> list[dl.Finding]:
        files = self._scanner.collect_markdown([repo_root])
        findings = self._broken_link_findings(files, base)
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

    def _reachable_md(self, files: list[Path], repo_root: Path) -> set[Path]:
        """Resolved `.md` paths reachable from the routing seeds by link-following."""
        by_path = {f.resolve(): f for f in files}
        root = repo_root.resolve()
        visited: set[Path] = set()
        queue: deque[Path] = deque()
        for resolved, _ in by_path.items():
            if resolved.name in SEED_NAMES:
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
        return visited

    def _under_ai_dir(self, file: Path, repo_root: Path) -> bool:
        try:
            rel = file.resolve().relative_to(repo_root.resolve())
        except ValueError:
            return False
        return "ai" in rel.parts[:-1]

    def _orphan_findings(self, files: list[Path], repo_root: Path, base: Path) -> list[dl.Finding]:
        if self._orphan_severity == "off":
            return []
        visited = self._reachable_md(files, repo_root)
        findings: list[dl.Finding] = []
        for file in files:
            if not self._under_ai_dir(file, repo_root):
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
                    message=f"orphaned doc — `{repo_rel}` exists but no routing table links to it",
                    file=rel,
                    remediation="Link it from an index/routing table (a `index.md`, `README.md`, or "
                    "`CLAUDE.md`), or allow-list it with `--allow` if it is intentionally unrouted.",
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
    repo_root, _ = cli.parse_repo_arg(rest)

    scanner = dl.MarkdownScanner()
    lint = DocReferenceLint(scanner, orphan_severity, allow)
    reporter = dl.NdjsonReporter()
    return reporter.emit(lint.check(repo_root, cli.base_dir(repo_root)))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
