# Evaluating harness changes

Pre-push eval for a harness change: declare the behavioral expectations the change makes, then test each one with a cold agent that has only the discovery chain.
A scenario fails in one of two places — the agent never reached the context, or it reached it and still didn't behave — and each failure points at a different fix.

## Rule

A change that adds context an agent is expected to act on declares one or more **behavioral expectations** and tests each one cold before push.
A behavioral expectation is a falsifiable claim of the form *an agent in situation S, with this context reachable, does behavior B.*
Each claim is encoded as a scenario (next section) and run by a fresh subagent whose only context is the discovery chain — `CLAUDE.md` → index → leaf — exactly what a production agent gets.

The eval reports two verdicts per scenario: **reached?** and **behaved?**.
The pair localizes the fix: *not reached* is a discoverability defect, *reached but not behaved* is a content defect.
Failing either means the change isn't ready to ship.

## Why

Context only earns its keep when a future agent, cold in a real task, both finds it and acts on it.
The cold spawn is the mechanism that tests both at once: a fresh agent with only the discovery chain proves whether the context is reachable (the chain delivered it) and whether the content lands (the body earned the behavior) in a single pass.
A warm agent already holds the change in context, so it proves neither — it would behave correctly from the in-session memory of the edit, not from the chain a production agent traverses.
Warm spawns are disallowed.

## The scenario shape

A scenario has these fields:

- **cue** — a realistic agent task that should make the context relevant. Phrase it as the task; never name the target doc.
- **expect** — the observable behavior, split in two:
  - **reached** — the agent traversed the discovery chain and consulted the intended context.
  - **behaved** — the agent produced the intended outcome.
- **via** — the intended progressive-disclosure path (`CLAUDE.md` → index → leaf) the agent should traverse to reach the context.
- **control** *(optional)* — a differential arm: without this change, the cold agent should fail or do measurably worse. Proves the context earns its keep rather than the agent doing the right thing anyway.
- **anti** *(optional)* — a cue where the context is *not* relevant; the agent should not apply it or drag it in. Guards against over-trigger and mis-scoping.

## Reached vs. behaved

Report each scenario as the two verdicts, never collapsed into one pass/fail — a single verdict can't tell a discoverability defect from a content defect, and the two need opposite fixes.

| reached? | behaved? | Diagnosis | Fix |
|----------|----------|-----------|-----|
| no | — | The chain didn't deliver the context: discoverability / progressive-disclosure defect | Fix the index row, the doc name, or the cross-links on the `via` path — leave the body alone |
| yes | no | The agent read the doc and still didn't act: content defect | Fix the body — sharpen the rule, the example, or the imperative; the discovery chain is fine |
| yes | yes | Pass | — |
| no | yes | The agent behaved without the context, so the change may not earn its keep | Run the `control` arm: if the agent behaves correctly without the change too, the context is dead weight |

## When an eval is owed

An eval is owed when the change makes a *new* falsifiable claim of the form "an agent in S does B":

- a new skill or agent — its description must route the right task to it;
- a new convention or rule a reviewer is expected to enforce;
- a new feedforward doc — "helper Y exists, use it";
- a routing change — which skill or agent should handle which task;
- a discoverability change — a new index row or cross-link whose whole job is to make existing context reachable from a cue.

No eval is owed for a copyedit, a typo fix, or a rewording that changes no claim and adds no reachable behavior.
When in doubt, ask whether the change adds a new "an agent in S does B" — if it does, it's owed an eval.
A reword that *broadens a trigger* — more situations now owe a behavior — adds such a claim and is owed an eval; a typo fix or pure copyedit is not.

## Worked examples

Each flavor below is one instance of the same scenario shape.

**Enforcement** — the negative-case reviewer eval, one instance of the model. A new convention adds a rule `context-reviewer` should catch.

- **cue** — "Review this skill doc." (hand the cold reviewer a fabricated fixture exhibiting the anti-pattern)
- **via** — the reviewer's lookups into the published conventions → the convention index → the new convention.
- **reached** — the report cites the new convention by file path.
- **behaved** — the report flags the anti-pattern under `## must-fix` or `## consider`.
- **control** — the same fixture reviewed without the new convention present: no flag.
- **anti** — a clean fixture: no false flag.

**Feedforward** — a new doc tells agents the `winter ws index <name>` helper computes a non-Greek env's deterministic index.

- **cue** — "I need the port base for a new feature env named `foo` — work it out." (never names the helper)
- **via** — workspace `CLAUDE.md` §"Feature environments and Greek letters" → the helper doc.
- **reached** — the agent runs `winter ws index foo`.
- **behaved** — it derives the port base from the returned index instead of hand-computing or hard-coding one.
- **control** — without the doc, the agent invents an ad-hoc numbering and gets a colliding base.
- **anti** — "list the active feature envs": the agent doesn't reach for the index helper.

**Discoverability** — the destroy flow is already documented; the change adds the `CLAUDE.md` cross-link that makes it reachable from a teardown cue.

- **cue** — "Tear down the gamma environment."
- **via** — workspace `CLAUDE.md` §"Tearing down a feature environment" → `ai/worktree-ops.md` §"Destroying a feature environment".
- **reached** — the agent opens the destroy section.
- **behaved** — it runs `winter ws destroy gamma` rather than `rm -rf gamma/`.
- **control** — without the cross-link, the agent reaches for `rm -rf gamma/` and orphans extension state.
- **anti** — "create a new environment": the agent lands on the init flow, not the destroy flow.

**Routing** — a change documents that small localized fixes go to `/wf-thaw`, not `/wf-blizzard`.

- **cue** — "Fix this off-by-one in the port-index calculation."
- **via** — the skill descriptions / routing doc → `/wf-thaw`.
- **reached** — the agent weighs the thaw-vs-blizzard distinction.
- **behaved** — it picks `/wf-thaw` for the narrow change.
- **control** — without the routing cue, the agent over-escalates a one-line fix to a full blizzard.
- **anti** — "design and build a new multi-repo sync subsystem": the agent picks blizzard, not thaw.

## Who runs it

The eval runs from a session that can open a fresh subagent — the orchestrating top-level session, or a skill that spawns one.
A non-spawning agent — a `developer` or reviewer one-shot delivering the change — cannot open the cold subagent the eval needs and cannot stand in for it warm.
When the agent that authored the change can't spawn, it hands the eval up to the session that can; it does not skip it or run it warm.
The cold spawn is the eval — an agent that can't make it can't run it.

## Running a scenario cold

Spawn a fresh subagent — no session history, no mention of the change — and give it the **cue** verbatim.
Let it traverse the discovery chain itself; observe what it reads (reached?) and what it does (behaved?).
For an enforcement scenario, the cold agent is the affected reviewer and the cue hands it a fixture:

```bash
mkdir -p /tmp/<rule-slug>-fixture
cat > /tmp/<rule-slug>-fixture/SKILL.md <<'EOF'
# Some skill

<paragraphs exhibiting the anti-pattern, written from scratch>

## Steps
1. ...
EOF
```

Keep the eval honest:

- **Phrase the cue as the task; never name the target doc.** "Read evaluating-harness-changes.md and..." shortcuts the discovery chain and turns the reached-test into a no-op.
- **Write fixtures and scenario text as fresh prose.** Not the convention's own `Do` / `Don't` examples, not lifted from a real repo file — the agent shown the canonical example proves nothing about generalization.
- **Keep the situation realistic.** A leading cue that telegraphs the answer measures nothing; use a task an agent actually receives.

## Single runs are stochastic

A cold spawn is one sample of a stochastic agent.
A single run is a smoke test — enough to catch context that's plainly unreachable or a body that plainly doesn't land.
For a gate-worthy change — a rule that blocks merges, a routing decision that sends work to the wrong place — run the scenario N times and take the majority; a scenario that passes 1-of-3 is not shippable.
N runs is N hand-driven cold spawns from the orchestrating session with the majority tallied by hand — there is no eval-runner tool.
Note the run count and the tally alongside the change so the next author knows the confidence behind the verdict.

## Don't

- **Skip the eval on a change that's owed one.** Context no cold agent is shown to reach and act on is aspiration, not harness.
- **Spawn warm.** The reviewer or agent running inside the authoring session has the change in context; the one in production has only what the discovery chain delivers.
- **Delegate the eval to a non-spawning agent.** A `developer` or reviewer one-shot can't open the cold subagent; it hands the eval up to a session that can, rather than skipping it or running warm.
- **Collapse reached and behaved into one verdict.** The pass/fail hides which of the two opposite fixes the failure needs.
- **Accept a behaved-without-reached as a pass.** Run the `control` arm — if the agent behaves correctly without the change, the context is dead weight.
- **Reuse the convention's own examples as the fixture or cue.** Showing the agent the canonical example proves nothing about generalization.

## See also

- [`./principles.md`](./principles.md) §"No retrospective framing" — concrete precedent: an enforcement rule whose efficacy depends on a paired reviewer surfacing the anti-pattern from fresh text.
- [`./index.md`](./index.md) — the discovery chain a cold agent traverses to reach a leaf convention.
