# The verifiability matrix

The **verifiability matrix** is a harness doc that inventories the verification methods available for an application — the concrete ways a skill or agent may verify work against it.
Canon governs its shape and requires its presence; the content belongs to the application's own harness.

## Rule

Every harness declares a verifiability matrix.
Its absence is a gap: without it, a skill that needs to verify work has no grounded source of verification methods and must embed them itself — which is methodology carrying facts it should not own.

## Shape

The document has three parts: a **Commands** table for verification that runs as a command, a **Manual testing** section for verification a single command can't perform, and a **Tools** section for the things an agent uses to set up the state a verification needs.

### Method identifiers

Every entry carries a stable **method id** — the handle a plan document references when it names how a change will be verified. The form is `<scope>:<method>`:

- **Commands** and **manual methods** are scoped by the project or component whose code or behavior they verify. The `<method>` is the verb: a command names its check (`api:unit-test`, `web:lint`), and a manual method uses the literal `manual` (`api:manual`, `web:manual` — the manual exercise for that service). The same method name recurs across components, so the scope says which one. A cross-cutting check owned by no single component may take a category scope instead — e.g. `smoke:startup`. When one scope has more than one manual exercise, distinguish them (`api:manual-curl`, `api:manual-load`).
- **Tools** are the exception: a tool is a general setup mechanism, not owned by one component, so it is **not scoped** — name it flatly under a `tool:` prefix: `tool:db-seed`, `tool:env-spinup`.

The id is stable — plans cite it, so a rename is a breaking change. A scoped entry without its scope is incomplete: a plan that references a bare `unit-test` cannot tell which component it runs against.

### Commands

A table of the methods that run as a command — a test suite, a linter, a type-checker, a build. Each row is a method and either the command that runs it or a link to the agent-facing doc that carries it:

| Column | Content |
|--------|---------|
| Method | The scoped method id (e.g. `api:unit-test`, `web:lint`) — see [Method identifiers](#method-identifiers) |
| Command | The command, typed exactly as it is run in the worktree — or a markdown link to the agent-facing documentation that contains it |

### Manual testing

Verification that no single command performs — it needs atypical setup, spans many invocations, or rests on judgment. Write it as prose under a sub-header per project or per concept, each leading with its scoped id whose method is `manual` (e.g. `api:manual`) and naming the surface, the setup it requires, and what a successful exercise looks like. For example, "Manual testing using `curl`" for an API that no one command exercises end to end; or exercising an application against a real environment when standing that environment up is itself part of the test.

A manual method may carry a **Gap** note when it is expected but not yet automated — present fact with a known automation shortfall, distinct from an aspirational method that does not exist at all. The DoD's "build a durable method" branch applies to a gap-noted method.

### Tools

Things an agent uses to manipulate state and stand up the scenario a verification needs — not assertions of correctness themselves, but the setup that makes one possible. A seeder that puts the database in a known state, a command that spins up a throwaway workspace or environment, a fixture or factory that creates an entity in a given condition. List each under its flat `tool:` id (e.g. `tool:db-seed`) with what it does and how an agent invokes it, so an agent can build the precondition a command or manual check then verifies against.

## Why

The matrix gives agents the verification methods available to them, so they know which tools to use rather than improvising or assuming none exists.
It lets an agent plan work knowing how the change will be verified — or, when no method covers it, knowing it must first build the mechanism to verify it.
The application maintains those methods in one authoritative place, so an agent reads the current set from there, and every agent picks up new methods as the application's verification surface grows.
The scoped method id is what makes that reference precise: a plan names `api:unit-test`, and the matrix resolves it to the exact command — rather than a bare `unit-test` an agent must guess the component for.

## Do

- Declare a verifiability matrix in the application's harness and link it from the harness index.
- Write rows for verification methods the application supports today — not aspirational ones.
- Give every entry a stable method id: scope a command or manual method by the project whose code or behavior it verifies (`<scope>:unit-test`, `<scope>:manual`); leave tools unscoped under a flat `tool:` prefix.
- Give each row's Exercise in the most concrete form it admits — an exact command where one exists, otherwise the technique or interaction (surface, gesture, expected outcome) stated precisely enough to perform without guessing.

## Don't

- Embed verification commands inside a skill or workflow prompt — those commands are facts about the application, not methodology about how to sequence a run.
- Leave the matrix absent and treat a skill's hard-coded commands as the source of truth — swap the skill and the verification strategy disappears.
- Write aspirational rows for methods not yet available — the matrix is an inventory of present fact.
- Write a scoped method's id without its scope — a plan referencing a bare `unit-test` can't resolve which component it runs against.

## See also

- [`./facts-vs-methodology.md`](./facts-vs-methodology.md) — the governing principle: verification methods are facts about the application and belong in the harness; how a skill runs them is methodology and belongs with the skill.
- [`./architecture-guidance.md`](./architecture-guidance.md) — the paired expectation: a harness also carries architecture guidance for planning and plan-review.
