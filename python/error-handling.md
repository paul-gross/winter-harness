# Error handling

## Rule

- Raise on failure; don't return `bool` for success/failure.
- Catch only at the boundary where you actually handle the error — to recover, transform, or surface it to a user-facing reporter.
- Don't catch-log-rethrow. If you're not doing specific handling, let the exception propagate.

## Why

Bool returns force every caller to check. Multi-step orchestrators turn into ladders of `if not self._step(): return False`, which interleaves failure handling with happy paths. Each step's catch + report logic gets duplicated.

Catch-log-rethrow has the same problem in disguise: every layer logs the same error before rethrowing, producing duplicate noise in logs while not actually handling anything. The exception still propagates; you've just polluted the trace.

Exceptions concentrate failure handling at the boundary that actually wants to handle it. Most code stays linear.

## Do

```python
def _apply_identity(self, repo_path: Path) -> None:
    if identity := self._workspace.git_identity:
        self._repo_repo.set_identity(repo_path, identity)


def _reconcile_source_checkout(self, repo, reporter) -> bool:
    try:
        self._repo_repo.clone(repo, repo.main_path)
        self._apply_identity(repo.main_path)
        self._write_excludes(repo.main_path, repo, reporter)
        self._run_cmds(repo.main_path, repo.name, list(repo.cmd), reporter)
        return True
    except (RepoError, OSError) as exc:
        reporter.repo_error(repo.name, str(exc))
        return False
```

## Don't

```python
def _apply_identity(self, repo_path, reporter, repo_name) -> bool:
    try:
        self._repo_repo.set_identity(repo_path, identity)
        return True
    except RepoError as exc:
        reporter.repo_error(repo_name, str(exc))
        return False


def _reconcile_source_checkout(self, repo, reporter):
    if not self._clone(repo, repo.main_path, reporter):
        return False
    if not self._apply_identity(repo.main_path, reporter, repo.name):
        return False
    if not self._write_excludes(repo.main_path, repo, reporter):
        return False
    if not self._run_cmds(repo.main_path, repo.name, list(repo.cmd), reporter):
        return False
    return True
```

## Don't catch-log-rethrow

```python
def _do_step(self):
    try:
        self._inner.something()
    except SomethingError as exc:
        logger.error("something failed: %s", exc)
        raise
```

This adds noise without value. The exception still propagates; you've just logged it at every level it passes through. The actual handler at the boundary will report it once with full context.

The rule is binary: catch and *handle* (do something specific — recover, transform, surface to a reporter), or don't catch at all.

## Custom error types

Create a custom domain error type (e.g. `RepoError`) when *callers handle that error specifically* — and would otherwise need to depend on the underlying library to do so. That's the YAGNI test.

`RepoError` earns its keep here because `InitService` boundaries catch `(RepoError, OSError)` to surface failures via `reporter.repo_error()`; they shouldn't have to import `git.GitCommandError` for that. If nothing catches your wrapper specifically — if every caller just propagates — you've added ceremony without value. Let the library exception bubble through.

When wrapping IS justified, do it at the call site. For ad-hoc wrapping, use `raise X from Y` so the original traceback is preserved:

```python
try:
    git.Repo.clone_from(repo.url, str(dest))
except git.GitCommandError as exc:
    raise RepoError(f"clone failed — {exc}") from exc
```

## Structured errors via an injected factory

Once the same wrap site appears in many places — every repository method, for instance — promote the wrapping to a factory and inject it. This:

- Centralizes the **log-once-at-wrap-site** convention (no catch-log-rethrow cascades).
- Captures structured fields (`subcommand`, `args`, `cwd`, `exit_code`, `stderr`) that the reporter and dashboard can render without re-parsing the message.
- Lets tests substitute a fake factory and assert error shapes.

The canonical shape:

```python
class IRepoErrorFactory(Protocol):
    def from_io(self, exc: Exception, *, subcommand: str, args: tuple[str, ...],
                cwd: Path | None = None) -> RepoError: ...
```

…with a concrete `RepoErrorFactory` bound in the DI container (singleton) and injected into every repository:

```python
class _WriteFooRepository:
    def __init__(self, error_factory: IRepoErrorFactory) -> None:
        self._errors = error_factory

    def save_thing(self, thing: Thing) -> None:
        try:
            some_io_library.write(thing.id, thing.payload)
        except some_io_library.IOError as exc:
            raise self._errors.from_io(exc, subcommand="save", args=(thing.id,))
```

`RepoError` itself becomes a dataclass-shaped exception carrying those fields, not just a message string. See `winter-harness:/exemplars/python/repo_pattern.py` for the full example, and `winter:tools/winter-cli/src/winter_cli/modules/workspace/internal/repo_error_factory.py` for the production factory in winter-cli (which wraps `git.GitCommandError`, `subprocess.CalledProcessError`, and other transport-level exceptions).

The factory is also where the **log-once-at-the-wrap-site** rule is enforced: it emits a single ERROR record with the structured fields before returning the wrapped exception. See `python/logging.md` for level conventions and why callers must not log it again.

## When `bool` is honest

Aggregator methods that run N independent steps and report "did all of them succeed?" can legitimately return `bool` — the result is data, not control flow. Example: `reconcile_all` runs projects → standalones → worktrees → workspace and returns `False` if any failed. That's fine. The smell is bool returns inside the leaves.
