# Standards

Review-time conventions for finished Python code — consulted when asking "is this code up to standard?" rather than when designing it. Where `architecture/` shapes how code is structured while it is being written, this domain is reached after the code exists and before it lands.

Parent: `../index.md` (root topology).

| Standard | When to read |
|----------|--------------|
| [./linting.md](./linting.md) | Before pushing Python changes, or setting up ruff in a new project |
| [./typechecking.md](./typechecking.md) | Before pushing Python changes, or setting up pyright in a new project |
| [./testing.md](./testing.md) | Adding or refactoring tests — pytest layout, conftest scoping, fake-vs-mock guidance |
| [./logging.md](./logging.md) | Adding a log call, picking a level, or deciding between logger / reporter / print |
| [./protocol-conformance.md](./protocol-conformance.md) | Adding a Protocol/adapter pair — pin conformance with a typecheck-time sentinel |
