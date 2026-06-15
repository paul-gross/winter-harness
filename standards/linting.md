# Linting and formatting

## Rule

- One tool: `ruff` for **both** linting and formatting. No separate `black`, `isort`, `flake8`, etc.
- Configured under `[tool.ruff]` in `pyproject.toml`. `ruff` is in the `dev` dependency group.
- Two `mise` tasks expose it: `mise run lint` and `mise run format`.
- Run both before pushing.

## Why

The delivery flow is "rebase onto `origin/master` and push" (see `workspace:/ai/project/contributing.md`). There is no PR/MR review and no CI gate yet, so lint/format drift lands silently unless the agent runs the tasks locally before push.

Single-tool ruff replaces the legacy `black + isort + flake8` triple — same coverage, one config block, one invocation, no tool-version skew.

## Do

Before pushing any Python change:

```bash
mise run format    # rewrites in place
mise run lint      # exits 0 on a clean tree
```

If `lint` reports issues, fix them and re-run until clean. Many violations are autofixable — pass `--fix` directly: `uv run ruff check --fix .` (no `mise` wrapper for this one-shot mode; it's the same `ruff` binary).

## Configuration

Canonical config — copy into a new project's `pyproject.toml`:

```toml
[dependency-groups]
dev = [
    "ruff>=0.8.0",
    # ... other dev deps
]

[tool.ruff]
line-length = 120
target-version = "py311"  # set to the minimum `requires-python`

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "C4", "SIM", "RUF"]

[tool.ruff.lint.per-file-ignores]
# Tests use loose patterns: long assertion messages, fixture functions
# whose names shadow imports. Relax line-length and bugbear's
# fixture-name shadowing here.
"tests/*" = ["E501", "B008"]
```

Rule families: pycodestyle errors (`E`), pyflakes (`F`), isort (`I`), pyupgrade (`UP`), flake8-bugbear (`B`), flake8-comprehensions (`C4`), flake8-simplify (`SIM`), Ruff-native (`RUF`).

Canonical `mise.toml` tasks:

```toml
[tasks.lint]
description = "Lint with ruff"
run = "uv run ruff check ."

[tasks.format]
description = "Format with ruff"
run = "uv run ruff format ."
```

## Per-file ignores

Use `[tool.ruff.lint.per-file-ignores]` for genuinely intentional patterns — not as a blanket escape hatch. Each entry should have a comment explaining *why* the rule doesn't apply.

Real examples from `winter-cli`:

```toml
# cli.py sets sys.pycache_prefix before importing click and winter_cli.* so
# their bytecode lands under the redirected cache (and never scribbles
# __pycache__ into plugin extension source trees) — that ordering is
# load-bearing, so E402 doesn't apply.
"src/winter_cli/cli.py" = ["E402"]
```

If a rule fires across many files for legitimate reasons, prefer fixing the code over disabling the rule globally. Reach for `select = [...]` adjustments only when an entire rule family is genuinely inappropriate for the codebase.

## When to enable more

The default `["E", "F", "I", "UP", "B", "C4", "SIM", "RUF"]` set is the floor, not the ceiling. Promising next steps:

- `S` (flake8-bandit) — security smells. Pair with `"tests/*" = ["S101"]` to allow `assert`.
- `PTH` (flake8-use-pathlib) — replace `os.path` calls with `pathlib`.
- `RET` (flake8-return) — cleaner return statements.
- `TCH` (flake8-type-checking) — move type-only imports under `if TYPE_CHECKING:`.

Enable one family per change so each autofix pass stays reviewable.
