# Worked example: the `winter` CLI

A guided tour of how the generic conventions in `python/*.md` get applied in the real `winter` (winter-cli) codebase. Read this when you're about to add or modify a `winter` subcommand and want to see the conventions in situ before diving in.

This is a **reference**, not a CLAUDE.md — it is not auto-loaded. Open it on demand from `winter-harness:/exemplars/python/cli-architecture.md`.

## Layout

```
src/winter_cli/
├── cli.py                 # click entry point — wires subcommand groups
├── cli_context.py         # shared CLI context object
├── container.py           # DI container — binds Protocol seams to concrete adapters
├── config/                # config loading (.winter/config.toml + config.local.toml)
├── core/                  # cross-cutting Protocol seams (≥2-feature usage)
│   ├── cli_output.py            # ICliOutputService — TUI/CLI output abstraction
│   ├── cli_input_validation.py  # ICliInputValidationService — click-bound validators
│   └── internal/                # adapters for the core Protocols
├── modules/               # feature packages
│   └── workspace/         # everything reachable from `winter ws *`
│       ├── command.py          # click commands — thin wrappers over handlers
│       ├── handler.py          # CLI-shaped output formatting + arg parsing
│       ├── *_service.py        # domain orchestration (init / destroy / sync / connect …)
│       ├── *_reporter.py       # stream / json reporters for lifecycle events
│       ├── repo_repository.py  # IReadRepoRepository / IWriteRepoRepository (Protocols)
│       └── internal/           # concrete adapters: git_repo_repository, repo_error_factory, …
├── plugins/               # plugin loader — discovers extension click commands + TUI plugins
└── util.py
tests/                     # pytest; DI-friendly via injected fixtures
```

The layout instantiates four `winter-harness:/python/*.md` rules at once:

- **`python/repository-pattern.md`** — `git`, `subprocess`, and other I/O libraries are confined to `modules/<feature>/internal/*.py`. The Protocol surface (`repo_repository.py` at the feature root) imports nothing from those libraries.
- **`python/dependency-injection.md`** — every service receives its collaborators via constructor injection; everything is wired in `container.py`.
- **`python/module-layout.md`** — Protocols at the feature root, adapters in `internal/`, cross-cutting Protocols in `core/`.
- **`python/error-handling.md`** — library exceptions are wrapped at the call site via an injected `IRepoErrorFactory`, never via ad-hoc `raise X from Y`.

## Adding a new `winter ws foo` subcommand

Follow this order — each step builds on the previous:

1. **click command** in `modules/workspace/command.py` — thin wrapper that parses click args and calls a handler.
2. **Handler** in `modules/workspace/handler.py` — receives parsed args, calls a service, renders output via `ICliOutputService` (or returns structured JSON for `--json`).
3. **Service** in `modules/workspace/foo_service.py` — domain orchestration; depends on Protocols, not concretes.
4. **New I/O seam** (only if needed) — Protocol at `modules/workspace/<seam>.py`, concrete adapter at `modules/workspace/internal/<seam>.py`. Apply the I-prefix rule.
5. **Bind** the service and any new adapters in `container.py`.
6. **Unit test** under `tests/` — inject fakes for the Protocols. See `tests/test_git_ops_service.py` and `tests/test_write_repo_repository.py` for the fixture pattern.
7. **Surface the new command** in `workspace:/ai/winter-cli/usage.md` so agents discover it from the docs, not from `--help`.

## Reporters as lifecycle event sinks

Services don't print. They emit lifecycle events to an injected reporter Protocol — `IInitReporter`, `IFetchReporter`, `IPullReporter`. Concrete reporters (`StreamReporter`, `JsonReporter`) translate those events into human or machine output.

Today the same reporter Protocol serves both `winter ws init` and `winter ws destroy` (the action vocabulary grew over time). When adding a new lifecycle action, extend the existing reporter event vocabulary — don't fork a new reporter Protocol unless the events truly don't overlap.

## Testing pattern

The fixture shape, from `tests/test_git_ops_service.py`:

- A fixture builds an `IRepoErrorFactory` (real or fake).
- A fixture builds an `IGitOpsService` (real with the factory injected, or fake).
- The service under test is constructed with the fixtures and asserted against directly.

Lift fixtures into `tests/conftest.py` as soon as a second test file needs them — don't copy them inline.

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

- Conventions this codebase instantiates: `python/dependency-injection.md`, `python/repository-pattern.md`, `python/error-handling.md`, `python/module-layout.md`.
- Repository-pattern reference implementation: `exemplars/python/repo_pattern.py`.
- User-facing CLI command reference: `workspace:/ai/winter-cli/usage.md`.
- Installation + extension hook contract: `workspace:/ai/winter-cli/setup.md`.
