# Testing

## Rule

- **`pytest` only.** No `unittest.TestCase`, no `nose`. Tests live under `tests/`.
- **Test paths mirror source paths.** `src/winter_cli/modules/workspace/init_service.py` is exercised by `tests/modules/workspace/test_init_service.py`.
- **Prefer hand-rolled fakes against the I-prefix Protocol seams** (see `../architecture/repository-pattern.md`). Reach for `unittest.mock.MagicMock` only at the orchestration edge.
- **Assertions match the layer**: services assert against event vocabularies on injected reporters; handlers assert exit codes and rendered output; adapters assert real I/O effects.
- Run `pytest` (typically `mise run test`) before pushing, alongside `mise run lint` and `mise run typecheck`.

## Why

The delivery flow is "rebase onto `origin/master` and push" (see `workspace:/ai/project/contributing.md`). There is no PR/MR review and no CI gate yet, so a regression that compiles and type-checks still lands silently unless the test suite catches it locally.

Hand-rolled fakes against Protocols (rather than `MagicMock` against concrete classes) keep the test surface aligned with the dependency-inversion seams already established by `../architecture/dependency-injection.md` and `../architecture/repository-pattern.md`. The test stays valid as long as the Protocol contract holds; refactors inside an adapter don't ripple into the suite.

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
- **Adapters (`internal/`)** — mock the underlying library at the adapter's import site (`monkeypatch.setattr(<adapter_module>, "<lib>", MagicMock())`); assert both the library-call shape and the adapter's return value. See `../architecture/repository-pattern.md` for the full rule.
  - **When an adapter's correctness lives in parsing an external tool's output** (e.g. `git status --porcelain`, a CLI's `--json`), back the import-site mocks with a few **real-I/O tests** that run the actual tool against a temp fixture — mocks encode the format you *expect* and keep passing when the real output drifts, so the real tests are what catch it. Extracting the parse into a pure function (string in, dataclass out) also makes it unit-testable over captured fixtures without a process. Reference: `read_repo_repository.py` (`_parse_*` functions + `test_real_*` git-against-`tmp_path` cases).
- **Container / DI** — `tests/test_container.py` resolves every provider to catch wiring regressions. One smoke test per Singleton is enough.

## Naming

- **Test files**: `test_<unit_under_test>.py`. One file per source module.
- **Test functions**: `test_<scenario>_<expected_outcome>` — read like a sentence. `test_reconcile_projects_clones_missing_repo`, `test_fetch_failed_with_empty_results_exits_nonzero_in_text_mode`.
- **Fakes**: `Fake<Protocol-without-the-I-prefix>` — `FakeFilesystem`, `FakeGitRepository`, `FakeInitReporter`. The class docstring restates the Protocol it satisfies.
- **Builder helpers**: `make_<thing>(...)` for low-ceremony constructors, reserved for one-call setup. Prefer fixtures for anything shared across tests.

## Convention tests

Some Python conventions describe AST-level patterns that `ruff`, `pyright`, and `import-linter` can't reach — Protocol naming (`I`-prefix), the no-whole-Config-injection rule, the no-catch-log-rethrow pattern, the service-based-behavior rule. Code review and the `code-reviewer` agent catch them probabilistically; promoting each rule to a small pytest file under `tests/conventions/` makes the check deterministic and runs it alongside the rest of `mise run test`.

### Layout

```
tests/conventions/
  conftest.py                     # shared walk_src() helper + collect_ignore
  test_protocol_naming.py         # one rule per file
  test_no_whole_config_injection.py
  test_no_catch_log_rethrow.py
  test_service_based_behavior.py
  fixtures/                       # excluded from collection
    violating_protocol_naming.py  # deliberately violates the rule
    violating_no_whole_config_injection.py
    violating_no_catch_log_rethrow.py
    violating_service_based_behavior.py
```

`conftest.py` exposes `walk_src() -> Iterator[(Path, ast.Module)]` that every rule file iterates, plus a module-level `collect_ignore = ["fixtures"]` so the deliberate violations don't surface as suite failures.

### Shape of a rule file

Each rule file factors detection into a pure function — `find_<rule>_violations(file_path, tree) -> list[str]` — and uses it twice:

1. A top-level test that walks `src/` and `pytest.fail`s with the joined violation list. Each violation cites file:line and the convention doc.
2. A regression test that parses the matching `fixtures/violating_<rule>.py` and asserts the function returns at least one violation. This keeps the lint honest — if a refactor silently disables detection, the fixture test fails.

Failure messages follow the pattern `f"{file}:{line}: <rule restatement> ({winter-harness:/architecture/<conv>.md})"` so the offending line and the convention citation are both inline.

### Carve-outs

The literal convention may permit narrow exceptions (e.g. `../architecture/dependency-injection.md` allows whole-`WorkspaceConfig` injection in translation services and workspace-lifecycle services). Encode those as an explicit `ALLOWED_FILES = frozenset({...})` at the top of the rule file, with each entry paired to the carve-out paragraph in the convention doc. New code that re-introduces the pattern outside the allowlist fails the test loudly. Mirror the existence of the test in the convention doc itself — add a short "Enforcement" pointer at the end of the convention so an agent reading the rule knows the gate exists.

### Adding a fourth rule

The shortest path is to copy `test_protocol_naming.py` and adapt it. The contract is:

1. Add `tests/conventions/test_<rule>.py`. Factor detection into a pure function with the signature `find_<rule>_violations(file_path: Path, tree: ast.Module) -> list[str]` — the existing `walk_src()` iteration depends on this exact shape.
2. Use the function twice in the same file: once in the src-wide test that fails with the joined violation list, once in a regression test that parses `fixtures/violating_<rule>.py` and asserts the returned list is non-empty.
3. Add `tests/conventions/fixtures/violating_<rule>.py` — deliberately violates the rule, syntactically valid (it gets `ast.parse`d by the regression test). The conftest's `collect_ignore` already excludes everything under `fixtures/`; no further wiring needed.
4. Cite the convention doc in the failure message, following the template above, and in the rule-file docstring.
5. Add an "Enforcement" pointer to the convention doc itself so the rule and its gate cross-link both ways.

## See also

- `../architecture/dependency-injection.md` — why services receive Protocols, not concretes.
- `../architecture/repository-pattern.md` — the I-prefix Protocol seam that makes fakes cheap to write.
- `exemplars/python/repo_pattern.py` — canonical `IReadFooRepository` / `IWriteFooRepository` shape.
- `architecture/winter-cli.md` — testing-pattern section, including the "lift to conftest" rule.
- `winter/tools/winter-cli/tests/` — the working reference for all patterns above. Start at `tests/conftest.py` and `tests/modules/workspace/test_init_service.py`.
