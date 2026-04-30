"""Canonical repository-pattern example.

Read this when adding a new repository class or extending an existing one.
The shape is:

  ReadFooRepository    # read-only operations, owns library imports
  WriteFooRepository   # extends Read, adds mutating operations

Coordinators inject the Write variant when they need both reads and writes;
inject Read where mutations are out of scope (the type documents the contract).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import some_io_library  # confined to this file


@dataclass
class Thing:
    """Domain object for whatever this repository deals with."""
    id: str
    payload: bytes


class FooError(Exception):
    """Raised by FooRepository methods to signal a failed operation.

    Wraps `some_io_library`'s exceptions so callers don't depend on the lib.
    """


class ReadFooRepository:
    """Read-only `some_io_library` implementation. All library usage is confined here."""

    def get_thing(self, thing_id: str) -> Thing:
        """Fetch a Thing by id. Raises FooError if not found or on I/O failure."""
        try:
            raw = some_io_library.fetch(thing_id)
        except some_io_library.NotFoundError as exc:
            raise FooError(f"thing {thing_id!r} not found") from exc
        except some_io_library.IOError as exc:
            raise FooError(f"fetch {thing_id!r} failed — {exc}") from exc
        return self._parse(thing_id, raw)

    def list_things(self, prefix: str) -> list[Thing]:
        """List all Things with ids starting with `prefix`."""
        try:
            entries = some_io_library.list(prefix)
        except some_io_library.IOError as exc:
            raise FooError(f"list {prefix!r} failed — {exc}") from exc
        return [self._parse(e.id, e.raw) for e in entries]

    @staticmethod
    def _parse(thing_id: str, raw: bytes) -> Thing:
        # Parsing is a private detail of this class — callers see only Thing.
        return Thing(id=thing_id, payload=raw)


class WriteFooRepository(ReadFooRepository):
    """Read-write variant. Mutating operations live here; reads inherited from Read."""

    def save_thing(self, thing: Thing) -> None:
        """Persist a Thing. Raises FooError on I/O failure."""
        try:
            some_io_library.write(thing.id, thing.payload)
        except some_io_library.IOError as exc:
            raise FooError(f"save {thing.id!r} failed — {exc}") from exc

    def delete_thing(self, thing_id: str) -> None:
        """Remove a Thing by id. Raises FooError if it doesn't exist."""
        try:
            some_io_library.delete(thing_id)
        except some_io_library.NotFoundError as exc:
            raise FooError(f"thing {thing_id!r} not found") from exc
        except some_io_library.IOError as exc:
            raise FooError(f"delete {thing_id!r} failed — {exc}") from exc
