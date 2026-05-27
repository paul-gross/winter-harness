# Evaluating harness changes

Pre-push eval for a harness change that adds a rule a reviewer agent is expected to enforce. Fabricate a fixture, spawn the reviewer cold against it, confirm the report flags the anti-pattern and cites the new convention by file path.

## Rule

A change to a convention file, agent prompt, skill, or `CLAUDE.md` entry that adds a rule a reviewer agent is expected to enforce requires a negative-case eval before push:

1. Author a fabricated fixture exhibiting the anti-pattern. Don't reuse the convention's own examples.
2. Spawn the affected reviewer cold against the fixture — fresh subagent, no session history.
3. Confirm the reviewer's report flags the fixture under `## must-fix` or `## consider` and references the new convention by file path.

Failing any of the three means the change isn't ready to ship — the convention text, the discovery chain, or the reviewer prompt needs work.

## Why

A new rule only earns its keep when a future reviewer surfaces violations to a future author. The eval is the only check that the rule traverses the discovery chain (the reviewer's `winter-harness:/` lookups, `harness/index.md`, the in-prompt references) and lands as a specific finding rather than dissolving into the noise of unrelated rules. The `Don't` block below covers the failure modes each step guards against.

## Do

Fabricate the fixture in the format the affected reviewer reads. For an agent-facing markdown rule paired with `context-reviewer`, that's a `SKILL.md`, README, or extension `index.md`; for a code rule paired with `code-reviewer`, a `.py` file. Write the anti-pattern in fresh text — not the convention's own `Don't` block, and not lifted from a real repo file:

```bash
mkdir -p /tmp/<rule-slug>-fixture
cat > /tmp/<rule-slug>-fixture/SKILL.md <<'EOF'
# Some skill

<paragraphs exhibiting the anti-pattern, written from scratch>

## Steps
1. ...
EOF
```

Spawn the affected reviewer cold against the fixture path. The report must:

- Flag the offending text under `## must-fix` or `## consider`.
- Cite the new convention by file path (`winter-harness:/...`).

Both holding means the rule reaches the reviewer through the same discovery chain a future agent will traverse.

## Don't

- **Skip the eval.** A rule that no reviewer is shown to catch is documentation, not enforcement.
- **Reuse the convention's `Do` / `Don't` blocks as the fixture.** The reviewer is being shown the canonical example; flagging it proves nothing about generalization.
- **Spawn warm.** A reviewer running inside the authoring session has the rule in context; the reviewer in production has only what the discovery chain delivers.
- **Accept a flag without a file-path citation.** A finding that doesn't reference the new convention by path means the reviewer caught the pattern some other way — the next reviewer on a different change won't.

## See also

- [`./principles.md`](./principles.md) §"No retrospective framing" — concrete precedent: a rule whose enforcement depends on a paired reviewer surfacing the anti-pattern from fresh text
- [`../workflows/feature-delivery.md`](../workflows/feature-delivery.md) §Pre-push checks — the broader pre-push surface for any winter ecosystem repo
- [`./index.md`](./index.md) — the discovery chain a cold reviewer traverses to reach this convention
