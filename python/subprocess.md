# Subprocess

## Rule

- All `subprocess.run` / `subprocess.Popen` usage is confined to a repository or adapter under `internal/` — see `python/repository-pattern.md`.
- Always `capture_output=True`, `text=True`, `check=False`. Inspect `returncode` explicitly.
- Wrap non-zero exits and `OSError` into the feature's `RepoError` via the injected `RepoErrorFactory` (see `python/error-handling.md`). Capture `subcommand`, `args`, `cwd`, `exit_code`, and `stderr` as structured fields, not as a concatenated message.
- Never `shell=True` for any command whose tokens come from a variable. Pass `cmd` as a `list[str]`.

## Why

`check=True` raises `CalledProcessError`, which leaks a subprocess-specific exception type into every caller. Wrapping at the boundary lets services catch `RepoError` without importing `subprocess`, and centralizes the structured fields the dashboard and CLI render.

`capture_output=True` + `text=True` keeps stdout and stderr decoded and available for the error wrapper. Streaming subprocesses are a different shape — use the `ISubprocessRunner.popen` seam, not raw `Popen`.

`shell=True` with variable inputs is a command-injection footgun. The list form is safe by default and indistinguishable in cost.

## Do

```python
def fetch(self, cwd: Path, remote: str) -> None:
    completed = subprocess.run(
        ["git", "fetch", remote],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise self._errors.from_subprocess(
            completed, subcommand="fetch", args=(remote,), cwd=cwd,
        )
```

The factory extracts `exit_code` and `stderr` off `completed` and attaches them to the `RepoError` as structured fields — same shape as `from_io(exc, ...)` in `python/error-handling.md`. Callers don't repeat that extraction at every wrap site.

## Don't

```python
# Leaks CalledProcessError; loses cwd/args structure; check=True hides exit_code.
subprocess.run(["git", "fetch", remote], cwd=cwd, check=True)

# shell=True with a variable — command injection if `remote` contains a space or `;`.
subprocess.run(f"git fetch {remote}", shell=True, check=False)

# Discards stderr — the wrap site has nothing to log or surface.
subprocess.run(["git", "fetch", remote], cwd=cwd)
```

## See also

- `python/error-handling.md` — structured errors via the injected factory; `from_io(exc, ...)` canonical shape.
- `python/repository-pattern.md` — why subprocess lives in `internal/`.
- `python/logging.md` — log levels for wrapped subprocess failures.
- `winter/tools/winter-cli/src/winter_cli/core/internal/local_subprocess_runner.py` — the production `ISubprocessRunner` adapter (`run` + `popen` seams).
- `winter/tools/winter-cli/src/winter_cli/modules/workspace/internal/repo_error_factory.py` — the production wrapping factory. Currently implements `from_git` only; `from_subprocess` is the canonical shape for new adapters.
