# Skill convention

How to author a skill across the winter ecosystem. Skills come in two shapes;
[`winter-canon:/facts-vs-methodology.md`](winter-canon:/facts-vs-methodology.md) owns the selection rule, and
[`./methodology-packaging.md`](./methodology-packaging.md) realizes the shared-core shape for winter.

## The two shapes

**Self-contained.** The entire procedure lives in `SKILL.md`. The body is the procedure. The only way to execute it is
to invoke the slash command. Example: `winter-workflow:/skills/commit/SKILL.md`.

**Shared-core.** `SKILL.md` is a thin session adapter that maps invocation inputs and points to a caller-neutral
procedure. Other executors can run the same core without firing the slash command. Example:
`winter-workflow:/skills/cold-review/SKILL.md` → `winter-workflow:/methodology/review/process.md`.

## When to pick the shared-core shape

Use the universal selection rule in [`winter-canon:/facts-vs-methodology.md`](winter-canon:/facts-vs-methodology.md).

Two corollaries:

- **A skill that just executes a single shell command** (or otherwise has no procedure worth re-reading) does not need a
  procedure doc. Don't force the shared-core shape on a one-liner.
- **A procedure that already has a reusable owner** should not be duplicated into `SKILL.md`. The skill is a thin
  pointer to the owner, not a second copy of it.

## Shared-core skill anatomy

### `skills/<name>/SKILL.md`

Frontmatter is the standard Claude Code skill set — `description`, `allowed-tools`, and `argument-hint` when the skill
takes `$ARGUMENTS`. Nothing shape-specific here; same fields a self-contained skill uses.

Do not declare a `name:` field. The skill's canonical name is the directory name (`foo/SKILL.md` → `foo`); a frontmatter
`name:` either restates it (drift risk) or contradicts it (loader confusion).

Do not declare a `model:` field. A skill runs inline in the calling session and inherits its model; pinning a model
forces a mid-session switch that invalidates the prompt cache on the way in and out, and on a tiered session (e.g. 1M
context) can fail to load the pinned model at all. When a sub-task genuinely needs a different model, spawn a subagent —
agent definitions carry their own `model:` — rather than switching the whole session.

The `description` field must cover **what the skill does and when to use it** — the skill picker reads it to decide
whether to fire on a given user prompt, so a description that says only "what" loses to one that also says "when".
Pattern: "<one-clause what>. Use when <trigger / cadence / context>." See
[`winter-workflow:/skills/harness-score/SKILL.md`](https://github.com/paul-gross/winter-workflow/blob/master/skills/harness-score/SKILL.md)
for an exemplar — it ends `… Use weekly to track progress or divergence.`

#### What a description must not contain

The description is loaded into context for **every** session — it is the always-on routing key, not documentation. The
body (or procedure doc) is loaded only when the skill is invoked, so anything the picker does not need to *route*
belongs there, not here. This same rule governs an agent's `description` (see
[`./writing-agent.md`](./writing-agent.md)). A description must **not** contain:

- **How the work is done** — the concrete procedure: which subagents it spawns, in what step sequence, the internal
  mechanics. That belongs in the loaded procedure, whether self-contained or shared-core. (The *high-level orchestration
  shape* that distinguishes a skill from its siblings — one sequential track vs. parallel across environments vs. a
  coordinated team — is part of the routing "what" and may be named; the banned part is the step-by-step procedure, not
  the shape.)
- **Rationale** — "so that…", "because…", why the approach is sound.
- **Restatement of loaded instructions** — identity, decision rules, output format.
- **Disambiguation lists** — "Do NOT use for X — that's `other`" enumerations against sibling skills/agents. Instead,
  name the *object the skill acts on* (the diff, agent-facing markdown, public docs, the harness seam) precisely enough
  that its scope stands alone. Add at most one "not X" pointer only if two siblings genuinely still collide after that.
- **Workflow-participation detail** — what coordinates it, what calls it, where it sits in a larger workflow.
- **Hard-coded workspace prefixes** — `/wf-foo`, `/ws-push`. Name the bare canonical skill or describe the action
  ("before pushing"); see [`./references.md`](./references.md).

There is no fixed token ceiling, but treat every clause as rent paid on every session: if a clause does not change the
routing decision, cut it.

Body — one short paragraph plus one execute line. Two jobs:

1. Point at the procedure: `The procedure for this skill is at \`<extension>:/<reusable-owner>/process.md\`.`
2. Under an `## Execute` heading, tell the executor to read the procedure doc and execute every step. Optionally one or
   two sentences of "in short" gloss for readers scanning `SKILL.md` without opening the doc.

When the skill accepts caller-specific syntax such as `$ARGUMENTS`, the adapter translates it into the procedure's
declared semantic inputs.

The body is declarative. No meta-commentary on the convention, no rationale for the file layout — the executing agent
does not need to be told why; it needs to be told what to do. Do not paraphrase the steps; the procedure doc is the
source of truth.

When the body needs to refer to the skill itself, use the **bare canonical name** (the directory name) — e.g. `foo`, not
`/foo`, not `/<prefix>-foo`, not `/wf-foo`. The prefix is workspace-configurable per
[`./references.md`](./references.md); hard-coding a specific prefix pins the file to one workspace.

All references from `SKILL.md` to files in the source extension — the procedure doc, shared assets, sibling skills — use
the `<extension>:/...` path notation, never relative paths. `SKILL.md` is installed into the consuming workspace's
`.claude/skills/<name>/SKILL.md` by a per-harness mechanism; a relative path like
`../../methodology/<operation>/process.md` resolves against the installed location and breaks. The extension-prefix path
resolves through the workspace's `AGENTS.winter.md` block and survives installation. See
[`./references.md`](./references.md) for the full notation.

The shared core owns the procedure, semantic input/output contract, caller-neutral voice, and supporting methodology
assets. Keep target facts in `context/`; follow [`./methodology-packaging.md`](./methodology-packaging.md) rather than
restating those ownership rules in `SKILL.md`.

## Cross-reference shape

The dependency direction is defined by [`./methodology-packaging.md`](./methodology-packaging.md). For a skill adapter,
it has these path consequences:

- **`SKILL.md` → anything in the source extension:** always use `<extension>:/...` notation (e.g.
  `winter-workflow:/methodology/<operation>/process.md`). `SKILL.md` is installed into the consuming workspace by a
  per-harness mechanism, so relative paths from it resolve against the installed location and break. The
  extension-prefix path resolves through `AGENTS.winter.md` and survives.
- **Within the reusable owner:** the procedure doc and its shared assets live together and are traversed in place;
  relative links (`./rubric.md`) are fine here.
- **Reusable procedure → `SKILL.md`:** don't. The procedure stands alone; callers reference it, not the other way
  around.
- **Cross-extension references** follow [`./references.md`](./references.md) regardless of file shape.

## Do

A minimal shared-core `skills/<name>/SKILL.md`:

```markdown
---
description: Score the current codebase against the harness maturity matrix and write an HTML report. Use weekly to track progress, or before a planning review.
allowed-tools: Bash, Read, Glob, Grep, Write
---

The procedure for this skill is at `<extension>:/<reusable-owner>/process.md`.

## Execute

Read `<extension>:/<reusable-owner>/process.md` and execute every step. Do not paraphrase or shortcut the steps.
```

Use `<extension>:/...` notation (not relative paths) for every reference out of `SKILL.md` — see
[Cross-reference shape](#cross-reference-shape) for why. The matching reusable procedure opens by declaring its semantic
inputs and outputs, then proceeds in imperative steps.

## Don't

```markdown
# /foo

When the user runs `/foo bar`, $ARGUMENTS contains the project name. ← assumes slash-command framing; breaks for agent
callers

## Step 1: Read the rubric

[full rubric pasted here] ← duplicates content that belongs with the reusable procedure

## Step 2: Score

Ask the user to confirm the score. ← "the user" — a foreman caller has none
```

## Anti-patterns

- **Paraphrasing the procedure inside `SKILL.md`.** If `SKILL.md` lists steps, scoring rules, or output schemas, the
  procedure has two homes that will drift. `SKILL.md` is a pointer; the doc is the procedure.
- **Duplicating rubric / template / schema content** into both `SKILL.md` and the reusable owner. Keep one canonical
  copy beside the procedure and link from the adapter.
- **Procedure doc that links back to its `SKILL.md`.** Dependency inversion: the procedure is the reusable abstraction;
  callers depend on it, not vice versa. A back-reference pins the procedure to one caller (the slash command) and
  silently lies to every other caller that reads it. The procedure must stand alone — anything it needs (frontmatter,
  argument hints, "who calls this") goes in its own header, not in a pointer back to one specific consumer.
- **Relative paths out of `SKILL.md`.** `../../methodology/<operation>/process.md` looks fine until `SKILL.md` is
  installed into the consuming workspace, where it resolves against the wrong directory. Use
  `<extension>:/methodology/<operation>/process.md` or the project's declared reusable owner.
- **`name:` in frontmatter.** The directory name is the canonical identifier; a `name:` field restates it (drift risk)
  or contradicts it (loader confusion). Omit it.
- **Hard-coded prefixed name in the body.** `/wf-foo`, `wf-foo`, or `/<prefix>-foo` pins the file to one workspace's
  prefix; another workspace installs with a different prefix and the reference goes stale. Use the bare canonical name
  (`foo`) per [`./references.md`](./references.md).
- **Splitting a self-contained skill that has no second caller.** The shared-core shape costs a directory and a level of
  indirection; pay it only when a non-slash-command caller is plausible.

## Current exemplars

- Self-contained procedure: `winter-workflow:/skills/commit/SKILL.md`
- Shared-core session adapter: `winter-workflow:/skills/cold-review/SKILL.md`
- Review core: `winter-workflow:/methodology/review/process.md`
- Shared methodology asset: `winter-workflow:/methodology/harness-score/rubric.md`

These paths exemplify semantic ownership, not a universal directory layout. Follow the owning project's declared
reusable location when it differs.
