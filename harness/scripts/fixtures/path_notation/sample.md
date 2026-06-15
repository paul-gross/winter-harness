# Path-notation fixture

Deliberate violations for `lint_path_notation.py` to detect. Pruned from any
default repo scan (it lives under `fixtures/`); the test targets it explicitly.

## Should be flagged (raw cross-context paths in code spans)

- An extension-install path: `.winter/ext/codeberg/ai/issue-format.md`
- A source-checkout path: `projects/winter-cli/README.md`
- A sibling-relative path: `../winter-product/ai/todos.md`
- A bare repo-name path: `winter-service-tmux/index.md`
- A machine-absolute path: `/home/alice/notes.md`

## Should NOT be flagged

- Intra-repo relative: `./architecture/error-handling.md`
- Intra-repo relative: `tools/winter-cli/pyproject.toml`
- Canonical notation: `workspace:/CLAUDE.md`
- Canonical notation: `winter-harness:/harness/index.md`
- Marked as illustration: `.winter/ext/foo/bar.md` <!-- winter-lint:example -->

A fenced block holds sample commands, so its raw paths are correct:

```bash
cd projects/winter-cli && cat .winter/ext/foo/config.toml
```
