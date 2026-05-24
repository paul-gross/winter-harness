# Feature delivery

Day-to-day flow for landing a change in any winter ecosystem repo (the framework, its extensions, standalone repos). Covers where work happens on disk, what branch it sits on, how it gets onto `origin/master`, and what to run before pushing. This doc is the ecosystem default; workspaces may override in `workspace:/ai/project/contributing.md`.

## Where work happens

All code changes happen inside a **feature environment worktree**, at:

    <workspace>/<env>/<repo>/

The `<env>` is a feature environment (Greek letters by convention — `alpha`, `beta`, … — but any name works). Each env contains one git worktree per project repo, all set up by `winter ws init <env>`.

The source checkouts under `<workspace>/projects/<repo>/` are **read-only references** — they exist so `git worktree add` has somewhere to share its object database. Never edit files under `projects/` directly; the changes won't appear in any feature env and will be lost the next time `winter ws sync` fast-forwards the checkout.

If unsure which env to work in, ask. Don't pick one silently.

## Branch naming

Two branch names matter, and they don't have to match:

- **Local branch** — always the env name. `winter ws init <env>` creates the worktree on a branch literally named `<env>` (see `workspace:/CLAUDE.md` for env naming and port assignment).
- **Remote feature branch** — set via `winter ws connect <env> <feature-branch>` when the env should push to a named remote branch instead of `master`. The remote name is independent of the local branch (e.g. local `alpha` → remote `feature/basic-addon`).

For the default delivery flow (push to `origin/master`), no `connect` is needed — `winter ws push` lands the env's commits directly on `master`.

## Push target

**Completed work pushes directly to `origin/master`** for each project repo. No PR, no MR, no review gate, no remote feature branches in the default flow.

Use the CLI:

```bash
winter ws push                  # every env's non-pinned worktrees
winter ws push <env>            # one env's non-pinned worktrees
winter ws push <env>/<repo>     # one specific worktree
winter ws push --include-pinned # also push pinned worktrees
```

`winter ws push` only pushes repos that are ahead of their upstream — clean repos are skipped silently. The full `push` command reference (patterns, pinned-repo semantics, `--standalone`, `--all`) is in `workspace:/ai/worktree-ops.md`.

When the env *is* connected to a remote feature branch, `winter ws push` pushes to that branch instead of `master` — use that path for shared in-progress work.

## Linear history — always rebase, never merge

Before pushing, the env must be rebased onto the latest `origin/master`. The ecosystem maintains a strictly linear `master` — no merge commits, one landed unit of work per commit.

Two routes:

```bash
winter ws sync <env>            # bulk: fetches every repo and ff-merges origin/<main>
git rebase origin/master        # single repo: from inside <env>/<repo>/
```

`winter ws sync` does an ff-only merge (with a 3-way fallback when ff isn't possible), which is fine for the common case where the env has no local commits yet on top of master. Once local commits exist, prefer `git rebase origin/master` in the affected repo so the new work sits cleanly on the tip and stays one commit per logical change.

If `git rebase` reports conflicts, resolve them in the worktree with raw git — `winter` does not own conflict resolution.

## Commit conventions

Use Conventional Commits with a scope, and include a `Closes #N` footer for any Codeberg issue this commit finishes:

    docs(winter-harness): tighten error-handling do/don't pairing

    Closes #12

Full rules — type vocabulary, scope choice, `Closes` / `Fixes` / `Refs` keywords, cross-repo `owner/repo#N` form — live in `workspace:/ai/project/contributing.md`. Don't restate them here; read that doc when drafting a commit message.

The `/commit` skill (from `winter-workflow`) generates commits in this exact format from the staged diff and the current conversation. Prefer it over hand-writing messages.

## Pre-push checks

No CI runs against `master`. Anything not run locally before push lands silently.

For Python repos, run all three before pushing:

```bash
mise run format     # rewrites in place
mise run lint       # exits 0 on a clean tree
mise run typecheck  # exits 0 on a clean tree
```

Rules and canonical config: `./python/linting.md` (ruff) and `./python/typechecking.md` (pyright). Other languages document their own pre-push checks in their `CONTRIBUTING.md` or `ai/` — read the target repo's `CONTRIBUTING.md` before pushing.

If the env spans multiple repos, run pre-push checks in every repo that has uncommitted or unpushed changes, not just the one you happened to touch last.

## See also

- `workspace:/ai/project/contributing.md` — canonical commit format, `Closes #N` footer rules, push policy
- `workspace:/ai/worktree-ops.md` — full reference for `winter ws init` / `sync` / `connect` / `pull` / `push` / `destroy`, including pinned-repo semantics
- `./python/linting.md`, `./python/typechecking.md` — pre-push tools for Python repos
- `./workflows/upstream-tracking.md` — separate flow for workspaces that customize an upstream framework repo
- `./CONTRIBUTING.md` — the same rules applied to this repo (`winter-harness`) specifically
