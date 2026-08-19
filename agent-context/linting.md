# Markdown convention lints

Four lint scripts in [`./scripts/`](./scripts/) enforce agent-facing markdown mechanically, and each follows the
`winter lint` script contract (NDJSON findings on stdout, exit 0 — see
`workspace:/context/winter-cli/configuration/lint.md`), so each is also registerable as a `winter lint` check. Three of
them check what a reference *means*: the canonical path notation in [`./references.md`](./references.md), the reference
integrity of the routing tables an agent navigates by, and the anchor validity of every `#fragment` link. The fourth
checks *shape* — line width, list markers, emphasis style, fence languages — by running two external tools, and is
described under [Mechanical style](#lint_markdown_stylepy--mechanical-format-and-structure) below. They ship in the
winter-harness agent-context domain because they enforce *its* conventions, so any ecosystem repo can run them against
its own docs. The three semantic checks are graph-free, which is what distinguishes them from the extractability lint at
`winter:/tools/winter-lint/extractability.py`: extractability asks whether a reference *already in* `<context>:/`
notation points at a declared dependency, while these ask whether a raw path *should be* in notation, whether a routing
link resolves at all, and whether a link's `#fragment` matches a real heading. Those three reuse extractability's
`<!-- winter-lint:example -->` marker and fenced-code-block skip — see that lint's README
(`winter:/tools/winter-lint/README.md`) for the marker semantics.

The marker exempts the **block** it sits in, not its own physical line. That is what keeps it working under `dprint`:
the formatter owns where lines break, so a marker parked at the end of a wrapped paragraph still covers the reference
reflow pushed three lines up. A block is a run of non-blank lines — which is why a **table's** marker goes *inside a
cell*. A comment above or below a table gets a blank line from the formatter, making it its own block and exempting
nothing.

## `lint_path_notation.py` — raw cross-context paths

Flags a path written without a `<context>:/` prefix when it unambiguously crosses a repo or context boundary — the kind
of reference that dies the moment an extension is renamed or its install path changes. It scans inline code spans (where
file references live in these docs), skips fenced code blocks (sample commands, where a raw relative path is correct),
and skips any line carrying the example marker. Findings are `warn` by default because path notation has fuzzy edges;
raise to `fail` per consumer with `--severity fail`.

It fires on five unambiguous shapes and leaves everything else alone:

| Flagged                          | Why                                               | Should be                                            |
| -------------------------------- | ------------------------------------------------- | ---------------------------------------------------- |
| `.winter/ext/<name>/…`           | install location varies per workspace             | `winter-<name>:/…`                                   |
| `projects/<repo>/…`              | `projects/` is a workspace-internal layout detail | `<repo>:/…`                                          |
| `../winter-<name>/…`             | sibling-relative path crossing a repo boundary    | `winter-<name>:/…`                                   |
| `winter-<name>/…`                | bare repo name, no context prefix                 | `winter-<name>:/…`                                   |
| `/home/…`, `/Users/…`, `/root/…` | machine-absolute path                             | a `<context>:/…` prefix <!-- winter-lint:example --> |

A repo's own files referred to with bare relative paths (`./architecture/error-handling.md`,
`tools/winter-cli/pyproject.toml`) and references already in canonical notation are never flagged.

## `lint_link_anchors.py` — link-target and anchor resolution

Resolves every markdown link's file target AND its `#fragment` anchor, flagging links that point at a heading that does
not exist or a file that is missing.

Four link forms are handled:

| Form                         | Resolution                                                                                                                                   |
| ---------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| `#anchor`                    | same-file headings                                                                                                                           |
| `path/to/file.md#anchor`     | file relative to the linking document                                                                                                        |
| `winter-foo:/path.md#anchor` | the selected module root for a `winter-foo` self-reference; otherwise the installed extension under `$WINTER_WORKSPACE_DIR/.winter/ext/foo/` |
| `workspace:/path.md#anchor`  | file under `$WINTER_WORKSPACE_DIR`                                                                                                           |

Two kinds of findings:

- **Dangling anchor** (`fail`) — the `#fragment` matches no heading slug in the target file, including the case where
  the target file itself does not exist. GitHub-style slugs are computed: lowercase, strip non-word chars (backtick-span
  content is inlined), spaces → hyphens, duplicate headings disambiguated as `slug`, `slug-1`, `slug-2`, …
- **Dead file target** (`fail`) — a link without a fragment whose target does not exist (relative links and cross-repo
  `<context>:/` links both checked). Dead-file detection also fires in `lint_doc_references`; the overlap is deliberate
  — each check's scope differs and double-reporting ensures coverage under `--changed`.

Canonical self-references from a module selected as a repository/worktree directory resolve against that selected root,
including standalone `--repo` runs. Foreign extension resolution requires `WINTER_WORKSPACE_DIR` (set by `winter lint`)
and uses the installed `.winter/ext/<name>/` copy; running standalone without it silently skips only those unresolved
foreign links. External URLs (`https://…`) and root-relative paths (`/…`) are never checked.

Under `--changed`, only links outbound from the changed files are validated; a heading renamed in file B will not flag
inbound links from unchanged file A.

Honors the `<!-- winter-lint:example -->` block marker and fenced-code-block skip.

## `lint_doc_references.py` — routing-table integrity

Two checks over the routing files (`AGENTS.md`, `AGENTS.winter.md`, `CLAUDE.md`, and every `index.md`):

- **Broken links** (`fail`) — a relative markdown link whose target does not exist strands an agent mid-disclosure.
  Targets with a scheme or path-notation prefix (`https:`, `workspace:/…`) are skipped — a single-repo lint can't
  resolve a cross-context reference, and extractability already validates those. Body docs (skills, agents) are out of
  scope here: their links often use a workspace-root-relative convention this lint can't model.
- **Orphans** (`warn`) — a markdown file under a `context/` or `methodology/` root that exists but is unreachable from
  any routing table or skill by link or `@import` chain is content no agent will be routed to. Reachability seeds from
  repository-root entrypoints (`AGENTS.md`, `AGENTS.winter.md`, `CLAUDE.md`, `index.md`, `README.md`) and from every
  `SKILL.md` found in the repo. A nested `index.md` or `README.md` is not an entrypoint by filename alone; it becomes
  reachable only through the link chain. Repo-local path-notation references inside a `SKILL.md` are followed for the
  extension name declared by that repo's `winter-ext.toml` and for the `local:` alias. `workspace:` is local only when
  the scanned root is the workspace root or the script is running standalone without an external workspace. Other
  extension identities are not stripped and resolved locally. `warn` by default; `--orphan-severity fail|off` to change
  it, `--allow '<glob>'` (repeatable, repo-relative) to exempt intentionally-unrouted files.

Reachability and orphan detection are whole-repo properties. Standalone `--repo` scans preserve the full-root behavior.
Under `winter lint`, direct broken-link checks honor every file or directory in `WINTER_LINT_PATHS`; orphan detection
runs separately against each selected path that is itself a repository/worktree directory root. A changed-file-only
scope cannot establish a whole repository without widening contributed-lint scope, so it checks direct routing links and
emits no orphan findings. The lint never substitutes or scans an unrelated `WINTER_WORKSPACE_DIR`; that variable is only
the reporting and workspace-identity base.

## `lint_markdown_style.py` — mechanical format and structure

Runs two external tools over each in-scope repo and re-emits their output as findings, so the shape layer the three
semantic lints deliberately ignore is gated too:

| Tool                                      | Config        | Check id          | Covers                                                                                                                                                                                      |
| ----------------------------------------- | ------------- | ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [`dprint`](https://dprint.dev/)           | `dprint.json` | `markdown-format` | One canonical rendering per file — 120-column wrap, `-` list markers, `*` emphasis, aligned tables. `dprint fmt` writes the fix.                                                            |
| [`rumdl`](https://github.com/rvben/rumdl) | `.rumdl.toml` | `markdown-lint`   | The structural rules a formatter cannot decide — a fence missing its language, a heading without its blank line, a dead relative link. `rumdl check . --fix` covers the autofixable subset. |

**The two config files are the opt-in.** A repo joins the gate by committing them; a repo carrying neither is silently
out of scope, and a repo may adopt one tool without the other. That is what lets the check ship from here and still
travel to a consumer that has not adopted the style. The ecosystem repos carrying both today: `winter`, `winter-canon`,
`winter-docs`, `winter-harness`, `winter-service-docker`, `winter-service-tmux`, `winter-workflow`.

Both tools honor `.gitignore`, so vendored trees (`node_modules/`, `.venv/`, `dist/`) need no exclusion. What *does*
need excluding is a deliberate-violation fixture directory — reflowing one rewrites the shapes its assertions pin — so
each repo's configs exclude its own (`excludes` in `dprint.json`, `exclude` in `.rumdl.toml`).

Two behaviors worth knowing:

- **A missing binary is a `warn`, not a `fail`** — one per repo, naming the install command. A machine without the tools
  sees the gap named instead of the whole lint run going red on an install problem.
- **Each tool always runs over the whole repo root**, then the findings are filtered to the selected files. Only a
  root-level run honors the tools' own exclusion lists, so this keeps a `--changed` run from reporting an excluded
  fixture that happens to have changed.

## Running them

Standalone against any checkout:

```bash
python3 agent-context/scripts/lint_path_notation.py --repo /path/to/checkout
python3 agent-context/scripts/lint_doc_references.py --repo /path/to/checkout --orphan-severity off
python3 agent-context/scripts/lint_link_anchors.py --repo /path/to/checkout
python3 agent-context/scripts/lint_markdown_style.py --repo /path/to/checkout
```

The style check is also the two tools directly, run from the checkout root — the form to reach for while fixing, since
one of them writes the fix:

```bash
dprint check          # dprint fmt to apply
rumdl check .         # rumdl check . --fix for the autofixable subset
```

All four are contributed to `winter lint` from this extension's `winter-ext.toml` `lint` field (a list, so each check
ships as its own script):

```toml
lint = [
    "agent-context/scripts/lint_path_notation.py",
    "agent-context/scripts/lint_doc_references.py",
    "agent-context/scripts/lint_link_anchors.py",
    "agent-context/scripts/lint_markdown_style.py",
]
```

The dispatcher runs each over the selected scope with the standard lint env (`WINTER_LINT_PATHS`,
`WINTER_WORKSPACE_DIR`, cwd at the workspace root) and groups their findings under the `[wh]` source. All four honor
`WINTER_LINT_PATHS`. The doc-reference lint performs whole-repo orphan analysis only when a selected path is a
repository/worktree root, and remains direct-check-only for selected files.

Directory targets walk every `*.md` beneath that target, pruning vendor directories and any nested checkout (a
subdirectory with its own `.git` is a separate repo, linted on its own). File targets check only that file.

## Maintaining the scripts

The scripts in [`./scripts/`](./scripts/) follow the service-class tier — plain concrete classes with constructor
injection, no `I`-prefix Protocols or DI container
([`../architecture/service-architecture.md`](../architecture/service-architecture.md)); the code itself is the reference
for their shape. Their stdlib `unittest` suites, driven by deliberate-violation fixtures under
[`./scripts/fixtures/`](./scripts/fixtures/) so the whole `scripts/` directory travels to any consumer intact, run
standalone:

```bash
cd agent-context/scripts && python3 -m unittest discover
```

`test_doclint.py` covers the three semantic lints against those fixtures; `test_markdown_style.py` covers the style
check by putting stub `dprint` / `rumdl` executables on `PATH`, so it needs neither tool installed.
