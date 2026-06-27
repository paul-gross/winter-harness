# Topology

Convention files live at the **top of the repo**, not under `context/`. `winter-harness` *is* the conventions repo; its content is its public surface, addressed via the `winter-harness:` path notation (e.g. `winter-harness:/architecture/error-handling.md`).

The repo is organized by **convention domain**: each directory names the subject it governs, not the repository. `harness` names this complete conventions system; the domains below partition it. Every convention belongs to the domain whose subject it governs — start at the domain hub for the topic you need and follow the one row that matches, rather than reading the whole tree.

| Domain hub | When to read |
|------------|--------------|
| [canon/index.md](./canon/index.md) | A universal harness convention true of *every* harness, independent of language, project, or workflow — cross-cutting authoring principles, progressive disclosure, the facts/methodology placement rule, the pre-push harness-change eval, the four levers |
| [agent-context/index.md](./agent-context/index.md) | Authoring or validating material an agent loads or traverses — agents, skills, extension `index.md`, routing, path notation, references, and the agent-context Markdown lints |
| [documentation/index.md](./documentation/index.md) | Public/adopter-facing documentation — README form, the no-undocumented-feature currency invariant, the canonical-source-vs-rendered-view rule, and consumable-vs-example catalog classification |
| [architecture/index.md](./architecture/index.md) | Before writing or changing the code of any winter application — the plan/build-time rules for how the code should be designed and structured |
| [standards/index.md](./standards/index.md) | Before pushing Python changes — the review-time checks for whether finished code is up to standard |
| [workflows/index.md](./workflows/index.md) | Decomposing a feature into phases, the day-to-day landing flow, or when a workspace customizes an upstream framework repo |
| [tooling/index.md](./tooling/index.md) | Cross-cutting rules for the external development tools the ecosystem drives — the GitHub CLI (`gh`) rule for all GitHub operations |
| [exemplars/python/repo_pattern.py](./exemplars/python/repo_pattern.py) | Reference for the repository pattern (I-prefix Protocol seam + `internal/` adapter + factory-injected errors) |
| [CONTRIBUTING.md](./CONTRIBUTING.md) | Before pushing — commit format, voice rules, link/reference validation |
