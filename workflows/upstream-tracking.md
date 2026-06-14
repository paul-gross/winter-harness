# Upstream tracking

How a workspace consumes an **upstream framework repo** while keeping its own customizations on top.

## Bootstrap

A fresh clone of the user's fork has only `origin` set. Wire up the upstream remote once:

```bash
git remote add <upstream-name> <upstream-url>
git fetch <upstream-name>
```

The upstream remote's name is conventionally the upstream project's short name — `winter` for a workspace tracking `pgross/winter`. Don't use the literal string `upstream`.

## Dual-remote layout

After bootstrap, the workspace repo has **two remotes**:

| Remote | Points at | Used for |
|--------|-----------|----------|
| `origin` | The user's fork (e.g. `git@github.com:<user>/<workspace>.git`) | Pushes |
| `<upstream-name>` | The upstream framework repo (e.g. `git@github.com:paul-gross/winter.git`) | Pulls |

Verify:

```bash
git remote -v
```

## Single-commit-on-top contract

Every workspace customization lives in **exactly one** commit on top of `<upstream-name>/master`. The commit message conventionally reads:

    feat(<workspace-name>): workspace configuration

The HEAD of `origin/master` is always:

    <upstream-name>/master + 1 commit

Never two, never zero. If new customizations are needed, **amend** the single commit; don't stack a second commit on top.

If `git log --oneline <upstream-name>/master..HEAD` prints more than one line, the workspace is out of contract — squash extras into the customization commit (`git rebase -i <upstream-name>/master`) before continuing.

## Inherited copies

Every file the customization commit does not own is an **inherited copy** — it lives in the upstream repo and travels downstream on the next *Sync flow*. The edit-time rule for these (check before editing; fix at the source repo, never hand-edit the downstream copy) belongs where an agent looks before touching a file, so it lives in `workspace:/ai/workspace-layout.md` §"Inherited docs at the workspace root" rather than being restated here.

## Sync flow

Run when upstream has advanced and the workspace needs to catch up:

```bash
git fetch <upstream-name>
git rebase <upstream-name>/master
git push --force-with-lease origin master
```

The rebase replays the single customization commit onto the new upstream tip. **Always `--force-with-lease`, never plain `--force`** — `--force-with-lease` aborts if `origin/master` has moved since the last fetch, which protects against overwriting another contributor's push to the fork.

**Agents: never force-push without explicit user sign-off.** `--force-with-lease` is still a history rewrite — anyone who fetched the prior tip needs to rebase after it lands. After the local rebase succeeds, stop and ask the user to confirm before running `git push --force-with-lease`.

If the rebase reports conflicts, the upstream has changed something the customization commit also touches. Resolve in the worktree with raw git, then continue with `git rebase --continue` and the force-push.

## Amend vs new commit

**Amend the customization commit** whenever you change workspace config — `.winter/config.toml`, `CLAUDE.md`, extension registrations, `ai/project/*.md`, anything that's part of the customization layer:

```bash
git add <files>
git commit --amend --no-edit          # keep the existing message
git push --force-with-lease origin master
```

**Never create a second customization commit.** Two commits on top of upstream breaks the single-commit contract and makes the next `git rebase <upstream-name>/master` ambiguous about which commit represents "the customization."

The same agent-sign-off rule from [Sync flow](#sync-flow) applies to the amend push.

Project repos are governed separately — see `./workflows/feature-delivery.md`.

## See also

- `./workflows/feature-delivery.md` — the flow for landing changes in project repos (linear history via rebase, push direct to `origin/master`, pre-push checks)
- `workspace:/ai/project/contributing.md` — commit format and `Closes #N` footer rules
- `workspace:/ai/worktree-ops.md` — `winter ws fetch` / `pull` / `push` reference (these operate on **project repos** inside the workspace, not on the workspace repo itself)
