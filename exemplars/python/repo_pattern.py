"""Canonical repository-pattern example.

Read this when adding a new repository class or extending an existing one.
The shape codifies three orthogonal seams the winter codebase has standardized on:

  1. **Protocol seams, I-prefix names.** The public callable surface is a
     `Protocol` named `IRead<Foo>Repository` / `IWrite<Foo>Repository`. The
     I-prefix is the convention — services depend on the Protocol, never on
     the concrete class.

  2. **`internal/` adapter placement.** Concrete implementations of the
     Protocols live under an `internal/` subpackage (e.g.
     `modules/<feature>/internal/foo_repository.py`). The Protocol file
     itself lives at the feature-package root, alongside the service that
     uses it. Anything under `internal/` is package-private and must not
     be imported from outside the feature.

  3. **Factory-injected error wrapping.** Library exceptions are turned
     into the domain `RepoError` by an injected `RepoErrorFactory.from_*`
     method, not by inline `raise X from Y` at every call site. The factory
     logs once at the wrap site and captures structured fields
     (subcommand, cmd_args, cwd, stderr, exit_code) so the reporter and
     dashboard can render them without re-parsing.

The DI container binds the Write variant where mutations are required and the
Read variant where they aren't — the Protocol type is the contract.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import some_io_library  # confined to this file (and any sibling internal/ adapters)


# --- Domain types ----------------------------------------------------------

@dataclass
class Thing:
    """Domain object for whatever this repository deals with."""
    id: str
    payload: bytes


class RepoError(Exception):
    """Raised by repository methods to signal a failed operation.

    Carries structured fields (subcommand, cmd_args, cwd, exit_code, stderr)
    populated by RepoErrorFactory at the wrap site. Callers depend on this
    type — never on `some_io_library`'s exception hierarchy.
    """
    def __init__(self, message: str, *, subcommand: str = "", cmd_args: tuple[str, ...] = (),
                 cwd: Path | None = None, exit_code: int | None = None, stderr: str = ""):
        super().__init__(message)
        self.subcommand = subcommand
        self.cmd_args = cmd_args
        self.cwd = cwd
        self.exit_code = exit_code
        self.stderr = stderr


# --- Error factory (injected) ---------------------------------------------

class RepoErrorFactory:
    """The injected error-wrapping seam.

    The factory exposes one `from_<transport>(...)` method per underlying
    exception type it knows how to translate. Each method is called by a
    repository at the boundary where the library exception is caught. The
    factory logs once at the wrap site (so we never get catch-log-rethrow
    cascades) and constructs a `RepoError` with the structured fields
    populated.

    The caller passes a high-level `message` describing what failed. The
    factory extracts `subcommand`, `cmd_args`, `exit_code`, and `stderr`
    off the exception itself — callers don't repeat that extraction at
    every wrap site.

    Production winter-cli currently exposes one method, `from_git`
    (wraps `git.GitCommandError`). New transports add new methods
    following the same shape — `from_subprocess(completed, message, *, cwd)`
    for `subprocess.CompletedProcess`, `from_http(response, message, *, cwd)`
    for an HTTP client, and so on.

    Inject the concrete class directly. An I-prefix `IRepoErrorFactory`
    Protocol is only worth extracting when a second factory shape appears
    (different field schema, different log policy); until then the concrete
    is the seam, and tests substitute a fake by type.
    """
    def from_io(self, exc: Exception, message: str, *,
                cwd: Path | None = None) -> RepoError: ...


# --- Public Protocols (the seam services depend on) -----------------------

class IReadFooRepository(Protocol):
    """Read-only operations against the Foo data store."""

    def get_thing(self, thing_id: str) -> Thing: ...
    def list_things(self, prefix: str) -> list[Thing]: ...


class IWriteFooRepository(IReadFooRepository, Protocol):
    """Read-write variant. Services that mutate state depend on this."""

    def save_thing(self, thing: Thing) -> None: ...
    def delete_thing(self, thing_id: str) -> None: ...


# --- Concrete adapter (lives at modules/<feature>/internal/foo_repository.py
# in production; shown here in one file for the exemplar) -------------------

class ReadFooRepository:
    """Read-only `some_io_library` adapter. All library usage is confined here."""

    def __init__(self, error_factory: RepoErrorFactory) -> None:
        self._errors = error_factory

    def get_thing(self, thing_id: str) -> Thing:
        try:
            raw = some_io_library.fetch(thing_id)
        except some_io_library.IOError as exc:
            raise self._errors.from_io(exc, f"fetch failed for {thing_id}")
        return self._parse(thing_id, raw)

    def list_things(self, prefix: str) -> list[Thing]:
        try:
            entries = some_io_library.list(prefix)
        except some_io_library.IOError as exc:
            raise self._errors.from_io(exc, f"list failed for prefix {prefix!r}")
        return [self._parse(e.id, e.raw) for e in entries]

    @staticmethod
    def _parse(thing_id: str, raw: bytes) -> Thing:
        # Parsing is a private detail of this class — callers see only Thing.
        return Thing(id=thing_id, payload=raw)


class WriteFooRepository(ReadFooRepository):
    """Read-write adapter. Mutating operations live here; reads inherited."""

    def save_thing(self, thing: Thing) -> None:
        try:
            some_io_library.write(thing.id, thing.payload)
        except some_io_library.IOError as exc:
            raise self._errors.from_io(exc, f"save failed for {thing.id}")

    def delete_thing(self, thing_id: str) -> None:
        try:
            some_io_library.delete(thing_id)
        except some_io_library.IOError as exc:
            raise self._errors.from_io(exc, f"delete failed for {thing_id}")


# Typecheck-time Protocol/adapter conformance sentinel. Pyright rejects the
# return if WriteFooRepository drifts from IWriteFooRepository. Lives next to
# the concrete so the Protocol module doesn't import its own adapter. Because
# IWriteFooRepository extends IReadFooRepository, this single sentinel pins
# both seams. See standards/protocol-conformance.md for the full pattern.
def _conforms_write_foo_repository(x: WriteFooRepository) -> IWriteFooRepository:
    return x


# --- DI container binding (lives in container.py in production) -----------
#
# from dependency_injector import containers, providers
#
# class Container(containers.DeclarativeContainer):
#     error_factory = providers.Singleton(RepoErrorFactory)
#     foo_repo: providers.Provider[IWriteFooRepository] = providers.Singleton(
#         WriteFooRepository, error_factory=error_factory,
#     )
#
# Services that only need reads declare their dependency as `IReadFooRepository`
# — the Singleton above satisfies the supertype too, and the type system makes
# the read-only intent visible at the consumer.
