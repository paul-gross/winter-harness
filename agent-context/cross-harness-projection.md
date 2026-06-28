# Cross-harness agent projection

How one winter-canonical agent definition becomes a native artifact in each target harness.

An agent is authored **once** as a canonical `.md` file — the frontmatter contract is in [`./writing-agent.md`](./writing-agent.md).
`winter ws init` transforms that canonical file into a per-harness copy for Claude Code, Codex, and OpenCode, written as git-excluded artifacts.
Never edit a harness copy; edit the canonical file and re-run init.
The transform lives in `winter:/tools/winter-cli/src/winter_cli/modules/workspace/agent_transform/`.

## Common fields vs. override blocks

Top-level frontmatter keys are the **common fields** — portable across every harness (`name`, `description`, `model`, `tools`; see [`./writing-agent.md`](./writing-agent.md)).

A top-level `claude:`, `codex:`, or `opencode:` block holds **harness-specific overrides**.
Projecting to a target harness keeps the common fields plus that harness's own block and **drops the other two blocks**.
A block's keys are passed through as native frontmatter for that harness; a block's `model:` key overrides the tier-table lookup (below) for that harness only.

```yaml
---
name: code-reviewer
description: |
  Reviews a change-set for correctness and design.
  Use this agent when you want a cold read on code quality.
model: opus
tools: [Bash, Read, Grep, Glob]
codex:
  sandbox_mode: read-only        # Codex-native; no common-field equivalent
opencode:
  permission:
    edit: deny                   # OpenCode-native; no common-field equivalent
claude:
  model: claude-opus-4-5         # pin a specific Claude release over the tier alias
---
```

Add an override block only when a harness needs something the common fields cannot express — a native access control, or a pinned model id.
An agent with no override blocks is a complete, valid canonical file.
OpenCode output carries `mode: subagent` by default so every rendered artifact is spawnable; an `opencode: {mode: ...}` override wins.

## Model tier → vendor id

The common `model` field is a **tier** (`haiku` / `sonnet` / `opus`), never a raw model id.
The transform resolves the tier to each harness's model id; a per-harness `model:` override wins over the table.

| Tier | Claude | Codex | OpenCode |
|------|--------|-------|----------|
| `opus` | `opus` | `gpt-5.4` | `anthropic/claude-opus-4-20250514` |
| `sonnet` | `sonnet` | `gpt-5.4` | `anthropic/claude-sonnet-4-20250514` |
| `haiku` | `haiku` | `gpt-5.4-mini` | `anthropic/claude-haiku-4-20250514` |

**Source of truth:** `winter:/tools/winter-cli/src/winter_cli/modules/workspace/agent_transform/model_tiers.py` (`MODEL_TIER_IDS`).
The table above mirrors it — a vendor model-id change lands there first, then here.
Claude accepts the tier alias directly; the Codex and OpenCode ids are pinned against vendor documentation.

## Lossy projection

A common field with **no native equivalent** in a target harness is **dropped with a warning** — never silently, never a hard failure.
The canonical example is `tools`:

- Claude understands `tools` and passes it through.
- Codex governs access through `sandbox_mode` and approvals — `tools` has no equivalent, so it is dropped.
- OpenCode governs access through a `permission:` map — `tools` has no equivalent, so it is dropped.

The warning is emitted at `winter ws init` time:

> `agent '<name>': common field 'tools' has no equivalent for vendor '<vendor>' and was dropped`

It is **actionable**: it is suppressed once the agent declares the harness-native equivalent — a `sandbox_mode` key in the `codex:` block, or a `permission` key in the `opencode:` block.
A **surviving** tools-drop warning therefore means exactly one thing: this agent restricts its tools for Claude but declares no equivalent for that vendor, so its access there is effectively unrestricted.
Declare the native access control in the override block to both restrict access and silence the warning.

`winter lint` does not verify drops.
It validates override-block well-formedness (block names are one of `claude` / `codex` / `opencode`, each block is a YAML mapping) and that `model` is a recognised tier.

## Identity across harnesses

The canonical `name` is the output filename stem for every harness, carrying the workspace-configurable install prefix (e.g. `<prefix>-developer.md`).
Each harness resolves agent identity differently:

- **Claude Code** resolves by the frontmatter `name` — `subagent_type: developer` finds the agent regardless of the prefixed filename.
- **Codex** carries the unprefixed canonical `name` in its TOML `name` field, same as Claude; the prefix lives only in the filename.
- **OpenCode** resolves by **filename**, so its invocation name includes the prefix (`<prefix>-developer`).

Claude and Codex invoke by the unprefixed canonical name; OpenCode invokes by the prefixed filename.
This divergence is accepted for the current iteration — a caller naming an OpenCode agent must include the workspace prefix.

Cross-extension uniqueness of the canonical `name` is the author's responsibility — two extensions shipping an agent of the same name collide in Claude/Codex resolution (the filename prefix disambiguates the file, not the name). `winter doctor` reports such a collision; keep canonical names distinct across installed extensions.

## Omitted names

An agent that declares no `name` adopts its **filename stem** as the canonical name — the transform derives it during projection, the same way OpenCode resolves identity from the filename.
This keeps a vanilla or not-yet-migrated agent projectable rather than dropping it at init; an authored agent should still declare `name` explicitly per [`./writing-agent.md`](./writing-agent.md).
