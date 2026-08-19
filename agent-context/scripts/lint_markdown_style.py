#!/usr/bin/env python3
"""Mechanical markdown-style lint — the `dprint` / `rumdl` gates as `winter lint` findings.

The sibling lints in this directory check what a reference *means*: whether a
path is canonically addressed, whether a routing link resolves, whether an
anchor exists. None of them says anything about shape — line width, list
markers, emphasis style, table alignment, fence languages, heading spacing.
Two external tools own that layer, and this check runs them:

  - `dprint check` (config `dprint.json`) — the formatter. One canonical
    rendering per file, so a diff carries content changes and nothing else.
  - `rumdl check` (config `.rumdl.toml`) — the structural markdown linter.
    The rules a formatter cannot fix, like a fence missing its language.

**The config files are the opt-in.** A repo joins the gate by committing
`dprint.json` and `.rumdl.toml`; a repo carrying neither is silently out of
scope, so this check ships from winter-harness and travels to any consumer
without forcing the style on repos that have not adopted it. Each tool runs
only where its own config is present — a repo may adopt one without the other.

A missing tool binary degrades to one `warn` per repo rather than a `fail`: a
machine without `dprint` or `rumdl` installed sees the gap named instead of the
whole lint run going red on an install problem.

Each tool always runs over its whole repo root rather than over the selected
files, because the tools own their own exclusion lists (`excludes` /
`exclude`) and only a root-level run honors them; a file-scoped run then
filters the findings down to the selected files. That keeps a `--changed` run
from reporting a deliberately-excluded fixture that happens to have changed.

This is a `winter lint` check following the standard script contract: NDJSON
findings on stdout, exit 0. It is also runnable standalone:

    python3 lint_markdown_style.py --repo /path/to/checkout
    python3 lint_markdown_style.py path/to/file.md ...
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _doclint as dl  # noqa: E402

FORMAT_CHECK = "markdown-format"
LINT_CHECK = "markdown-lint"

DPRINT_CONFIG = "dprint.json"
RUMDL_CONFIG = ".rumdl.toml"

# Both tools are told NO_COLOR, but a pager or CI wrapper can still leak escapes.
_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")

# rumdl's text format: `<path>:<line>:<col>: [MD013] <message>`, with a trailing
# ` [*]` on the rules its own `--fix` can resolve.
_RUMDL_RE = re.compile(r"^(?P<path>.+?):(?P<line>\d+):\d+: (?P<message>\[MD\d+\] .*?)(?: \[\*\])?$")

# Tools are fast (milliseconds on these repos); the ceiling only bounds a hang.
_TIMEOUT_SECONDS = 300


class ToolRunner:
    """Runs a style tool in a repo root, returning None when its binary is absent.

    Constructor injection: `timeout` bounds a hung tool. Separated from the lint
    so the test suite can drive the parsing without a subprocess.
    """

    def __init__(self, timeout: int = _TIMEOUT_SECONDS) -> None:
        self._timeout = timeout

    def run(self, argv: list[str], cwd: Path) -> subprocess.CompletedProcess[str] | None:
        env = dict(os.environ, NO_COLOR="1")
        try:
            return subprocess.run(argv, cwd=cwd, env=env, capture_output=True, text=True, timeout=self._timeout)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return None


class MarkdownStyleLint:
    """Runs the configured style tools over each governed repo root in scope.

    Constructor injection: `runner` executes the tools; `scanner` supplies the
    shared relpath helper so reported paths match the sibling lints'.
    """

    def __init__(self, runner: ToolRunner, scanner: dl.MarkdownScanner) -> None:
        self._runner = runner
        self._scanner = scanner

    def check(self, paths: list[Path], base: Path) -> list[dl.Finding]:
        findings: list[dl.Finding] = []
        for root, selected in sorted(self.group_scope(paths).items()):
            if (root / DPRINT_CONFIG).is_file():
                findings.extend(self.check_format(root, selected, base))
            if (root / RUMDL_CONFIG).is_file():
                findings.extend(self.check_structure(root, selected, base))
        return findings

    def group_scope(self, paths: list[Path]) -> dict[Path, set[Path] | None]:
        """Map each governed repo root to the selected files under it.

        `None` means the whole repo is selected (a directory root was handed in);
        a set means only those files are (the `changed` scope hands files).
        """
        groups: dict[Path, set[Path] | None] = {}
        for path in paths:
            resolved = path.resolve()
            if resolved.is_dir():
                if self.is_governed(resolved):
                    groups[resolved] = None
            elif resolved.suffix == ".md" and resolved.is_file():
                root = self.owning_root(resolved)
                if root is None:
                    continue
                selected = groups.setdefault(root, set())
                if selected is not None:
                    selected.add(resolved)
        return groups

    def label(self, root: Path, base: Path) -> str:
        """How a repo root is named in a message — its path from the base, or its own name at the base."""
        rel = self._scanner.relpath(root, base)
        return root.name if rel == "." else rel

    def is_governed(self, root: Path) -> bool:
        return (root / DPRINT_CONFIG).is_file() or (root / RUMDL_CONFIG).is_file()

    def owning_root(self, file: Path) -> Path | None:
        """Nearest ancestor carrying either config — the repo the file belongs to."""
        for parent in file.parents:
            if self.is_governed(parent):
                return parent
        return None

    def check_format(self, root: Path, selected: set[Path] | None, base: Path) -> list[dl.Finding]:
        proc = self._runner.run(["dprint", "check", "--list-different"], root)
        if proc is None:
            return [self.missing_tool(FORMAT_CHECK, "dprint", "cargo install dprint", root, base)]
        if proc.returncode == 0 and not proc.stdout.strip():
            return []
        findings: list[dl.Finding] = []
        named = False
        for raw in _ANSI_RE.sub("", proc.stdout).splitlines():
            candidate = Path(raw.strip())
            if not candidate.is_absolute() or candidate.suffix != ".md":
                continue
            named = True
            if selected is not None and candidate not in selected:
                continue
            findings.append(
                dl.Finding(
                    check=FORMAT_CHECK,
                    status="fail",
                    message=f"not formatted per `{self._scanner.relpath(root / DPRINT_CONFIG, base)}`",
                    file=self._scanner.relpath(candidate, base),
                    remediation=f"Run `dprint fmt` in {self.label(root, base)}.",
                )
            )
        if named:
            return findings
        return self.tool_failure(FORMAT_CHECK, "dprint", proc, root, base)

    def check_structure(self, root: Path, selected: set[Path] | None, base: Path) -> list[dl.Finding]:
        proc = self._runner.run(["rumdl", "check", ".", "--color", "never", "--output-format", "text"], root)
        if proc is None:
            return [self.missing_tool(LINT_CHECK, "rumdl", "uv tool install rumdl", root, base)]
        if proc.returncode == 0:
            return []
        findings: list[dl.Finding] = []
        named = False
        for raw in _ANSI_RE.sub("", proc.stdout).splitlines():
            m = _RUMDL_RE.match(raw.strip())
            if m is None:
                continue
            named = True
            reported = (root / m.group("path")).resolve()
            if selected is not None and reported not in selected:
                continue
            findings.append(
                dl.Finding(
                    check=LINT_CHECK,
                    status="fail",
                    message=m.group("message"),
                    file=self._scanner.relpath(reported, base),
                    line=int(m.group("line")),
                    remediation=f"Run `rumdl check . --fix` in {self.label(root, base)} "
                    "for the autofixable subset; the rest are hand fixes.",
                )
            )
        if named:
            return findings
        return self.tool_failure(LINT_CHECK, "rumdl", proc, root, base)

    def missing_tool(self, check: str, tool: str, install: str, root: Path, base: Path) -> dl.Finding:
        return dl.Finding(
            check=check,
            status="warn",
            message=f"`{tool}` is not on PATH — {self.label(root, base)} was not checked",
            remediation=f"Install it: `{install}`.",
        )

    def tool_failure(
        self, check: str, tool: str, proc: subprocess.CompletedProcess[str], root: Path, base: Path
    ) -> list[dl.Finding]:
        """A non-zero exit that named no file — a config or invocation error, not a violation.

        A file-scoped run that parsed real violations and filtered them all away
        is a genuine pass and never reaches here.
        """
        detail = _ANSI_RE.sub("", proc.stderr + proc.stdout).strip().splitlines()
        return [
            dl.Finding(
                check=check,
                status="fail",
                message=f"`{tool}` failed in {self.label(root, base)}: "
                f"{detail[-1] if detail else f'exit {proc.returncode}, no output'}",
            )
        ]


def main(argv: list[str]) -> int:
    cli = dl.LintCli()
    repo_root, paths_args = cli.parse_repo_arg(argv)
    scope = cli.resolve_scope(paths_args, repo_root)

    lint = MarkdownStyleLint(ToolRunner(), dl.MarkdownScanner())
    reporter = dl.NdjsonReporter()
    return reporter.emit(lint.check(scope, cli.base_dir(repo_root)))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
