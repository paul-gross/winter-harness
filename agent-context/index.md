# Agent-context conventions

Conventions for authoring and validating **agent context** — the material an agent loads or traverses to do work: agents, skills, extension `index.md` files, routing tables, cross-context path references, and the lints that mechanically enforce them. Specific to winter.

This domain owns the machine-consumed authoring surface. It does **not** own public README / docs-site policy — that is [`../documentation/index.md`](../documentation/index.md); application architecture — [`../architecture/index.md`](../architecture/index.md); or general development tools — [`../tooling/github.md`](../tooling/github.md).

Paired reviewer: `context-reviewer` enforces these conventions when reviewing agent-facing markdown, discovering them by walking the workspace's discovery chain rather than from a hard-coded path.

Parent: `../index.md` (root topology).

| File | When to read |
|------|--------------|
| [`./references.md`](./references.md) | Writing a cross-context path reference, naming an agent / skill / slash command, or reviewing any document that does so |
| [`./writing-convention.md`](./writing-convention.md) | Authoring or editing a convention file — a `Rule` / `Why` / `Do` / `Don't` doc under any domain — its skeleton and the shared authoring voice |
| [`./writing-agent.md`](./writing-agent.md) | Authoring an agent — the frontmatter contract (`name`, `description`, `model`, `tools`) and the canonical-name rule |
| [`./cross-harness-projection.md`](./cross-harness-projection.md) | Understanding how one canonical agent becomes per-harness copies — the `claude:`/`codex:`/`opencode:` override blocks, the model-tier→id table, lossy projection, and identity across harnesses |
| [`./writing-skill.md`](./writing-skill.md) | Authoring a skill — picking between the self-contained and thin (`SKILL.md` + `context/<name>/process.md`) shapes |
| [`./writing-extension-index.md`](./writing-extension-index.md) | Writing, editing, or auditing a winter extension's top-level `index.md` — what belongs there vs. what's behind-the-scenes (the file is auto-loaded into every agent context) |
| [`./linting.md`](./linting.md) | Mechanically checking the path-notation, routing-reference, and link-anchor conventions — the three `winter lint` scripts in [`./scripts/`](./scripts/), what each flags, and how to run them |
