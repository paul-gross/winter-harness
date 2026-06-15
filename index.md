# Topology

Convention files in this extension live at the **top of the repo**, not under an `ai/` subdirectory. This is deliberate — `winter-harness` *is* the conventions repo, so its content is its public surface, addressed directly via the `winter-harness:` path notation (e.g. `winter-harness:/architecture/error-handling.md`). Do not look for these files under `ai/`.

Four layers, each in its own directory:

- **Canon** (`canon/`) — the universal, enforceable substrate true of every harness, independent of language, project, or workflow. Self-contained: it references only itself. `canon/index.md` is the entry point.
- **Markdown** (`harness/`) — winter-ecosystem conventions for writing the agent-facing markdown the framework is composed of (READMEs, extension `index.md` files, path references, agent / skill / command names). Rests on the Canon. `harness/index.md` is the entry point.
- **Code** (`architecture/`, `standards/`, `exemplars/`) — conventions for writing application code: `architecture/` for design and structural rules consulted at **PLAN/BUILD** time (how should this be written?), `standards/` for quality rules consulted at **REVIEW** time (is this finished code up to standard?), and `exemplars/` for reference shapes in isolation. `architecture/index.md` is the entry point for plan/build; `standards/index.md` for review.
- **Process** (`workflows/`) — conventions for the day-to-day workflows by which changes are delivered. `workflows/index.md` is the entry point.

| Layer hub | When to read |
|-----------|--------------|
| [canon/index.md](./canon/index.md) | Reasoning about a universal harness convention — cross-cutting authoring principles, the facts/methodology placement rule, the pre-push harness-change eval, or the four levers |
| [harness/index.md](./harness/index.md) | Authoring or auditing winter-ecosystem agent-facing markdown (README, extension `index.md`, agent, skill, doc governance) |
| [architecture/index.md](./architecture/index.md) | Before writing new code or changing the code of any winter application — the plan/build-time rules for how the code should be designed and structured |
| [standards/index.md](./standards/index.md) | Before pushing Python changes — the review-time checks for whether finished code is up to standard |
| [workflows/index.md](./workflows/index.md) | Decomposing a feature into phases, or when a workspace customizes an upstream framework repo |
| [exemplars/python/repo_pattern.py](./exemplars/python/repo_pattern.py) | Reference for the repository pattern (I-prefix Protocol seam + `internal/` adapter + factory-injected errors) |
| [CONTRIBUTING.md](./CONTRIBUTING.md) | Before pushing — commit format, voice rules, link/reference validation |

## Tooling

- **GitHub interactions** should be done via the [`gh`](https://cli.github.com/) CLI (issues, PRs, releases, repo management). Never script against the web UI. The full winter-side workflow lives in `winter-github:/ai/gh-cli.md` and `workspace:/ai/github.md` (canonical label set). This extension only states the rule.
