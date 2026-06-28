# Agent-context conventions

Conventions for authoring and validating **agent context** — the material an agent loads or traverses to do work: agents, skills, extension `index.md` files, routing tables, cross-context path references, and the lints that mechanically enforce them. Specific to winter; the universal substrate they rest on is the [Canon](../canon/index.md).

This domain owns the machine-consumed authoring surface. It does **not** own public README / docs-site policy — that is [`../documentation/index.md`](../documentation/index.md); application architecture — [`../architecture/index.md`](../architecture/index.md); or general development tools — [`../tooling/index.md`](../tooling/index.md).

Paired reviewer: `context-reviewer` enforces these conventions and the [Canon](../canon/index.md) when reviewing agent-facing markdown, discovering them by walking the workspace's discovery chain rather than from a hard-coded path. The cold behavioral-expectation eval in [`../canon/evaluating-harness-changes.md`](../canon/evaluating-harness-changes.md) applies whenever a change adds context an agent is expected to act on — review being one instance.

Parent: `../index.md` (root topology).

| File | When to read |
|------|--------------|
| [`./references.md`](./references.md) | Writing a cross-context path reference, naming an agent / skill / slash command, or reviewing any document that does so |
| [`./writing-agent.md`](./writing-agent.md) | Authoring an agent — the frontmatter contract (`name`, `description`, `model`, `tools`) and the canonical-name rule |
| [`./cross-harness-projection.md`](./cross-harness-projection.md) | Understanding how one canonical agent becomes per-harness copies — the `claude:`/`codex:`/`opencode:` override blocks, the model-tier→id table, lossy projection, and identity across harnesses |
| [`./writing-skill.md`](./writing-skill.md) | Authoring a skill — picking between the self-contained and thin (`SKILL.md` + `context/<name>/process.md`) shapes |
| [`./writing-extension-index.md`](./writing-extension-index.md) | Writing, editing, or auditing a winter extension's top-level `index.md` — what belongs there vs. what's behind-the-scenes (the file is auto-loaded into every agent context) |
| [`./linting.md`](./linting.md) | Mechanically checking the path-notation, routing-reference, and link-anchor conventions — the three `winter lint` scripts in [`./scripts/`](./scripts/), what each flags, and how to run them |
