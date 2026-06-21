# Service-based architecture

Winter code is **service-based**: behavior lives in service classes whose collaborators are injected at construction, reached through Protocol seams. Module-level free functions are reserved for pure, dependency-free helpers — they are the exception, not the default.

This is the principle the other Python conventions are facets of. Dependency injection (`./dependency-injection.md`) is *how* a service receives its collaborators; module layout (`./module-layout.md`) is *where* the service and its Protocol seam live; the repository pattern (`./repository-pattern.md`) is the I/O-owning service shape. Read this first — it names the shape those three assume.

## Core tenet: interchangeability

**Adapters behind a Protocol seam are interchangeable, and the seam keeps them that way.** Any code that drives a swappable backend — a service orchestrator, a git provider, a config source — depends on a **winter-defined, stable contract**: a fixed, documented set of operations and options that *winter* owns, not the backend. Swapping the adapter behind the seam must not change what callers can ask for. This is the *why* behind the protocol-seam pattern the other conventions describe: the seam exists so the thing behind it can be replaced.

**Define the contract; never pass arguments through.** A command surface over a swappable backend exposes exactly the options winter defines and maps them onto whatever adapter is plugged in. It does not forward arbitrary caller arguments down to the backend. Pass-through couples every caller to one backend's flag vocabulary — the moment a caller passes a backend-specific flag, swapping the backend breaks them, and the seam stops being a seam. The contract does exactly what winter defines, and each adapter is responsible for realizing that contract on its own terms.

- **Do.** `winter service up <env>` exposes winter's fixed action set (`up` / `down` / `status` / `restart` / `logs`); each orchestrator adapter implements those actions. A different orchestrator slots in without changing the command surface.
- **Don't.** A `winter service <action> <env> -- <raw backend args>` pass-through that forwards tmux-specific flags to the tmux adapter — callers that learned the tmux flags can't move to another orchestrator, so the orchestrators are no longer interchangeable.

The contract is the abstraction the Dependency Inversion section below depends on: callers depend on winter's operation set (the Protocol), never on a concrete backend's argument surface. See `./dependency-injection.md` for how the chosen adapter is wired and `../standards/protocol-conformance.md` for pinning each adapter to the seam it must satisfy.

## Rule

- **Behavior belongs in a class.** Anything that orchestrates collaborators — calls a repository, drives another service, picks an adapter, emits to a reporter — is a method on a service class. The class declares its collaborators in `__init__` and receives them via the container.
- **Collaborators are injected, never reached for.** A service depends on a Protocol (`IReadFooRepository`, `ICliOutputService`), not a concrete class and not a module-level singleton. It never constructs its own collaborators or imports them at module scope to call them directly.
- **Free functions are pure helpers only.** A module-level function is legitimate when it takes plain values (stdlib types, domain dataclasses) and returns a value with no injected collaborator and no I/O — `is_transient_git_error(stderr: str) -> bool`, a parsing or formatting helper, a small predicate. The moment a function needs a collaborator, it is behavior, and behavior is a service method.

## The boundary

| Stays a free function | Must be a service method |
|-----------------------|--------------------------|
| Takes only stdlib types / domain dataclasses (`ProjectRepository`, `FeatureWorktree`) | Takes or needs an injected collaborator — a Protocol seam (`IReadFooRepository`, `ICliOutputService`) or the adapter behind it |
| Pure: same inputs → same output | Performs I/O, or orchestrates multiple steps with side effects |
| No knowledge of how the app is wired | Resolved from `container.py` and depends on the Protocol seam |

The test is collaborators, not line count. A long pure transform is fine as a free function; a two-line function that calls a repository is not. A *domain dataclass* whose name ends in a role-like noun — `ProjectRepository`, `StandaloneRepository` — is a value, not a collaborator; passing one to a free function is fine.

## Why: dependency inversion

The service shape exists to serve the **Dependency Inversion Principle** — high-level behavior depends on abstractions (Protocols, domain objects), never on concretes or global state. A free function that reaches for a collaborator hard-wires that dependency: it can't be substituted at the test boundary, can't be re-pointed at a different adapter, and hides what it consumes from its signature. Lifting it into a service whose `__init__` declares the Protocol inverts the arrow — the full reasoning, and the testability / pluggability / discoverability payoffs, are in `./dependency-injection.md` and `./module-layout.md`.

## Do

```python
class SyncService:
    def __init__(self, repo_repo: IWriteRepoRepository, reporter: IPullReporter) -> None:
        self._repo_repo = repo_repo
        self._reporter = reporter

    def sync(self, repo: ProjectRepository, env: FeatureWorktree) -> None:
        self._reporter.started(repo.name)
        self._repo_repo.pull(repo, env.branch)


# Pure helper — no collaborator, stays a free function:
def is_transient_git_error(stderr: str) -> bool:
    return any(pattern in stderr for pattern in _TRANSIENT_PATTERNS)
```

## Don't

```python
# Behavior as a free function reaching for a collaborator — the procedural
# anti-pattern. Not testable without monkeypatching, not pluggable, and the
# dependency on GitPythonRepository is invisible at the call site.
def sync(repo: ProjectRepository, env: FeatureWorktree) -> None:
    repo_repo = GitPythonRepository()          # constructs its own collaborator
    repo_repo.pull(repo, env.branch)
```

## Enforcement

In winter-cli, this rule is checked at `mise run test` time by `winter:/tools/winter-cli/tests/conventions/test_service_based_behavior.py`. It flags the tractable, false-positive-free signal: a **module-level function whose parameter is annotated with an `I`-prefixed Protocol** — the form every injected collaborator takes (DI consumers depend on the Protocol seam, and the `I`-prefix is reserved for Protocols by the naming check). A free function receiving a Protocol is behavior that escaped its class. Matching the `I`-prefix rather than a concrete role suffix is deliberate: domain dataclasses share those nouns (`ProjectRepository` is a value, not a collaborator), so a suffix match would flag the pure helpers this principle permits. The check is also narrow on purpose — it catches the Protocol-param signal, not a function that *constructs* collaborators inside its body (that's `./repository-pattern.md`'s territory). The `_conforms_*` conformance sentinels (`../standards/protocol-conformance.md`) take a concrete adapter, not an `I*` Protocol, so they fall outside the signal automatically.

## See also

- `./dependency-injection.md` — how collaborators get injected, and the no-whole-config rule.
- `./module-layout.md` — where the service, its Protocol seam, and its adapter live.
- `./repository-pattern.md` — the service that owns I/O against one external system.
- `../standards/protocol-conformance.md` — pinning the Protocol/adapter seam each service depends on.
- `./winter-cli.md` — the principle applied end-to-end in winter-cli.
