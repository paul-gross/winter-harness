# Progressive disclosure

How agent-facing docs are structured so an agent finds the one fact it needs without loading the rest. The structural complement to [`./principles.md`](./principles.md) §"Point, don't duplicate": that rule governs how one doc references another; this one governs how a topic is split across files so those references have well-shaped targets to point at.

Each rule follows a `Rule` / `Why` / `Do` / `Don't` shape.

## Hub-and-spoke split

**Rule.** When a topic outgrows a screenful or spans distinct sub-topics, split it into a hub `index.md` that carries a routing table plus one file per sub-topic. The hub holds only what every reader of the topic needs — the one-line framing and the router; each spoke holds one sub-topic's detail. References from elsewhere point at the hub, not at a monolith and not at a deep leaf, so the reader enters at the router and descends only the one branch they need. When a single spoke itself outgrows a screenful or spans sub-topics, it becomes a hub in turn (a sub-directory with its own `index.md`), and the chain deepens by one.

**Why.** A monolith forces every agent to load the whole topic to reach any part of it, paying token rent on every fact for the sake of one. A flat pile of sibling files with no hub forces the agent to guess which file holds the fact, and a reference straight to a deep leaf hides the sibling branches the agent might actually need. The hub-and-spoke shape lets an agent read one short router, see every branch at once, and descend exactly one — discovery cost stays bounded as the topic grows.

**Do.**

- A command reference where each command has its own file: a hub `index.md` with a routing row per command, and `init.md`, `destroy.md`, `status.md` beside it. A command group with many sub-commands earns its own sub-directory with its own hub.
- A convention area: a hub `index.md` whose rows route to one convention file each, and which itself names its parent layer for the reader climbing back up.

**Don't.**

- A single file that grows section after section until an agent must load all of it to answer one question — split it once it crosses a screenful or starts spanning sub-topics.
- A reference that points past the hub straight at a leaf, so the reader never sees the router and the sibling branches stay invisible.

## An index row is a router, not a contents list

**Rule.** Every row of a hub `index.md` states **when to read** the target — the trigger or condition that sends the reader there — and links to it. A row never describes **what is inside** the target. The "when to read" framing is a router that survives every edit to the target; a contents description is a second copy of the target that drifts the moment the target changes (the [`./principles.md`](./principles.md) §"Point, don't duplicate" rule, applied to the row shape).

**Why.** An agent traversing a hub is deciding *which branch to descend*, and that decision is a match against its current need — "I am about to do X, which file covers X." A read-trigger row answers exactly that question and stays answerable no matter how the target's contents shift. A contents-summary row answers a different question ("what does this file contain") that the agent does not yet have, asserts a list that the target now owns in two places, and reads as complete — so the next author trusts the stale summary instead of the target.

**Do.**

```
| ./principles.md | Cross-cutting principles for any agent-facing markdown file — read before authoring or editing one |
```

The row names the condition under which the reader descends — a trigger, not an inventory.

**Don't.**

```
| ./principles.md | The no-retrospective-framing, no-line-wrapping, and point-don't-duplicate rules |
```

The row inventories the target's contents; it must be re-synced by hand every time a principle is added or renamed, and it is wrong the first time the target changes.

## Tables for a set of options

**Rule.** Present a set of parallel choices — files to route to, commands to pick among, modes to compare — as a table, not as sequential prose. One column carries the choice (the link, the command, the option), the next carries the discriminator that tells the reader which one is theirs.

**Why.** A table lets an agent scan one column for the row that matches its need and stop, reading one row instead of the whole block. Sequential prose forces a linear read of every option to find the relevant one, and buries the discriminator that distinguishes them inside sentences. The table makes the parallelism structural, so the reader sees the full option set at a glance and the discriminator sits where it can be compared across rows.

**Do.** A routing table whose rows are `| destination | when to read |`, or a command table whose rows are `| command | usage | purpose |` — the reader scans the discriminator column and descends one row.

**Don't.** A paragraph that names each option in turn — "For X, read A. For Y, read B. For Z, read C." — which the reader must consume whole to find their case.

## Indexes warrant more scrutiny than leaves

**Rule.** A hub `index.md` is held to a higher bar than the files it routes to. Every agent working anywhere downstream of a hub traverses it first, so a wrong or vague routing row is a fault multiplied by every reader who needed a branch it failed to point at. Review an index row for whether its read-trigger is precise enough that the right agent descends and the wrong one does not.

**Why.** A leaf file is read by the agents that already chose to descend to it; a mistake there costs those readers. A hub is read by every agent traversing the topic; a mistake there — a missing row, a trigger so vague that no one matches it, a row that points at the wrong target — silently blocks discovery of everything beyond it, and the blocked agent has no signal that the fact it needed exists at all. The blast radius of an index defect is the entire sub-tree it gates, which is why the index earns the closer read.

**Do.** When adding a spoke, add its routing row to the hub in the same change, and check that the trigger is specific enough to be matched — and to be *not* matched by agents whose need is a sibling branch.

**Don't.** Add a file under a hub without a routing row — an unrouted file is undiscoverable; the hub is the only path to it.

**See also.** [`./principles.md`](./principles.md) §"Point, don't duplicate" — the reference-shape rule this article's structure exists to serve.
