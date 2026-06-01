# Topology

Convention files in this extension live at the **top of the repo**, not under an `ai/` subdirectory. This is deliberate — `winter-harness` *is* the conventions repo, so its content is its public surface, addressed directly via the `winter-harness:` path notation (e.g. `winter-harness:/python/error-handling.md`). Do not look for these files under `ai/`.

Four layers, each in its own directory:

- **Canon** (`canon/`) — the universal, enforceable substrate true of every harness, independent of language, project, or workflow. Self-contained: it references only itself. `canon/index.md` is the entry point.
- **Markdown** (`harness/`) — winter-ecosystem conventions for writing the agent-facing markdown the framework is composed of (READMEs, extension `index.md` files, path references, agent / skill / command names). Rests on the Canon. `harness/index.md` is the entry point.
- **Code** (`python/`, `exemplars/`) — conventions for writing application code, with reference files showing the expected shape.
- **Process** (`workflows/`) — conventions for the day-to-day workflows by which changes are delivered.

| File | When to read |
|------|--------------|
| `canon/index.md` | Reasoning about a universal harness convention — cross-cutting authoring principles, the facts/methodology placement rule, the pre-push harness-change eval, or the four levers |
| `harness/index.md` | Authoring or auditing winter-ecosystem agent-facing markdown (README, extension `index.md`, agent, skill, doc governance) |
| `python/service-architecture.md` | Before authoring new behavior — the service-based principle the other Python conventions assume: behavior in injected service classes, free functions for pure helpers only |
| `python/domain-modeling.md` | Adding a domain type, refactoring a function with many parameters |
| `python/error-handling.md` | Writing any function that can fail |
| `python/dependency-injection.md` | Adding a new service or wiring it into the container |
| `python/repository-pattern.md` | Touching git, filesystem, or any external I/O |
| `python/protocol-conformance.md` | Adding a Protocol/adapter pair — pin conformance with a typecheck-time sentinel |
| `python/subprocess.md` | Shelling out — `subprocess.run` / `Popen` conventions and error wrapping |
| `python/logging.md` | Adding a log call, picking a level, or deciding between logger / reporter / print |
| `python/module-layout.md` | Adding a `core/` cross-cutting protocol or a `modules/<feature>/internal/` adapter |
| `python/plugin-author.md` | Authoring a winter TUI plugin — a `plugin.py` that contributes dashboard badges, TUI screens, or keybound actions |
| `python/linting.md` | Before pushing Python changes, or setting up ruff in a new project |
| `python/typechecking.md` | Before pushing Python changes, or setting up pyright in a new project |
| `python/testing.md` | Adding or refactoring tests — pytest layout, conftest scoping, fake-vs-mock guidance |
| `exemplars/python/repo_pattern.py` | Reference for the repository pattern (I-prefix Protocol seam + `internal/` adapter + factory-injected errors) |
| `exemplars/python/cli-architecture.md` | Guided tour of how the conventions are applied in winter-cli — read before adding a `winter ws foo` subcommand |
| `workflows/feature-delivery.md` | Day-to-day flow for landing a change: worktree model, branch naming, push target, rebase rule, pre-push checks |
| `workflows/upstream-tracking.md` | When a workspace customizes an upstream framework repo — dual-remote layout, single-commit-on-top, sync via rebase + force-with-lease |
| `CONTRIBUTING.md` | Before pushing — commit format, voice rules, link/reference validation |

## Tooling

- **GitHub interactions** should be done via the [`gh`](https://cli.github.com/) CLI (issues, PRs, releases, repo management). Never script against the web UI. The full winter-side workflow lives in `winter-github:/ai/gh-cli.md` and `workspace:/ai/github.md` (canonical label set). This extension only states the rule.
