# Domain modeling

## Rule

Prefer domain models in service layers where domain logic lives. Domain-agnostic services and infrastructure can have
their own preferred call patterns — primitives are fine where there's no domain to model.

## Why

The service layer encodes business and workflow logic. Methods there speak in domain concepts: a `FeatureWorktree`, a
`ProjectRepository`, a `Workspace`. Passing primitives at that layer forces every call site to re-derive the domain
concept, scatters related state across parameter lists, and hides the abstraction the layer is supposed to be
expressing.

Infrastructure (managed-block services, generic file utilities, formatters, parsers) is domain-agnostic by design.
Forcing domain types into it creates artificial coupling and prevents reuse — a generic `ManagedBlockService` shouldn't
know what a worktree is.

## Do (service layer)

```python
def add_worktree(self, worktree: FeatureWorktree) -> None:
    # branch = worktree.environment.name
    # source = worktree.repository.main_path
    # base   = worktree.repository.main_branch
    # dest   = worktree.path
    ...
```

## Don't (service layer)

```python
def add_worktree(
    self,
    source_path: Path,
    worktree_path: Path,
    branch_name: str,
    base_branch: str,
) -> None:
    ...
```

## Do (infrastructure)

```python
class ManagedBlockService:
    def upsert(self, content: str, name: str, body_lines: list[str]) -> str:
        ...
```

The service has no business knowing about `FeatureWorktree` or `Workspace`. Primitives are honest here — it's text
manipulation, not domain workflow.

## Parameters outside the domain

Even in service-layer methods, not every parameter is a domain object. Some are *targets*, *outputs*, or *concepts that
haven't been modeled yet*. Those stay as primitives.

Example: `WriteRepoRepository.clone(repo: IWorkspaceRepository, dest: Path)`. The repo is a domain entity (we model it).
The destination path is not a domain concept — it's just where the bits should land. We don't model "clone targets"
because we don't need the abstraction yet. If we wanted to clone to disk *or* over SSH *or* to S3, we'd introduce a
`CloneTarget` domain object and pass that. Absent that need, `Path` is honest.

The heuristic: ask "is this thing modeled in the domain?" If yes, pass the model. If no, pass whatever primitive shape
fits the operation. Don't invent domain types preemptively for things you haven't decided to abstract over.

## Asymmetry note

Some domain types have one of a kind (`StandaloneRepository.path`), others have many (`ProjectRepository.main_path` plus
per-worktree paths). Name fields to reflect the multiplicity. `main_path` signals "there are siblings"; `path` signals
"this is the only one." Don't flatten siblings into single-name fields for false symmetry.
