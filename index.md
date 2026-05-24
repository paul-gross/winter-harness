# Topology

Convention files in this extension live at the **top of the repo**, not under an `ai/` subdirectory. This is deliberate — `winter-harness` *is* the conventions repo, so its content is its public surface, addressed directly via the `winter-harness:` path notation (e.g. `winter-harness:/python/error-handling.md`). Do not look for these files under `ai/`.

Three layers, each in its own directory:

- **Meta** (`harness/`) — conventions for writing the agent-facing markdown of the winter ecosystem (READMEs, extension `index.md` files, path references, agent / skill / command names). `harness/index.md` is the entry point.
- **Code** (`python/`, `exemplars/`) — conventions for writing application code, with reference files showing the expected shape.
- **Process** (`workflows/`) — conventions for the day-to-day workflows by which changes are delivered.

| File | When to read |
|------|--------------|
| `harness/index.md` | Authoring or auditing any agent-facing markdown (README, extension `index.md`, agent, skill, doc) |
| `python/domain-modeling.md` | Adding a domain type, refactoring a function with many parameters |
| `python/error-handling.md` | Writing any function that can fail |
| `python/dependency-injection.md` | Adding a new service or wiring it into the container |
| `python/repository-pattern.md` | Touching git, filesystem, or any external I/O |
| `python/protocol-conformance.md` | Adding a Protocol/adapter pair — pin conformance with a typecheck-time sentinel |
| `python/subprocess.md` | Shelling out — `subprocess.run` / `Popen` conventions and error wrapping |
| `python/logging.md` | Adding a log call, picking a level, or deciding between logger / reporter / print |
| `python/module-layout.md` | Adding a `core/` cross-cutting protocol or a `modules/<feature>/internal/` adapter |
| `python/linting.md` | Before pushing Python changes, or setting up ruff in a new project |
| `python/typechecking.md` | Before pushing Python changes, or setting up pyright in a new project |
| `python/testing.md` | Adding or refactoring tests — pytest layout, conftest scoping, fake-vs-mock guidance |
| `exemplars/python/repo_pattern.py` | Reference for the repository pattern (I-prefix Protocol seam + `internal/` adapter + factory-injected errors) |
| `exemplars/python/cli-architecture.md` | Guided tour of how the conventions are applied in winter-cli — read before adding a `winter ws foo` subcommand |
| `workflows/feature-delivery.md` | Day-to-day flow for landing a change: worktree model, branch naming, push target, rebase rule, pre-push checks |
| `workflows/upstream-tracking.md` | When a workspace customizes an upstream framework repo — dual-remote layout, single-commit-on-top, sync via rebase + force-with-lease |
| `CONTRIBUTING.md` | Before pushing — commit format, voice rules, link/reference validation |

## Tooling

- **Codeberg interactions** should be done via the [`tea`](https://gitea.com/gitea/tea) CLI (issues, PRs, releases, repo management). Never script against the web UI. The full winter-side workflow lives in `winter-codeberg:/ai/tea-cli.md` and `workspace:/ai/codeberg.md` (canonical label set, capability matrix). This extension only states the rule.
