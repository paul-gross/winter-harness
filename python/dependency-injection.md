# Dependency injection

Dependency injection (DI) is the mechanism we use to achieve the **Dependency Inversion Principle**. By injecting dependencies at construction time rather than instantiating them inside a class, modules end up depending on abstractions (interfaces, domain objects, typed configs) rather than on concrete implementations or low-level schemas. The rules below — singletons via DI, per-call values via method args, no whole-config injection — all flow from that goal.

## Rule

- DI for ambient singletons (the workspace, services, factories).
- Method args for per-call values (a specific repo, env, worktree).
- **App config stays at the app level.** Modules don't see `WorkspaceConfig`. The app derives module-scoped state — domain objects like `Workspace`, or module-specific config dataclasses — and injects those.

## Why: dependency inversion

Whole-config injection is a textbook violation of the Dependency Inversion Principle: high-level modules end up depending on the low-level app config schema. Adding a field to the TOML schema implicitly affects every service that reads `self._config`, and you can't tell from a service's constructor what it actually consumes.

The right shape inverts the dependency:

- **The module declares what it needs** — typically a domain object (`Workspace`) or a small typed dataclass containing just the fields it uses.
- **The app conforms to the module's contract** — it derives those values from app config and passes them in at construction time.

Now the module doesn't know `WorkspaceConfig` exists. It can be extracted, tested with a hand-rolled `Workspace`, or reused in another app, without dragging the TOML schema along. The dependency arrow points app → module, not module → app.

## Layers

```
TOML on disk
   ↓ parse
WorkspaceConfig          app config — schema-shaped, lives at app boundary
   ↓ derive
Workspace                domain object — workspace-wide values needed by many modules
   ↓ inject
InitService, ...         modules consume domain objects / module configs
```

Each layer's job:

- **App config** (`WorkspaceConfig`) — schema for the TOML file. Read once at startup by services whose job *is* parsing/loading. After that, hidden behind domain objects.
- **Domain objects / module configs** (`Workspace`, plus future `BlizzardSettings`, etc.) — runtime-shaped, typed, scoped to what modules actually need. Multiple modules can share one (`Workspace`) or each can get its own.
- **Modules** — declare dependencies on domain objects / module configs in their constructor. They don't reach back to app config.

## Do

```python
def __init__(
    self,
    repo_factory: RepositoryFactory,
    repo_repo: WriteRepoRepository,
    workspace: Workspace,
) -> None:
    self._workspace = workspace
    ...

def _apply_identity(self, repo_path: Path) -> None:
    if identity := self._workspace.git_identity:
        self._repo_repo.set_identity(repo_path, identity)
```

## Don't

```python
def __init__(self, config: WorkspaceConfig, ...) -> None:
    self._config = config


def _apply_identity(self, repo_path):
    identity = self._config.git_identity  # reaches into the app schema
    ...
    # This service now "depends on" the entire WorkspaceConfig type, even
    # though it only reads one field. Dependency arrow points the wrong way.
```

## When app config IS the right injection

Two narrow categories legitimately consume `WorkspaceConfig` directly:

1. **Adapter / loader services** that exist specifically to translate app config into runtime types — e.g. `RepositoryFactory` building `ProjectRepository` instances from `[[project_repository]]` entries, or the service that constructs `Workspace` from `WorkspaceConfig`. Translation is their entire job.
2. **Workspace-lifecycle services** that reconcile the whole workspace against the config — e.g. `InitService`, `DestroyService`, `PruneService`, and the `Extension*Service` family. They read several cross-cutting fields (`workspace_root`, `git_identity`, `git_excludes`, `adopt_extensions`, the full `[[project_repository]]` and `[[standalone_repository]]` lists) and walk every declared repo. A small dataclass would either duplicate the schema or omit fields the next reconcile step needs.

Everything else — handlers, per-feature services, status services — consumes domain objects (`Workspace`, `ProjectRepository`, `FeatureWorktree`) only. The smell to watch for is a service taking `WorkspaceConfig` but only reading one or two scalar fields; that one should declare a typed dataclass.
