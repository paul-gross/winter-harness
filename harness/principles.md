# Principles for agent-facing markdown

Cross-cutting principles that apply to every agent-facing markdown file in the winter ecosystem — READMEs, extension `index.md`, skills, agents, `CLAUDE.md`, `ai/` convention docs. Principles that apply to one specific file shape live in their own convention file (`writing-readme.md`, `writing-skill.md`, etc.) and are not duplicated here.

Each principle follows the `Rule` / `Why` / `Do` / `Don't` shape from [`../CONTRIBUTING.md`](../CONTRIBUTING.md).

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

**See also.** [`./writing-readme.md`](./writing-readme.md) §"Voice — common pitfalls" — sibling voice rules (positioning relative to siblings, colon-then-elaboration).
