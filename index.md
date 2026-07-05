# Topology

Convention files live at the **top of the repo**, not under `context/`. `winter-harness` *is* the conventions repo; its content is its public surface, addressed via the `winter-harness:` path notation (e.g. `winter-harness:/architecture/error-handling.md`).

The repo is organized by **convention domain**: each directory names the subject it governs, not the repository. `harness` names this complete conventions system; the domains below partition it. Every convention belongs to the domain whose subject it governs — start at the domain hub for the topic you need and follow the one row that matches, rather than reading the whole tree.

| Domain hub | When to read |
|------------|--------------|
| [canon/index.md](./canon/index.md) | A universal harness convention true of *every* harness, independent of language, project, or workflow — read when authoring or organizing any agent-facing markdown, or building any agentic feature |
| [agent-context/index.md](./agent-context/index.md) | Authoring or validating material an agent loads or traverses — read when writing or reviewing an agent, skill, extension `index.md`, routing table, or cross-context path reference |
| [documentation/index.md](./documentation/index.md) | Public / adopter-facing documentation — read when writing or auditing a README or the docs site, or classifying a repo for the public catalog |
| [architecture/index.md](./architecture/index.md) | Before writing or designing the code of any winter application — how the code is structured and shaped |
| [standards/index.md](./standards/index.md) | The concrete Python code-quality rules — lint, typecheck, test layout, log levels, protocol sentinels — the finished code is held to, consulted as you write it and before it lands |
| [verification/index.md](./verification/index.md) | Verifying a change to any winter component — the verifiability matrix of concrete commands, CLI probes, and manual methods a skill or agent runs to assert the change is correct |
| [workflows/index.md](./workflows/index.md) | Decomposing a feature into phases, the day-to-day landing flow, or when a workspace customizes an upstream framework repo |
| [tooling/github.md](./tooling/github.md) | Any GitHub operation — issues, PRs, releases, repo management go through the `gh` CLI, never the web UI |
| [exemplars/python/repo_pattern.py](./exemplars/python/repo_pattern.py) | Reference for the repository pattern (I-prefix Protocol seam + `internal/` adapter + factory-injected errors) |
| [CONTRIBUTING.md](./CONTRIBUTING.md) | Before pushing — commit format, voice rules, link/reference validation |
