# Documentation convention

The "no undocumented feature" invariant for the winter ecosystem. A change that adds or alters user-facing surface updates the documentation that describes that surface, in the same unit of work — the expectation the harness already holds for tests, applied to docs.

## Rule

When a change touches **user-facing surface**, the documentation that describes that surface is updated in the same commit. User-facing surface is anything an adopter learns winter from:

- a `winter` subcommand, flag, or `config.toml` key;
- an extension capability — a hook, a service, a dashboard plugin, an env-root file (`up` / `down` / `status`, `.winter.env`);
- a skill or agent the workspace installs;
- a convention an agent is expected to follow.

The unit of work is the commit. A feature commit with no documentation delta is the anti-pattern, the same way a feature commit with no test is. Documented state then only holds or improves as features land — it never silently rots.

## One source per fact

Every concept has exactly one canonical home: the agent-facing markdown already in the ecosystem — `context/` directories, extension `index.md` files, and the `winter-harness` convention files. That is what an authoring change edits.

If the ecosystem publishes a rendered documentation site, its pages are a **human-facing view over** those canonical sources, not a fork of them. The rendered site may be an in-repo `docs/` tree built by a static-site generator, **or a separate docs-site repo** — for this ecosystem it is the latter: **`winter-docs`**, a standalone repo, not a `docs/` tree inside the code repos (see [`./documentation-governance.md`](./documentation-governance.md) for what it is). Do not conclude "nothing rendered narrates this surface" just because the changed repo has no `docs/` tree; the public site lives in `winter-docs`, so a surface change in `winter` or an extension still owes a `winter-docs` check. A docs page narrates a concept for an adopter and **links back** to the canonical source for authoritative detail (exact flags, config keys, convention text). It does not re-copy that detail — a second copy drifts the moment the canonical source changes, and the drift is invisible until an adopter hits it.

So "update the docs" has two halves, and a change owes both:

1. **Currency** — the canonical `context/` / `index.md` / convention source for the changed surface is updated in the same commit.
2. **Non-duplication** — if the rendered site (`winter-docs`) already narrates that surface, its page is updated to match, and it still references rather than restates the canonical detail. `winter-docs` is a separate repo, so this half of the invariant reaches across repos — see [`../workflows/feature-delivery.md`](../workflows/feature-delivery.md) §"Anatomy of feature delivery" for where it sits in a delivery.

## No negative space

Document the **positive contract** of a surface — when, where, and how it fires — and let the absence of a stated trigger mean it doesn't fire. Do not enumerate the cases where a hook, command, or flag does *not* fire, or the conditions under which it doesn't apply.

State scope affirmatively: *"the `on_env_init` hook fires during `winter ws init`, once per repo, after the worktree is created."* A reader infers when it does *not* fire from the absence of that trigger. A "does not fire on …" clause is open-ended — the negative set is unbounded, so any enumeration is incomplete and rots as sibling surfaces appear.

This bars documenting where a *runtime behavior* — a hook, command, or flag — does not fire. It does not bar an authoring rule from scoping itself with an explicit out-of-scope / exclusions section: that bounds a reviewer's expectations, not a feature's behavior, and is closed rather than open-ended.

## Why

A doc that lags its feature is worse than no doc — it tells an adopter something that is no longer true. The only reliable gate is the unit of work: if the docs delta rides in the same commit as the feature, the two cannot diverge. Deferring it to "a docs pass later" guarantees divergence, because the next author has no signal that the gap exists. Tests earn their place in the commit for the same reason; docs are no different.

## Do

- Land the canonical-source edit in the same commit as the feature. A new `winter ws foo` subcommand updates `winter-cli`'s `context/` reference in that commit; a new extension hook updates the extension's `index.md` in that commit.
- In a rendered docs page (in `winter-docs`), link to the canonical source for the authoritative detail: *"see [feature-delivery](…) for the full pre-push sequence."*
- When a feature has no adopter-facing angle yet (internal refactor, scaffolding), say so — the absence of a docs delta is a deliberate, reviewable call, not an oversight.

## Don't

- Ship a `winter` subcommand, extension capability, skill, agent, or convention change with no documentation delta anywhere in the commit.
- Copy a command's flag list, a `config.toml` schema, or a convention's exact wording into a `winter-docs` page. Link to the canonical source instead — the copy will drift.
- Conclude no docs update is owed because the changed repo has no in-repo `docs/` tree. The public site is the separate `winter-docs` repo — check it.
- Defer the docs update to a follow-up commit "once the feature settles." The follow-up is the divergence.

## See also

- [`../workflows/feature-delivery.md`](../workflows/feature-delivery.md) §Pre-push checks — where the invariant rides the existing pre-push gate.
- [`../canon/principles.md`](../canon/principles.md) §"No retrospective framing" — the canonical-source-is-current-state rule a docs page must also obey.
- [`../canon/progressive-disclosure.md`](../canon/progressive-disclosure.md) — how to structure the canonical source itself for discovery: when to split a doc into a hub `index.md` plus per-sub-topic files, and how to write the routing rows.
- [`./writing-extension-index.md`](./writing-extension-index.md) — what belongs in an extension `index.md`, the most common canonical source a feature touches.
- [`./documentation-governance.md`](./documentation-governance.md) — the companion contract: which content belongs on which documentation surface, and the consumable-extension vs. example distinction. This file keeps docs current; that one places them.
- [`../canon/evaluating-harness-changes.md`](../canon/evaluating-harness-changes.md) — the cold behavioral-expectation eval that extends this invariant from currency to efficacy: currency keeps the doc true, that eval proves a cold agent reaches and acts on it.
