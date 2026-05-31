# Principles for agent-facing markdown

Cross-cutting principles that apply to every agent-facing markdown file in the winter ecosystem — READMEs, extension `index.md`, skills, agents, `CLAUDE.md`, `ai/` convention docs. Principles that apply to one specific file shape live in their own convention file (`writing-readme.md`, `writing-skill.md`, etc.) and are not duplicated here.

Each principle follows a `Rule` / `Why` / `Do` / `Don't` shape.

## No retrospective framing

**Rule.** Don't anchor current-state explanations to prior versions of the same doc, the prior shape of the code it describes, or the change history that produced today's state. State the current rule and the forward-looking reason behind it.

Phrases the pattern wears: *"earlier drafts..."*, *"previously this was..."*, *"we used to..."*, *"the old approach was Z, but..."*, *"this used to be X"*. When the draft reaches for one of these, the rewrite is to delete the historical clause and keep the forward-looking reason underneath.

**Why.** A doc that says *"earlier drafts delegated to X, which silently broke"* is loaded into every future agent context, where it pays token rent to describe a version of the doc no reader will ever see. The reader needs the current rule and the reason it exists today; the historical clause is dead weight. Change history belongs in commit messages and PR descriptions — different audience, different lifetime.

**Exception.** History-by-design files keep their framing — `CHANGELOG.md`, `retrospective.md`, migration notes, post-mortem reports. There the change history *is* the content.

**Do.**

- *"Each prompt is inlined to keep step 4 self-contained — no cross-file step-number references."*
- *"Synthesis sections use `## must-fix` / `## consider` / `## clean` to match reviewer output vocabulary."*
- *"`SKILL.md` holds the workflow directly — no sibling doc indirection."*

State the rule, then the forward-looking reason.

**Don't.**

- *"Earlier drafts delegated to `X/SKILL.md` step 4 by step number, which silently broke when those skills renumbered, so the prompts are inlined here."*
- *"Previously the synthesis section was called `## Blocking`, but that collided with the `blocking` mode arg, so we renamed it."*
- *"This used to be a thick `SKILL.md` that delegated to a sibling doc, but we collapsed it."*

Each frames the current state as a correction to an invisible prior version. Strip the historical clause; what remains is the convention.

## No manual line wrapping

**Rule.** Don't hard-wrap prose. Put one sentence or one paragraph per physical line and let the editor and renderer soft-wrap it; never reflow prose to a fixed column. Scope is prose only — code fences, tables, and YAML metadata blocks keep their own formatting and are exempt.

**Why.** Hard-wrapping makes a one-word edit reflow every line below it in the paragraph, so the diff buries the real change in reflow churn and the reviewer can't see what actually moved. One sentence per line keeps each edit localized to the line it touches — the diff shows exactly the words that changed, and reviews stay legible.

**Do.**

```
The reviewer reads the harness conventions before reviewing any agent-facing markdown, so a new rule reaches it through the same discovery chain a future author will traverse.
Each sentence sits on its own physical line; the editor soft-wraps it to the viewport.
```

One sentence per physical line — editing a word touches only that line.

**Don't.**

```
The reviewer reads the harness conventions before reviewing any
agent-facing markdown, so a new rule reaches it through the same
discovery chain a future author will traverse. Each sentence is
hard-wrapped at a fixed column, so editing one word reflows every
line beneath it.
```

Prose reflowed to a fixed column — a one-word edit churns every wrapped line below it.

## Point, don't duplicate

**Rule.** When one agent-facing doc points at another file or section — an index or "when to read" table row, a `CLAUDE.md` navigation entry, an extension `index.md` line, a cross-reference — describe the target by what the reader gets there or when to go, not by enumerating or copying its contents. A pointer that restates its target's contents is a second copy of them, and the copy drifts the moment the target changes.

**Why.** Duplicated contents rot silently. An index row that lists the rules inside the file it points at keeps asserting the old list after a rule is added or renamed, and nothing flags the staleness until a reader follows the link and hits the mismatch. A pointer written as an outcome — "read before authoring an agent-facing file" — stays true across every edit to the target, and the reader follows the link for the current detail, which lives in exactly one place.

**Do.**

- Index / "when to read" row described by read-trigger: `| ./principles.md | Cross-cutting principles for any agent-facing markdown file — read before authoring or editing one |`
- `CLAUDE.md` navigation row described by destination: `| Worktree git operations | ai/worktree-ops.md |` — names where to go, not the steps the target lists.

Describe the destination; let the reader follow the link for the contents.

**Don't.**

- Index row enumerating the target's contents: `| ./principles.md | The no-retrospective-framing, no-manual-line-wrapping, and point-don't-duplicate rules |` — the list must be re-synced by hand every time a principle is added or renamed.
- An extension `index.md` line or `CLAUDE.md` row that restates the contents of the file it points at, instead of naming the destination — a second copy that drifts.

The enumerated list reads as complete, so the next author trusts it instead of the target — and it is wrong the first time the target changes.

**See also.** [`./evaluating-harness-changes.md`](./evaluating-harness-changes.md) — the cold behavioral-expectation eval to run before shipping this principle; its enforcement instance applies, since `context-reviewer` enforces it.
