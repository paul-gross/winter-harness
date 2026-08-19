# Standards

The concrete Python code-quality conventions — the lint, typecheck, test-layout, logging, and protocol-conformance rules
a change must satisfy. Where `architecture/` governs how code is *structured and designed*, this domain governs the
*code-quality details* of the result — consulted both while writing the affected code (picking a log level, adding a
Protocol sentinel) and when reviewing whether it is up to standard before it lands.

Parent: `../index.md` (root topology).

| Standard                                               | When to read                                                                         |
| ------------------------------------------------------ | ------------------------------------------------------------------------------------ |
| [./linting.md](./linting.md)                           | Before pushing Python changes, or setting up ruff in a new project                   |
| [./typechecking.md](./typechecking.md)                 | Before pushing Python changes, or setting up pyright in a new project                |
| [./testing.md](./testing.md)                           | Adding or refactoring tests — pytest layout, conftest scoping, fake-vs-mock guidance |
| [./logging.md](./logging.md)                           | Adding a log call, picking a level, or deciding between logger / reporter / print    |
| [./protocol-conformance.md](./protocol-conformance.md) | Adding a Protocol/adapter pair — pin conformance with a typecheck-time sentinel      |
