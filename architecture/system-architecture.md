# System architecture: contracts over swappable backends

Winter's **system architecture** is built from swappable backends behind winter-owned contracts — a service orchestrator, a git provider, a config source. Winter defines what callers can ask for; each backend realizes that on its own terms. This is a *system-design* concern — how winter's command surface relates to the extensions plugged in behind it — distinct from the in-process service shape in [`./service-architecture.md`](./service-architecture.md) (injected classes, Protocol seams, free functions), which governs how a single codebase's behavior is wired. Read this when designing or reviewing the boundary between winter and a pluggable backend; read that when designing the code on either side of it.

## Core tenet: interchangeability

**Adapters behind a Protocol seam are interchangeable, and the seam keeps them that way.** Any code that drives a swappable backend — a service orchestrator, a git provider, a config source — depends on a **winter-defined, stable contract**: a fixed, documented set of operations and options that *winter* owns, not the backend. Swapping the adapter behind the seam must not change what callers can ask for. This is the *why* behind the protocol-seam pattern the code conventions describe: the seam exists so the thing behind it can be replaced.

**Define the contract; never pass arguments through.** A command surface over a swappable backend exposes exactly the options winter defines and maps them onto whatever adapter is plugged in. It does not forward arbitrary caller arguments down to the backend. Pass-through couples every caller to one backend's flag vocabulary — the moment a caller passes a backend-specific flag, swapping the backend breaks them, and the seam stops being a seam. The contract does exactly what winter defines, and each adapter is responsible for realizing that contract on its own terms.

- **Do.** `winter service up <env>` exposes winter's fixed action set (`up` / `down` / `status` / `restart` / `logs`); each orchestrator adapter implements those actions. A different orchestrator slots in without changing the command surface.
- **Don't.** A `winter service <action> <env> -- <raw backend args>` pass-through that forwards tmux-specific flags to the tmux adapter — callers that learned the tmux flags can't move to another orchestrator, so the orchestrators are no longer interchangeable.

This contract is dependency inversion at the system scale: callers depend on winter's operation set (the Protocol), never on a concrete backend's argument surface. See `./dependency-injection.md` for how the chosen adapter is wired in process and `../standards/protocol-conformance.md` for pinning each adapter to the seam it must satisfy.

## See also

- `./service-architecture.md` — the in-process service shape the seam is built from: behavior in injected classes, Protocol seams, free functions for pure helpers only.
- `./dependency-injection.md` — how the chosen adapter is wired into the container.
- `../standards/protocol-conformance.md` — pinning each adapter to the seam it must satisfy.
