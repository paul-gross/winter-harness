# Authoring a winter TUI plugin

A **winter TUI plugin** extends the `winter` dashboard from outside the CLI's own source tree — it contributes dashboard badges, TUI screens, and keybound actions. (Distinct from a **winter extension**, which integrates with the *workspace* via `winter-ext.toml` lifecycle hooks; an extension may ship a TUI plugin alongside its hooks — `winter-service-tmux` does both.) The contract lives in `winter:tools/winter-cli/src/winter_cli/plugins/types.py` (the Protocols and the registration dataclass) and is enforced by the loader at `winter:tools/winter-cli/src/winter_cli/plugins/loader.py`. Worked example: `winter-service-tmux:/plugin.py` — a single-file plugin that paints a tmux-session badge on each feature-env header.

## The `create_plugin()` discovery contract

The loader imports a module named **`plugin.py`** and calls its module-level **`create_plugin()`** factory, which must return an object satisfying `IWinterPlugin`. Three sources are searched, **first wins on name collision**:

1. **Workspace-local** — `<workspace>/.winter/plugins/<name>/plugin.py`
2. **User-global** — `~/.config/winter/plugins/<name>/plugin.py`
3. **Installed extensions** — `<standalone_repo>/plugin.py`, so an extension ships its dashboard plugin alongside its `winter-ext.toml` hooks without the user copying anything into `.winter/plugins/`.

A `config.toml` sitting next to `plugin.py` is parsed and passed to `register(config)`; absent or unparseable, `register` receives `{}`.

A plugin that has no `create_plugin()`, or whose `create_plugin()` / `register()` raises, is **logged and skipped** — a buggy plugin never takes the CLI offline. Author defensively: a decorator that raises blanks out its dashboard cell for every refresh, so catch and degrade (see the worked example's `except` returning a "stopped" badge).

## `IWinterPlugin`

All three Protocols below are `@runtime_checkable`; snippets show the signatures only.

```python
class IWinterPlugin(Protocol):
    name: str
    def register(self, config: object) -> PluginRegistration: ...
```

`name` should match the directory/extension name the loader discovered it under. `register` is called once at discovery; do all contribution wiring there and return a `PluginRegistration`.

## `PluginRegistration`

Every field defaults empty — populate only what the plugin contributes:

| Field | Type | Contributes |
|-------|------|-------------|
| `worktree_repo_decorators` | `list[IWorktreeRepoDecorator]` | badges on a repo's dashboard status row |
| `environment_decorators` | `list[IEnvironmentDecorator]` | badges on a feature-env header |
| `tui_screens` | `list[Any]` | full dashboard screens |
| `tui_actions` | `list[TuiAction]` | keybound actions, scoped via `ActionScope` |
| `metadata` | `dict` | free-form plugin metadata |
| `commands` | `list[click.Command]` | reserved — the loader collects these, but `cli.py` does not attach them, so plugin subcommands do not run today |

`commands` is part of the dataclass but is **not wired**: click resolves the subcommand before the plugin registry is built (the registry is constructed inside the `_cli_group` callback). Wiring it means building the registry at group-construction time. Until then, ship behavior through the dashboard surfaces above.

## Decorator Protocols

Both are `__call__(status, path) -> None` callables that **mutate** the status object's `extensions` dict in place; whatever you store there is appended to the rendered cell verbatim, joined by spaces.

```python
class IWorktreeRepoDecorator(Protocol):
    def __call__(self, repo_status: object, repo_path: object) -> None: ...

class IEnvironmentDecorator(Protocol):
    def __call__(self, env_status: object, env_path: object) -> None: ...
```

- `IWorktreeRepoDecorator` fires **once per repo per refresh**; write `repo_status.extensions[<key>] = <value>` for a per-repo badge.
- `IEnvironmentDecorator` fires **once per environment per refresh**; write `env_status.extensions[<key>] = <value>` for a badge in the env's matrix-grid column header and detail-screen header.

Keep the `<key>` short and plugin-unique (the worked example uses `"wst"`).

## Pinned public names

These names are the plugin author's API surface — an author typechecks `create_plugin() -> IWinterPlugin` against them. Renaming any of them is a breaking change for external plugins and **must update this doc in the same change** (the analog of `python/protocol-conformance.md` pinning Protocol/adapter pairs):

`IWinterPlugin`, `PluginRegistration`, `IWorktreeRepoDecorator`, `IEnvironmentDecorator`, `TuiAction`, `ActionScope`, and the `create_plugin` / `plugin.py` discovery names.

## See also

- `winter-service-tmux:/plugin.py` — the canonical single-file worked example.
- `winter:tools/winter-cli/src/winter_cli/plugins/types.py` — the contract; `loader.py` (same dir) — discovery and the load-and-skip-on-error behavior.
- `python/protocol-conformance.md` — pinning a typed `create_plugin() -> IWinterPlugin` annotation with a conformance sentinel.
