# Architecture

Cross-cutting and application-specific architecture concerns for the winter ecosystem — how the generic conventions in `../python/*.md` are realized in each real application, and design tenets that span applications. Where `python/` states a language-level rule and `exemplars/` shows a shape in isolation, this layer documents the architecture of a concrete winter application end to end.

**Read this index before changing the code of any winter application** — the `winter` CLI, an extension's Python, a service orchestrator. It routes you to the architecture doc for the surface you're touching so you build with the existing structure rather than reverse-engineering it. Follow the one row that matches your change; don't read the whole tree.

| Architecture doc | Read when… |
|------------------|------------|
| [winter-cli.md](./winter-cli.md) | …you're adding or changing a `winter` CLI command — its module layout, handler/service split, or argument surface. |

As more applications gain architecture docs, they fan out from this index.
