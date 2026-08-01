# Convention-file convention

How to author a **convention file** — one of the `Rule` / `Why` / `Do` / `Don't` docs under `architecture/`, `standards/`, `documentation/`, and the other domains of this repo. These files are the ecosystem's agent-facing rules; this one governs their shape and voice.

## Shape

A convention file follows a `Rule` / `Why` / `Do` / `Don't` / `See also` skeleton, with feature-specific sections inserted as needed. Match the closest existing sibling in `architecture/` or `standards/` rather than inventing a layout.

- **Rule** — the convention itself, stated as an imperative or an invariant. Terse, no preamble.
- **Why** — the forward-looking reason the rule exists: the failure it prevents, not the change history that produced it.
- **Do** / **Don't** — paired concrete examples, the smallest surface that makes the rule land. Prefer a code block or a one-line example over prose.
- **See also** — pointers to the adjacent conventions, described by read-trigger, never by restating their contents.

A doc whose sections need different read-triggers or serve different audiences is two conventions — split it, or turn the leaf into a hub.

## Voice

Terse, opinionated, code-first — Do/Don't pairs over prose. One sentence per physical line. Habits a careless first draft produces that the finished file has trimmed past:

- **Describe outcomes, not contents.** A section body or router row says what the reader gets or when to go, not what sits inside a file. "An opinionated guide for X" is the whole clause; the list of what it covers does not belong.
- **One point, no restatement.** Resist a second supporting paragraph that re-says the first. If two feel needed, the first is too vague.
- **Don't position relative to siblings.** State what THIS rule is, not "X lives in A, Y lives in B." A cross-reference earns its place only when readers will otherwise confuse the two.
- **Beware colon-then-elaboration.** A clause of the form `**Name** — summary: detail, detail, detail` almost always reads better with everything after the colon cut; if the details matter they earn their own bullet or the linked file's job.

## See also

- [`../documentation/writing-readme.md`](../documentation/writing-readme.md) — the sibling shape guide for README files (a different reader, a different skeleton) that shares this voice.
