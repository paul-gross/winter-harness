# README convention

Conventions for `README.md` files across the winter ecosystem (the framework, extensions, and meta workspaces). The point is consistency — readers should be able to scan any winter repo's README and find the same things in roughly the same order.

## Rule

- Title is `# <emoji> <repo-name>` — every winter repo uses ❄️ as the title emoji.
- Every top-level section (`##`) starts with an emoji, **except `License`**.
- One-paragraph lede directly under the title: what this is and what it does. No "## Overview" header.
- A one-line link to the published documentation site directly under the lede, before the first `##`: `📚 **Documentation:** <https://paul-gross.github.io/winter-docs/>` — same label and placement in every ecosystem repo, so the rendered docs are reachable from any front page. (`winter-docs` is that site; its own README links its deployed URL near the top rather than repeating this line.)
- Sections appear in the order listed below. Skip sections that don't apply rather than rearrange.
- Link to other ecosystem repos with their full GitHub URL — never bare names.

## Voice — common pitfalls

READMEs share the winter authoring voice — the general habits to trim past (describe outcomes not contents, one point with no restating second paragraph, don't position relative to siblings, beware colon-then-elaboration) are owned by [`../agent-context/writing-convention.md`](../agent-context/writing-convention.md) §Voice. README-specific:

- **One-paragraph lede, no follow-up.** The lede is a single paragraph under the title — what this is and what it does. Resist a second supporting paragraph that re-states it; if two feel needed, the first is too vague.
- **Installation tells the reader how to install. Period.** Don't list what gets symlinked, what becomes spawnable, or what path notation is unlocked afterward. Effects belong in `index.md` (see `winter-harness:/agent-context/writing-extension-index.md` for what specifically) or in the file itself — not in Installation.

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

A [winter](https://github.com/paul-gross/winter) extension that adds product-workflow tooling to a winter workspace: planning conventions, product agents, and the `todo` skill.

📚 **Documentation:** <https://paul-gross.github.io/winter-docs/>

## ✨ Features

- **Planning conventions** — ...
- **Product agents** — ...

## 🚀 Installation

Add to `.winter/config.toml`:

\`\`\`toml
[[standalone_repository]]
name = "winter-product"
url = "git@github.com:paul-gross/winter-product.git"
\`\`\`

Then run `winter ws init`.

## 🎯 Scope

Planning and task tracking only. Code conventions live in [winter-harness](https://github.com/paul-gross/winter-harness).

## License

MIT.
```

## Don't

```markdown
# winter-product                              ← missing ❄️

A winter extension that ...                   ← no 📚 docs-site link under the lede

## Overview                                   ← redundant with the lede paragraph

## Installation                               ← missing emoji

## 🎉 License                                 ← License never gets an emoji
```
