# Markdown convention lints

Three conventions for agent-facing markdown are enforced mechanically here: the canonical path notation in [`./references.md`](./references.md), the reference integrity of the routing tables an agent navigates by, and the anchor validity of every `#fragment` link.
The three lint scripts in [`./scripts/`](./scripts/) check each convention in turn and follow the `winter lint` script contract (NDJSON findings on stdout, exit 0 — see `workspace:/context/winter-cli/configuration/lint.md`), so each is also registerable as a `winter lint` check.
They ship in the winter-harness agent-context domain because they enforce *its* conventions, so any ecosystem repo can run them against its own docs.
They are graph-free, which is what distinguishes them from the extractability lint at `winter:/tools/winter-lint/extractability.py`: extractability asks whether a reference *already in* `<context>:/` notation points at a declared dependency, while these ask whether a raw path *should be* in notation, whether a routing link resolves at all, and whether a link's `#fragment` matches a real heading.
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

A repo's own files referred to with bare relative paths (`./architecture/error-handling.md`, `tools/winter-cli/pyproject.toml`) and references already in canonical notation are never flagged.

## `lint_link_anchors.py` — link-target and anchor resolution

Resolves every markdown link's file target AND its `#fragment` anchor, flagging links that point at a heading that does not exist or a file that is missing.

Four link forms are handled:

| Form | Resolution |
|------|------------|
| `#anchor` | same-file headings |
| `path/to/file.md#anchor` | file relative to the linking document |
| `winter-foo:/path.md#anchor` | extension file under `$WINTER_WORKSPACE_DIR/.winter/ext/foo/` |
| `workspace:/path.md#anchor` | file under `$WINTER_WORKSPACE_DIR` |

Two kinds of findings:

- **Dangling anchor** (`fail`) — the `#fragment` matches no heading slug in the target file, including the case where the target file itself does not exist.
  GitHub-style slugs are computed: lowercase, strip non-word chars (backtick-span content is inlined), spaces → hyphens, duplicate headings disambiguated as `slug`, `slug-1`, `slug-2`, …
- **Dead file target** (`fail`) — a link without a fragment whose target does not exist (relative links and cross-repo `<context>:/` links both checked).
  Dead-file detection also fires in `lint_doc_references`; the overlap is deliberate — each check's scope differs and double-reporting ensures coverage under `--changed`.

Cross-repo resolution requires `WINTER_WORKSPACE_DIR` (set by `winter lint`); running standalone without it silently skips cross-context links.
External URLs (`https://…`) and root-relative paths (`/…`) are never checked.

Under `--changed`, only links outbound from the changed files are validated; a heading renamed in file B will not flag inbound links from unchanged file A.

Honors the `<!-- winter-lint:example -->` line marker and fenced-code-block skip.

## `lint_doc_references.py` — routing-table integrity

Two checks over the routing files (`AGENTS.md`, `AGENTS.winter.md`, `CLAUDE.md`, and every `index.md`):

- **Broken links** (`fail`) — a relative markdown link whose target does not exist strands an agent mid-disclosure.
  Targets with a scheme or path-notation prefix (`https:`, `workspace:/…`) are skipped — a single-repo lint can't resolve a cross-context reference, and extractability already validates those.
  Body docs (skills, agents) are out of scope here: their links often use a workspace-root-relative convention this lint can't model.
- **Orphans** (`warn`) — a `context/**/*.md` file that exists but is unreachable from any routing table or skill by link or `@import` chain is content no agent will be routed to.
  Reachability seeds from both routing-table files (`AGENTS.md`, `AGENTS.winter.md`, `CLAUDE.md`, `index.md`, `README.md`) and from every `SKILL.md` found in the repo.
  Path-notation references inside a `SKILL.md` (e.g. `` `workspace:/context/foo.md` ``) are resolved against the repo root so that docs linked only from a skill are not falsely orphaned.
  `warn` by default; `--orphan-severity fail|off` to change it, `--allow '<glob>'` (repeatable, repo-relative) to exempt intentionally-unrouted files.

Reachability and orphan detection are whole-repo properties, so this lint always scans the full `--repo` root, not a changed-file subset.

## Running them

Standalone against any checkout:

```bash
python3 agent-context/scripts/lint_path_notation.py --repo /path/to/checkout
python3 agent-context/scripts/lint_doc_references.py --repo /path/to/checkout --orphan-severity off
python3 agent-context/scripts/lint_link_anchors.py --repo /path/to/checkout
```

All three are contributed to `winter lint` from this extension's `winter-ext.toml` `lint` field (a list, so each check ships as its own script):

```toml
lint = [
    "agent-context/scripts/lint_path_notation.py",
    "agent-context/scripts/lint_doc_references.py",
    "agent-context/scripts/lint_link_anchors.py",
]
```

The dispatcher runs each over the selected scope with the standard lint env (`WINTER_LINT_PATHS`, `WINTER_WORKSPACE_DIR`, cwd at the workspace root) and groups their findings under the `[wh]` source. `lint_path_notation` and `lint_link_anchors` honor `WINTER_LINT_PATHS`; `lint_doc_references` always scans the whole `WINTER_WORKSPACE_DIR` (reachability is a whole-repo property), so under a narrower scope it still reports against the full workspace.

All walk every `*.md` under the target, pruning vendor directories and any nested checkout (a subdirectory with its own `.git` is a separate repo, linted on its own).

## Maintaining the scripts

The scripts in [`./scripts/`](./scripts/) follow the service-class tier — plain concrete classes with constructor injection, no `I`-prefix Protocols or DI container ([`../architecture/service-architecture.md`](../architecture/service-architecture.md)); the code itself is the reference for their shape.
Their stdlib `unittest` suite, driven by deliberate-violation fixtures under [`./scripts/fixtures/`](./scripts/fixtures/) so the whole `scripts/` directory travels to any consumer intact, runs standalone:

```bash
cd agent-context/scripts && python3 -m unittest test_doclint
```
