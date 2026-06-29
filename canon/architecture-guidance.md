# Architecture guidance

**Architecture guidance** is a harness doc that describes an application's structural invariants, design decisions, and the constraints a change must honor.
A harness is expected to carry it.
Canon governs the expectation; the content belongs to the application's harness.

## Rule

Every harness carries architecture guidance.
Its absence is a gap: a planner without it must infer structure from code, and a plan reviewer cannot check whether a proposed design respects the invariants the application owns.

## Why

Architecture guidance gives planning and review a stable, single-owned reference.
Without it, every planner infers the architecture independently, every reviewer applies their own heuristic, and neither flags a contradiction because they have no documented invariant to contradict.
With it, the invariants are a fact the application maintains in one place and every planner and reviewer reads from there — evolve the guidance and every future plan and review picks it up.

## Do

- Carry architecture guidance in the application's harness and link it from the harness index.
- State invariants as facts: what must be true of the application's structure, not how a workflow uses it.
- Update guidance when an invariant changes; the guidance is the single source of truth for the application's structural constraints.

## Don't

- Embed architectural constraints in a planner or reviewer prompt — those are facts about the application and belong in the guidance doc.
- Leave guidance absent and rely on planners to infer structure from code — inference diverges across runs and leaves no shared reference for contradiction checks.

## See also

- [`./facts-vs-methodology.md`](./facts-vs-methodology.md) — the governing principle: architectural invariants are facts and live in the harness; how a planner drafts or a reviewer sequences is methodology and lives with the skill.
- [`./verifiability-matrix.md`](./verifiability-matrix.md) — the paired expectation: a harness also declares a verifiability matrix.
