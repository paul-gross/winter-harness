# Protocol/adapter conformance

When a Protocol seam is wired through a DI container, Pyright can lose sight of the contract. The `dependency-injector` accessors used in this codebase — `provided.<method>.call(...)`, `Provide[...]`, etc. — return `Any`, which launders the Protocol type past every consumer. Drift in an adapter's signature (renamed method, changed arity, swapped kwarg, wrong return type) then sails through `mise run typecheck` because nothing structurally compares the adapter against its Protocol.

## Rule

For every Protocol that has a canonical concrete adapter, add a typecheck-time **conformance sentinel** at the bottom of the **adapter module**:

```python
# in modules/<feature>/internal/foo_repository.py
# Import the Protocol from the feature-root module (one directory up),
# NOT from a sibling under internal/ — the adapter depends on the Protocol,
# not the other way around.
from <package>.modules.foo.foo_repository import IWriteFooRepository


class WriteFooRepository(ReadFooRepository):
    ...


def _conforms_write_foo_repository(x: WriteFooRepository) -> IWriteFooRepository:
    return x
```

The function is never called. Pyright type-checks the `return x` against the annotated return type, so if `WriteFooRepository` no longer structurally conforms to `IWriteFooRepository` the check fails:

```
error: Type "WriteFooRepository" is not assignable to return type "IWriteFooRepository"
  "WriteFooRepository" is incompatible with protocol "IWriteFooRepository"
    "save_thing" is not present (reportReturnType)
```

Zero runtime cost — Pyright catches the drift, `mise run typecheck` surfaces it, the build stops before drifted code lands.

## Place the sentinel next to the adapter, not the Protocol

The sentinel lives in the **adapter module** so the dependency arrow stays correct. The Protocol is the abstraction; the adapter conforms to it. Making the Protocol module import its own adapter would invert the relationship and force `if TYPE_CHECKING:` guards to dodge cycles. Adapters already depend on the Protocol they implement — the sentinel just makes that dependency explicit and verifiable.

## One sentinel per Protocol/adapter pair

- Each `IReadXRepository` / `ReadXRepository` pair gets a `_conforms_read_x_repository` sentinel in `read_x_repository.py`.
- Each `IWriteXRepository` / `WriteXRepository` pair gets `_conforms_write_x_repository` in `write_x_repository.py`.
- When a Write Protocol extends its Read counterpart (and the Write adapter inherits from the Read adapter), the Write sentinel alone pins both seams — Read is the supertype, so a Writer-conforming adapter trivially conforms to Reader too. Drop the Read sentinel in that case.
- When two Protocols are satisfied by the same adapter (e.g. `IFilesystemReader` + `IFilesystemWriter` both implemented by `LocalFilesystem`, with Writer extending Reader), one sentinel returning the more-specific Protocol covers both.
- When two adapters implement the same Protocol (e.g. `StreamReporter` and `JsonReporter` both implementing `IInitReporter`, co-located in `init_reporter.py`), each adapter gets its own sentinel.

## When this doesn't apply

Skip the sentinel for Protocols that have no canonical adapter:

- **Structural-only Protocols** satisfied by domain dataclasses (e.g. `IWorkspaceRepository` satisfied by a `Workspace` dataclass). The dataclass *is* the conformance proof.
- **Protocols satisfied by stdlib types** (e.g. `IStreamingProcess` satisfied by `subprocess.Popen`). The stdlib type isn't ours to annotate, and the seam exists for substitution at the test boundary.

## Why this beats a runtime test

A runtime test using `inspect.signature` equality (the previous approach in this codebase) only checks the Protocols it's explicitly parametrized over, compares raw annotation strings (so it misses variance, defaults, kw-only differences, and overloads), and costs test-suite time. A Pyright sentinel uses the real subtype logic, covers any seam you write one for, costs zero runtime, and lives next to the code it pins so the next reader finds it.

## See also

- `python/module-layout.md` — the Protocol-at-feature-root + adapter-in-`internal/` layout these sentinels reinforce.
- `python/dependency-injection.md` — the DI container that launders Protocol types and motivates the sentinel.
- `exemplars/python/repo_pattern.py` — canonical Protocol/adapter file with the sentinel in place.
