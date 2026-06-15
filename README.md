# ❄️ winter-harness

A [winter](https://github.com/paul-gross/winter) extension curated for the meta [winter-workspace](https://github.com/paul-gross/winter-workspace) itself.

📚 **Documentation:** <https://paul-gross.github.io/winter-docs/>

## ✨ Features

- **Exemplar for others** — serves as an example harness project, a reference others can pull ideas from when assembling their own harness.
- **Architecture conventions** (`architecture/`) — an opinionated guide for structuring Python applications, read at plan/build time: the generic design and structure rules plus application-specific architecture docs (e.g. `architecture/winter-cli.md`, the live tour of how the conventions are applied in winter-cli today). `architecture/index.md` is the entry point.
- **Standards conventions** (`standards/`) — an opinionated guide for reviewing finished Python code, read at review time.
- **Agent-facing markdown conventions** (`harness/`) — an opinionated guide for writing the markdown that agents read across the winter ecosystem.
- **Canonical exemplars** (`exemplars/python/`) — reference `.py` files showing the expected shape of recurring patterns (repository class, domain object).

## 🚀 Installation

Add to the workspace's `.winter/config.toml`:

```toml
[[standalone_repository]]
name = "winter-harness"
url = "git@github.com:paul-gross/winter-harness.git"
```

Then run `winter ws init`.

## 🎯 Scope

Provides additional guidance to agents working on functionality within the target of the winter workspace, improving the quality of agent output within winter itself.

See [`index.md`](./index.md) for the file topology.

## License

MIT.
