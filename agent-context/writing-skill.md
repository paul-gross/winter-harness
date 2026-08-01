# Skill convention

How to author a skill across the winter ecosystem. Skills come in two shapes; this file documents both and the test for picking between them. The [Precedent](#precedent) section links the exemplars.

## The two shapes

**Self-contained.** The entire procedure lives in `SKILL.md`. The body is the procedure. The only way to execute it is to invoke the slash command. Examples: `winter-workflow:/skills/snowball/SKILL.md`, `winter-workflow:/skills/commit/SKILL.md`.

**Thin SKILL.md backed by a `context/` procedure doc.** `SKILL.md` is a small entry point that names a `context/<name>/process.md` and tells the executor to run every step. The procedure itself lives in `context/<name>/process.md`. Other agents (an `iceberg` foreman, another skill, an ad-hoc subagent) can `Read` the procedure and execute it as a substep without firing the slash command. Example: `winter-workflow:/skills/harness-score/SKILL.md` → `winter-workflow:/context/harness-score/process.md`.

## When to pick the thin shape

The test:

> If you can imagine a non-slash-command caller (an iceberg foreman, another skill, an ad-hoc agent) wanting to execute this procedure as a substep, choose the thin shape. If the procedure is the slash command's entire identity — nothing else will ever want to run it — the self-contained shape is fine.

Two corollaries:

- **A skill that just executes a single shell command** (or otherwise has no procedure worth re-reading) does not need a procedure doc. Don't force the thin shape on a one-liner.
- **A procedure that already lives in `context/`** (e.g., a doc another agent already reads) should not be duplicated into `SKILL.md`. The skill is a thin pointer to the doc, not a second copy of it.

## Thin shape — anatomy

### `skills/<name>/SKILL.md`

Frontmatter is the standard Claude Code skill set — `description`, `allowed-tools`, and `argument-hint` when the skill takes `$ARGUMENTS`. Nothing shape-specific here; same fields a self-contained skill uses.

Do not declare a `name:` field. The skill's canonical name is the directory name (`foo/SKILL.md` → `foo`); a frontmatter `name:` either restates it (drift risk) or contradicts it (loader confusion).

Do not declare a `model:` field. A skill runs inline in the calling session and inherits its model; pinning a model forces a mid-session switch that invalidates the prompt cache on the way in and out, and on a tiered session (e.g. 1M context) can fail to load the pinned model at all. When a sub-task genuinely needs a different model, spawn a subagent — agent definitions carry their own `model:` — rather than switching the whole session.

The `description` field must cover **what the skill does and when to use it** — the skill picker reads it to decide whether to fire on a given user prompt, so a description that says only "what" loses to one that also says "when". Pattern: "<one-clause what>. Use when <trigger / cadence / context>." See [`winter-workflow:/skills/harness-score/SKILL.md`](https://github.com/paul-gross/winter-workflow/blob/master/skills/harness-score/SKILL.md) for an exemplar — it ends `… Use weekly to track progress or divergence.`

#### What a description must not contain

The description is loaded into context for **every** session — it is the always-on routing key, not documentation. The body (or procedure doc) is loaded only when the skill is invoked, so anything the picker does not need to *route* belongs there, not here. This same rule governs an agent's `description` (see [`./writing-agent.md`](./writing-agent.md)). A description must **not** contain:

- **How the work is done** — the concrete procedure: which subagents it spawns, in what step sequence, the internal mechanics. That is the body's job. (The *high-level orchestration shape* that distinguishes a skill from its siblings — one sequential track vs. parallel across environments vs. a coordinated team — is part of the routing "what" and may be named; the banned part is the step-by-step procedure, not the shape.)
- **Rationale** — "so that…", "because…", why the approach is sound.
- **Restatement of the body** — identity, decision rules, output format.
- **Disambiguation lists** — "Do NOT use for X — that's `other`" enumerations against sibling skills/agents. Instead, name the *object the skill acts on* (the diff, agent-facing markdown, public docs, the harness seam) precisely enough that its scope stands alone. Add at most one "not X" pointer only if two siblings genuinely still collide after that.
- **Workflow-participation detail** — what coordinates it, what calls it, where it sits in a larger workflow.
- **Hard-coded workspace prefixes** — `/wf-foo`, `/ws-push`. Name the bare canonical skill or describe the action ("before pushing"); see [`./references.md`](./references.md).

There is no fixed token ceiling, but treat every clause as rent paid on every session: if a clause does not change the routing decision, cut it.

Body — one short paragraph plus one execute line. Two jobs:

1. Point at the procedure: `The procedure for this skill is at \`<extension>:/context/<name>/process.md\`.`
2. Under an `## Execute` heading, tell the executor to read the procedure doc and execute every step. Optionally one or two sentences of "in short" gloss for readers scanning `SKILL.md` without opening the doc.

The body is declarative. No meta-commentary on the convention, no rationale for the file layout — the executing agent does not need to be told why; it needs to be told what to do. Do not paraphrase the steps; the procedure doc is the source of truth.

When the body needs to refer to the skill itself, use the **bare canonical name** (the directory name) — e.g. `foo`, not `/foo`, not `/<prefix>-foo`, not `/wf-foo`. The prefix is workspace-configurable per [`./references.md`](./references.md); hard-coding a specific prefix pins the file to one workspace.

All references from `SKILL.md` to files in the source extension — the procedure doc, shared assets, sibling skills — use the `<extension>:/...` path notation, never relative paths. `SKILL.md` is symlinked into the consuming workspace's `.claude/skills/<name>/SKILL.md`; a relative path like `../../context/<name>/process.md` resolves against the symlinked location and breaks. The extension-prefix path resolves through the workspace's `AGENTS.winter.md` block and survives the symlink. See [`./references.md`](./references.md) for the full notation.

### `context/<name>/process.md`

The procedure, in imperative second-person voice (see [Voice rule](#voice-rule-for-the-procedure-doc) below). Numbered steps. Concrete commands, paths, and outputs. Whatever scoring rules, schemas, or output templates belong with the procedure live here — not in `SKILL.md`.

### Shared assets

Rubrics, templates, sample artifacts, and other supporting files live in `context/<name>/` alongside `process.md` — e.g. `context/<name>/rubric.md`, `context/<name>/template.html`. The procedure doc references them with relative paths (`./rubric.md`).

## Voice rule for the procedure doc

The procedure doc is read by whoever is executing the procedure — sometimes that is a slash-command invocation, sometimes another agent that found the doc via `Read`. The voice must read correctly in both cases.

- **Imperative second-person.** "Read the rubric." "Spawn an `arctic-explorer`." "Write the report."
- **Address "the executing agent", not "the user".** A non-slash-command caller has no user. If a step genuinely needs user interaction, say "if a human caller is present, ask via `AskUserQuestion`; otherwise take the input from the caller's invocation".
- **Do not assume slash-command framing.** No "when the user types `/foo bar`", no "`$ARGUMENTS` contains …" at the top. Inputs come from "the caller" — the slash command and the agent caller both qualify.
- **Report the result to "the caller", not "the user".** The slash command's user is one kind of caller; another agent is another.

## Cross-reference shape

References point **downward only** — from the caller to the procedure, never back. `SKILL.md` depends on `context/<name>/process.md`; the procedure does not depend on any of its callers. This is dependency inversion: the procedure is the reusable abstraction, every caller (the slash command, a foreman, another skill) is one consumer among many. A back-reference inverts the direction and pins the procedure to one specific caller — see the anti-pattern in [Anti-patterns](#anti-patterns).

- **`SKILL.md` → anything in the source extension:** always use `<extension>:/...` notation (e.g. `winter-workflow:/context/harness-score/process.md`). `SKILL.md` is symlinked into the consuming workspace, so relative paths from it resolve against the symlink target and break. The extension-prefix path resolves through `AGENTS.winter.md` and survives.
- **Within `context/<name>/`:** the procedure doc and its shared assets (`rubric.md`, `template.html`, etc.) live together and are not symlinked. Relative links (`./rubric.md`) are fine here.
- **`context/<name>/process.md` → `SKILL.md`:** don't. The procedure stands alone; callers reference it, not the other way around.
- **Cross-extension references** follow [`./references.md`](./references.md) regardless of file shape.

## Do

A minimal thin `skills/<name>/SKILL.md`:

```markdown
---
description: Score the current codebase against the harness maturity matrix and write an HTML report. Use weekly to track progress, or before a planning review.
allowed-tools: Bash, Read, Glob, Grep, Write
---

The procedure for this skill is at `<extension>:/context/<name>/process.md`.

## Execute

Read `<extension>:/context/<name>/process.md` and execute every step. Do not paraphrase or shortcut the steps.
```

Use `<extension>:/...` notation (not relative paths) for every reference out of `SKILL.md` — see [Cross-reference shape](#cross-reference-shape) for why. The matching `context/<name>/process.md` opens by stating who reads it and why, then proceeds in imperative steps — see the harness-score precedent in [Precedent](#precedent).

## Don't

```markdown
# /foo

When the user runs `/foo bar`, $ARGUMENTS contains the project name.   ← assumes slash-command framing; breaks for agent callers

## Step 1: Read the rubric
[full rubric pasted here]                                              ← duplicates content that belongs in context/<name>/

## Step 2: Score
Ask the user to confirm the score.                                     ← "the user" — a foreman caller has none
```

## Anti-patterns

- **Paraphrasing the procedure inside `SKILL.md`.** If `SKILL.md` lists steps, scoring rules, or output schemas, the procedure has two homes that will drift. `SKILL.md` is a pointer; the doc is the procedure.
- **Duplicating rubric / template / schema content** into both `SKILL.md` and `context/<name>/`. Pick one home (`context/<name>/`) and link from the other.
- **Procedure-doc voice that assumes slash-command framing.** "When the user runs `/foo`", "`$ARGUMENTS` is …", "ask the user" at the top of a step. A foreman reading the doc has no `$ARGUMENTS` and no user.
- **Procedure doc that links back to its `SKILL.md`.** Dependency inversion: the procedure is the reusable abstraction; callers depend on it, not vice versa. A back-reference pins the procedure to one caller (the slash command) and silently lies to every other caller that reads it. The procedure must stand alone — anything it needs (frontmatter, argument hints, "who calls this") goes in its own header, not in a pointer back to one specific consumer.
- **Relative paths out of `SKILL.md`.** `../../context/<name>/process.md` looks fine until `SKILL.md` is symlinked into the consuming workspace, then resolves against the wrong directory. Use `<extension>:/context/<name>/process.md`.
- **`name:` in frontmatter.** The directory name is the canonical identifier; a `name:` field restates it (drift risk) or contradicts it (loader confusion). Omit it.
- **Hard-coded prefixed name in the body.** `/wf-foo`, `wf-foo`, or `/<prefix>-foo` pins the file to one workspace's prefix; another workspace installs with a different prefix and the reference goes stale. Use the bare canonical name (`foo`) per [`./references.md`](./references.md).
- **Shared assets outside `context/<name>/`.** A rubric at `context/rubric.md` or `skills/<name>/rubric.md` invites the next author to put a sibling somewhere else again. Keep the cluster together.
- **Splitting a self-contained skill that has no second caller.** The thin shape costs a directory and a level of indirection; pay it only when a non-slash-command caller is plausible.

## Precedent

[`paul-gross/winter-workflow#9`](https://github.com/paul-gross/winter-workflow/pull/9) split `harness-score` along these lines:

- Thin entry point: `winter-workflow:/skills/harness-score/SKILL.md`
- Procedure: `winter-workflow:/context/harness-score/process.md`
- Shared asset (rubric): `winter-workflow:/context/harness-score/rubric.md`
