# Static type checking

## Rule

- One tool: `pyright`. No `mypy`, no running both checkers.
- Configured under `[tool.pyright]` in `pyproject.toml`. `pyright` is in the `dev` dependency group.
- One `mise` task exposes it: `mise run typecheck`.
- Run before pushing, alongside `mise run lint` and `mise run format`.

## Why

The delivery flow is "rebase onto `origin/master` and push" (see `workspace:/ai/project/contributing.md`). There is no PR/MR review and no CI gate yet, so type drift lands silently unless the agent runs the task locally before push.

`pyright` is orthogonal to `ruff`: lint catches style and obvious bugs; the type checker catches wrong arg types, `None` deref, missing return paths, and incompatible overrides — bugs that only surface at runtime otherwise. Pydantic v2 models, click commands, and dependency-injector containers carry rich type information, and the checker validates it for free.

## Do

Before pushing any Python change:

```bash
mise run typecheck   # exits 0 on a clean tree
```

Treat type errors the same as lint errors: fix them, then re-run until clean. Prefer fixing the underlying type imprecision (narrow a `cast`, add a `None` guard, tighten a return type) over `# pyright: ignore[...]`. When an ignore is genuinely needed (third-party stubs that contradict runtime behaviour, conditional imports, etc.), the directive must be accompanied by a one-line comment explaining *why* this case is unfixable — not just *what* is being ignored.

## Configuration

Canonical config — copy into a new project's `pyproject.toml`:

```toml
[dependency-groups]
dev = [
    "pyright>=1.1.380",
    # ... other dev deps
]

[tool.pyright]
include = ["src", "tests"]
pythonVersion = "3.11"           # match `requires-python`
typeCheckingMode = "standard"
reportMissingTypeStubs = false
```

`standard` (not `strict`) is the right starting mode. `strict` flags every untyped function and would require a one-time annotation pass before the tree was clean — better scoped as a follow-up once the codebase is fully annotated. Standard still catches the high-value bugs (wrong arg types, `None` deref, incompatible overrides).

`reportMissingTypeStubs = false` silences the per-package "no type stubs" notice for third-party libraries that don't ship them. Genuine import resolution failures still surface as `reportMissingImports`.

Canonical `mise.toml` task:

```toml
[tasks.typecheck]
description = "Type-check with pyright"
run = "uv run pyright"
```

## Common fix patterns

- **`bytes | str` from GitPython** — narrow with `isinstance(x, bytes)` and decode (`utf-8`, `errors="replace"`).
- **`list[str | None]` flowing into `list[str]`** — filter the comprehension with `if x is not None` and annotate the binding (`xs: list[str] = [...]`).
- **`importlib.util.spec_from_file_location` returns `ModuleSpec | None`** — guard with `if spec is None or spec.loader is None: raise ImportError(...)` before use.
- **Textual `App[Unknown]` from `screen.app`** — wrap with `cast(MyApp, self.app)` (forward-ref string when `MyApp` is only imported under `TYPE_CHECKING`).
- **Textual `BINDINGS` override** — declare as `ClassVar[list[BindingType]]`, not `ClassVar[list[Binding]]`. `ClassVar[list[X]]` is invariant in `X`, and the base class declares it as the looser `BindingType` union — narrowing to `Binding` breaks the override.
- **Textual `DataTable.columns[key]`** — wrap `key` with `ColumnKey(key)` (or `RowKey(key)` for `update_cell`) when assigning into the dict.

## When to enable more

`standard` is the floor, not the ceiling. Once a codebase is fully annotated, consider promoting to `strict` in a dedicated change. Avoid mixing modes mid-tree — set the mode once at the top level and let the whole package conform.

## Why not mypy

Single-checker rule prevents tool-version skew and contradictory diagnostics. Pyright is fast (Node-based, incremental), ships sound stubs for stdlib and most popular libraries, and matches what Pylance — the default Python language server in VS Code — uses, so editor diagnostics and CLI diagnostics agree.
