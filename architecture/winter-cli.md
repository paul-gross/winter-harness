# winter-cli architecture

The architecture of the real `winter` (winter-cli) codebase — how the generic conventions in `../python/*.md` are realized here, plus the CLI's own argument conventions. Read this before adding or modifying a `winter` subcommand, so you build with the existing structure instead of reverse-engineering it.

This is a **reference**, not a CLAUDE.md — it is not auto-loaded. Open it on demand from `winter-harness:/architecture/winter-cli.md` (reached via `architecture/index.md`).

## Layout

```
src/winter_cli/
├── cli.py                 # click entry point — wires subcommand groups
├── cli_context.py         # shared CLI context object
├── container.py           # DI container — binds Protocol seams to concrete adapters
├── config/                # config loading (.winter/config.toml + config.local.toml)
├── core/                  # cross-cutting Protocol seams (≥2-feature usage)
│   ├── cli_output_service.py            # ICliOutputService — TUI/CLI output abstraction
│   ├── cli_input_validation_service.py  # ICliInputValidationService — click-bound validators
│   ├── config_file.py                   # IConfigFileReader — TOML loader seam
│   ├── filesystem.py                    # IFilesystem — file/dir read/write seam
│   ├── subprocess_runner.py             # ISubprocessRunner — process execution seam
│   └── internal/                        # adapters for the core Protocols
├── modules/               # feature packages
│   ├── workspace/         # everything reachable from `winter ws *` and `winter repo *`
│   │   ├── command.py             # click commands — thin wrappers over handlers
│   │   ├── handlers/              # CLI-shaped output formatting + arg parsing
│   │   │   ├── init_handler.py        # `winter ws init`
│   │   │   ├── destroy_handler.py     # `winter ws destroy`
│   │   │   ├── workspace_handler.py   # `winter ws {list,status,connect,disconnect,checkout,fetch,pull,push,prune,index,diff}`
│   │   │   └── repo_handler.py        # `winter repo {list,add,remove}`
│   │   ├── *_service.py           # domain orchestration (init / destroy / workspace (omnibus) / prune)
│   │   ├── *_reporter.py          # stream / json reporters for lifecycle events
│   │   ├── reporter_factory.py    # picks stream-vs-json reporter from --json flag
│   │   ├── repository_factory.py  # builds per-repo IWriteRepoRepository instances
│   │   ├── models/                # domain + service models (enums, dataclasses)
│   │   ├── repo_repository.py     # IReadRepoRepository / IWriteRepoRepository (Protocols)
│   │   ├── workspace_repository.py # IReadWorkspaceRepository (Protocol)
│   │   └── internal/              # concrete adapters: git_ops_service, gitpython_repository, repo_error_factory, …
│   └── tui/               # textual-based dashboard (`winter dashboard`)
├── plugins/               # plugin loader — discovers extension click commands + TUI plugins
└── util.py
tests/                     # pytest; DI-friendly via injected fixtures (see tests/conftest.py)
```

The layout instantiates the `winter-harness:/python/*.md` rules at once:

- **`python/service-architecture.md`** — behavior lives in injected service classes (`*_service.py`), not module-level free functions; the other three rules below are facets of this one.
- **`python/repository-pattern.md`** — `git`, `subprocess`, and other I/O libraries are confined to `modules/<feature>/internal/*.py` (and `core/internal/` for cross-cutting seams like `local_subprocess_runner.py`). The Protocol surface (`repo_repository.py`, `workspace_repository.py`) imports nothing from those libraries.
- **`python/dependency-injection.md`** — every service receives its collaborators via constructor injection; everything is wired in `container.py`.
- **`python/module-layout.md`** — Protocols at the feature root, adapters in `internal/`, cross-cutting Protocols in `core/`. Handlers may live as a flat `handler.py` or as a `handlers/` subpackage once the feature grows past one CLI surface (see [Handlers: flat vs. subpackage](#handlers-flat-vs-subpackage) below).
- **`python/error-handling.md`** — library exceptions are wrapped at the call site via an injected concrete `RepoErrorFactory`, never via ad-hoc `raise X from Y`.

## Handlers: flat vs. subpackage

`modules/workspace/` outgrew a single `handler.py` and split into a `handlers/` subpackage organized by CLI surface (init, destroy, the workspace omnibus, repo). The split rule: keep a flat `handler.py` while a feature has one cohesive handler; promote to `handlers/<surface>_handler.py` files when distinct CLI surfaces start sharing little code. Re-export the handler classes from `handlers/__init__.py` so callers import from the subpackage root.

`python/module-layout.md` shows the flat form as the default. This exemplar is the canonical reference for the split form.

## Argument conventions

Read this before designing a new command's signature — the existing `winter ws` family is uniform, and a new command joins it.

**Target selection is a positional, segment-aware glob `PATTERN` over `<env>/<repo>`.** Every command that acts on worktrees (`status`, `pull`, `push`, `merge`, `fetch`, `diff`, …) takes its targets as positional `PATTERNS`, not a flag. The glob is segment-aware: `*` does not cross `/`, and a bare env name with no `/` is treated as `<env>/*`.

```
winter ws status                 # all environments
winter ws status alpha           # alpha's worktrees (== alpha/*)
winter ws status alpha/winter    # one specific worktree
winter ws status '*/winter'      # every env's winter worktree
winter ws status '*/*'           # every env's every worktree (explicit)
```

A new command that selects worktrees **reuses this positional `PATTERNS` form** — it does not introduce a `--env NAME` or `--name` flag for a target the positional pattern already expresses. The pattern already covers single-env, single-worktree, and cross-env selection; a parallel flag fractures the surface and can't express `*/winter`. Match `winter ws status` / `winter ws pull` (`[PATTERNS]...`, defaulting to all) for read-shaped commands; match `winter ws merge` (a leading required positional like `SOURCE_REF`, then `[PATTERNS]...` with no implicit "all" default) when an action needs an explicit target.

Reserve `--flags` for *modifiers* on the selected set, not for selection itself — `--json`, `--standalone`, `--all`, `--exclude-pinned`, `--rebase`. The positional answers *which worktrees*; flags answer *how to act on them*.

## Adding a new `winter ws foo` subcommand

Follow this order — each step builds on the previous:

1. **click command** in `modules/workspace/command.py` — thin wrapper that parses click args and calls a handler.
2. **Handler** in `modules/workspace/handlers/<surface>_handler.py` (or a new `foo_handler.py` if `foo` is its own surface) — receives parsed args, calls a service, renders output via `ICliOutputService` (or returns structured JSON for `--json`).
3. **Service** — either extend `WorkspaceService` for read-shaped or env-spanning operations, or add `modules/workspace/foo_service.py` for a top-level lifecycle action (like `init` and `destroy`). Behavior goes in the service class, not module-level free functions — see `python/service-architecture.md` (enforced by `tests/conventions/test_service_based_behavior.py`). Services depend on Protocols, not concretes.
4. **New I/O seam** (only if needed) — Protocol at `modules/workspace/<seam>.py`, concrete adapter at `modules/workspace/internal/<seam>.py`. Apply the I-prefix rule (enforced by `tests/conventions/test_protocol_naming.py`).
5. **Bind** the service and any new adapters in `container.py`. Services consume domain objects, not `WorkspaceConfig` directly — see `python/dependency-injection.md` for the carve-outs (enforced by `tests/conventions/test_no_whole_config_injection.py`).
6. **Unit test** under `tests/modules/workspace/` (service tests) or `tests/modules/workspace/internal/` (adapter tests) — inject fakes for the Protocols. See `tests/modules/workspace/internal/test_git_ops_service.py` and `tests/modules/workspace/internal/test_write_repo_repository.py` for the fixture pattern.
7. **Surface the new command** in the docs so agents discover it from the docs, not from `--help`. Start at the usage index `workspace:/ai/winter-cli/usage/index.md` and follow it to the right per-topic file — for a `winter ws` subcommand that's its own file under `workspace:/ai/winter-cli/usage/ws/` (e.g. `usage/ws/checkout.md`), added to the `winter ws` hub's command table. If it's a whole new topic, add the file under `usage/` and a row routing to it from `usage/index.md`.

## Startup latency: lazy imports

`winter` is invoked per-command (e.g. the editor's worktrees picker shells out to `winter ws worktrees --json`), so import cost on the hot path is felt directly. Two seams keep the cold imports off the `winter ws` path; respect both when adding commands.

- **`LazyGroup` (cli.py).** The root group is a `LazyGroup` whose `_LAZY_SUBCOMMANDS` maps each top-level command name to a `"module:attribute"` reference, imported only when that command is dispatched (`--help` still lists them all without importing). **Adding a new top-level command** (a sibling of `ws` / `doctor` / `dashboard`, not a `winter ws foo` subcommand) means adding an entry here — don't `add_command` an eagerly-imported object.
- **`_lazy()` providers (container.py).** The DI `Container` is built on *every* invocation, so a module-top `import` of a command-specific tree (the `doctor`, `lint`, and `tui`/textual trees) would load it for `winter ws` too. Those providers use `providers.Factory(_lazy("module:Class"), ...)`, which imports the class on first resolution instead. **When binding a provider whose class drags in a heavy tree only one command needs**, wrap it in `_lazy(...)` rather than importing at the top; the workspace/core seams that `ws` itself needs stay eagerly imported.

`cli.py` also sets `sys.pycache_prefix` (a per-user cache dir) instead of `sys.dont_write_bytecode = True`, so the core package keeps a warm `.pyc` cache across runs while plugin extension source trees stay free of `__pycache__/`. The ordering — set before importing `click` / `winter_cli.*` — is load-bearing (hence the `E402` ignore for `cli.py`).

## Reporters as lifecycle event sinks

Services don't print. They emit lifecycle events to an injected reporter Protocol. Three reporter Protocols exist today:

- `IInitReporter` — used by both `winter ws init` and `winter ws destroy` (the destroy action vocabulary fits the init event shape).
- `IFetchReporter` — used by `winter ws fetch`.
- `IPullReporter` — used by `winter ws pull` and `winter ws push`.

For each Protocol there is a `Stream*Reporter` (human output) and `Json*Reporter` (`--json` mode). `ReporterFactory` picks one based on the `--json` flag.

When adding a new lifecycle action, **extend an existing reporter's event vocabulary first** — don't fork a new reporter Protocol unless the events truly don't overlap with init/fetch/pull. The `IInitReporter` reuse for destroy is the precedent.

## Testing pattern

Full testing conventions — directory layout, conftest scoping, fake-vs-mock guidance, and per-layer assertion patterns — live in `python/testing.md`. The winter-cli tree under `tests/` is its working reference; start at `tests/conftest.py` and `tests/modules/workspace/test_init_service.py`.

## Network resilience

`GitOpsService` wraps every `git fetch` / `pull` / `push` and retries up to 3 times with jittered exponential backoff when the stderr matches a transient pattern:

```
Connection closed by ... port 22
kex_exchange_identification
remote end hung up
Connection timed out
```

Anything else is a hard failure on the first attempt. `is_transient_git_error` in `modules/workspace/internal/git_ops_service.py` is the source of truth for the substring list — extend it there when a new transient class appears.

## Cross-references

- Conventions this codebase instantiates: `python/service-architecture.md`, `python/dependency-injection.md`, `python/repository-pattern.md`, `python/error-handling.md`, `python/module-layout.md`.
- Repository-pattern reference implementation: `exemplars/python/repo_pattern.py`.
- User-facing CLI command reference (hub): `workspace:/ai/winter-cli/index.md`.
- Installation + extension hook contract: `workspace:/ai/winter-cli/setup.md`.
