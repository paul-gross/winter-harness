# Agent-facing markdown conventions

The **meta layer** of winter-harness: conventions for the agent-facing markdown that the rest of the winter ecosystem is composed of. Independent of language or runtime. Pairs with code conventions (`python/`) and process conventions (`workflows/`).

Paired reviewer: `context-reviewer` reads this directory before reviewing any change to agent-facing markdown.

| File | When to read |
|------|--------------|
| `./winter-references.md` | Writing a cross-context path reference, naming an agent / skill / slash command, or reviewing any document that does so |
| `./writing-readme.md` | Writing or editing a `README.md` for any winter ecosystem repo |
| `./writing-extension-index.md` | Writing, editing, or auditing a winter extension's top-level `index.md` — what belongs there vs. what's behind-the-scenes (the file is auto-loaded into every agent context) |
| `./writing-skill.md` | Authoring a skill — picking between the self-contained and thin (`SKILL.md` + `ai/<name>/process.md`) shapes |

This directory is intended to grow with companion docs (e.g. `writing-agent.md`, `writing-claude-md.md`, `writing-ai-doc.md`) as their need surfaces.
