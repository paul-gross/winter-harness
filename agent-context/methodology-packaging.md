# Methodology packaging convention

The universal ownership and selection rules are owned by [`winter-canon:/facts-vs-methodology.md`](winter-canon:/facts-vs-methodology.md).
This convention defines only winter's packaging realization after that rule selects a shared method.

## Shared-core shape

Winter workflow products realize a shared method with this dependency shape:

```text
skills/<name>/SKILL.md ---------\
                                 > methodology/<operation>/process.md + adjacent assets
agents/<name>.md ---------------/
```

`shared-core` names this semantic shape, not a required directory name for every product.
Within `winter-workflow`, use the roots below:

| Concern | Winter root |
|---------|-------------|
| Caller-neutral process | `methodology/<operation>/process.md` |
| Reusable rubric, schema, or template | Beside the process, unless the methodology router declares another owner |
| Session adapter | `skills/<name>/SKILL.md` |
| Isolated-runtime adapter | `agents/<name>.md` |
| Target inputs | The target's canonically addressed context files |

The adapters point to the process with `winter-workflow:/methodology/<operation>/process.md` notation.
Files within the methodology root use relative links to adjacent assets.

## Adapter and runtime ports

- A skill adapter translates session syntax such as `$ARGUMENTS` into the process's semantic inputs, then loads and executes the process.
- A spawning caller supplies the isolated run's preamble, restrictions, input mapping, and return destination.
- An agent adapter supplies stable role and runtime behavior shared by every spawn of that agent.
- A process names runtime operations semantically; each winter harness adapter maps them to native tools, projected agent identities, and available coordination capabilities.
- An adapter reports the process's declared unsupported-capability behavior when its harness cannot provide a required port.

Keep projection and identity mechanics in [`./cross-harness-projection.md`](./cross-harness-projection.md), and keep the workflow's port vocabulary in `winter-workflow:/methodology/runtime-ports.md`.

## Do

```text
methodology/assess/process.md       # caller-neutral steps and semantic input contract
methodology/assess/rubric.md        # reusable asset
skills/assess/SKILL.md              # session adapter and argument translation
agents/assessor.md                  # isolated-runtime adapter
<target>:/context/project-constraints.md  # canonically addressed target input
```

Both adapters point to `winter-workflow:/methodology/assess/process.md`; the process receives the target context path as an input.

## Don't

```text
skills/assess/SKILL.md              # full procedure copy
agents/assessor.md                  # second full procedure copy
methodology/project-constraints.md  # target input placed in the workflow package
```

Do not put `$ARGUMENTS`, native tool names, projected agent ids, task-list mechanics, or a run-specific preamble in the shared process.

## See also

- [`./writing-skill.md`](./writing-skill.md) — apply this packaging rule to a skill/session adapter.
- [`./writing-agent.md`](./writing-agent.md) — apply this packaging rule to an agent/isolated-runtime adapter.
- [`./writing-extension-index.md`](./writing-extension-index.md) — route a methodology product from an extension's auto-loaded entry point.
- [`winter-canon:/facts-vs-methodology.md`](winter-canon:/facts-vs-methodology.md) — universal owner for facts, methodology ownership, and shared-vs-self-contained selection.
