# Contributing

`winter-context` is a docs repo — it contains conventions, exemplars, and the README guide that the rest of the winter
ecosystem reads. Changes target a convention file directly.

## Commit messages

Conventional Commits with a scope:

```text
<type>(<scope>): <description>

[optional body]
```

- Types: `feat`, `fix`, `docs`, `chore`, `refactor`, `test`, `perf`, `style`, `ai`. `docs` is the common case here.
- Scope: `context` (or a subsystem like `python`, `exemplars`).
- Use `Closes #N` to link a GitHub issue this commit finishes (workspace-level rules at
  `workspace:/context/project/contributing.md`).
- The `/wf-commit` skill from [winter-workflow](https://github.com/paul-gross/winter-workflow) generates commits in this
  format.

Example:

```text
docs(context): tighten error-handling do/don't pairing

Closes #12
```

## Voice

This repo's conventions follow a shared shape and voice — the `Rule` / `Why` / `Do` / `Don't` / `See also` skeleton and
a terse, code-first, Do/Don't-over-prose voice. Read `agent-context/writing-convention.md` before editing or adding a
convention file; it owns the skeleton and the voice habits to trim past. Match the shape of the closest existing sibling
in `architecture/` or `standards/`.

## Pre-commit checks

Four markdown lints ship in this repo and are registered with `winter lint` via `winter-ext.toml` — path notation,
routing-reference integrity, link anchors, and mechanical style. Run them before pushing; `agent-context/linting.md` is
the owner for what each flags and how to run them standalone. When touching the scripts themselves, also run their test
suites (`cd agent-context/scripts && python3 -m unittest discover`).

The style gate is two external tools, and one of them writes the fix — run them from the repo root, not through the lint
script, while you are still editing:

```bash
dprint check          # dprint fmt to apply
rumdl check .         # rumdl check . --fix for the autofixable subset
```

Every markdown file here is held to both; `dprint.json` and `.rumdl.toml` declare the rules and are the repo's opt-in to
the gate.

Two things the lints do not cover — validate these by hand:

- **Backticked file references** — the lints resolve markdown links, not `` `path` `` code spans; a relative path inside
  backticks must still resolve from the file that states it.
- **Code references** — any production example cited via path notation (e.g. `winter:/tools/winter-cli/...`) still
  exists at that path with the claimed shape. Conventions go stale when winter-cli refactors; if you spot drift while
  reading, fix it.

## Delivery

- Default branch: `master`.
- **Primary contributors** push directly to `master` — no PR, no review. Rebase onto the latest `origin/master` first so
  history stays linear.
- **Outside contributors** are welcome — open a PR against `master` and I'll review and merge.
