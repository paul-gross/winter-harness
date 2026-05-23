# Topology

Convention files in this extension live at the **top of the repo**, not under an `ai/` subdirectory. This is deliberate — `winter-harness` *is* the conventions repo, so its content is its public surface, addressed directly via the `winter-harness:` path notation (e.g. `winter-harness:/python/error-handling.md`). Do not look for these files under `ai/`.

| File | When to read |
|------|--------------|
| `python/domain-modeling.md` | Adding a domain type, refactoring a function with many parameters |
| `python/error-handling.md` | Writing any function that can fail |
| `python/dependency-injection.md` | Adding a new service or wiring it into the container |
| `python/repository-pattern.md` | Touching git, filesystem, or any external I/O |
| `python/subprocess.md` | Shelling out — `subprocess.run` / `Popen` conventions and error wrapping |
| `python/logging.md` | Adding a log call, picking a level, or deciding between logger / reporter / print |
| `python/module-layout.md` | Adding a `core/` cross-cutting protocol or a `modules/<feature>/internal/` adapter |
| `python/linting.md` | Before pushing Python changes, or setting up ruff in a new project |
| `python/typechecking.md` | Before pushing Python changes, or setting up pyright in a new project |
| `python/testing.md` | Adding or refactoring tests — pytest layout, conftest scoping, fake-vs-mock guidance |
| `exemplars/python/repo_pattern.py` | Reference for the repository pattern (I-prefix Protocol seam + `internal/` adapter + factory-injected errors) |
| `exemplars/python/cli-architecture.md` | Guided tour of how the conventions are applied in winter-cli — read before adding a `winter ws foo` subcommand |
| `writing-readme.md` | Writing or editing a `README.md` for any winter ecosystem repo |

## Tooling

- **Codeberg interactions** should be done via the [`tea`](https://gitea.com/gitea/tea) CLI (issues, PRs, releases, repo management). Never script against the web UI. The full winter-side workflow lives in `winter-codeberg:/ai/tea-cli.md` and `workspace:/ai/codeberg.md` (canonical label set, capability matrix). This extension only states the rule.
