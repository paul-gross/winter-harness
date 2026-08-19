# Architecture — winter

Winter's **architecture guidance** — the structural invariants, design decisions, and constraints a change must honor.

Plan/build-time conventions for the winter ecosystem — how to structure and design Python code, how the generic rules
are realized in concrete winter applications. Consulted when writing new code or designing a feature; the companion
`standards/` domain carries the concrete code-quality rules (lint, typecheck, tests, logging, protocol sentinels) the
finished code is held to.

**Read this index before changing the code of any winter application** — the `winter` CLI, an extension's Python, a
service orchestrator. It routes you to the doc for the surface you're touching so you build with the existing structure
rather than reverse-engineering it. Follow the one row that matches your change; don't read the whole tree.

Parent: `../index.md` (root topology).

| Architecture doc                                       | When to read                                                                                                                                                         |
| ------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [./service-architecture.md](./service-architecture.md) | Before authoring new behavior — the service-based principle the other conventions assume: behavior in injected service classes, free functions for pure helpers only |
| [./system-architecture.md](./system-architecture.md)   | Designing or reviewing boundaries between winter and other systems or extensions — the winter-owned contract over swappable backends, and the no-pass-through rule   |
| [./dependency-injection.md](./dependency-injection.md) | Adding a new service or wiring it into the container                                                                                                                 |
| [./module-layout.md](./module-layout.md)               | Adding a `core/` cross-cutting protocol or a `modules/<feature>/internal/` adapter                                                                                   |
| [./repository-pattern.md](./repository-pattern.md)     | Touching git, filesystem, or any external I/O                                                                                                                        |
| [./domain-modeling.md](./domain-modeling.md)           | Adding a domain type, refactoring a function with many parameters                                                                                                    |
| [./subprocess.md](./subprocess.md)                     | Shelling out — `subprocess.run` / `Popen` conventions and error wrapping                                                                                             |
| [./error-handling.md](./error-handling.md)             | Writing any function that can fail                                                                                                                                   |
| [./plugin-author.md](./plugin-author.md)               | Authoring a winter TUI plugin — a `plugin.py` that contributes dashboard badges, TUI screens, or keybound actions                                                    |
| [./winter-cli.md](./winter-cli.md)                     | Adding or changing a `winter` CLI command — its module layout, handler/service split, or argument surface                                                            |
