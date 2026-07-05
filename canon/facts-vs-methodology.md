# Facts in the harness, methodology in the workflow

When you build an agentic feature — a reviewer agent, a review skill, a context doc, a new harness convention — the **facts** it acts on and the **methodology** it applies belong in different places, and must not be conflated. This is the rule that keeps them apart.

## Rule

- **Facts and invariants live in the harness.** What must be true of the code or docs under review — the conventions, patterns, practices, and invariants a change has to honor — is a *fact*. It lives in a harness doc: a **shared harness** for facts common across projects, or the **target project's own harness** for invariants that only make sense inside that project.
- **Methodology lives in the workflow.** How a particular workflow conducts a review — which agents it spawns, cold vs. warm, what it sequences, how it categorizes findings — is *methodology*. It is one team's swappable opinion and lives with the reviewer (the agent/skill), not in the harness.
- **Reviewers derive criteria; they do not embed them.** A reviewer is built to **read** the harness and the target project, discover the invariants and patterns that apply, and review against those. It must not hard-code domain criteria into its own prompt.
- **Domain-specific invariants stay in the target.** An invariant that only makes sense within the thing under review belongs in that target's harness, reached by reading the target — not carried as a copy inside the reviewer.
- **Generic methodology criteria may live in the workflow.** Cross-project review opinions a workflow always applies (report cold, categorize `must-fix` / `consider`, output shape) are methodology and may live with the reviewer. Anything domain-specific does not.

## Why

A reviewer with the project's invariants baked into its prompt is a fork waiting to happen. Swap the workflow and the facts leave with it; change the project and the reviewer silently reviews against stale criteria. Keeping facts in the harness makes it the single source of truth for *what is true*, and keeps the workflow a swappable opinion about *how to act on it* — so a consumer can replace the entire workflow and still inherit every fact, and a project can evolve its invariants in one place and have every reviewer pick them up on the next run.

This is dependency inversion across the harness/workflow seam: the reviewer depends on the *abstraction* (read whatever facts the harness and target publish), never on a *copy* of today's facts.

## Do

The workflow's documentation-review skill reads a shared harness and the target project's own conventions, then reviews the target against them:

```markdown
## Execute
Spawn `documentation-reviewer` cold against <target>. Instruct it to read the
governing facts — a shared harness plus the target project's own
harness/conventions — and report violations against what it finds there.
```

The facts (`governance.md`, `writing-readme.md`, the target's invariants) live in the harness. The skill supplies only methodology: cold spawn, scope, output format.

## Don't

A reviewer prompt that pastes the project's invariants inline and reviews against that copy:

```markdown
You are the doc reviewer. Enforce these naming rules:           ← domain facts copied into the reviewer
- skills are named <verb>-<noun>
- every index.md must have a Scope section
- the catalog lists winter-product, winter-service-tmux, ...     ← will rot the moment the project changes
Review the target against the list above.
```

The facts now live in two places and drift; the reviewer cannot be reused against a project with different facts. Move the list into the relevant harness and have the reviewer read it.

## See also

- [`./principles.md`](./principles.md) — cross-cutting authoring principles for the markdown these features are written in.
