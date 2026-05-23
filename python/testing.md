# Testing

## Rule

- **`pytest` only.** No `unittest.TestCase`, no `nose`. Tests live under `tests/`.
- **Test paths mirror source paths.** `src/winter_cli/modules/workspace/init_service.py` is exercised by `tests/modules/workspace/test_init_service.py`.
- **Prefer hand-rolled fakes against the I-prefix Protocol seams** (see `python/repository-pattern.md`). Reach for `unittest.mock.MagicMock` only at the orchestration edge.
- **Assertions match the layer**: services assert against event vocabularies on injected reporters; handlers assert exit codes and rendered output; adapters assert real I/O effects.
- Run `pytest` (typically `mise run test`) before pushing, alongside `mise run lint` and `mise run typecheck`.

## Why

The delivery flow is "rebase onto `origin/master` and push" (see `workspace:/ai/project/contributing.md`). There is no PR/MR review and no CI gate yet, so a regression that compiles and type-checks still lands silently unless the test suite catches it locally.

Hand-rolled fakes against Protocols (rather than `MagicMock` against concrete classes) keep the test surface aligned with the dependency-inversion seams already established by `python/dependency-injection.md` and `python/repository-pattern.md`. The test stays valid as long as the Protocol contract holds; refactors inside an adapter don't ripple into the suite.

## Directory layout

```
tests/
  conftest.py                       # shared fixtures + cross-feature fakes
  test_container.py                 # DI graph smoke tests
  modules/
    workspace/
      test_init_service.py          # service-level: fakes injected for every Protocol
      test_workspace_handler.py     # handler-level: MagicMock services, capsys for output
      internal/
        test_git_ops_service.py     # adapter-level: real adapter against real I/O or tight fakes
        test_write_repo_repository.py
  core/
    internal/
      test_click_cli_output_service.py
```

The tree mirrors `src/winter_cli/`. When you add `src/winter_cli/modules/foo/bar_service.py`, the test file is `tests/modules/foo/test_bar_service.py`. Adapters in `internal/` map to `tests/.../internal/test_<adapter>.py`.

## Conftest scoping

Three conftest tiers, picked by reach:

1. **`tests/conftest.py`** — fixtures and fakes used by two or more sibling subtrees (e.g. `FakeFilesystem`, `FakeSubprocessRunner`, `FakeGitRepository`, `tmp_workspace_root`).
2. **`tests/<feature>/conftest.py`** — fixtures scoped to one feature subtree. Add when a fake is feature-local but used by more than one test file inside it.
3. **Inline `@pytest.fixture` in the test file** — first use. Lift to a `conftest.py` the moment a second file needs it; don't copy.

Default fixture scope is `function`. Promote to `session` only for genuinely immutable, expensive setup (rare). Per-test isolation beats shaving milliseconds.

## Hand-rolled fakes vs `Mock`

| Use a hand-rolled fake when | Use `MagicMock` when |
|---|---|
| The collaborator is one of your `I`-prefix Protocols (a repository, a reporter, a subprocess runner). | The collaborator is a thick service whose contract you don't want to re-implement (e.g. a `WorkspaceService` stubbed inside a handler test). |
| Tests need to assert against captured state (`fake.clones == [...]`, `reporter.actions`). | Tests only need to observe that a method was called, or return a canned value. |
| The Protocol has multiple methods with intertwined state (filesystem, git repo). | The seam is one or two methods and stubbing is shorter than a class. |

Hand-rolled fakes live next to the tests that need them — typically in `tests/conftest.py` (see `FakeFilesystem`, `FakeSubprocessRunner`, `FakeGitRepository`, `FakeInitReporter` in winter-cli). They expose public lists/dicts so tests assert against captured calls directly, without `mock.call(...)` ceremony.

`pyfakefs`, `responses`, and similar third-party fakes are fine for adapter-level tests where re-implementing the seam would be a bigger lift than the test, but a small explicit fake usually reads better and pins behavior gaps explicitly.

## Worked example: injected fake against `IFooRepository`

Given a service that depends on the Protocol from `exemplars/python/repo_pattern.py`:

```python
class FooService:
    def __init__(self, foo_repo: IWriteFooRepository) -> None:
        self._foo_repo = foo_repo

    def rename(self, thing_id: str, new_payload: bytes) -> None:
        thing = self._foo_repo.get_thing(thing_id)
        self._foo_repo.save_thing(Thing(id=thing.id, payload=new_payload))
```

The test injects a fake satisfying `IWriteFooRepository` — no `MagicMock`, no patching:

```python
class FakeFooRepository:
    """In-memory IWriteFooRepository — records saves, returns canned reads."""

    def __init__(self, things: dict[str, Thing] | None = None) -> None:
        self.things: dict[str, Thing] = dict(things or {})
        self.saved: list[Thing] = []

    def get_thing(self, thing_id: str) -> Thing:
        return self.things[thing_id]

    def list_things(self, prefix: str) -> list[Thing]:
        return [t for tid, t in self.things.items() if tid.startswith(prefix)]

    def save_thing(self, thing: Thing) -> None:
        self.saved.append(thing)
        self.things[thing.id] = thing

    def delete_thing(self, thing_id: str) -> None:
        del self.things[thing_id]


def test_rename_writes_new_payload() -> None:
    repo = FakeFooRepository(things={"t1": Thing(id="t1", payload=b"old")})
    svc = FooService(foo_repo=repo)

    svc.rename("t1", b"new")

    assert repo.saved == [Thing(id="t1", payload=b"new")]
```

The fake satisfies the Protocol structurally — pyright/mypy will reject a divergent signature, and the test asserts against the captured `saved` list rather than `mock.call(...)` chains. When the same fake is needed in a second test file, lift it to `tests/<feature>/conftest.py`.

## Assertion patterns by layer

- **Services** — assert against the **event vocabulary** captured by injected reporter fakes and against repository call logs. Example: `assert ("demo", path, "cloned", "") in init_reporter.actions` and `assert git.clones == [(url, dest)]`. Don't assert on stdout — services don't print.
- **Handlers** — assert **exit codes** (`pytest.raises(SystemExit)`) and **rendered output** via `capsys`. Stub the underlying services with `MagicMock` since the handler's contract is "translate CLI args ↔ service calls ↔ output."
- **Adapters (`internal/`)** — assert real I/O effects against `tmp_path` or a real `git.Repo`. Helpers like `make_git_repo(path)` in `tests/conftest.py` provide a bootstrapped repo so each adapter test doesn't reinvent init + identity + commit.
- **Container / DI** — `tests/test_container.py` resolves every provider to catch wiring regressions. One smoke test per Singleton is enough.

## Naming

- **Test files**: `test_<unit_under_test>.py`. One file per source module.
- **Test functions**: `test_<scenario>_<expected_outcome>` — read like a sentence. `test_reconcile_projects_clones_missing_repo`, `test_fetch_failed_with_empty_results_exits_nonzero_in_text_mode`.
- **Fakes**: `Fake<Protocol-without-the-I-prefix>` — `FakeFilesystem`, `FakeGitRepository`, `FakeInitReporter`. The class docstring restates the Protocol it satisfies.
- **Builder helpers**: `make_<thing>(...)` for low-ceremony constructors (`make_git_repo`), reserved for one-call setup. Prefer fixtures for anything shared across tests.

## See also

- `python/dependency-injection.md` — why services receive Protocols, not concretes.
- `python/repository-pattern.md` — the I-prefix Protocol seam that makes fakes cheap to write.
- `exemplars/python/repo_pattern.py` — canonical `IReadFooRepository` / `IWriteFooRepository` shape.
- `exemplars/python/cli-architecture.md` — testing-pattern section, including the "lift to conftest" rule.
- `winter/tools/winter-cli/tests/` — the working reference for all patterns above. Start at `tests/conftest.py` and `tests/modules/workspace/test_init_service.py`.
