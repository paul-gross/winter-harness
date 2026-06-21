# Authoring a winter TUI plugin

A **winter TUI plugin** extends the `winter` dashboard from outside the CLI's own source tree — it contributes dashboard badges, TUI screens, and keybound actions. (Distinct from a **winter extension**, which integrates with the *workspace* via `winter-ext.toml` lifecycle hooks; an extension may ship a TUI plugin alongside its hooks — `winter-service-tmux` does both.)

The contract a plugin codes against is the **`winter-plugin-api`** package ([github.com/paul-gross/winter-plugin-api](https://github.com/paul-gross/winter-plugin-api)) — a narrow, semver-versioned, typed surface with **zero dependency on winter-cli**. A plugin imports its entire contribution surface from `winter_plugin_api` and typechecks `create_plugin() -> IWinterPlugin` in its own repo. winter-cli keeps its own runtime copy of the seam (`winter:/tools/winter-cli/src/winter_cli/plugins/types.py`, enforced by `loader.py`) and is kept in sync with the package by hand (see [Versioning](#versioning)). Worked example: `winter-service-tmux:/plugin.py` — a single-file plugin that paints a tmux-session badge on each feature-env header (it ships in-tree and imports winter-cli directly rather than depending on the package).

## Depending on the package

Add `winter-plugin-api` as a **dev dependency** pinned to a tag, then import the contract directly:

```toml
# pyproject.toml
[dependency-groups]
dev = [
    "winter-plugin-api @ git+https://github.com/paul-gross/winter-plugin-api@v0.1.0",
]
```

```python
from winter_plugin_api import IWinterPlugin, PluginRegistration, IEnvironmentStatusView
```

It is a **dev/test** dependency, not a runtime one: winter supplies the contract in its own process when it loads your `plugin.py` (winter runs winter-cli via `uv run`, so the package is present). You pin it only so your own typechecker resolves the imports — which is why the old lazy-`import`-inside-`register()` workaround is no longer needed. Pin the **lowest** version exposing every name you use, so your plugin stays loadable against the widest range of winter builds.

## The `create_plugin()` discovery contract

The loader imports a module named **`plugin.py`** and calls its module-level **`create_plugin()`** factory, which must return an object satisfying `IWinterPlugin`. Three sources are searched, **first wins on name collision**:

1. **Workspace-local** — `<workspace>/.winter/plugins/<name>/plugin.py`
2. **User-global** — `~/.config/winter/plugins/<name>/plugin.py`
3. **Installed extensions** — `<standalone_repo>/plugin.py`, so an extension ships its dashboard plugin alongside its `winter-ext.toml` hooks without the user copying anything into `.winter/plugins/`.

A `config.toml` sitting next to `plugin.py` is parsed and passed to `register(config)`; absent or unparseable, `register` receives `{}`.

A plugin that has no `create_plugin()`, or whose `create_plugin()` / `register()` raises, is **logged and skipped** — a buggy plugin never takes the CLI offline. Author defensively: a decorator that raises blanks out its dashboard cell for every refresh, so catch and degrade (see the worked example's `except` returning a "stopped" badge).

## `IWinterPlugin`

All Protocols below are imported from `winter_plugin_api`; the behavioral ones are `@runtime_checkable`; snippets show the signatures only.

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
| `detail_panels` | `list[IDetailPanel]` | named info panels in the detail screen (tabs) |
| `tui_screens` | `list[Any]` | full dashboard screens |
| `tui_actions` | `list[TuiAction]` | keybound actions, scoped via `ActionScope` |
| `metadata` | `dict` | free-form plugin metadata |
| `commands` | `list[click.Command]` | reserved — the loader collects these, but `cli.py` does not attach them, so plugin subcommands do not run today |

`commands` is part of the dataclass but is **not wired**: click resolves the subcommand before the plugin registry is built (the registry is constructed inside the `_cli_group` callback). Wiring it means building the registry at group-construction time. Until then, ship behavior through the dashboard surfaces above.

A `TuiAction.key` is the action's **default** binding only: users can remap it from `.winter/config.toml` under `[keybindings.bindings]` via the action id `plugin.<name>` (where `<name>` is your `TuiAction.name`), and may even bind it to a multi-key chord. Pick a sensible single-key default and keep `name` stable — it is the user-facing config id. Set `key` as a raw Textual key token (`"e"`, `"ctrl+e"`, `"enter"`); the config-override grammar is documented in `workspace:/ai/winter-cli/usage/dashboard.md#keybindings`.

## Decorator Protocols

Both are `__call__(status, path) -> None` callables that **mutate** the status object's `extensions` dict in place; whatever you store there is appended to the rendered cell verbatim, joined by spaces. The `status` payload is a **narrow read-only view**, not winter-cli's concrete model — you can read the view's properties and write its `extensions`, and the typechecker rejects anything off-contract.

```python
class IWorktreeRepoDecorator(Protocol):
    def __call__(self, repo_status: IWorktreeRepoStatusView, repo_path: Path) -> None: ...

class IEnvironmentDecorator(Protocol):
    def __call__(self, env_status: IEnvironmentStatusView, env_path: Path) -> None: ...
```

- `IWorktreeRepoDecorator` fires **once per repo per refresh**; write `repo_status.extensions[<key>] = <value>` for a per-repo badge. The view exposes `worktree` (an `IFeatureWorktreeView`), `branch`, `ahead`, `behind`, `dirty_count`, and the writable `extensions`.
- `IEnvironmentDecorator` fires **once per environment per refresh**; write `env_status.extensions[<key>] = <value>` for a badge in the env's matrix-grid column header and detail-screen header. The view exposes `environment` (an `IEnvironmentView`, with `.name`, `.index`, `.path`, and `.workspace`) and the writable `extensions`.

Keep the `<key>` short and plugin-unique (the worked example uses `"wst"`).

### The view Protocols

Decorator and panel payloads are typed as **view Protocols** — narrow, read-only windows onto winter-cli's domain and status models. They expose only what a plugin may read, so the package needs no dependency on winter-cli and a model rename can't quietly change what you receive:

| View | Exposes |
|------|---------|
| `IWorkspaceView` | `root_path`, `session_prefix`, `main_branch` |
| `IEnvironmentView` | `name`, `index`, `path`, `workspace: IWorkspaceView` |
| `IProjectRepositoryView` | `name` |
| `IFeatureWorktreeView` | `path`, `repository: IProjectRepositoryView`, `environment: IEnvironmentView`, `workspace: IWorkspaceView` |
| `IStandaloneRepositoryView` | `name`, `path` |
| `IEnvironmentWorktreesView` | `environment: IEnvironmentView`, `worktrees: Sequence[IFeatureWorktreeView]` |
| `IEnvironmentStatusView` | `environment: IEnvironmentView`, writable `extensions: dict[str, str]` |
| `IWorktreeRepoStatusView` | `worktree: IFeatureWorktreeView`, `branch`, `ahead`, `behind`, `dirty_count`, writable `extensions: dict[str, object]` |

## Keybound actions (`TuiAction`)

A `TuiAction` binds a key to a handler that runs against a **dashboard area**. Declare the area(s) it applies to with `scope`; winter routes the keypress to the focused area and hands your handler the selection there.

```python
@dataclasses.dataclass
class TuiAction:
    name: str                                    # stable id -> `plugin.<name>`
    scope: ActionScope | Sequence[ActionScope]   # one area, or several
    key: str                                     # default keybinding
    description: str                             # footer label
    handler: Callable[[ActionInvocation], None]
```

`ActionScope` names the four areas a key can fire in, each with the selection context your handler receives for it:

| Scope | Area | Selection context |
|-------|------|-------------------|
| `workspace` | the workspace as a whole | `WorkspaceContext` |
| `feature_environment` | a feature env (alpha, beta, …) | `FeatureEnvironmentContext` |
| `feature_worktree` | one repo worktree within an env | `FeatureWorktreeContext` |
| `standalone_repository` | a standalone repo in the standalone panel | `StandaloneRepoContext` |

### One command across several areas, one key

`scope` accepts a **single** `ActionScope` or a **sequence** of them. Pass several to make one command — one `name`, one `action_id` (`plugin.<name>`), one key — work in multiple areas. The areas never hold focus simultaneously, so the same key in each is unambiguous; winter dispatches to whichever area is focused. Two same-key plugin actions collide only when their declared areas **overlap** — disjoint areas (e.g. one `standalone_repository`, one `feature_worktree`) coexist on the same key, and a single multi-scope action never collides with itself. A plugin key also collides with any **built-in** action bound to the same key, regardless of area — this is the more common real-world conflict when picking a default `key`, so consult the built-in action table in `workspace:/ai/winter-cli/usage/dashboard.md#keybindings` before committing to a default.
The workspace screen routes a multi-scope action to the **focused area** (standalone panel vs. feature grid); the detail screens (worktree detail, standalone detail) route to the **most-specific declared scope** they can host — so a `[feature_worktree, standalone_repository]` action fires with a `FeatureWorktreeContext` on the worktree detail screen and with a `StandaloneRepoContext` on the standalone detail screen, regardless of what is focused.

```python
TuiAction(
    name="codediff",
    scope=[ActionScope.standalone_repository, ActionScope.feature_worktree],
    key="d",
    description="Open diff",
    handler=on_diff,
)
```

### The handler receives an `ActionInvocation`

Your handler is called with an `ActionInvocation`, not a bare context:

```python
@dataclasses.dataclass
class ActionInvocation:
    scope: ActionScope       # which area the key was pressed in
    context: ActionContext   # that area's selection (one of the *Context types above)
```

Read `inv.scope` to branch on **where** the key fired, and `inv.context` for the selection. Attribute access falls through to the inner context, so `inv.repo` / `inv.worktree` / `inv.suspend` resolve directly — a single-area handler written against the bare context keeps working unchanged.
Prefer `inv.context.repo` / `inv.context.worktree` for type-checked access: pyright can verify the field exists on the concrete `*Context` type, whereas `inv.repo` goes through `__getattr__` and is typed as `Any`, so your own typecheck stops being a meaningful gate.

```python
def on_diff(inv: ActionInvocation) -> None:
    if inv.scope is ActionScope.standalone_repository:
        repo = inv.context.repo                  # IStandaloneRepositoryView (or inv.repo)
    else:
        repo = inv.context.worktree.repository   # the focused worktree's repository view
    ...
```

### What each context carries

The selection context exposes everything winter already loaded for that area at dispatch — so an env-wide action never has to re-derive the repo set by scanning `env.path` or parsing `.winter/config.toml`. Each model field is a **view**, not a concrete winter-cli model:

| Context | Fields |
|---------|--------|
| `WorkspaceContext` | `workspace: IWorkspaceView` |
| `FeatureEnvironmentContext` | `environment: IEnvironmentView`; `worktrees: Sequence[IFeatureWorktreeView]` — every project-repo worktree in the env (each carries `path`, `repository.name`, and `environment`/`workspace` handles) |
| `FeatureWorktreeContext` | `worktree: IFeatureWorktreeView`; `environment_worktrees: IEnvironmentWorktreesView \| None` — the env's sibling worktrees (`.environment` + `.worktrees`), so a worktree cell can drive an env-wide action; `workspace: IWorkspaceView \| None` — explicit handle (also reachable via `worktree.workspace`) |
| `StandaloneRepoContext` | `repo: IStandaloneRepositoryView` |

Every context also carries an optional `suspend` (a context manager that pauses the TUI while a handler shells out). The `worktrees` / `environment_worktrees` / `workspace` fields are **additive** — older plugins that ignore them are unaffected. Use them to act across the whole feature env without extra git or filesystem I/O:

```python
def on_diff_all(inv: ActionInvocation) -> None:
    if inv.scope is ActionScope.feature_environment:
        worktrees = inv.context.worktrees                       # env-scoped: the full set
    else:
        siblings = inv.context.environment_worktrees            # worktree-scoped: reach env-wide
        worktrees = siblings.worktrees if siblings else [inv.context.worktree]
    paths = [str(wt.path) for wt in worktrees]                  # each repo's worktree path
    ...
```

`environment_worktrees` and `workspace` are typed `| None` so a context can be hand-constructed in a test without them, but the dashboard always populates them when it dispatches a real keypress.

## Detail panels (`IDetailPanel`)

Decorators contribute terse badge *strings*; a **detail panel** contributes a whole named pane of read-only info in the detail screen, surfaced as a tab alongside the built-in repo info. The same panels render in **both** the feature-environment detail view (`WorktreeDetailScreen`) and the standalone-repo detail view (`StandaloneDetailScreen`).

```python
class IDetailPanel(Protocol):
    name: str   # stable identifier
    title: str  # tab label
    def render(self, context: DetailPanelContext) -> object: ...
```

`render` is called on each detail refresh and returns **rich-console markup** (a `str`) or any Rich renderable — that becomes the panel body. It is handed a `DetailPanelContext` describing the focused repo the screen is showing — the focused worktree in a feature-env view, the standalone repo in a standalone view. Its fields are **views**, not concrete models:

```python
@dataclasses.dataclass
class DetailPanelContext:
    worktree: IFeatureWorktreeView | None = None   # set in a feature-env detail view
    repo: IStandaloneRepositoryView | None = None  # set in a standalone detail view
```

Exactly one field is set. Branch on whichever you need; treat it as read-only.

Two behaviors the screen guarantees, so author to them:

- **Error isolation** — a panel whose `render` raises shows an error state in *its* tab only; the rest of the screen keeps rendering (same contract as a decorator that raises). You still want to catch and degrade for a useful message rather than a stack-trace string.
- **No empty tab bar** — with zero contributed panels the detail screen renders exactly the built-in info (no tabs). Tabs appear only once at least one panel is registered.

`render` runs on the dashboard's refresh worker thread and must not touch Textual widgets — return a renderable and let the screen mount it.

## Versioning

The contract is **semver-versioned in the `winter-plugin-api` package**, independent of winter-cli's *unversioned* internal model. That separation is the whole point: winter-cli's domain model evolves freely; only the narrow seam carries a version.

- **Major bump** — a breaking change: a removed/renamed public name, a narrowed view, a changed `__call__` / `register` signature, a removed dataclass field. Update your plugin before moving to the new major.
- **Minor bump** — a backward-compatible addition: a new view property, a new optional `PluginRegistration` field, a new decorator/panel Protocol, a new `ActionScope` member. Existing plugins keep working. (Pre-1.0, treat a `0.x` minor as potentially breaking.)
- **Patch bump** — docs / typing-only, no surface change.

winter-cli keeps its **own runtime copy** of the seam (`plugins/types.py`); the package is a deliberate hand-curated copy of it, not a re-export. The two are **kept in sync by hand**: a seam rename in winter-cli must be mirrored into the package as a major bump and reflected here, in the same change. There is no automated conformance check wiring the two together today — pinning winter-cli to the package with conformance sentinels (the `../standards/protocol-conformance.md` pattern), so a model rename would fail winter-cli's own typecheck, is a possible future addition.

## See also

- [github.com/paul-gross/winter-plugin-api](https://github.com/paul-gross/winter-plugin-api) — the contract package: `views` (read-only view Protocols) and `seam` (the dataclasses/Protocols a plugin constructs), plus the full versioning policy.
- `winter-service-tmux:/plugin.py` — the canonical single-file worked example (an in-tree extension that imports winter-cli directly; an external plugin would import `winter_plugin_api` instead).
- `winter:/tools/winter-cli/src/winter_cli/plugins/types.py` — winter-cli's runtime copy of the seam; `loader.py` (same dir) — discovery and the load-and-skip-on-error behavior.
- `../standards/protocol-conformance.md` — the conformance-sentinel pattern that could pin winter-cli's models and seam against the package (a possible future addition; not wired today).
