# ❄️ winter-harness

A [winter](https://codeberg.org/pgross/winter) extension curated for the meta [winter-workspace](https://codeberg.org/pgross/winter-workspace) itself.

## ✨ Features

- **Exemplar for others** — serves as an example harness project, a reference others can pull ideas from when assembling their own harness.
- **Python conventions** (`python/`) — an opinionated guide for developing Python applications.
- **Agent-facing markdown conventions** (`harness/`) — an opinionated guide for writing the markdown that agents read across the winter ecosystem.
- **Canonical exemplars** (`exemplars/python/`) — reference `.py` files showing the expected shape of recurring patterns (repository class, domain object) plus `cli-architecture.md`, the live tour of how the conventions are applied in winter-cli today.

## 🚀 Installation

Add to the workspace's `.winter/config.toml`:

```toml
[[standalone_repository]]
name = "winter-harness"
url = "git@codeberg.org:pgross/winter-harness.git"
```

Then run `winter ws init`.

## 🎯 Scope

Provides additional guidance to agents working on functionality within the target of the winter workspace, improving the quality of agent output within winter itself.

See [`index.md`](./index.md) for the file topology.
