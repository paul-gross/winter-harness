# Contributing

`winter-harness` is a docs repo — it contains conventions, exemplars, and the README guide that the rest of the winter ecosystem reads. Changes target a convention file directly.

## Commit messages

Conventional Commits with a scope:

    <type>(<scope>): <description>

    [optional body]

- Types: `feat`, `fix`, `docs`, `chore`, `refactor`, `test`, `perf`, `style`, `ai`. `docs` is the common case here.
- Scope: `harness` (or a subsystem like `python`, `exemplars`).
- Use `Closes #N` to link a GitHub issue this commit finishes (workspace-level rules at `workspace:/context/project/contributing.md`).
- The `/wf-commit` skill from [winter-workflow](https://github.com/paul-gross/winter-workflow) generates commits in this format.

Example:

    docs(harness): tighten error-handling do/don't pairing

    Closes #12

## Voice

This repo's conventions are written in a specific voice — terse, opinionated, code-first, Do/Don't pairs over prose. Read `documentation/writing-readme.md` before editing or adding a convention file; the "Voice — common pitfalls" section covers the habits to resist (describe outcomes not contents, no second supporting paragraph, no positioning relative to siblings, beware colon-then-elaboration). New convention files generally follow a `Rule` / `Why` / `Do` / `Don't` / `See also` skeleton with feature-specific sections inserted as needed — match the shape of the closest existing sibling in `architecture/` or `standards/`.

## Pre-commit checks

Three markdown lints ship in this repo and are registered with `winter lint` via `winter-ext.toml` — path notation, routing-reference integrity, and link anchors. Run them before pushing; `agent-context/linting.md` is the owner for what each flags and how to run them standalone. When touching the scripts themselves, also run their test suite (`cd agent-context/scripts && python3 -m unittest test_doclint`).

Two things the lints do not cover — validate these by hand:

- **Backticked file references** — the lints resolve markdown links, not `` `path` `` code spans; a relative path inside backticks must still resolve from the file that states it.
- **Code references** — any production example cited via path notation (e.g. `winter:/tools/winter-cli/...`) still exists at that path with the claimed shape. Conventions go stale when winter-cli refactors; if you spot drift while reading, fix it.

## Delivery

- Default branch: `master`.
- **Primary contributors** push directly to `master` — no PR, no review. Rebase onto the latest `origin/master` first so history stays linear.
- **Outside contributors** are welcome — open a PR against `master` and I'll review and merge.
