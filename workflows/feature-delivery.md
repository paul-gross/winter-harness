# Feature delivery

Day-to-day flow for landing a change in any winter ecosystem repo (the framework, its extensions, standalone repos). Covers where work happens on disk, what branch it sits on, how it gets onto `origin/master`, and what to run before pushing. This doc is the ecosystem default; workspaces may override in `workspace:/context/project/contributing.md`.

## Where work happens

All code changes happen inside a **feature environment worktree**, at:

    <workspace>/<env>/<repo>/

The `<env>` is a feature environment (Greek letters by convention — `alpha`, `beta`, … — but any name works). Each env contains one git worktree per project repo, all set up by `winter ws init <env>`.

The source checkouts under `<workspace>/projects/<repo>/` are **read-only references** — they exist so `git worktree add` has somewhere to share its object database. Never edit files under `projects/` directly; the changes won't appear in any feature env and will be lost the next time `winter ws fetch` fast-forwards the checkout.

If unsure which env to work in, ask. Don't pick one silently.

## Anatomy of feature delivery

A complete delivery touches every surface the change has, not just the code. This surface set is the definition of done, and it is consulted **twice**:

- **At planning time** — when a feature is decomposed into phases (in a build skill or ad hoc), enumerate the surfaces the change will owe and make each a planned phase or work-item from the outset. A surface that doesn't apply is a deliberate, noted N/A, not a silent omission. Enumerating here is what keeps the separate-repo surfaces (below) from being discovered late.
- **At pre-push** — walk the same list again to confirm each planned surface is actually current or deliberately N/A.

The surfaces:

- **Code** — the implementation, in the repo that owns the surface.
- **Tests** — coverage for the new or changed behaviour, in the same unit of work. A feature commit with no test is the anti-pattern.
- **Canonical `context/` docs** — the agent-facing source of truth for the surface: the owning repo's `context/` reference, an extension `index.md`, or a `winter-harness` convention file. This is the *currency* half of the no-undocumented-feature invariant.
- **Public docs site** — the human-facing documentation site, which for this ecosystem is its **own repo, `winter-docs`** (a separate repo, *not* an in-repo `docs/` tree — see `../documentation/governance.md` for what it is). If any page there narrates the surface you changed, plan its update as its own work-item, and reference rather than restate the canonical detail. This is the *non-duplication* half of the invariant.

The documentation surfaces span repos: a change in `winter` or an extension that alters user-facing surface usually owes a `winter-docs` edit too, even though `winter-docs` is a separate repo with no commits of its own yet. **`winter-docs` is the surface most easily missed** — structurally, not for lack of attention: it is a separate repo with no artifact co-located with the code change to trigger the thought. The in-repo `context/` docs get pulled in because they sit next to the code; the separate public-docs repo does not. That is exactly why it must be enumerated at planning time — so a `winter-docs` phase is a first-class planning output rather than a pre-push catch. The full invariant and the canonical-source-vs-rendered-site relationship live in `../documentation/feature-documentation.md`; which repo the public site is is recorded in `../documentation/governance.md`.

When a surface genuinely doesn't apply (an internal refactor with no adopter-facing angle, a change no `winter-docs` page narrates), the absence is a deliberate, reviewable call — note it at planning time rather than leaving it silent.

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

`winter ws push` only pushes repos that are ahead of their upstream — clean repos are skipped silently. Full reference: `workspace:/context/worktree-ops.md`.

## Linear history — always rebase, never merge

Before pushing, the env must be rebased onto the latest `origin/master`. The ecosystem maintains a strictly linear `master` — no merge commits, one landed unit of work per commit.

Two routes:

```bash
winter ws merge master <env>    # bulk: offline ff-only against local master (run `winter ws fetch` first if you need fresh refs)
git rebase origin/master        # single repo: from inside <env>/<repo>/
```

`winter ws merge` does an ff-only merge by default and does not hit the remote, so it's safe to fan across multiple envs in a single call (`winter ws merge master alpha beta gamma`) without redundant per-env fetches. Pass `--merge` for a 3-way fallback when ff-only would refuse. Once local commits exist, prefer `git rebase origin/master` in the affected repo so the new work sits cleanly on the tip and stays one commit per logical change.

`winter ws pull <env>` fetches and ff-integrates every worktree in one env in a single per-env call — and because it fetches, it fast-forwards the source checkouts too.

If `git rebase` reports conflicts, resolve them in the worktree with raw git — `winter` does not own conflict resolution.

## Commit conventions

Use Conventional Commits with a scope, and include a `Closes #N` footer for any GitHub issue this commit finishes:

    docs(winter-harness): tighten error-handling do/don't pairing

    Closes #12

Full rules — type vocabulary, scope choice, `Closes` / `Fixes` / `Refs` keywords, cross-repo `owner/repo#N` form — live in `workspace:/context/project/contributing.md`. Don't restate them here; read that doc when drafting a commit message.

The `commit` skill (from `winter-workflow`) generates commits in this exact format from the staged diff and the current conversation. Prefer it over hand-writing messages.

### How we commit: one unit of work, one commit

A branch reaches push time as **one commit per landed unit of work** (see *Linear history* above). What counts as "a unit" depends on how the work arrived:

- **Ad-hoc work** (conversational, no tracking issue) — keep rolling into a **single** commit. When the user gives follow-up feedback on unpushed work, `git commit --amend` or squash it into the existing commit; don't stack a second `feedback revisions` commit on top.
- **Work-item / issue work** — **one commit per tracked work item**, each carrying its own issue-closing footer (`Closes #N` or the tracker's equivalent). Don't fold several work items into one commit, and don't split one across several. When a single env touches multiple work items, land them as separate commits.

If unpushed work has drifted to more than one commit for its unit, squash before pushing (`git rebase -i origin/master`).

## Pre-push checks

No CI runs against `master`. Anything not run locally before push lands silently.

For Python repos, run all three before pushing:

```bash
mise run format     # rewrites in place
mise run lint       # exits 0 on a clean tree
mise run typecheck  # exits 0 on a clean tree
```

Rules and canonical config: `../standards/linting.md` (ruff) and `../standards/typechecking.md` (pyright). Other languages document their own pre-push checks in their `CONTRIBUTING.md` or `context/` — read the target repo's `CONTRIBUTING.md` before pushing.

If the env spans multiple repos, run pre-push checks in every repo that has uncommitted or unpushed changes, not just the one you happened to touch last.

**No undocumented feature.** A change to user-facing surface — a `winter` subcommand or flag, an extension capability, a skill or agent, an env-root file or a convention — carries its documentation delta in the same unit of work, the same way it carries its tests. Before pushing, walk the *Anatomy of feature delivery* checklist above: confirm the canonical `context/` / `index.md` / convention source for the changed surface is current, **and** confirm the public docs site (`winter-docs`) is current — if a page there narrates the changed surface, it is updated and still references rather than restates the canonical detail. The full invariant is `../documentation/feature-documentation.md`; a pre-push review gate surfaces a missing-docs delta the same way it surfaces a missing test — but such a gate only sees repos with commits, so the `winter-docs` currency check is yours to run even when `winter-docs` has none.

## Verify against the real environment

Automated tests are necessary but not sufficient. Before a change is done, **exercise it through the environment's real entrypoints** — the installed `winter` CLI and any env-root entrypoints an extension installs that a user would actually invoke — not throwaway stubs wired straight at the in-progress worktree. A green suite over a stub proves the code compiles, not that the wired-up system runs it: an env left on the old install executes the old code no matter what the worktree says. This is what "tested" means here, and it is the failure mode behind a change that "passed" yet broke the moment the user ran it for real. State in the delivery summary **which wiring you actually exercised**, and call out anything verified only against a stub.

The real entrypoints resolve to *installed* code by default, so two mechanisms point them at the in-progress worktree:

- **The CLI** — the `winter` launcher takes a `--winter=PATH` override as its **first** argument, where `PATH` is an env (or any dir) containing `tools/winter-cli`; the launcher runs that tree's CLI against the current workspace (e.g. `winter --winter=./alpha/winter ws status`). It is per-invocation — no restore step — and fails fast on a missing path or one without `tools/winter-cli`.
- **Extension-installed entrypoints** — entrypoints an extension installs at the env root (commonly symlinks) resolve to the *installed* extension code, not the worktree. winter has no flag to override these; the procedure to repoint one at a worktree and restore it after is owned by the installing extension — see that extension's docs. Restoring is mandatory: a left-over override silently makes every later call in that env run worktree code.

## After pushing

Fast-forward the source checkout in `projects/<repo>/` after a push lands. `winter ws init <env>` branches new envs from the local `projects/<repo>/master`, so any commit on `origin/master` not reflected there starts the next env behind.

```bash
winter ws fetch <env>    # refreshes remote refs and fast-forwards every projects/<repo>/master to origin/master
```

Run it against the env you just pushed from — `winter ws fetch` fast-forwards every source checkout to `origin/master`; the feature worktrees are left untouched. Full reference: `workspace:/context/worktree-ops.md`.

For single-repo work, the raw equivalent is:

```bash
git -C ./projects/<repo>/ fetch origin
git -C ./projects/<repo>/ merge --ff-only origin/master
```

Direct edits under `projects/` are otherwise discouraged — the source checkouts are read-only references (see *Where work happens*). This fast-forward is the narrow exception.

## Delivery sequence — end to end

The sections above are organized by topic; this is the ordered walkthrough that sequences them once the change is built and its surfaces are current (see *Anatomy of feature delivery*). Each step defers to its detailed section — follow the link for the commands and rules.

1. **Rebase onto the latest `origin/master`** so history stays linear — see *Linear history — always rebase, never merge* for the merge-vs-pull-vs-rebase choice (`git rebase origin/master` once you have local commits).
2. **Ensure the pre-push gate has run on this change-set — once.** Run the gates in *Pre-push checks* and the `pre-push` review skill (from `winter-workflow`), but only if they haven't already run since your last change. The step is idempotent: don't re-run a gate that's still green.
3. **Push to `origin/master`** with explicit user sign-off — see *Push target*.
4. **Catch up the source checkouts** for the env you pushed from — see *After pushing* (`winter ws fetch <env>`; this fast-forwards the read-only checkouts, distinct from the step-1 worktree rebase).
5. **If you delivered to a repo the workspace tracks as an upstream framework, re-sync the workspace.** When the change landed in a repo the workspace itself consumes upstream — for this workspace, `winter` — that repo's `master` has advanced and the workspace repo now sits behind its upstream tip. Replay the workspace's single customization commit onto the new tip per `./upstream-tracking.md` (*Sync flow*: fetch the upstream remote, rebase, force-with-lease — with sign-off). Skip this step when the delivered repo isn't one the workspace tracks upstream (most extension and standalone changes).

## See also

- `workspace:/context/project/contributing.md` — canonical commit format, `Closes #N` footer rules, push policy
- `workspace:/context/worktree-ops.md` — full reference for `winter ws init` / `sync` / `connect` / `pull` / `push` / `destroy`, including pinned-repo semantics
- `../standards/linting.md`, `../standards/typechecking.md` — pre-push tools for Python repos
- `../documentation/feature-documentation.md` — the "no undocumented feature" invariant the pre-push doc-currency check enforces
- `./upstream-tracking.md` — separate flow for workspaces that customize an upstream framework repo
- `../CONTRIBUTING.md` — the same rules applied to this repo (`winter-harness`) specifically
