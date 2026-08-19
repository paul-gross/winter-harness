# References to winter things

How to write references to files, agents, skills, and slash commands across the winter ecosystem. The point is
portability — every reference should resolve the same way regardless of which workspace consumes the documentation.

## Path notation

Refer to files in other repos or contexts using a `<context>:<path>` prefix. The context determines how the path
resolves on disk.

| Prefix               | Resolves to                                                              | Example                                          |
| -------------------- | ------------------------------------------------------------------------ | ------------------------------------------------ |
| `workspace:`         | The current workspace root                                               | `workspace:/CLAUDE.md`                           |
| `<env>:`             | A feature environment under the workspace (Greek-letter or feature name) | `alpha:/winter/tools/winter-cli/`                |
| `<extension-name>:`  | An installed winter extension                                            | `winter-harness:/architecture/error-handling.md` |
| `<standalone-name>:` | A standalone repository cloned in the workspace                          | `my-app:/context/architecture.md`                |

Notes:

- Extension and standalone notations resolve via the consuming workspace's `AGENTS.winter.md` block — the on-disk path
  varies (e.g. `.winter/ext/<name>/` for adopted extensions, `<name>/` for top-level clones). Authors do not encode the
  on-disk path.
- Do not write absolute paths or sibling-relative paths (`../winter-product/...`) when crossing a repo or context
  boundary. Always use a prefix so the reference survives directory and adoption changes. <!-- winter-lint:example -->
- A repo's own files may be referred to with bare relative paths (`./architecture/error-handling.md` from inside
  `winter-harness/index.md`). The prefix is only required when *crossing* a context. <!-- winter-lint:example -->

## Names for agents, skills, and slash commands

When an extension installs an agent, skill, or slash command into a workspace, the install symlinks add a
**workspace-configurable prefix** at the seam (commonly `wf-`, `wp-`, `wc-` — set per workspace in
`.winter/config.toml`). The prefix is not part of the canonical name and is not guaranteed across deployments — a
different workspace may set a different prefix or none at all.

**Rule:** in extension documentation, refer to agents, skills, and slash commands by their **canonical, unprefixed name
— with no leading slash**. A slash form reads as a typeable command, and the typeable command always carries the
workspace prefix: `/commit` is not invocable in any workspace, so writing it helps no one. Write "the `commit` skill"
and let the reader (or the executing agent, via its installed-skills list) resolve the locally installed name. The slash
belongs only where the literal typed command is known — workspace-level docs and README typing examples (see below) —
and to unprefixed workspace-core skills (e.g. `/ws-push`), whose typed form is their canonical name. Examples:

| Kind            | Canonical name                                                        | Common installed/typed name                 |
| --------------- | --------------------------------------------------------------------- | ------------------------------------------- |
| Agent           | `ice-carver`, `winter-architect`, `cold-reviewer`, `harness-reviewer` | `wf-ice-carver`, `wf-winter-architect`, ... |
| Agent           | `product-specialist`                                                  | `wp-product-specialist`                     |
| Skill / command | `glacier`, `snowball`, `commit`, `cold-review`, `harness-review`      | `/wf-glacier`, `/wf-snowball`, ...          |
| Skill / command | `refine`, `todo`                                                      | `/wp-refine`, `/wp-todo`                    |
| Skill / command | `issue`                                                               | `/wg-issue`                                 |

### What this rule does NOT cover

- **Workspace-level documentation** — the consuming workspace's own `CLAUDE.md`, READMEs, and quick-starts may name the
  installed prefix because that is what the user actually types in *that* workspace. This convention only binds
  extension-internal docs, where the prefix isn't knowable at authoring time.
- **Installation snippets** in an extension's own README may show the default prefix as a typing example, but should
  make clear the prefix is workspace-configurable.

### For reviewers

Do not flag unprefixed agent / skill / slash-command names in extension documentation as an inconsistency with the
workspace's installed names. The mismatch is intentional: extension docs are authored portably while the workspace is
configured locally. Confirm against this convention before raising a finding.
