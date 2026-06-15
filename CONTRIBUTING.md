# Contributing

`winter-harness` is a docs repo — it contains conventions, exemplars, and the README guide that the rest of the winter ecosystem reads. Changes target a convention file directly.

## Commit messages

Conventional Commits with a scope:

    <type>(<scope>): <description>

    [optional body]

- Types: `feat`, `fix`, `docs`, `chore`, `refactor`, `test`, `perf`, `style`, `ai`. `docs` is the common case here.
- Scope: `harness` (or a subsystem like `python`, `exemplars`).
- Use `Closes #N` to link a GitHub issue this commit finishes (workspace-level rules at `workspace:/ai/project/contributing.md`).
- The `/wf-commit` skill from [winter-workflow](https://github.com/paul-gross/winter-workflow) generates commits in this format.

Example:

    docs(harness): tighten error-handling do/don't pairing

    Closes #12

## Voice

This repo's conventions are written in a specific voice — terse, opinionated, code-first, Do/Don't pairs over prose. Read `harness/writing-readme.md` before editing or adding a convention file; the "Voice — common pitfalls" section covers the habits to resist (describe outcomes not contents, no second supporting paragraph, no positioning relative to siblings, beware colon-then-elaboration). New convention files generally follow a `Rule` / `Why` / `Do` / `Don't` / `See also` skeleton with feature-specific sections inserted as needed — match the shape of the closest existing sibling in `architecture/` or `standards/`.

## Pre-commit checks

No linters, formatters, or tests are wired in. Before pushing, manually validate:

- **Internal links** — every `winter-harness:/path/file.md` reference, every relative link inside this repo, resolves to an existing file.
- **Code references** — any production example cited via path notation (e.g. `winter:tools/winter-cli/...`) still exists at that path with the claimed shape. Conventions go stale when winter-cli refactors; if you spot drift while reading, fix it.
- **Cross-repo refs** — `winter-harness:/...`, `winter-workflow:/...` etc. point at real files in those repos.

## Delivery

- Default branch: `master`.
- **Primary contributors** push directly to `master` — no PR, no review. Rebase onto the latest `origin/master` first so history stays linear.
- **Outside contributors** are welcome — open a PR against `master` and I'll review and merge.
