# Agent convention

How to author an agent definition across the winter ecosystem.
An agent is a single **canonical** `.md` file: winter projects it into each harness's native artifact (Claude Code, Codex, OpenCode) at `winter ws init`.
This file documents the frontmatter contract common to every harness, the canonical-name rule, and the two agent-body shapes; [`./cross-harness-projection.md`](./cross-harness-projection.md) covers the per-harness override blocks, the model-tier→id table, and lossy projection.
[`./methodology-packaging.md`](./methodology-packaging.md) owns how reusable methodology is separated from runtime adapters.

## Frontmatter contract

Every agent must declare four keys:

```yaml
---
name: <agent-name>
description: |
  <what the agent does and when to use it>
model: haiku | sonnet | opus
tools:
  - Bash
  - Read
  # … the permissive set for this role
---
```

`winter lint` enforces `name`, `description`, `model`, and `tools`.
An agent missing any of these, or one that declares `allowed-tools` instead of `tools`, fails the lint.

### `name:` — required for agents

Declare `name:` in every agent frontmatter.
The `name:` value is the functional identifier the Agent tool uses to resolve `subagent_type` — it is the mechanism by which a caller's `subagent_type: ice-carver` finds `ice-carver.md`.
Without it, resolution fails silently and the agent is unreachable.

This is the opposite rule from skills.
Skills forbid `name:` because a skill's canonical identifier is its directory name (`foo/SKILL.md` → `foo`), and a `name:` field either restates it (drift risk) or contradicts it (loader confusion).
For agents there is no directory-name convention: the file is a flat `<name>.md`, and the Agent tool reads `name` from frontmatter directly.
The field is not redundant — it is the resolution key.

Keep the `name:` value identical to the filename stem (`ice-carver.md` → `name: ice-carver`).
When they diverge the filename is silently bypassed and the canonical value is whatever the frontmatter says; the filename becomes a misleading label.

`name` is technically optional: an agent that omits it falls back to the filename stem. Authored agents declare it explicitly. For the transform mechanism and why the fallback exists, see [`./cross-harness-projection.md`](./cross-harness-projection.md) §"Omitted names".

### `description:` — what the agent does and when to use it

The description must cover **what the agent does and when to spawn it** — the same two-part contract as skills.
The caller reads this field to decide whether to spawn the agent for a given sub-task.
Pattern: `"<one-clause what>. Use this agent when <trigger / context>."`.
The `description` is loaded into every session that can reach the agent — it is a routing key, not documentation. The exclusion rules — including distinguishing confusable reviewers by the *object each acts on* rather than by "Do NOT use" lists — are shared with skills: see [what a description must not contain](./writing-skill.md#what-a-description-must-not-contain).

### `model:` — a tier label

Pick the tier appropriate for the role's reasoning load — a built-in tier, or a custom label a workspace defines in `[model_tiers]`:

- `haiku` — fast, cheap; suitable for classifiers, formatters, structured output
- `sonnet` — balanced default; suitable for implementation, exploration, most review roles
- `opus` — heavyweight; reserve for roles that need deep reasoning (architecture, adversarial review)
- a workspace-defined custom label (e.g. `"big-thinker"`) — see [`./cross-harness-projection.md`](./cross-harness-projection.md#workspace-overridable-tier-table)

Do not use a full model ID string at the top level.
`winter lint` does not validate the tier label; an unknown one is surfaced at render time — `winter ws init` warns and skips the agent (other agents still install), and `winter doctor` reports a WARN.
A per-harness override block *may* pin a vendor-specific model id when the tier default is wrong for that harness — see [`./cross-harness-projection.md`](./cross-harness-projection.md).

### `tools:` — permissive grant for the role

List every tool the agent is permitted to use across all callers.
This is the **permissive set**; the spawning skill's preamble narrows it per run.
Use `tools:` not `allowed-tools:` — `winter lint` rejects `allowed-tools` pre-push; Claude Code silently ignores it at runtime if lint is skipped, leaving the agent with an unrestricted grant.

See [`winter-workflow:/agents/README.md#convention-tool-grant-vs-preamble`](winter-workflow:/agents/README.md#convention-tool-grant-vs-preamble) for the tool-grant vs. preamble split: the key principle is that the agent definition stays stable while each spawning skill's preamble restricts the grant to what its coordination shape needs.

## Agent body

The body owns the agent's stable role identity and isolated-runtime behavior.
For a self-contained agent, it also owns the procedure's decision and output rules; for a shared-core agent, those rules live in the shared methodology.
It does not describe how the role participates in any particular workflow; that is the spawning skill's responsibility to inject via its coordination preamble.

Write the body in second-person imperative voice addressed to the executing agent.
Reference "your caller" rather than any named coordinator or skill.
Do not include `TaskList`/`TaskUpdate` instructions — those are injected by skills that need them.

## The two shapes

**Self-contained.** Keep the complete procedure in the agent body when isolated-runtime behavior is part of the procedure's identity and no concrete second executor is plausible.
The body still uses caller-neutral language; self-contained does not mean coupled to one spawning skill.

**Shared-core.** Keep stable isolated-runtime behavior in the agent definition and point it at the project-declared reusable procedure.
The shared core owns semantic decisions, escalation rules, and output contracts that apply across executors.

Use [`winter-canon:/facts-vs-methodology.md`](winter-canon:/facts-vs-methodology.md) to choose between these shapes, then [`./methodology-packaging.md`](./methodology-packaging.md) to realize the shared-core roots, adapter boundaries, and runtime ports; do not restate those rules in the agent definition.
Do not paraphrase the reusable procedure's steps, rules, or output schema in a shared-core body.

## Do

```yaml
---
name: summarizer
description: |
  Reads a set of files and produces a structured summary.
  Use this agent when you need a concise, structured account of content
  you cannot fit into your own context.
model: haiku
tools:
  - Read
  - Bash
---
```

`name` matches the filename stem; `description` covers what and when; `model` is a tier name; `tools` is the permissive set.

A shared-core body stays thin:

```markdown
The procedure for this agent is at `<extension>:/<reusable-owner>/process.md`.

## Execute

Read `<extension>:/<reusable-owner>/process.md` and execute every step using the inputs supplied by your caller.
Return the procedure's declared output to your caller.
```

Use `<extension>:/...` notation for the reusable owner so the reference survives projection and installation; follow [`./references.md`](./references.md) for cross-context references.

## Don't

```yaml
---
description: Summarizes files.
allowed-tools:
  - Read
  - Bash
---
```

Missing `name` (resolution fails), vague `description` (no "when to use"), `allowed-tools` instead of `tools` (`winter lint` rejects this pre-push; Claude Code silently ignores it at runtime, leaving the agent with the full grant).

Do not make a shared-core body a second procedure copy or put one spawning skill's coordination preamble in it.
