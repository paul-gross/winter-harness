# Topology

Convention files live at the **top of the repo**, not under `context/`. `winter-harness` *is* the conventions repo; its content is its public surface, addressed via the `winter-harness:` path notation (e.g. `winter-harness:/architecture/error-handling.md`).

Four layers — Canon (universal substrate), Markdown (winter-ecosystem agent-facing docs), Code (application code conventions), and Process (delivery workflows) — each in its own directory. Start at the layer hub for the topic you need.

| Layer hub | When to read |
|-----------|--------------|
| [canon/index.md](./canon/index.md) | Reasoning about a universal harness convention — cross-cutting authoring principles, the facts/methodology placement rule, the pre-push harness-change eval, or the four levers |
| [harness/index.md](./harness/index.md) | Authoring or auditing winter-ecosystem agent-facing markdown (README, extension `index.md`, agent, skill, doc governance) |
| [harness/tooling.md](./harness/tooling.md) | The tooling conventions — the GitHub CLI (`gh`) rule for all GitHub operations |
| [architecture/index.md](./architecture/index.md) | Before writing new code or changing the code of any winter application — the plan/build-time rules for how the code should be designed and structured |
| [standards/index.md](./standards/index.md) | Before pushing Python changes — the review-time checks for whether finished code is up to standard |
| [workflows/index.md](./workflows/index.md) | Decomposing a feature into phases, or when a workspace customizes an upstream framework repo |
| [exemplars/python/repo_pattern.py](./exemplars/python/repo_pattern.py) | Reference for the repository pattern (I-prefix Protocol seam + `internal/` adapter + factory-injected errors) |
| [CONTRIBUTING.md](./CONTRIBUTING.md) | Before pushing — commit format, voice rules, link/reference validation |
