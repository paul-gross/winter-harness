# Principles for agent-facing markdown

Cross-cutting principles that apply to every agent-facing markdown file in the winter ecosystem — READMEs, extension `index.md`, skills, agents, `CLAUDE.md`, `context/` convention docs. Principles that apply to one specific file shape live in their own convention file (`writing-readme.md`, `writing-skill.md`, etc.) and are not duplicated here.

Each principle follows a `Rule` / `Why` / `Do` / `Don't` shape.

## No retrospective framing

**Rule.** Don't anchor current-state explanations to prior versions of the same doc, the prior shape of the code it describes, or the change history that produced today's state. State the current rule and the forward-looking reason behind it.

Phrases the pattern wears: *"earlier drafts..."*, *"previously this was..."*, *"we used to..."*, *"the old approach was Z, but..."*, *"this used to be X"*. When the draft reaches for one of these, the rewrite is to delete the historical clause and keep the forward-looking reason underneath.

**Why.** A doc that says *"earlier drafts delegated to X, which silently broke"* is loaded into every future agent context, where it pays token rent to describe a version of the doc no reader will ever see. The reader needs the current rule and the reason it exists today; the historical clause is dead weight. Change history belongs in commit messages and PR descriptions — different audience, different lifetime.

**Exception.** History-by-design files keep their framing — `CHANGELOG.md`, `retrospective.md`, migration notes, post-mortem reports. There the change history *is* the content.

**Where superseded history goes.** The framing rule has a placement complement: a current reference page describes only the supported present and its forward-looking rationale. Superseded behavior, before/after examples, upgrade steps, and breaking-change narratives are not rewritten in place — they move to a changelog or an explicitly named migration document, and the current page links there only while an active migration still needs the reader to find it. When no active migration needs it, the dead history is deleted outright, not relocated to preserve it: a reference page carries the present, and the commit history already carries the past.

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

## One canonical owner per fact

**Rule.** Every behavioral rule, schema field, default, protocol requirement, or operational invariant has exactly one authoritative document — its canonical owner. Any other document that needs the fact links to the owner and may state *why* the reader should follow the link, but never restates the detail. When two files describe the same fact, exactly one is canonical and the rest are pointers; "for convenience" is not a second owner.

**Why.** A fact written in two places is a fact that will be edited in one. The unedited copy keeps asserting the superseded value, and nothing flags the divergence until a reader follows the stale copy and acts on it. Single ownership makes the canonical value the only value: every reader resolves to the same place, and an edit there reaches all of them at once. Which document *is* the owner follows the reader's task — see [`./organization.md`](./organization.md) §"Classify content by the reader's task".

**Do.**

- Pick the owner, name it, and point every other mention at it: *"Binding a provider is a configuration concern — see `capabilities.md`."* The pointer carries the stake, not the option list.
- When you find the same fact in two files, make one canonical and reduce the other to a pointer in the same change.

**Don't.**

- Repeat a table, option list, default set, or contract clause in a second file so a reader "doesn't have to follow the link" — the convenience lasts until the first edit, then the copy lies.
- Leave two files each describing the schema with neither marked as the owner, so the next editor changes whichever they happened to open.

**For reviewers.** Flag repeated tables, option lists, defaults, contract wording, and exhaustive summaries; identify which file remains canonical and reduce the rest to pointers.

## Point, don't duplicate

The reference-shape corollary of one-canonical-owner: that rule says a fact lives in one place; this one says what the *other* places may say about it.

**Rule.** When one agent-facing doc points at another file or section — an index or "when to read" table row, a `CLAUDE.md` navigation entry, an extension `index.md` line, a cross-reference — describe the target by what the reader gets there or when to go, not by enumerating or copying its contents. A pointer that restates its target's contents is a second copy of them, and the copy drifts the moment the target changes.

**Why.** Duplicated contents rot silently. An index row that lists the rules inside the file it points at keeps asserting the old list after a rule is added or renamed, and nothing flags the staleness until a reader follows the link and hits the mismatch. A pointer written as an outcome — "read before authoring an agent-facing file" — stays true across every edit to the target, and the reader follows the link for the current detail, which lives in exactly one place.

**Do.**

- Index / "when to read" row described by read-trigger: `| ./principles.md | Cross-cutting principles for any agent-facing markdown file — read before authoring or editing one |`
- `CLAUDE.md` navigation row described by destination: `| Worktree git operations | context/worktree-ops.md |` — names where to go, not the steps the target lists.

Describe the destination; let the reader follow the link for the contents.

**Don't.**

- Index row enumerating the target's contents: `| ./principles.md | The no-retrospective-framing, no-manual-line-wrapping, and point-don't-duplicate rules |` — the list must be re-synced by hand every time a principle is added or renamed.
- An extension `index.md` line or `CLAUDE.md` row that restates the contents of the file it points at, instead of naming the destination — a second copy that drifts.

The enumerated list reads as complete, so the next author trusts it instead of the target — and it is wrong the first time the target changes.

**See also.** [`./evaluating-harness-changes.md`](./evaluating-harness-changes.md) — the cold behavioral-expectation eval to run before shipping this principle; its enforcement instance applies, since `context-reviewer` enforces it.

## Examples are illustrative, not normative

**Rule.** An example shows the smallest surface that makes the canonical rule concrete. It never reproduces a whole schema, template, exhaustive option set, or second specification already owned elsewhere. If an example would have to change every time the canonical contract changes, it is too big: cut it to the part that illustrates the point and link to the owner for the rest.

**Why.** A full-schema "example" is a second copy of the schema wearing an example's clothes. It drifts from its canonical owner exactly like any other duplicate (the one-canonical-owner rule), but the word "example" disguises the duplication so a reviewer waves it through and the field list now lives in two places. A minimal example carries no contract of its own — there is nothing in it to keep in sync.

**Do.**

- Show one representative entry, enough to make the shape concrete, and link to the canonical schema for the full field set.
- When an example must demonstrate a non-obvious or counter-example form, mark it so a lint or reviewer does not mistake it for a live reference (`<!-- winter-lint:example -->`; see [`../agent-context/references.md`](../agent-context/references.md)).

**Don't.**

- Paste an entire manifest block with every field "as an example" into a file that does not own the schema — the field list is now duplicated, and it is wrong the first time the schema changes.

**For reviewers.** Flag an example that must be synchronized whenever the canonical contract changes; it is a disguised duplicate, not an illustration.
