# Tooling conventions

Cross-cutting rules for the **external development tools** the winter ecosystem drives — the tools themselves, not the markdown a rule happens to be written in.

This domain owns conventions for external tools such as the `gh` CLI. It does **not** own Markdown authoring merely because a rule is written in Markdown — that is agent context ([`../agent-context/index.md`](../agent-context/index.md)).

Parent: `../index.md` (root topology).

| File | When to read |
|------|--------------|
| [`./github.md`](./github.md) | Any GitHub operation — issues, PRs, releases, repo management go through the `gh` CLI, never the web UI |
