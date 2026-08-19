# Documentation conventions

Conventions for **public / adopter-facing documentation** — the published docs site (`winter-docs`) and every repo's
`README.md`: README form, the no-undocumented-feature currency invariant, the canonical-source-versus-rendered-view
rule, and the consumable-extension-versus-example catalog classification. The audience is a human evaluating or adopting
winter, not an agent traversing context.

This domain owns public / adopter-facing documentation policy. It does **not** own agent / skill prompt structure or
Markdown path-notation mechanics — those are agent context ([`../agent-context/index.md`](../agent-context/index.md)).

Paired reviewer: `documentation-reviewer` enforces these conventions when reviewing human-facing public documentation,
discovering them by walking the workspace's discovery chain rather than from a hard-coded path.

Parent: `../index.md` (root topology).

| File                                                       | When to read                                                                                                                                                                                  |
| ---------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [`./governance.md`](./governance.md)                       | Authoring or auditing the public framework docs (docs site, READMEs) — the consumable-extension catalog vs. the Examples list, and the consumable-extension vs. example/reference distinction |
| [`./writing-readme.md`](./writing-readme.md)               | Writing or editing a `README.md` for any winter ecosystem repo                                                                                                                                |
| [`./feature-documentation.md`](./feature-documentation.md) | Landing a feature — the "no undocumented feature" invariant: a change to user-facing surface updates the docs that render it, in the same commit                                              |
