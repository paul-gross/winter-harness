# Extension `index.md` convention

Conventions for the top-level `index.md` of a winter extension (the file resolved by the extension's path-notation prefix — e.g. `winter-harness:/index.md`).

## Why this matters

A workspace's `AGENTS.md` `@`-includes each installed extension's `index.md` via `AGENTS.winter.md` (and `CLAUDE.md` is the committed shim that reaches it), so the file is loaded into **every agent context** opened against the workspace. That makes it an auto-loaded entry point, and the canon's [`../canon/organization.md`](../canon/organization.md) §"Charge auto-loaded entry points a higher context cost" sets what such a file may hold: only universally-required operational rules and navigation, everything else behind links. The rule below is that principle applied to an extension `index.md` — the "universally required" surface here is what the user needs to *run* the workspace.

## Rule

`index.md` contains **only the workspace-runtime surface** of the extension — what the user (or an agent acting on the user's behalf) needs to know to operate the workspace correctly. Nothing else.

In scope:
- What the extension contributes to a workspace at runtime (commands the user runs, files in env roots, conventions to follow while developing in a feature env).
- Rules and invariants the user / agent must respect while the workspace is live (`./up` not `nohup &`, capture-pane not `tail -f`, etc.).
- Naming conventions and identifiers the user will see or type — session names, file paths in env roots, pane targets, env-var names.
- Pointers to the project-specific configuration the extension reads (`workspace:/context/project/foo.sh`).

Out of scope — these belong elsewhere:
- **Lifecycle-hook tables** (`on_env_init` / `on_env_destroy` script names, what each does). Behind-the-scenes — the user doesn't invoke these; `winter ws init/destroy` does. The manifest at `winter-ext.toml` is self-documenting for anyone modifying the extension.
- **Doctor probe internals** (which probes the script emits, the NDJSON shape, exit-code semantics). The user reads `winter doctor`'s rendered output, not the probe internals. The contract lives in `workspace:/context/winter-cli/configuration/doctor.md#probe-output-contract`.
- **Manifest schema, plugin internals, hook-script implementation details.** All behind-the-scenes.
- **Installation steps.** Those belong in `README.md` (see `winter-harness:/documentation/writing-readme.md`).
- **Setup walkthroughs.** Those belong in `context/` (e.g. `context/workflow-setup.md`) and are referenced *from* `index.md` with a one-line pointer.

## Structure

How an `index.md` is shaped for discovery — when to split it into a hub plus per-topic files, and how to write its routing rows as read-triggers rather than contents summaries — is the canon's [`../canon/progressive-disclosure.md`](../canon/progressive-disclosure.md). This file does not restate it. The extension-specific overlay is scope: an extension `index.md` is the hub for the extension's *workspace-runtime* surface only (the Rule above), so its routing rows point at the deeper `context/<topic>.md` walkthroughs and project-config files an operator descends to, not at the behind-the-scenes detail.

## Where the rejected content goes

If you're tempted to add a section that's out-of-scope per the rule above:

| Content type | Home |
|--------------|------|
| Hook tables, probe internals, manifest details | The extension's source — `winter-ext.toml`, the hook script's header comment, the probe script's header comment. Self-documenting code beats redundant markdown. |
| Setup walkthroughs and interactive guides | `context/<topic>.md` inside the extension. Reference from `index.md` with one line. |
| User-facing feature pitch, installation, scope | `README.md`. See `winter-harness:/documentation/writing-readme.md`. |
| Cross-cutting engineering conventions | `winter-harness:/`. |

## Do

```markdown
# Winter service orchestration via tmux

Tmux-based service orchestration for winter workspaces. Runs project services
in a per-env tmux session via `./up` / `./down` / `./status` scripts, so
multiple envs can run side-by-side without port conflicts.

## Feature environment setup steps

This extension needs `workspace:/context/project/setup-tmux.sh`. Walk the user
through [context/workflow-setup.md](./context/workflow-setup.md) to generate it.

## Service management rules

- Never start services as background processes — always go through `./up`.
- Never kill services directly — always `./down`.
- Read pane output with `tmux capture-pane` against the targets in
  `workspace:/context/project/setup-tmux.md`.
```

Every section is something the user (or an agent acting for the user) must know to operate the workspace correctly.

## Don't

```markdown
## Lifecycle hooks                              ← behind-the-scenes; user doesn't invoke these

| Hook | Script | When | What it does |
| `on_env_init` | `hooks/init-worktree.sh` | ... | ... |
| `on_env_destroy` | `hooks/destroy-worktree.sh` | ... | ... |

## Doctor probe                                 ← behind-the-scenes; user reads `winter doctor` output, not the probe shape

| Probe | What it checks |
| `tmux binary` | ... |
| `SESSION_PREFIX declared` | ... |
```

If a future agent needs the hook table or the probe table to do their job, they will find it in `winter-ext.toml` and the script headers — that's the right place for it. Don't pay the auto-load tax to keep it in `index.md`.
