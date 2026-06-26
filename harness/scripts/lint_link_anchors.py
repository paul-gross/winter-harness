#!/usr/bin/env python3
"""Link-anchor lint for agent-facing markdown.

Resolves markdown link targets and their `#fragment` anchors, flagging:
- A fragment that matches no heading slug in the target file — `fail`.
- A relative or cross-repo link (no fragment) whose target file does not exist — `fail`.

Four link forms are handled:
  `#anchor`                      same-file anchor
  `path/to/file.md#anchor`       relative-path anchor
  `winter-foo:/path/file.md#anchor`  cross-repo canonical-notation anchor
  `workspace:/path/file.md#anchor`   workspace-root anchor

Heading slugs follow GitHub's algorithm: lowercase, strip non-word/space/hyphen
characters (backtick spans are inlined before stripping), spaces to hyphens,
duplicate headings disambiguated as `slug`, `slug-1`, `slug-2`, …

Cross-repo resolution uses `WINTER_WORKSPACE_DIR` to locate installed
extensions under `.winter/ext/<name>/`. If the env var is absent the lint
silently skips cross-context links it cannot resolve.

Honors the `<!-- winter-lint:example -->` line marker and fenced-code-block
skip (mirroring the other markdown lints in this directory).

This is a `winter lint` check: NDJSON findings on stdout, exit 0.
Also runnable standalone:
    python3 lint_link_anchors.py --repo /path/to/checkout
    python3 lint_link_anchors.py path/to/file.md ...
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _doclint as dl  # noqa: E402

CHECK = "link-anchors"

# GitHub-style slug: strip non-word/space/hyphen chars after lowercasing.
# `\w` is `[a-zA-Z0-9_]`; hyphens and spaces are kept (spaces become hyphens).
_SLUG_STRIP_RE = re.compile(r"[^\w\s-]", re.UNICODE)

# Backtick spans in heading text: GitHub inlines the content without the ticks.
_BACKTICK_RE = re.compile(r"`([^`]*)`")

# Markdown heading line: `# Title`, `## Title`, …
_HEADING_RE = re.compile(r"^#{1,6}\s+(.*)")

# Any URI scheme (`https://`, `mailto:`, `tel:`, `ftp://`, …) — not resolvable
# locally.  The `+` and `.` in the character class allow e.g. `svn+ssh:`.
_ANY_SCHEME_RE = re.compile(r"^[a-z][a-z0-9+.-]*:")

# Cross-repo context prefix, e.g. `winter-foo:/` or `workspace:/`.
_CONTEXT_RE = re.compile(r"^([a-z][a-z0-9-]*):/(.*)$")


# ── slug helpers ──────────────────────────────────────────────────────────────


def _compute_slug(text: str) -> str:
    """GitHub-style slug for a single heading text string.

    Each whitespace character is replaced individually (two spaces → two
    hyphens), and no leading/trailing hyphens are stripped — both match
    GitHub's github-slugger behaviour.
    """
    text = _BACKTICK_RE.sub(r"\1", text)  # `code` → code
    text = text.lower()
    text = _SLUG_STRIP_RE.sub("", text)
    text = re.sub(r"\s", "-", text)
    return text


def _extract_heading_slugs(lines: list[str], scanner: dl.MarkdownScanner) -> set[str]:
    """Extract heading slugs from a line list, using the scanner for fence-skipping.

    Only ATX-style headings (lines starting with `#`) are recognised;
    setext-style headings (`===` / `---` underlines) are not slugged.
    """
    slugs: set[str] = set()
    counts: dict[str, int] = {}
    for _, line in scanner.iter_content_lines("\n".join(lines)):
        m = _HEADING_RE.match(line)
        if not m:
            continue
        base = _compute_slug(m.group(1))
        if not base:
            continue
        if base not in counts:
            counts[base] = 0
            slugs.add(base)
        else:
            counts[base] += 1
            slugs.add(f"{base}-{counts[base]}")
    return slugs


def file_heading_slugs(file: Path) -> set[str]:
    """Set of all valid heading slugs in a markdown file.

    Duplicate headings are disambiguated GitHub-style: first occurrence → `slug`,
    second → `slug-1`, third → `slug-2`, and so on.  Headings inside fenced
    code blocks are skipped.  Only ATX-style headings (`#`-prefixed) are
    recognised; setext headings (`===` / `---` underlines) are not slugged.
    """
    try:
        lines = file.read_text(errors="replace").splitlines()
    except OSError:
        return set()
    return _extract_heading_slugs(lines, dl.MarkdownScanner())


# ── lint class ────────────────────────────────────────────────────────────────


class LinkAnchorLint:
    """Checks markdown files for dangling link anchors and dead file targets.

    Constructor injection: `scanner` provides file collection and line parsing;
    `workspace_dir` is the absolute workspace root used to resolve cross-repo
    `winter-<name>:/` and `workspace:/` links (may be None when running
    standalone without `WINTER_WORKSPACE_DIR`).
    """

    def __init__(self, scanner: dl.MarkdownScanner, workspace_dir: Path | None = None) -> None:
        self._scanner = scanner
        self._workspace_dir = workspace_dir
        self._slug_cache: dict[Path, set[str]] = {}

    def _get_slugs(self, file: Path) -> set[str]:
        if file not in self._slug_cache:
            lines = self._scanner.read_lines(file)
            self._slug_cache[file] = (
                _extract_heading_slugs(lines, self._scanner) if lines is not None else set()
            )
        return self._slug_cache[file]

    def _resolve_context(self, context: str, rest: str) -> Path | None:
        """Resolve a `<context>:/rest` prefix to an absolute path.

        Returns None when the workspace directory is unavailable or the context
        is not a known resolvable form (`workspace` or `winter-<name>`).

        Note: `winter-<name>:/` links are resolved to `.winter/ext/<name>/`
        under the workspace root.  This path is a workspace-layout convention,
        not a configurable value; cross-repo fragment links will false-fail in
        workspaces that install extensions to a non-standard location.
        """
        if self._workspace_dir is None:
            return None
        if context == "workspace":
            return (self._workspace_dir / rest).resolve()
        if context.startswith("winter-"):
            ext_name = context[len("winter-"):]
            return (self._workspace_dir / ".winter" / "ext" / ext_name / rest).resolve()
        return None

    def _parse_raw_target(self, raw: str) -> tuple[str | None, str | None]:
        """Split a raw link target into (file_part, fragment).

        Returns (None, None) for targets that should be skipped entirely.
        `file_part` is empty string for same-file anchors (`#anchor`).
        `fragment` is None when the link has no `#` component.
        """
        if raw.startswith("/"):
            return None, None  # root-relative, ambiguous in a single-repo lint
        if set(raw) <= {".", "…"}:
            return None, None  # ellipsis placeholder (`…`, `...`) — not a real path
        if "#" in raw:
            file_part, fragment = raw.split("#", 1)
            if not fragment:
                return None, None  # bare `#` or empty fragment — nothing to check
        else:
            file_part, fragment = raw, None
        # Cross-repo context prefixes (`winter-foo:/`, `workspace:/`) are
        # handled by `_resolve_file_part`; check them first so `workspace:/…`
        # is not mistakenly caught by the URI-scheme guard below.
        if _CONTEXT_RE.match(file_part):
            return file_part, fragment
        # Skip any other URI scheme (`https://`, `mailto:`, `tel:`, …).
        if _ANY_SCHEME_RE.match(file_part):
            return None, None
        return file_part, fragment

    def _resolve_file_part(self, file_part: str, from_file: Path) -> Path | None:
        """Resolve the file portion of a link to an absolute path.

        Returns None for cross-context refs whose workspace is unknown.
        """
        if not file_part:
            return from_file
        m = _CONTEXT_RE.match(file_part)
        if m:
            return self._resolve_context(m.group(1), m.group(2))
        return (from_file.parent / file_part).resolve()

    def check(self, paths: list[Path], base: Path) -> list[dl.Finding]:
        findings: list[dl.Finding] = []
        for file in self._scanner.collect_markdown(paths):
            lines = self._scanner.read_lines(file)
            if lines is None:
                continue
            for lineno, line in self._scanner.iter_content_lines("\n".join(lines)):
                if self._scanner.has_example_marker(line):
                    continue
                for raw in self._scanner.raw_link_targets(line):
                    file_part, fragment = self._parse_raw_target(raw)
                    if file_part is None:
                        continue
                    resolved = self._resolve_file_part(file_part, file)
                    if resolved is None:
                        continue  # unresolvable cross-context ref — skip
                    if fragment is not None:
                        if not resolved.exists():
                            findings.append(
                                dl.Finding(
                                    check=CHECK,
                                    status="fail",
                                    message=f"dangling anchor `{raw}` — target file does not exist",
                                    file=self._scanner.relpath(file, base),
                                    line=lineno,
                                    remediation="Fix the file path, or remove the link.",
                                )
                            )
                        else:
                            slugs = self._get_slugs(resolved)
                            if fragment not in slugs:
                                findings.append(
                                    dl.Finding(
                                        check=CHECK,
                                        status="fail",
                                        message=(
                                            f"dangling anchor `#{fragment}` in `{raw}` — "
                                            f"no matching heading in target"
                                        ),
                                        file=self._scanner.relpath(file, base),
                                        line=lineno,
                                        remediation=(
                                            "Fix the anchor to match an existing heading slug, "
                                            "or remove the fragment."
                                        ),
                                    )
                                )
                    else:
                        if not resolved.exists():
                            findings.append(
                                dl.Finding(
                                    check=CHECK,
                                    status="fail",
                                    message=f"dead link `{raw}` — target does not exist",
                                    file=self._scanner.relpath(file, base),
                                    line=lineno,
                                    remediation="Fix the path or remove the link.",
                                )
                            )
        return findings


# ── entry point ───────────────────────────────────────────────────────────────


def main(argv: list[str]) -> int:
    cli = dl.LintCli()
    repo_root, paths_args = cli.parse_repo_arg(argv)
    scope = cli.resolve_scope(paths_args, repo_root)

    workspace_dir_raw = os.environ.get("WINTER_WORKSPACE_DIR")
    workspace_dir = Path(workspace_dir_raw) if workspace_dir_raw else None

    scanner = dl.MarkdownScanner()
    lint = LinkAnchorLint(scanner, workspace_dir)
    reporter = dl.NdjsonReporter()
    return reporter.emit(lint.check(scope, cli.base_dir(repo_root)))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
