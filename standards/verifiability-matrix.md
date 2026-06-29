# Verifiability matrix — winter

An inventory of the verification methods available for the winter ecosystem. Each row is one method a skill or agent may use to assert a winter change is correct. Conforms to the Canon concept at [`../canon/verifiability-matrix.md`](../canon/verifiability-matrix.md).

All runnable commands execute from `tools/winter-cli/` inside the `winter` repo worktree unless stated otherwise. `winter` CLI probes run from a configured workspace root.

## Matrix

| Method | Exercise |
|--------|----------|
| build | `uv sync` — installs all dependencies including the `dev` group (pytest, ruff, pyright). Exit 0 = environment ready. |
| unit-test | `uv run pytest` — runs the full pytest suite under `tests/`. Exit 0 = all tests pass. Shorthand: `mise run test`. |
| lint | `uv run ruff check .` — ruff linting over `src/` and `tests/`. Exit 0 = clean tree. Shorthand: `mise run lint`. |
| typecheck | `uv run pyright` — pyright type-checking over `src/` and `tests/` in standard mode. Exit 0 = no type errors. Shorthand: `mise run typecheck`. |
| cli-probe:doctor | `winter doctor` — runs built-in preflight probes for the workspace and every installed extension; reports pass/warn/fail per probe with remediation hints. Exit 0 = all probes pass (warnings allowed); exit 1 = any probe failed. |
| cli-probe:status | `winter ws status <env>` — lists git repo status across all worktrees in a feature env; surfaces untracked files, uncommitted changes, and ahead/behind counts. |
| cli-probe:graph | `winter graph` — prints the extension dependency graph. Verifies that every declared extension resolves and the wiring is coherent. |
| cli-probe:lint | `winter lint` — runs all registered lint checks: the built-in extractability check (`tools/winter-lint/extractability.py`) plus harness-registered checks (path notation, doc references, anchor lint from `winter-harness`). Emits NDJSON findings; exits non-zero on any finding. |
| real-tmux-e2e | Conceptual interaction. Surface: the winter-service-tmux orchestrator bound to the workspace's `service` capability slot. Gesture: `winter service up <env>` followed by `winter service status <env>`. Expected outcome: all declared panes appear in the named tmux session and every service entry reports running; `winter service down <env>` tears the session down cleanly. Requires a workspace with `[capabilities] service = "winter-service-tmux"` and a valid service manifest; the host must have `tmux` installed. **Gap**: no automated harness drives a real tmux session; this method is exercised manually in a development workspace. Verifier hygiene: match the full unique command string when probing pids — never a short prefix that can match your own shell process; verify the pids you act on are the intended ones; let the session settle before reading status. |
| worktree-spin-up | `winter ws init <env-name>` — creates all project worktrees under `<env-name>/` by cloning or adding git worktrees for every repo declared in `.winter/config.toml`; exit 0 = feature environment ready. Tear down with `winter ws destroy <env-name>`. Exercises the full init/destroy lifecycle against real git remotes. **Gap**: no dedicated CI job runs this against a throwaway workspace; it is exercised as part of normal feature development. |

## See also

- [`../canon/verifiability-matrix.md`](../canon/verifiability-matrix.md) — the Canon concept this doc conforms to: shape rules, the Do/Don't list, and why the matrix belongs in the harness.
- [`./testing.md`](./testing.md) — pytest layout, conftest scoping, and fake-vs-mock guidance for unit-test rows.
- [`./linting.md`](./linting.md) — ruff configuration and `mise run lint` / `mise run format` convention.
- [`./typechecking.md`](./typechecking.md) — pyright configuration and `mise run typecheck` convention.
