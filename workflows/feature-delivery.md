# Feature delivery

Day-to-day flow for landing a change in any winter ecosystem repo (the framework, its extensions, standalone repos). Covers where work happens on disk, what branch it sits on, how it gets onto `origin/master`, and what to run before pushing. This doc is the ecosystem default; workspaces may override in `workspace:/ai/project/contributing.md`.

## Where work happens

All code changes happen inside a **feature environment worktree**, at:

    <workspace>/<env>/<repo>/

The `<env>` is a feature environment (Greek letters by convention — `alpha`, `beta`, … — but any name works). Each env contains one git worktree per project repo, all set up by `winter ws init <env>`.

The source checkouts under `<workspace>/projects/<repo>/` are **read-only references** — they exist so `git worktree add` has somewhere to share its object database. Never edit files under `projects/` directly; the changes won't appear in any feature env and will be lost the next time `winter ws sync` fast-forwards the checkout.

If unsure which env to work in, ask. Don't pick one silently.

## Pinned repos

All project repos are **pinned** in `.winter/config.toml` — pinned worktrees track `origin/master` and pushes land directly on `master`. No feature branches, no `winter ws connect`. A contributor may add unpinned repos to a local `.winter/config.toml` overlay to test or verify in-progress functionality against a non-canonical upstream; treat those as scratch, not part of the delivery path.

## Push target

**Agents: never push without explicit user sign-off.** `master` is shared and lands immediately — no PR review, no CI gate, and reverting a bad push requires a force-push (destructive). After committing, stop and ask the user to confirm before running `winter ws push` or raw `git push`. "Work on issue #N" is not authorization to push the resulting commit; commit and wait.

**Completed work pushes directly to `origin/master`** for each project repo. No PR, no MR, no review gate.

```bash
winter ws push <env> --include-pinned         # every repo in <env> that's ahead of master
winter ws push <env>/<repo> --include-pinned  # one specific repo's worktree
git push                                      # from inside <env>/<repo>/, single repo
```

`winter ws push` only pushes repos that are ahead of their upstream — clean repos are skipped silently. Full reference: `workspace:/ai/worktree-ops.md`.

## Linear history — always rebase, never merge

Before pushing, the env must be rebased onto the latest `origin/master`. The ecosystem maintains a strictly linear `master` — no merge commits, one landed unit of work per commit.

Two routes:

```bash
winter ws merge master <env>    # bulk: offline ff-only against local master (run `winter ws fetch` first if you need fresh refs)
git rebase origin/master        # single repo: from inside <env>/<repo>/
```

`winter ws merge` does an ff-only merge by default and does not hit the remote, so it's safe to fan across multiple envs in a single call (`winter ws merge master alpha beta gamma`) without redundant per-env fetches. Pass `--merge` for a 3-way fallback when ff-only would refuse. Once local commits exist, prefer `git rebase origin/master` in the affected repo so the new work sits cleanly on the tip and stays one commit per logical change.

`winter ws sync <env>` bundles fetch + ff-merge + source-checkout FF for one env — use it when you want all three in a single command and don't mind the per-env remote call.

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

## After pushing

Fast-forward the source checkout in `projects/<repo>/` after a push lands. `winter ws init <env>` branches new envs from the local `projects/<repo>/master`, so any commit on `origin/master` not reflected there starts the next env behind.

```bash
winter ws sync <env>    # fast-forwards every projects/<repo>/master to origin/master as a side effect
```

Run it against the env you just pushed from — the worktrees are at master (no commits to integrate), and the side effect catches every source checkout up. Full reference: `workspace:/ai/worktree-ops.md`.

For single-repo work, the raw equivalent is:

```bash
git -C ./projects/<repo>/ fetch origin
git -C ./projects/<repo>/ merge --ff-only origin/master
```

Direct edits under `projects/` are otherwise discouraged — the source checkouts are read-only references (see *Where work happens*). This fast-forward is the narrow exception.

## See also

- `workspace:/ai/project/contributing.md` — canonical commit format, `Closes #N` footer rules, push policy
- `workspace:/ai/worktree-ops.md` — full reference for `winter ws init` / `sync` / `connect` / `pull` / `push` / `destroy`, including pinned-repo semantics
- `./python/linting.md`, `./python/typechecking.md` — pre-push tools for Python repos
- `./workflows/upstream-tracking.md` — separate flow for workspaces that customize an upstream framework repo
- `./CONTRIBUTING.md` — the same rules applied to this repo (`winter-harness`) specifically
