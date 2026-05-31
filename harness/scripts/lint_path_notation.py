#!/usr/bin/env python3
"""Path-notation lint for agent-facing markdown.

`workspace:/CLAUDE.md` and `winter-harness:/harness/winter-references.md` define
the canonical way to address a file in another repo or context: a
`<context>:/path` prefix (`workspace:/…`, `winter-<name>:/…`, `alpha:/…`). A
*raw* cross-context path — `.winter/ext/github/ai/issue-format.md`,
`projects/winter-cli/README.md`, `../winter-product/ai/todos.md` — is a dead
pointer the moment an extension is renamed or its on-disk install path changes.

This lint flags raw cross-context paths that should carry a prefix. It is
deliberately conservative: path notation has fuzzy edges, so it fires only on
patterns that *unambiguously* cross a context boundary, and only inside inline
code spans (where file references live in these docs). A repo's own files
referred to with bare relative paths (`./python/error-handling.md`,
`tools/winter-cli/pyproject.toml`) are legitimate and never flagged. Findings
are `warn` by default — raise to `fail` per consumer with `--severity fail`.

Scope: inline code spans in every in-scope `*.md`, skipping fenced code blocks
(sample commands, where a raw path is correct) and any line carrying the
`<!-- winter-lint:example -->` marker (a reference that only illustrates a path,
not one that must resolve).

This is a `winter lint` check following the standard script contract: NDJSON
findings on stdout, exit 0. It is also runnable standalone:

    python3 lint_path_notation.py --repo /path/to/checkout
    python3 lint_path_notation.py path/to/file.md ...
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _doclint as dl  # noqa: E402

CHECK = "path-notation"

# Each pattern marks a substring that unambiguously names something *outside the
# current repo* and so should be written in canonical notation. The shared
# lookbehind keeps matches on a token boundary, so `my-projects/` and
# `apphttps://` don't trip the `projects/` and bare-name forms. Every pattern
# requires a `/` after the name, so a filename like `winter-ext.toml` (a `.`
# follows) never matches.
_BOUNDARY = r"(?<![A-Za-z0-9_./-])"
_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (
        re.compile(_BOUNDARY + r"\.winter/ext/[a-z0-9-]+/"),
        "raw extension-install path — install location varies per workspace",
    ),
    (
        re.compile(_BOUNDARY + r"projects/[a-z0-9][\w-]*/"),
        "raw source-checkout path — `projects/` is a workspace-internal layout detail",
    ),
    (
        re.compile(_BOUNDARY + r"(?:\.\./)+winter-[a-z0-9-]+/"),
        "sibling-relative path crossing a repo boundary",
    ),
    (
        re.compile(_BOUNDARY + r"/(?:home|Users|root)/"),
        "machine-absolute path",
    ),
)

# A bare `winter-<name>/` path names another repo without a prefix — checked
# last so the more specific patterns above win, and gated on a denylist of
# `winter-*` tokens that are *not* standalone repos: the git-exclude sentinel
# (`# >>> winter-dir/<name>`), the manifest stem (`winter-ext.toml`), and the
# in-`winter` tool directory (`tools/winter-lint/`).
_BARE_REPO_RE = re.compile(_BOUNDARY + r"winter-([a-z0-9-]+)/")
_NON_REPO = frozenset({"winter-dir", "winter-ext", "winter-lint"})

# A span that begins with canonical notation — `<context>:/…` — is already
# correctly addressed, even if it later contains a `.winter/ext/…` segment.
_CANONICAL_RE = re.compile(r"^[a-z][a-z0-9-]*:/")


class PathNotationLint:
    """Checks markdown files for raw cross-context paths that need a prefix.

    Constructor injection: `scanner` provides file collection and line parsing;
    `severity` is the finding level (`warn` or `fail`).
    """

    def __init__(self, scanner: dl.MarkdownScanner, severity: str) -> None:
        self._scanner = scanner
        self._severity = severity

    def check(self, paths: list[Path], base: Path) -> list[dl.Finding]:
        findings: list[dl.Finding] = []
        for file in self._scanner.collect_markdown(paths):
            lines = self._scanner.read_lines(file)
            if lines is None:
                continue
            for lineno, line in self._scanner.iter_content_lines("\n".join(lines)):
                if self._scanner.has_example_marker(line):
                    continue
                for span in self._scanner.code_spans(line):
                    reason = self.classify_span(span)
                    if reason is not None:
                        findings.append(
                            dl.Finding(
                                check=CHECK,
                                status=self._severity,
                                message=f"`{span}` is a raw path — {reason}",
                                file=self._scanner.relpath(file, base),
                                line=lineno,
                                remediation="Use canonical path notation: `workspace:/…`, `winter-<name>:/…`, "
                                "or a `<env>:/…` prefix. If the path only illustrates notation, mark the line "
                                "`<!-- winter-lint:example -->`.",
                            )
                        )
        return findings

    def classify_span(self, span: str) -> str | None:
        """Return a reason if the span holds a raw cross-context path, else None."""
        s = span.strip()
        if _CANONICAL_RE.match(s):
            return None
        for pattern, reason in _PATTERNS:
            if pattern.search(s):
                return reason
        m = _BARE_REPO_RE.search(s)
        if m and f"winter-{m.group(1)}" not in _NON_REPO:
            return "bare repo-name path — names another repo without a context prefix"
        return None


def main(argv: list[str]) -> int:
    severity = "warn"
    rest: list[str] = []
    i = 0
    while i < len(argv):
        if argv[i] == "--severity":
            if i + 1 >= len(argv) or argv[i + 1] not in {"warn", "fail"}:
                sys.stderr.write("--severity requires warn|fail\n")
                return 2
            severity = argv[i + 1]
            i += 2
            continue
        rest.append(argv[i])
        i += 1

    cli = dl.LintCli()
    repo_root, paths_args = cli.parse_repo_arg(rest)
    scope = cli.resolve_scope(paths_args, repo_root)

    scanner = dl.MarkdownScanner()
    lint = PathNotationLint(scanner, severity)
    reporter = dl.NdjsonReporter()
    return reporter.emit(lint.check(scope, cli.base_dir(repo_root)))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
