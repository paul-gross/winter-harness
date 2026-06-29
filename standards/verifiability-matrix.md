# Verifiability matrix — winter

An inventory of the verification methods available for the winter ecosystem. Each entry is one way a skill or agent may assert a winter change is correct. Conforms to the Canon concept at [`../canon/verifiability-matrix.md`](../canon/verifiability-matrix.md).

Method ids follow the Canon's [scheme](../canon/verifiability-matrix.md#method-identifiers): commands and manual methods are `<scope>:<method>` (a manual method's method name is `manual`); `cli-probe:*` is a category scope for the workspace-level `winter` CLI probes; tools are unscoped under a flat `tool:`. The `winter:*` Python-QA rows run from `tools/winter-cli/` inside the `winter` repo worktree; each sibling project's rows run from that project's own worktree; `cli-probe:*` run from a configured workspace root. Choosing a scope for a new winter method: Python QA of winter's own source is `winter:*`; a behavioral probe of the installed CLI against a workspace is `cli-probe:*`.

## Commands

Verification that runs as a single command — exit 0 is the pass signal unless noted.

| Method | Command |
|--------|---------|
| winter:build | `uv sync` — installs all dependencies including the `dev` group (pytest, ruff, pyright). Exit 0 = environment ready. |
| winter:unit-test | `uv run pytest` — runs the full pytest suite under `tests/`. Shorthand: `mise run test`. |
| winter:lint | `uv run ruff check .` — ruff linting over `src/` and `tests/`. Shorthand: `mise run lint`. |
| winter:typecheck | `uv run pyright` — pyright type-checking over `src/` and `tests/` in standard mode. Shorthand: `mise run typecheck`. |
| winter-service-tmux:build | `uv sync` — install deps in `alpha/winter-service-tmux/`. |
| winter-service-tmux:unit-test | `uv run pytest` (`mise run test`). |
| winter-service-tmux:lint | `uv run ruff check .` (`mise run lint`). |
| winter-service-tmux:typecheck | `uv run pyright` (`mise run typecheck`). |
| winter-service-docker:build | `uv sync` — install deps in `alpha/winter-service-docker/`. |
| winter-service-docker:unit-test | `uv run pytest` (`mise run test`). |
| winter-service-docker:lint | `uv run ruff check .` (`mise run lint`). |
| winter-service-docker:typecheck | `uv run pyright` (`mise run typecheck`). |
| winter-plugin-api:build | `uv sync` — install deps in `alpha/winter-plugin-api/`. |
| winter-plugin-api:unit-test | `uv run pytest` (`mise run test`). |
| winter-plugin-api:lint | `uv run ruff check .` (`mise run lint`). |
| winter-plugin-api:typecheck | `uv run pyright` (`mise run typecheck`). |
| cli-probe:doctor | `winter doctor` — built-in preflight probes for the workspace and every installed extension; pass/warn/fail per probe with remediation hints. Exit 1 = any probe failed (warnings allowed). The command that turns the always-exit-0 introspection probes below into a failing gate. |
| cli-probe:status | `winter ws status <env>` — git status across all worktrees in a feature env: untracked files, uncommitted changes, ahead/behind counts. |
| cli-probe:graph | `winter graph` — prints the extension dependency graph; verifies every declared extension resolves and the wiring is coherent. |
| cli-probe:lint | `winter lint` — runs all registered lint checks (built-in extractability plus harness-registered path-notation, doc-reference, and anchor checks). Emits NDJSON findings; non-zero on any finding. |
| cli-probe:capabilities | `winter capabilities` — lists every capability slot, its bound extension, how the binding resolved, and whether each candidate entrypoint exists on disk. Always exits 0 — assert on the output (or `--json`); `winter doctor` is what fails on misconfiguration. |
| cli-probe:ext-verify | `winter ext verify <extension>` — runs the capability-spec conformance checks (accepts-action / refuses-unknown / forwards-params) against a provider's entrypoint. Exit 0 = conforms. Accepts a local path, so it verifies an in-progress provider worktree: `winter ext verify ./alpha/winter-service-tmux`. |
| cli-probe:env | `winter env <scope>` — prints the computed runtime env vars (port base, env-band entries) for `<env>` or `workspace`. Assert the ports and injected vars match expectation. |
| cli-probe:provision-plan | `winter provision <env> --dry-run` — resolves and prints the provision handler plan without running anything or starting a service. Validates handler wiring non-destructively; add `--json` for a structured plan. |
| cli-probe:service-describe | `winter service describe` — the bound provider reports its declared service catalog; confirms the service manifest parses and services are discoverable. |

## Manual testing

Verification no single command performs — it needs a running stack, spans many invocations, or rests on judgment. Any of these can be pointed at in-progress code with the override Tools below.

### winter-service-tmux:manual — service orchestration end-to-end (tmux)
Surface: the `winter-service-tmux` provider bound to the `service` slot. Bring a feature env's services up, then confirm state: `winter service up <env>` followed by `winter service status <env>`. Pass: every declared pane appears in the named tmux session and each service reports running; `winter service down <env>` tears the session down cleanly. Requires `[capabilities] service = "winter-service-tmux"`, a valid service manifest, and `tmux` on the host. **Gap**: no automated harness drives a real tmux session — exercised manually in a development workspace. Verifier hygiene: match the full unique command string when probing pids (never a short prefix that can match your own shell process); confirm the pids you act on are the intended ones; let the session settle before reading status.

### winter-service-docker:manual — service orchestration end-to-end (docker)
Surface: the `winter-service-docker` provider. Same up/status/down gestures, but the provider reports real container health, so `winter service up <env> --wait` is a genuine readiness gate. Pass: containers reach healthy, `winter service status` maps container state to winter state, and per-env isolation holds — distinct `COMPOSE_PROJECT_NAME` and `WSD_PORT_*` host ports let two envs run side by side without collision. Requires the docker daemon and compose v2 (checked by `winter doctor`). **Gap**: no automated harness drives real containers. Bounded follow: `winter service logs '<glob>' -f` blocks until SIGINT — bound it (`timeout -s INT 10 winter service logs '*/backend' -f`) or run it backgrounded and cancel when done.

### winter:manual — feature-environment lifecycle (ws init/destroy)
`winter ws init <env>` creates every project worktree declared in `.winter/config.toml` by cloning or adding git worktrees; `winter ws destroy <env>` removes them. Exit 0 plus the expected worktrees on disk verifies the init/destroy path against real git remotes. **Gap**: no dedicated CI job runs this against a throwaway workspace — exercised as part of normal feature development.

### winter-test-service:manual — full-stack app exercise
Stand up `winter-test-service` (web + api + worker + Postgres + RabbitMQ) under a feature env to exercise orchestration, provisioning, port-band isolation, and log capture against a real multi-service application rather than a single command. Drive its built-in diagnostic controls — induced API crash, slow boot, error output — to put services into known failure and health states and confirm the orchestrator observes and reports them. See `tool:winter-test-service` below for the app and its controls.

## Tools

Setup an agent uses to stand up the scenario a verification needs — not assertions of correctness themselves.

| Tool | Use |
|------|-----|
| tool:winter-ws-init | `winter ws init <env>` / `winter ws destroy <env>` — create or remove a throwaway feature environment to verify against. |
| tool:winter-provision | `winter provision <env>` runs dependency → resource → data to bring an env to a working state. Put state in a known shape: `winter provision <env> data` (wipe-and-reload baseline), `resource --reset` (destroy + recreate databases / queues / buckets), `resource --seed` (resources then data). Handlers are idempotent. |
| tool:winter-core-override | `winter --winter=<path> …` runs the CLI from `<path>/tools/winter-cli` against the current workspace, so any command above exercises feature-branch core without reinstalling — e.g. `winter --winter=./alpha/winter ws status alpha`. |
| tool:service-orchestrator-override | `winter --service-orchestrator=<path-or-name> service …` redirects `service` dispatch at a worktree provider or a registered name. Combine with `--winter` when the change touches the status path (env enumeration lives in core): `winter --winter=./alpha/winter --service-orchestrator=./alpha/winter-service-docker service status alpha`. |
| tool:direct-entrypoint | The override redirects the `winter service …` door but not every door. **tmux env-root door — Gap ([winter-service-tmux#26](https://github.com/paul-gross/winter-service-tmux/issues/26)):** the env-root `./up` / `./down` / `./status` symlinks ignore `WINTER_EXT_DIR`, so to run worktree code through them you must repoint the symlink at the worktree copy, run it, then **restore the symlink** — mandatory; a leftover override silently routes every later call in that env through worktree code. Once #26 lands, an exported `WINTER_EXT_DIR` covers this door too and the repoint goes away. **docker (no env-root door):** to invoke the entrypoint without the CLI, export `WINTER_WORKSPACE_DIR` / `WINTER_EXT_DIR` / `WINTER_EXT_CONFIG_DIR` and run `workflow/service <action>` under `PYTHONPATH=$WINTER_EXT_DIR/src`. |
| tool:winter-test-service | A full-stack sample app (React web, FastAPI api, background worker, Postgres, RabbitMQ) winter can manage. Stand it up as the workload behind `winter-test-service:manual`; its diagnostic controls trigger crashes, slow boots, and error output on demand, creating the known failure and health states an orchestration check observes. |

## See also

- [`../canon/verifiability-matrix.md`](../canon/verifiability-matrix.md) — the Canon concept this doc conforms to: shape rules, the Do/Don't list, and why the matrix belongs in the harness.
- [`./testing.md`](./testing.md) — pytest layout, conftest scoping, and fake-vs-mock guidance for unit-test rows.
- [`./linting.md`](./linting.md) — ruff configuration and `mise run lint` / `mise run format` convention.
- [`./typechecking.md`](./typechecking.md) — pyright configuration and `mise run typecheck` convention.
- `workspace:/context/winter-cli/root-flags.md` — the `--winter` and `--service-orchestrator` override flags in full.
- `winter-service-tmux:/context/orchestrator-dev-loop.md` and `winter-service-docker:/context/dev-loop.md` — the direct-entrypoint dev loops for exercising changed orchestrator code.
- `workspace:/context/winter-cli/usage/provision.md` — the full `winter provision` surface for resource and seed-data setup.
