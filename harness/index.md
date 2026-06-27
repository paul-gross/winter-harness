# Agent-facing markdown conventions

Winter-ecosystem conventions for the agent-facing markdown the framework is composed of — READMEs, extension `index.md` files, skills, doc governance, path references. These are specific to winter; the universal substrate they rest on is the [Canon layer](../canon/index.md). Pairs with code conventions (`architecture/`, `standards/`) and process conventions (`workflows/`).

Paired reviewers: `context-reviewer` enforces these conventions and the [Canon](../canon/index.md) when reviewing agent-facing markdown; `documentation-reviewer` enforces the doc-authoring conventions here (`writing-readme.md`, `writing-documentation.md`, `documentation-governance.md`) when reviewing human-facing public documentation. Both discover these conventions by walking the workspace's discovery chain, not from a hard-coded path. The cold behavioral-expectation eval in [`../canon/evaluating-harness-changes.md`](../canon/evaluating-harness-changes.md) applies whenever a change adds context an agent is expected to act on — review being one instance.

| File | When to read |
|------|--------------|
| `./documentation-governance.md` | Authoring or auditing the public framework docs (docs site, READMEs) — the consumable-extension catalog vs. the Examples list, and the consumable-extension vs. example/reference distinction |
| `./markdown-lints.md` | Mechanically checking the path-notation, routing-reference, and link-anchor conventions — the three `winter lint` scripts in `./scripts/`, what each flags, and how to run them |
| `./winter-references.md` | Writing a cross-context path reference, naming an agent / skill / slash command, or reviewing any document that does so |
| `./writing-documentation.md` | Landing a feature — the "no undocumented feature" invariant: a change to user-facing surface updates the docs that render it, in the same commit |
| `./writing-extension-index.md` | Writing, editing, or auditing a winter extension's top-level `index.md` — what belongs there vs. what's behind-the-scenes (the file is auto-loaded into every agent context) |
| `./writing-readme.md` | Writing or editing a `README.md` for any winter ecosystem repo |
| `./writing-agent.md` | Authoring an agent — the frontmatter contract (`name`, `description`, `model`, `tools`) and the canonical-name rule |
| `./writing-skill.md` | Authoring a skill — picking between the self-contained and thin (`SKILL.md` + `context/<name>/process.md`) shapes |
| `./tooling.md` | Workspace tooling conventions — GitHub CLI (`gh`) rule |
