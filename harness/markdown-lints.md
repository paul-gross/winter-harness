# Markdown convention lints

Two conventions for agent-facing markdown are documented but otherwise enforced only by reading habit: the canonical path notation in [`./winter-references.md`](./winter-references.md), and the reference integrity of the routing tables an agent navigates by.
The lints here mechanically check both.
They ship in the winter-harness Markdown layer because they enforce *its* conventions, so any ecosystem repo can run them against its own docs.

Both live in [`./scripts/`](./scripts/) and follow the `winter lint` script contract (NDJSON findings on stdout, exit 0 — see `winter:/ai/winter-cli/setup.md` "Lint checks"), so each is also registerable as a `winter lint` check.
They are graph-free, which is what distinguishes them from the extractability lint at `winter:/tools/winter-lint/extractability.py`: extractability asks whether a reference *already in* `<context>:/` notation points at a declared dependency, while these ask whether a raw path *should be* in notation and whether a routing link resolves at all.
They reuse extractability's `<!-- winter-lint:example -->` line marker and fenced-code-block skip — see that lint's README (`winter:/tools/winter-lint/README.md`) for the marker semantics.

## `lint_path_notation.py` — raw cross-context paths

Flags a path written without a `<context>:/` prefix when it unambiguously crosses a repo or context boundary — the kind of reference that dies the moment an extension is renamed or its install path changes.
It scans inline code spans (where file references live in these docs), skips fenced code blocks (sample commands, where a raw relative path is correct), and skips any line carrying the example marker.
Findings are `warn` by default because path notation has fuzzy edges; raise to `fail` per consumer with `--severity fail`.

It fires on five unambiguous shapes and leaves everything else alone:

| Flagged | Why | Should be |
|---------|-----|-----------|
| `.winter/ext/<name>/…` | install location varies per workspace | `winter-<name>:/…` |
| `projects/<repo>/…` | `projects/` is a workspace-internal layout detail | `<repo>:/…` |
| `../winter-<name>/…` | sibling-relative path crossing a repo boundary | `winter-<name>:/…` |
| `winter-<name>/…` | bare repo name, no context prefix | `winter-<name>:/…` |
| `/home/…`, `/Users/…`, `/root/…` | machine-absolute path | a `<context>:/…` prefix | <!-- winter-lint:example -->

A repo's own files referred to with bare relative paths (`./python/error-handling.md`, `tools/winter-cli/pyproject.toml`) and references already in canonical notation are never flagged.

## `lint_doc_references.py` — routing-table integrity

Two checks over the routing files (`CLAUDE.md`, `CLAUDE.winter.md`, and every `index.md`):

- **Broken links** (`fail`) — a relative markdown link whose target does not exist strands an agent mid-disclosure.
  Targets with a scheme or path-notation prefix (`https:`, `workspace:/…`) are skipped — a single-repo lint can't resolve a cross-context reference, and extractability already validates those.
  Body docs (skills, agents) are out of scope here: their links often use a workspace-root-relative convention this lint can't model.
- **Orphans** (`warn`) — an `ai/**/*.md` file that exists but is unreachable from any routing table by link or `@import` chain is content no agent will be routed to.
  `warn` by default; `--orphan-severity fail|off` to change it, `--allow '<glob>'` (repeatable, repo-relative) to exempt intentionally-unrouted files.

Reachability and orphan detection are whole-repo properties, so this lint always scans the full `--repo` root, not a changed-file subset.

## Running them

Standalone against any checkout:

```bash
python3 harness/scripts/lint_path_notation.py --repo /path/to/checkout
python3 harness/scripts/lint_doc_references.py --repo /path/to/checkout --orphan-severity off
```

Both are contributed to `winter lint` from this extension's `winter-ext.toml` `lint` field (a list, so each check ships as its own script):

```toml
lint = [
    "harness/scripts/lint_path_notation.py",
    "harness/scripts/lint_doc_references.py",
]
```

The dispatcher runs each over the selected scope with the standard lint env (`WINTER_LINT_PATHS`, `WINTER_WORKSPACE_DIR`, cwd at the workspace root) and groups their findings under the `[wh]` source. `lint_path_notation` honors `WINTER_LINT_PATHS`; `lint_doc_references` always scans the whole `WINTER_WORKSPACE_DIR` (reachability is a whole-repo property), so under a narrower scope it still reports against the full workspace.

Both walk every `*.md` under the target, pruning vendor directories and any nested checkout (a subdirectory with its own `.git` is a separate repo, linted on its own).

## Code shape

The three files in [`./scripts/`](./scripts/) follow the service-class tier — plain concrete classes with constructor injection, no `I`-prefix Protocols or DI container:

- **`_doclint.py`** — shared domain object and services: `Finding` (frozen dataclass with `to_json()`), `MarkdownScanner` (file collection, fenced-block-aware line iteration, code-span / link / import extraction, relpath), `NdjsonReporter` (emits NDJSON, returns 0), and `LintCli` (parses argv + the injected environment into a repo root, scan scope, and report base).
- **`lint_path_notation.py`** — `PathNotationLint(scanner, severity)` with a `check(paths, base) -> list[Finding]` method and `classify_span(span) -> str | None` as a method. `main()` constructs `MarkdownScanner`, `PathNotationLint`, and `NdjsonReporter`, then wires them.
- **`lint_doc_references.py`** — `DocReferenceLint(scanner, orphan_severity, allow)` with a `check(repo_root, base) -> list[Finding]` method; broken-link detection, reachability BFS, and orphan detection are private methods. `main()` constructs the collaborators and wires them.

## Tests

```bash
cd harness/scripts && python3 -m unittest test_doclint
```

Stdlib `unittest` only, driven by deliberate-violation fixtures under [`./scripts/fixtures/`](./scripts/fixtures/) — so the whole `scripts/` directory travels to any consumer intact.
Tests construct `MarkdownScanner`, `PathNotationLint`, and `DocReferenceLint` directly and drive them via their methods.
