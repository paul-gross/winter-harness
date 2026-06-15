# Subprocess

## Rule

- All `subprocess.run` / `subprocess.Popen` usage is confined to a repository or adapter under `internal/` — see `./repository-pattern.md`.
- Always `capture_output=True`, `text=True`, `check=False`. Inspect `returncode` explicitly.
- Wrap non-zero exits and `OSError` into the feature's `RepoError` via the injected `RepoErrorFactory` (see `./error-handling.md`). Capture `subcommand`, `cmd_args`, `cwd`, `exit_code`, and `stderr` as structured fields, not as a concatenated message.
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
            completed, f"fetch {remote} failed", cwd=cwd,
        )
```

The factory extracts `subcommand`, `cmd_args`, `exit_code`, and `stderr` off `completed.args` and attaches them to the `RepoError` as structured fields — same shape as `from_git(exc, message, *, cwd)` in `./error-handling.md`. Callers pass only the high-level `message` and don't repeat the extraction at every wrap site.

**Method-name convention:** the factory has one method per underlying transport — `from_git` for `git.GitCommandError`, `from_subprocess` for `subprocess.CompletedProcess`, and so on. Production winter-cli currently exposes only `from_git`; `from_subprocess` is the canonical shape for new adapters that wrap raw `subprocess`.

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

- `./error-handling.md` — structured errors via the injected factory; `from_<transport>(exc, message, *, cwd)` canonical shape.
- `./repository-pattern.md` — why subprocess lives in `internal/`.
- `../standards/logging.md` — log levels for wrapped subprocess failures.
- `winter/tools/winter-cli/src/winter_cli/core/internal/local_subprocess_runner.py` — the production `ISubprocessRunner` adapter (`run` + `popen` seams).
- `winter/tools/winter-cli/src/winter_cli/modules/workspace/internal/repo_error_factory.py` — the production wrapping factory. Currently implements `from_git` only; `from_subprocess` is the canonical shape for new adapters.
