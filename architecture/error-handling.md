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

The example below is synthetic — a stand-in `FooService` that runs four
steps against a `FooRepository`. The point is the shape, not the API: a
single `try/except` at the boundary that wants to handle the failure,
with the happy path staying linear.

```python
def _apply_tag(self, foo_id: str) -> None:
    if tag := self._workspace.foo_tag:
        self._foo_repo.set_tag(foo_id, tag)


def _reconcile_foo(self, foo, reporter) -> bool:
    try:
        self._foo_repo.create(foo, foo.main_path)
        self._apply_tag(foo.main_path)
        self._write_metadata(foo.main_path, foo, reporter)
        self._run_hooks(foo.main_path, foo.name, list(foo.hooks), reporter)
        return True
    except (FooError, OSError) as exc:
        reporter.foo_error(foo.name, str(exc))
        return False
```

## Don't

```python
def _apply_tag(self, foo_id, reporter, foo_name) -> bool:
    try:
        self._foo_repo.set_tag(foo_id, tag)
        return True
    except FooError as exc:
        reporter.foo_error(foo_name, str(exc))
        return False


def _reconcile_foo(self, foo, reporter):
    if not self._create(foo, foo.main_path, reporter):
        return False
    if not self._apply_tag(foo.main_path, reporter, foo.name):
        return False
    if not self._write_metadata(foo.main_path, foo, reporter):
        return False
    if not self._run_hooks(foo.main_path, foo.name, list(foo.hooks), reporter):
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

In winter-cli, this is checked at `mise run test` time by `winter:tools/winter-cli/tests/conventions/test_no_catch_log_rethrow.py`. CLI entrypoints (`cli.py`, `__main__.py`) are exempt — that's the boundary where log-and-exit is the actual handling. See the test's docstring for the two detection blind spots (`if/else` arms; nested control flow).

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
- Captures structured fields (`subcommand`, `cmd_args`, `cwd`, `exit_code`, `stderr`) that the reporter and dashboard can render without re-parsing the message.
- Lets tests substitute a fake factory and assert error shapes.

A concrete `RepoErrorFactory` bound in the DI container (singleton) and injected into every repository is enough — the seam is exercised by tests through a fake factory, and there has not yet been a need for a second adapter behind it. Consider extracting an `IRepoErrorFactory` Protocol when (and only when) a second factory shape appears (e.g. a non-git transport that needs a different `from_*` constructor).

Until then, inject the concrete class:

```python
class WriteFooRepository:
    def __init__(self, error_factory: RepoErrorFactory) -> None:
        self._errors = error_factory

    def save_thing(self, thing: Thing) -> None:
        try:
            some_io_library.write(thing.id, thing.payload)
        except some_io_library.IOError as exc:
            raise self._errors.from_io(exc, f"save failed for {thing.id}")
```

The factory has one `from_<transport>(exc, message, *, cwd)` method per underlying exception type it knows how to translate — `from_git` for `git.GitCommandError`, `from_subprocess` for `subprocess.CompletedProcess`, `from_io` for a generic IO library, etc. Each method extracts the structured fields (`subcommand`, `cmd_args`, `exit_code`, `stderr`) off the exception itself; callers pass only the high-level `message`. Production winter-cli currently exposes only `from_git`.

`RepoError` itself becomes a dataclass-shaped exception carrying those fields, not just a message string. See `winter-harness:/exemplars/python/repo_pattern.py` for the full example, and `winter:tools/winter-cli/src/winter_cli/modules/workspace/internal/repo_error_factory.py` for the production factory in winter-cli (which wraps `git.GitCommandError`, `subprocess.CalledProcessError`, and other transport-level exceptions).

The factory is also where the **log-once-at-the-wrap-site** rule is enforced: it emits a single ERROR record with the structured fields before returning the wrapped exception. See `../standards/logging.md` for level conventions and why callers must not log it again.

## When `bool` is honest

Aggregator methods that run N independent steps and report "did all of them succeed?" can legitimately return `bool` — the result is data, not control flow. Example: `reconcile_all` runs projects → standalones → worktrees → workspace and returns `False` if any failed. That's fine. The smell is bool returns inside the leaves.
