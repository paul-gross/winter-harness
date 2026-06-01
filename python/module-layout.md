# Module layout

The winter-cli codebase has standardized on a layered layout that separates the **public Protocol surface** of each feature from its **adapter implementations**, and pulls cross-cutting Protocols into a top-level `core/`.

## Two-level structure

```
src/<package>/
├── container.py              # DI container — wires Protocols to concrete adapters
├── core/                     # Cross-cutting Protocol seams (used by ≥2 modules)
│   ├── cli_output.py         # ICliOutputService — the Protocol
│   └── internal/             # Adapters for the core Protocols
│       └── click_cli_output.py
└── modules/
    └── <feature>/
        ├── command.py        # click commands — thin wrappers over handlers
        ├── handler.py        # CLI-shaped: parses args, formats output, calls services
        ├── service.py        # Domain orchestration
        ├── foo_repository.py # IReadFooRepository / IWriteFooRepository — the Protocol
        └── internal/         # Adapters for this feature's Protocols
            └── git_foo_repository.py
```

Start with a flat `handler.py`. Promote to a `handlers/` subpackage once the feature has multiple distinct CLI surfaces that share little code:

```
modules/<feature>/
├── handlers/
│   ├── __init__.py           # re-exports the handler classes
│   ├── <surface_a>_handler.py
│   └── <surface_b>_handler.py
└── …
```

`exemplars/python/cli-architecture.md` walks through `modules/workspace/handlers/` as the canonical reference for this split.

## Rules

1. **Protocols at the feature root.** A feature's public callable surface is a Protocol file at the feature's package root (e.g. `modules/workspace/repo_repository.py`). Anything that depends on the feature imports the Protocol from there.

2. **Adapters in `internal/`.** Concrete classes implementing the Protocols live under `<feature>/internal/`. The `internal/` package is package-private — nothing outside the feature should import from it.

3. **I-prefix on Protocols.** `IReadFooRepository`, `IWriteFooRepository`, `ICliOutputService`. The I-prefix marks Protocol files at a glance. Concrete adapters drop the I.

4. **`core/` is for cross-cutting.** A Protocol lives in `core/` only when ≥2 features depend on it (CLI output, click input validation, error factories). Otherwise it belongs to its owning feature. Don't preemptively hoist a Protocol into `core/` — wait for the second consumer.

5. **`container.py` is the single binding point.** All `IFoo` → concrete-`_FooAdapter` bindings live in the DI container. Features never construct each other's adapters — they receive Protocols via the container.

## Why

- **Testability.** A service depending on `IWriteFooRepository` accepts a test double trivially. No monkeypatching, no `mock.patch`, no global state.
- **Pluggability.** Swapping the adapter (e.g., from `GitFooRepository` to `LibgitFooRepository`) is a one-line container change. Consumers don't even recompile.
- **Discoverability for agents.** The Protocol file at the feature root is the agent's first read when asked to extend a feature. They see the surface area without scanning every concrete file.
- **Encapsulation.** `internal/` is a hard signal that imports from outside are wrong. Linters and code reviewers can enforce it mechanically.

## Enforcement

In winter-cli, the I-prefix-on-Protocols rule and the no-Protocols-in-`internal/` rule are checked at `mise run test` time by `winter:tools/winter-cli/tests/conventions/test_protocol_naming.py`. The check walks every class definition; a class is treated as a Protocol if its bases include `typing.Protocol` or it carries `@runtime_checkable`. Violations fail with file:line and a back-link here.

## See also

- `python/service-architecture.md` — the service-based principle this layout houses: behavior in injected service classes, free functions for pure helpers only.
- `python/dependency-injection.md` — the DI conventions and `Workspace` injection rule.
- `python/repository-pattern.md` — the rule about confining library imports.
- `python/protocol-conformance.md` — pin each Protocol/adapter pair with a typecheck-time sentinel so DI-laundered drift fails the build.
- `exemplars/python/repo_pattern.py` — full worked example combining all three.
