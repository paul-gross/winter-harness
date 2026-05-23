# Logging

## Rule

- One logger per module: `logger = logging.getLogger(__name__)` at module top, immediately under imports.
- Levels:
  - **ERROR** — wrapped exceptions at the boundary that transforms them. Logged once by the `RepoErrorFactory` (or equivalent), never again by callers (see `python/error-handling.md`).
  - **WARNING** — recoverable conditions the caller continued past (skipped repo, missing optional config).
  - **INFO** — major lifecycle events (`init started`, `reconcile complete`). One line per event, not per item.
  - **DEBUG** — per-item traces (per-repo step, per-file action). Opt-in via `LOG_LEVEL=DEBUG`.
- Structured fields go on the exception object (`RepoError(subcommand=..., exit_code=...)`), not interpolated into the log message. The wrap site reads them off the exception and emits one record.
- No `print()` in service code. Use the injected reporter for user-facing output (see `python/dependency-injection.md`) or the logger for diagnostics. `print()` belongs in `__main__` or top-level CLI glue only.

## Why

`getLogger(__name__)` gives every record a dotted path the user can filter on (`winter_cli.modules.workspace.init_service`). A single shared root logger loses that.

The wrap-once-at-the-boundary rule keeps stack traces clean — catch-log-rethrow produces N duplicate records for the same failure, one per layer the exception passed through. Concentrating the log call inside the factory means the trace is recorded exactly where the exception is transformed, with full structured context.

Structured fields on the exception let the reporter, dashboard, and JSON output all render the same failure consistently without parsing message strings.

`print()` writes to stdout regardless of verbosity flags, breaks `--quiet`, and pollutes machine-readable output. The reporter exists so handlers can pick the right surface (TTY, JSON, log file) per invocation.

## Do

```python
import logging

logger = logging.getLogger(__name__)


class InitService:
    def reconcile(self, repos: list[Repo]) -> None:
        logger.info("reconcile started: %d repos", len(repos))
        for repo in repos:
            logger.debug("reconciling %s", repo.name)
            try:
                self._reconcile_one(repo)
            except RepoError:
                # already logged by RepoErrorFactory at ERROR; just continue
                continue
        logger.info("reconcile complete")
```

## Don't

```python
# Module-private root logger — loses the dotted-path filter.
logger = logging.getLogger()

# Catch-log-rethrow — duplicate records, no new information.
try:
    self._inner.something()
except SomethingError as exc:
    logger.error("something failed: %s", exc)
    raise

# print() in a service — bypasses the reporter and verbosity flags.
print(f"cloning {repo.url}…")

# Structured data smuggled into the message string instead of the exception.
logger.error(f"git fetch failed cwd={cwd} exit={code} stderr={stderr}")
```

## See also

- `python/error-handling.md` — log-once-at-the-wrap-site; structured errors via the injected factory.
- `python/subprocess.md` — what to capture from a failed subprocess for the log record.
- `python/dependency-injection.md` — reporters vs loggers; how user-facing output is routed.
