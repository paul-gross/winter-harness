# Documentation governance

The contract for the winter ecosystem's **public framework documentation** — the published docs site (the `winter-docs` repo) and every repo's `README.md` — and specifically for the distinction between *consumable* and *example* extensions. This is the harness-owned source of truth a documentation reviewer checks the public docs against. How to *write* the content lives in sibling conventions and is referenced, not duplicated, here.

## What this contract governs

This file governs the **public framework-docs surface** — the published documentation site and every winter repo's `README.md`, the docs a consumer reads to decide whether and how to adopt winter. The published documentation site is its own repo, **`winter-docs`** (Astro/Starlight, deployed to GitHub Pages) — it is *not* an in-repo `docs/` tree, so it is a delivery target in its own right, not only the dev service that `workspace:/context/project/setup-tmux.md` runs. Keeping its pages current with the surfaces they narrate is the no-undocumented-feature invariant in [`./feature-documentation.md`](./feature-documentation.md); placing a change's commits within a feature delivery is [`../workflows/feature-delivery.md`](../workflows/feature-delivery.md). On that surface its one job is the **consumable-extension catalog** and the **Examples** list defined below: which repos appear in each, and how each is framed.

It is deliberately narrow, and it does **not** enumerate every place documentation lives — `context/` docs, the harness conventions themselves, agent and skill definitions, and `architecture/`/`standards/` guides all carry documentation and are governed elsewhere. The adjacent surfaces a change commonly touches have their own owners: a repo's `README.md` structure → [`./writing-readme.md`](./writing-readme.md); an extension's auto-loaded `index.md` → [`../agent-context/writing-extension-index.md`](../agent-context/writing-extension-index.md); keeping any doc current with the code it describes → [`./feature-documentation.md`](./feature-documentation.md). This contract's only concern is that a reference implementation is classified and placed correctly on the public surface.

`AGENTS.winter.md` is **not** an authored surface. The CLI generates it by listing every installed standalone that has a root `index.md`, so each extension's `<name>:` path notation resolves. It is runtime state, not curated documentation — the consumable-vs-example classification is **not** expressed there. Do not hand-edit it, and do not treat its uniform list as a statement that every entry is a consumable product.

## Consumable extensions vs. examples

Two kinds of repository compose into a winter workspace, and the docs must not blur them.

**Consumable extension.** A *generic, opinion-neutral* capability any workspace installs to gain function — service orchestration, issue tooling, a backlog model. The reader wants the function and adopts it without buying into anyone's methodology. Current consumables: `winter-product`, `winter-service-tmux`, `winter-github`.

**Example (reference implementation).** The maintainer's own *opinionated* implementation of a swappable concern — the agentic workflow, the conventions, the workspace itself. It installs and runs like any extension and is fully usable as-is, but it embodies one personal take that winter deliberately keeps interchangeable; the docs offer it as a reference to adopt **or** fork, not as a fixed part of the framework. Current examples:

- `winter-workflow` — the maintainer's personal agentic workflow (the blizzard team, the review loops). Turnkey — install it and the `/wf-*` skills and `wf-*` agents work — but interchangeable by design: adopt it as-is or fork your own.
- `winter-harness` — the maintainer's own conventions library. Usable directly (reference its files by path notation), but a personal, opinionated set — adopt it or fork the shape and supply your own facts.
- `winter-workspace` — the meta-workspace winter itself is built in, pre-wired to the maintainer's repos. A worked example of an assembled workspace, not a template to clone.

The discriminator: **is this a generic, opinion-neutral capability (consumable), or the maintainer's personal, opinionated implementation of a swappable concern (example)?** Both install and run the same way; the difference is whether it adds a neutral function or embodies one interchangeable opinion. When in doubt, ask whether the reader is adopting a *function* or adopting *someone's way of working*.

## Rule

- The framework's **consumable-extension catalog lists only consumable extensions.** Never list an example there.
- Reference implementations appear in a separate **Examples** list. Each entry states **what it is** and **why it is a personal, swappable reference** — one to adopt as-is or fork, not a neutral framework part.
- The two lists are visibly distinct — a reader scanning the catalog must never mistake one of the maintainer's opinionated, swappable instances for a neutral, canonical capability.

## Why

The catalog is a buy-list of functions. An example sitting in it reads as a neutral, canonical capability, so the reader adopts the maintainer's personal workflow or conventions as *the* way to work — never realizing winter intends these to be swapped for their own. Grouping examples separately, each labelled with what it is and why it's a personal reference, tells the reader: this one is opinionated — use it or fork it, your call. The classification is a documentation concern, not a packaging one: an example installs and runs exactly like a consumable; only how the docs present it changes.

## Do

```markdown
## Extensions

| Extension | Adds |
|-----------|------|
| **winter-product** | A product backlog model with refinement agents and skills. |
| **winter-service-tmux** | tmux-based service orchestration. |
| **winter-github** | AI-native GitHub issue tooling. |

## Examples

The maintainer's own opinionated, swappable implementations — use them as-is or fork your own.

- **winter-workflow** — the maintainer's agentic workflow. Turnkey, but interchangeable:
  adopt its agent roles and review loops, or fork them for your own.
- **winter-harness** — the maintainer's conventions library. Usable as-is, or a
  worked example of encoding conventions to fork and adapt.
- **winter-workspace** — the meta-workspace winter is built in. A worked example of
  an assembled workspace, not a template to clone.
```

## Don't

```markdown
## The maintained extensions

| Extension | Adds |
|-----------|------|
| **winter-harness**  | The conventions layer. |     ← example listed as a consumable product
| **winter-workflow** | The agentic workflow. |        ← example listed as a consumable product
| **winter-product**  | A product backlog model. |
```

Listing `winter-harness` and `winter-workflow` in the consumable catalog presents the maintainer's personal conventions and workflow as neutral framework capabilities. They are opinionated, swappable instances — they belong in an Examples list that says so.

## See also

- [`../canon/facts-vs-methodology.md`](../canon/facts-vs-methodology.md) — the general rule this contract is an instance of: the doc-classification facts live here in the harness; the workflow's documentation-review skill reads them rather than carrying a copy.
- [`./feature-documentation.md`](./feature-documentation.md) — the companion docs convention: this file governs *what content belongs on which surface*; that one governs *keeping it current* (the "no undocumented feature" invariant) and the canonical-source-vs-rendered-site relationship.
- [`../agent-context/writing-extension-index.md`](../agent-context/writing-extension-index.md) — what belongs in an extension's auto-loaded `index.md` (the runtime-surface rule this contract points to for that surface).
- [`./writing-readme.md`](./writing-readme.md) — README structure for the framework and extension docs.
- [`../canon/evaluating-harness-changes.md`](../canon/evaluating-harness-changes.md) — the cold behavioral-expectation eval to run before shipping a change to this contract; its enforcement instance applies, since a reviewer enforces it.
