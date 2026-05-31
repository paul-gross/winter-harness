# Agent-facing markdown conventions

The **meta layer** of winter-harness: conventions for the agent-facing markdown that the rest of the winter ecosystem is composed of. Independent of language or runtime. Pairs with code conventions (`python/`) and process conventions (`workflows/`).

Paired reviewers: `context-reviewer` reads this directory before reviewing agent-facing markdown; `documentation-reviewer` reads the doc-authoring conventions here (`writing-readme.md`, `writing-documentation.md`, `documentation-governance.md`) before reviewing human-facing public documentation. The eval procedure in `./evaluating-harness-changes.md` is broader than review — it applies whenever a change adds context an agent is expected to act on, the enforcement-rule case being one instance.

| File | When to read |
|------|--------------|
| `./documentation-governance.md` | Authoring or auditing the public framework docs (docs site, READMEs) — the consumable-extension catalog vs. the Examples list, and the consumable-extension vs. example/reference distinction |
| `./evaluating-harness-changes.md` | Shipping a change that adds context an agent should act on (new skill, agent, rule, feedforward doc, or routing) — the cold-spawn behavioral-expectation eval to run before push |
| `./facts-vs-methodology.md` | Building any agentic feature (reviewer, skill, context doc) — deciding where the facts it acts on live (the harness, or the review target's own harness) vs. where the methodology it applies lives (the workflow) |
| `./markdown-lints.md` | Mechanically checking the path-notation and routing-reference conventions — the two `winter lint` scripts in `./scripts/`, what each flags, and how to run them |
| `./principles.md` | Cross-cutting principles for any agent-facing markdown file — read before authoring or editing one |
| `./winter-references.md` | Writing a cross-context path reference, naming an agent / skill / slash command, or reviewing any document that does so |
| `./writing-documentation.md` | Landing a feature — the "no undocumented feature" invariant: a change to user-facing surface updates the docs that render it, in the same commit |
| `./writing-extension-index.md` | Writing, editing, or auditing a winter extension's top-level `index.md` — what belongs there vs. what's behind-the-scenes (the file is auto-loaded into every agent context) |
| `./writing-readme.md` | Writing or editing a `README.md` for any winter ecosystem repo |
| `./writing-skill.md` | Authoring a skill — picking between the self-contained and thin (`SKILL.md` + `ai/<name>/process.md`) shapes |
