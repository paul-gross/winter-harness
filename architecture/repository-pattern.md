# Repository pattern

## Rule

All reads from and writes to *external systems* live in repository classes. Other modules go through repository methods; they don't import the underlying library directly.

"External" means outside the application's process — git, filesystem, HTTP APIs, databases, queues, cloud services, IPC. Git and filesystem are the typical examples in this codebase.

## Why

When external-system access sprawls across services, every consumer has to handle that system's exceptions, parse its output, and know its error model. When it's confined to one place:

- Tests only mock the repository, not the underlying library.
- Error wrapping happens once (at one `RepoError`-style boundary), if it's wrapped at all.
- Migrating to a different library or backend happens in one file.
- The library's exception types don't escape into business logic.

In this codebase, `ReadRepoRepository`/`WriteRepoRepository` confine all GitPython usage; same principle applies to any other external system you depend on.

## Layout

```
modules/<feature>/
  internal/
    read_repo_repository.py   # all GitPython here, read-only
    write_repo_repository.py  # extends Read, adds mutations
  service.py                  # uses repo via constructor injection
```

`Read` and `Write` split for a specific reason: **`Read` is usable everywhere — including up at CLI handlers — as the way to reconstitute domain objects from external state. `Write` should be orchestrated by domain services, because mutations carry business meaning, ordering, and side effects.**

This eliminates forced passthrough methods on the service layer. A CLI handler that just needs to display data calls `Read` directly; it doesn't need a service method that wraps a `repo.get_X()`. Service methods exist where there's *actual orchestration* — multiple steps, business logic, side effects beyond the write itself.

This applies the **Dependency Inversion Principle** at the service/infrastructure boundary (high-level modules depend on the repository abstraction, not on the concrete library) and follows the standard **Clean Architecture** layering — outer layers can read through the abstraction, but state changes flow through inner-layer services that own the business semantics.

## Do

```python
class WriteRepoRepository(ReadRepoRepository):
    def clone(self, repo: IWorkspaceRepository, dest: Path) -> None:
        if not repo.url:
            raise RepoError(f"no url for {repo.name}; cannot clone")
        try:
            git.Repo.clone_from(repo.url, str(dest))
        except git.GitCommandError as exc:
            raise RepoError(f"clone failed — {exc}") from exc


# In a coordinator:
self._repo_repo.clone(repo, dest)
```

## Don't

```python
# In a service that has no business knowing about GitPython:
import git

try:
    git.Repo.clone_from(url, str(repo_path))
except git.GitCommandError as exc:
    reporter.repo_error(name, str(exc))
    return False
```

## Class-docstring contract

Every class names its single responsibility in its docstring. That sentence becomes the contract: anything outside that responsibility belongs in a different class.

Example from this codebase:

```python
class ReadRepoRepository:
    """Read-only GitPython implementation. All GitPython usage is confined here."""
```

That sentence is load-bearing — reviewers reject any `import git` outside repository classes because the docstring explicitly claims the boundary. The same applies to every class: write the responsibility down, and reject code in the file that doesn't fit it.

If the docstring is hard to write — if it's vague, or you keep wanting to use "and" — that's a smell that the class has more than one responsibility.

## What stays out

- High-level orchestration (which entity to read, when to retry, which path to take) lives in services, not in the repository.
- A repository owns I/O against *its* external system. A git-scoped repository doesn't own unrelated filesystem checks; a filesystem-scoped one doesn't own HTTP. Cross-system orchestration is the caller's job.

## Testing adapters

**Rule**: adapter tests mock the underlying library at the adapter's import site, not at the library's source. Use `monkeypatch.setattr(<adapter_module>, "<library_symbol>", MagicMock())` per test. No shared mock fixtures across the file — each test asserts a distinct library-call shape and must be self-contained.

```python
# correct — patch at the adapter's import site
from winter_cli.core.internal import local_subprocess_runner

def test_run_passes_args(monkeypatch):
    fake = MagicMock()
    fake.run.return_value = MagicMock(returncode=0, stdout="", stderr="")
    monkeypatch.setattr(local_subprocess_runner, "subprocess", fake)
    ...

# wrong — patch at the library's source
monkeypatch.setattr("subprocess.run", fake_run)
```

Assert both the library-call shape (`fake.run.assert_called_once_with(...)`) and the adapter's return value. Both matter: the first pins the contract, the second pins the translation logic.

Use the real exception class for error-path tests (`OSError`, `git.GitCommandError`, `tomllib.TOMLDecodeError`). A `MagicMock(spec=ExcClass)` won't satisfy an `except ExcClass` clause.

**Tradeoff**: this pattern catches contract bugs in the adapter — wrong arguments, missing keyword, wrong exception wrapping. It does not catch library-version drift (the real `subprocess.run` signature changing, or GitPython changing a method name). Library-version drift requires an integration or smoke test that runs the real library against real I/O.

**Integration coverage**: adapter unit tests do not catch library-version drift. A smoke harness that exercises adapters against real external systems (a real git repo, a real filesystem, a live subprocess) supplements adapter unit tests and lives outside `pytest`; it does not replace them.

## See also

- `./service-architecture.md` — the service-based principle a repository is one shape of: an injected class that owns I/O against one external system.
- `../exemplars/python/repo_pattern.py` — canonical shape for new repository classes.
- `./subprocess.md` — the concrete shape for shelling out from inside a repository (`capture_output` / `check=False` / wrap via the injected factory).
- `../standards/testing.md` — full test strategy; the Adapters bullet in the assertion-patterns section applies here.
