"""Shared helpers for the agent-facing markdown lints.

`lint_path_notation.py` and `lint_doc_references.py` both ship here in the
winter-context Meta layer and both follow the `winter lint` script contract
(see `workspace:/context/winter-cli/configuration/lint.md`): NDJSON findings on stdout, one JSON
object per line, exit 0 regardless of verdict so the dispatcher aggregates the
statuses. Each is *also* runnable standalone against an arbitrary checkout.

This module holds only what both share — the `Finding` shape, the
`MarkdownScanner` service (markdown collection, line iteration, span/link/import
extraction, and relpath resolution), the `NdjsonReporter` service, and the
scope/arg helpers. The rules themselves live in the two lint scripts.

Env contract (set by `winter lint`, all optional for standalone use):
  WINTER_WORKSPACE_DIR  absolute workspace root — base for reported paths
  WINTER_LINT_PATHS     newline-delimited absolute paths in scope
  WINTER_LINT_SCOPE     scope kind (all/repo/env/changed) — informational
  WINTER_CLI            path to the winter CLI (unused here; the doc lints are
                        graph-free, unlike extractability)
"""

from __future__ import annotations

import json
import os
import re
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

# Directories never worth walking. `fixtures` is pruned so a default repo scan
# never trips over the lints' own deliberate-violation fixtures; tests target
# those paths explicitly, which bypasses the prune.
PRUNE_DIRS = frozenset(
    {".git", ".venv", "node_modules", "__pycache__", ".mypy_cache", ".ruff_cache", "fixtures", "dist", "build"}
)

# An inline code span: `like this`. Doubled-backtick spans are rare in these
# docs; the single-backtick form covers every path reference we care about.
_CODE_SPAN_RE = re.compile(r"`([^`]+)`")

# A markdown link target: [text](target). Title and angle-bracket forms handled
# by the caller via `link_target`.
_LINK_RE = re.compile(r"\[(?:[^\]]*)\]\(([^)]+)\)")

# A Claude `@import` at the start of a line — `@context/project/index.md`. A routing
# mechanism alongside markdown links, so reachability must follow it.
_IMPORT_RE = re.compile(r"^\s*@(\S+)")

# Illustrative-example exemption — identical marker to the extractability lint,
# so authors learn one escape hatch for both. Block-scoped, not line-scoped: see
# `MarkdownScanner.exempt_lines`.
_MARKER_RE = re.compile(r"<!--\s*winter-lint:\s*example\s*-->", re.IGNORECASE)


@dataclass(frozen=True)
class Finding:
    """One lint finding, serialized as a line of NDJSON for `winter lint`."""

    check: str
    status: str  # pass | warn | fail
    message: str
    file: str | None = None
    line: int | None = None
    remediation: str | None = None

    def to_json(self) -> str:
        payload: dict[str, object] = {"check": self.check, "status": self.status, "message": self.message}
        if self.file is not None:
            payload["file"] = self.file
        if self.line is not None:
            payload["line"] = self.line
        if self.remediation is not None:
            payload["remediation"] = self.remediation
        return json.dumps(payload)


class MarkdownScanner:
    """Collects markdown files and provides line/span/link extraction methods.

    Constructor injection: `prune_dirs` defaults to the module-level
    `PRUNE_DIRS` frozenset and may be overridden by tests or callers that need
    a different exclusion set.
    """

    def __init__(self, prune_dirs: frozenset[str] = PRUNE_DIRS) -> None:
        self._prune_dirs = prune_dirs

    def collect_markdown(self, paths: list[Path]) -> list[Path]:
        """Every `*.md` reachable from `paths`, pruning prune_dirs, de-duplicated."""
        out: list[Path] = []
        seen: set[Path] = set()
        for p in paths:
            if p.is_file():
                if p.suffix == ".md" and p not in seen:
                    seen.add(p)
                    out.append(p)
                continue
            for dirpath, dirnames, filenames in os.walk(p):
                # Prune prune_dirs and any nested checkout — a subdirectory holding
                # its own `.git` is a separate repo (a sibling project, a feature
                # worktree, an installed extension) and is linted on its own, not as
                # part of this one. The walk root itself is never pruned.
                dirnames[:] = [
                    d for d in dirnames if d not in self._prune_dirs and not (Path(dirpath) / d / ".git").exists()
                ]
                for name in sorted(filenames):
                    if name.endswith(".md"):
                        f = Path(dirpath) / name
                        if f not in seen:
                            seen.add(f)
                            out.append(f)
        return out

    def read_lines(self, file: Path) -> list[str] | None:
        try:
            return file.read_text(errors="replace").splitlines()
        except OSError:
            return None

    def iter_content_lines(self, text: str):
        """Yield (lineno, line) for lines outside fenced code blocks.

        Fenced blocks (``` or ~~~) hold sample commands and example prompts whose
        literal relative paths are legitimate — a prefix would be wrong there — so
        both lints skip them, mirroring the extractability lint.
        """
        in_fence = False
        for lineno, line in enumerate(text.splitlines(), start=1):
            stripped = line.lstrip()
            if stripped.startswith("```") or stripped.startswith("~~~"):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            yield lineno, line

    def code_spans(self, line: str) -> list[str]:
        """The contents of every inline code span on a line."""
        return _CODE_SPAN_RE.findall(line)

    def link_targets(self, line: str) -> list[str]:
        """Resolved-ready targets of every markdown link on a line.

        Strips an optional title (`(path "Title")`), angle brackets (`(<path>)`),
        and a trailing `#anchor`. Returns the raw target string; the caller decides
        what to resolve.
        """
        out: list[str] = []
        for t in self.raw_link_targets(line):
            file_part = t.split("#", 1)[0]
            if file_part:
                out.append(file_part)
        return out

    def raw_link_targets(self, line: str) -> list[str]:
        """Targets of every markdown link on a line, preserving any #fragment.

        Same as `link_targets` but does not strip the fragment — the caller
        receives the full target string (e.g. `path/to/file.md#heading` or
        `#same-file-anchor`) and is responsible for splitting on `#`.
        """
        out: list[str] = []
        for raw in _LINK_RE.findall(line):
            target = raw.strip()
            if target.startswith("<") and ">" in target:
                target = target[1 : target.index(">")]
            else:
                target = target.split()[0] if target.split() else ""
            if target:
                out.append(target)
        return out

    def import_targets(self, line: str) -> list[str]:
        """The target of a line-leading `@import`, if it is path-shaped."""
        m = _IMPORT_RE.match(line)
        if not m:
            return []
        raw = m.group(1)
        if "/" not in raw and "." not in raw:  # `@param`-style mention, not a path
            return []
        return [raw]

    def exempt_lines(self, text: str) -> set[int]:
        """Line numbers covered by an `<!-- winter-lint:example -->` marker.

        The marker exempts the whole **block** it sits in, not just its own
        physical line. A markdown formatter owns where lines break, so a marker
        at the end of a wrapped paragraph must still cover the reference that
        reflow pushed three lines up; a line is not a stable unit of meaning once
        `dprint fmt` runs. A block is a run of non-blank lines.

        The consequence for tables: a formatter puts a blank line between a table
        and a comment above or below it, which makes the comment its own block and
        exempts nothing. Put a table's marker *inside a cell* — cell content
        survives reformatting, and the row is its own line.
        """
        exempt: set[int] = set()
        lines = text.splitlines()
        start = 0
        marked = False
        for index, line in enumerate(lines):
            if line.strip():
                marked = marked or bool(_MARKER_RE.search(line))
                continue
            if marked:
                exempt.update(range(start + 1, index + 1))
            start = index + 1
            marked = False
        if marked:
            exempt.update(range(start + 1, len(lines) + 1))
        return exempt

    def relpath(self, file: Path, base: Path) -> str:
        try:
            return str(file.resolve().relative_to(base.resolve()))
        except ValueError:
            return str(file)


class NdjsonReporter:
    """Emits findings as NDJSON to stdout and returns exit 0."""

    def emit(self, findings: list[Finding]) -> int:
        """Print findings as NDJSON and return 0 — verdicts live in the statuses."""
        for finding in findings:
            print(finding.to_json())
        return 0


# ── invocation parsing ────────────────────────────────────────────────────────


class LintCli:
    """Resolves a lint script's repo root, scan scope, and report base from argv + environment.

    The process environment is injected so the `WINTER_LINT_PATHS` /
    `WINTER_WORKSPACE_DIR` contract is read in one place — and so tests drive it
    without monkeypatching `os.environ`. Construct it in a script's `main()`,
    which is the composition root.
    """

    def __init__(self, env: Mapping[str, str] | None = None) -> None:
        self._env = os.environ if env is None else env

    def parse_repo_arg(self, args: list[str]) -> tuple[Path, list[str]]:
        """Split `--repo PATH` out of an argv tail, returning (repo_root, rest).

        repo_root defaults to WINTER_WORKSPACE_DIR, then cwd.
        """
        repo_root = Path(self._env.get("WINTER_WORKSPACE_DIR") or Path.cwd())
        rest: list[str] = []
        i = 0
        while i < len(args):
            arg = args[i]
            if arg == "--repo":
                if i + 1 >= len(args):
                    sys.stderr.write("--repo requires a path argument\n")
                    raise SystemExit(2)
                repo_root = Path(args[i + 1])
                i += 2
                continue
            if arg.startswith("--repo="):
                repo_root = Path(arg[len("--repo=") :])
                i += 1
                continue
            rest.append(arg)
            i += 1
        return repo_root, rest

    def resolve_scope(self, argv: list[str], repo_root: Path) -> list[Path]:
        """Paths to scan, in priority order: WINTER_LINT_PATHS, argv, then repo root.

        `winter lint` sets WINTER_LINT_PATHS; standalone callers pass paths (or a
        `--repo` that became `repo_root`) and fall back to scanning the whole repo.
        """
        raw = self._env.get("WINTER_LINT_PATHS")
        if raw is not None:
            return [Path(line) for line in raw.splitlines() if line.strip()]
        if argv:
            return [Path(a) for a in argv]
        return [repo_root]

    def base_dir(self, repo_root: Path) -> Path:
        """Base for reported paths — WINTER_WORKSPACE_DIR, else the repo root."""
        return Path(self._env.get("WINTER_WORKSPACE_DIR") or repo_root)

    def has_contributed_scope(self) -> bool:
        """Whether winter supplied an explicit contributed-lint scope."""
        return "WINTER_LINT_PATHS" in self._env

    def selected_repository_roots(self, paths: list[Path]) -> list[Path]:
        """Selected directory paths that are repository or worktree roots.

        A file-only scope cannot safely be widened for a whole-repository check,
        so files are deliberately omitted. The caller may still apply direct
        file-local checks to them.
        """
        roots: list[Path] = []
        seen: set[Path] = set()
        for path in paths:
            resolved = path.resolve()
            if not resolved.is_dir() or not (resolved / ".git").exists() or resolved in seen:
                continue
            seen.add(resolved)
            roots.append(resolved)
        return roots
