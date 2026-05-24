# README convention

Conventions for `README.md` files across the winter ecosystem (the framework, extensions, and meta workspaces). The point is consistency — readers should be able to scan any winter repo's README and find the same things in roughly the same order.

## Rule

- Title is `# <emoji> <repo-name>` — every winter repo uses ❄️ as the title emoji.
- Every top-level section (`##`) starts with an emoji, **except `License`**.
- One-paragraph lede directly under the title: what this is and what it does. No "## Overview" header.
- Sections appear in the order listed below. Skip sections that don't apply rather than rearrange.
- Link to other ecosystem repos with their full codeberg URL — never bare names.

## Voice — common pitfalls

Habits to resist. Each one is something a careless first draft will produce; the README only earns its keep when it's been trimmed past them.

- **Describe outcomes, not contents.** Feature bullets and section bodies say what the reader gets, not what's inside the directory or file. "An opinionated guide for developing Python applications" is the whole bullet — the list of what the guide covers does not belong here.
- **One-paragraph lede, no follow-up.** Resist the urge to add a second supporting paragraph that re-states the first. If two paragraphs feel needed, the first is too vague.
- **Installation tells the reader how to install. Period.** Don't list what gets symlinked, what becomes spawnable, or what path notation is unlocked afterward. Effects belong in `index.md` (see `winter-harness:/harness/writing-extension-index.md` for what specifically) or in the file itself — not in Installation.
- **Don't position relative to siblings.** Avoid "X lives in winter-workflow, Y lives in winter-service-tmux." Tell the reader what THIS repo is. Cross-references only earn their place when readers will otherwise actively confuse repos.
- **Beware colon-then-elaboration.** A bullet of the form `**Name** — summary: detail, detail, detail.` almost always reads better with everything after the colon deleted. If the details matter, they earn their keep as their own bullets or as the linked file's job.

## Common sections (extensions)

In order. Use these names verbatim when the section applies.

| Section | Emoji | When to include |
|---------|-------|-----------------|
| `# ❄️ <name>` | ❄️ | Always — title |
| `## ✨ Features` | ✨ | Always — bulleted feature list |
| `## 🚀 Installation` | 🚀 | Always — `[[standalone_repository]]` snippet + `winter ws init`. Title as `## 🚀 Installation & Setup` when post-install setup steps are required (/ws-setup integration). |
| `## ⚙️ Configuration` | ⚙️ | When the extension exposes settings (`winter-ext.toml` options, env vars, config keys consumers must set) |
| `## 🧩 How it works` | 🧩 | When the extension has non-obvious mechanics worth explaining |
| `## 🎯 Scope` | 🎯 | When boundaries against other extensions need calling out |
| _project-specific sections_ | various | As needed (see below) |
| `## License` | (none) | Always last — no emoji |

Between Scope and License, add any project-specific sections the repo needs — e.g. `🌿 Forking`, `🧭 Principles`, or framework-only sections like `🌲 Winter Ecosystem`, `⌨️ Winter CLI`, `🚀 Quick Start`, `💭 Why the name, Winter?`. Pick emojis using the guidance below.

## Emoji choices

When an extension needs a section not in the table above, pick an emoji that's:

- **Concrete** — a thing, not an abstraction. 🧭 (compass) for principles beats 💡 (idea).
- **Distinct** — don't reuse an emoji that already appears in the standard set above for a different meaning.
- **Theme-coherent** — the framework uses 🌲 / 🌿 for the ecosystem; extensions can lean into nature/winter motifs (🏔️, 🌨️, 🪵) when it fits.

## Do

```markdown
# ❄️ winter-product

A [winter](https://codeberg.org/pgross/winter) extension that adds product-workflow tooling to a winter workspace: planning conventions, product agents, and the `todo` skill.

## ✨ Features

- **Planning conventions** — ...
- **Product agents** — ...

## 🚀 Installation

Add to `.winter/config.toml`:

\`\`\`toml
[[standalone_repository]]
name = "winter-product"
url = "git@codeberg.org:pgross/winter-product.git"
\`\`\`

Then run `winter ws init`.

## 🎯 Scope

Planning and task tracking only. Code conventions live in [winter-harness](https://codeberg.org/pgross/winter-harness).

## License

MIT.
```

## Don't

```markdown
# winter-product                              ← missing ❄️

## Overview                                   ← redundant with the lede paragraph

## Installation                               ← missing emoji

## 🎉 License                                 ← License never gets an emoji
```
