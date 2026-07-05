# The four levers

The Canon names **four levers** of agent productivity: **observability**, **testability**, **discoverability**, and **pluggability**.
A system an agent can see into, verify, navigate, and swap parts of is a system an agent can extend.
These are universal — true of any harness, in any language, project, or workflow — which is why they are Canon rather than any one workflow's opinion.

## The levers

- **Observability** — the agent can *see into* the system. Logs, status surfaces, diffs, and readable state let it know what happened without reverse-engineering the code.
- **Testability** — the agent can *verify* its own work. A feedback loop tight enough (compile, lint, test, eval) that the agent confirms correctness before handing off, rather than throwing the change over the wall.
- **Discoverability** — the agent can *navigate* to what it needs. A discovery chain (`CLAUDE.md` → index → leaf) delivers the right context to a cold agent without it knowing where to look in advance.
- **Pluggability** — the agent can *swap parts*. Extension seams and interfaces let it add or replace a component without rewriting the whole.

## Why these four

They compound: an agent that can see the system's state, verify its own changes, find the context that governs them, and replace a part in isolation can extend the system end-to-end on its own. A harness weak on any one of them caps agent autonomy at that lever — invisible state forces guesswork, an absent feedback loop forces a human verifier, a broken discovery chain forces hand-fed context, a monolith forces a full rewrite to change one part. A change that strengthens any of the four makes the next agent task more autonomous, which is the standard a harness change is held to.

## See also

- [`./facts-vs-methodology.md`](./facts-vs-methodology.md) — pluggability across the harness/workflow seam: the workflow is swappable because the facts it reads live in the harness.
