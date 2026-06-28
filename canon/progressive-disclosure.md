# Progressive disclosure

How agent-facing docs are structured so an agent finds the one fact it needs without loading the rest. The structural complement to [`./principles.md`](./principles.md) §"Point, don't duplicate": that rule governs how one doc references another; this one governs how a topic is split across files so those references have well-shaped targets to point at.

Each rule follows a `Rule` / `Why` / `Do` / `Don't` shape.

## Hub-and-spoke split

**Rule.** When a reader seeking one fact in a topic would have to load substantial unrelated material to reach it, or the topic spans distinct sub-topics, split it into a hub `index.md` that carries a routing table plus one file per sub-topic — the threshold is semantic load, not length (§"Split by semantic load, not word count"). The hub holds only what every reader of the topic needs — the one-line framing and the router; each spoke holds one sub-topic's detail. General navigation into the topic enters at the hub, so the reader sees the sibling branches and descends only the one they need; a reference straight to a deep leaf is reserved for when the referring sentence needs one already-known fact and discovery is not the reader's task (§"Intermediate hubs for discovery, deep links for exact facts"). When a single spoke itself grows into distinct sub-topics, it becomes a hub in turn (a sub-directory with its own `index.md`), and the chain deepens by one.

**Why.** A monolith forces every agent to load the whole topic to reach any part of it, paying token rent on every fact for the sake of one. A flat pile of sibling files with no hub forces the agent to guess which file holds the fact, and a reference straight to a deep leaf hides the sibling branches the agent might actually need. The hub-and-spoke shape lets an agent read one short router, see every branch at once, and descend exactly one — discovery cost stays bounded as the topic grows.

**Do.**

- A command reference where each command has its own file: a hub `index.md` with a routing row per command, and `init.md`, `destroy.md`, `status.md` beside it. A command group with many sub-commands earns its own sub-directory with its own hub.
- A convention area: a hub `index.md` whose rows route to one convention file each, and which itself names its parent domain for the reader climbing back up.

**Don't.**

- A single file that grows section after section until an agent must load all of it to answer one question — split it once a reader seeking one fact must wade through unrelated material, or it starts spanning sub-topics.
- A *discovery* reference that points past the hub straight at a leaf, so the reader never sees the router and the sibling branches stay invisible. (A reference that already knows its exact target is a different case — §"Intermediate hubs for discovery, deep links for exact facts".)

## Split by semantic load, not word count

**Rule.** No numeric length threshold decides structure — not a line count, not a "screenful." A document becomes a hub with routed spokes when a reader after one fact must load substantial unrelated material to reach it, when its routing description needs several independent clauses to cover what it holds, or when its sections can be entered independently without reading the rest. The converse holds too: a long but cohesive contract a reader consumes as a whole stays one file, and a short file mixing unrelated purposes still splits. Size is a symptom, not the test.

**Why.** Length proxies for load but does not equal it. Cut a long cohesive contract at an arbitrary line count and you sever a single thread the reader follows end to end, forcing a hub-hop through the middle of one idea; leave a short mixed-purpose file whole and a reader after one of its purposes loads the others. Measuring load directly — does reaching one fact cost unrelated reading? — splits exactly the files that tax a reader and leaves the rest alone.

**Do.** Ask what a reader seeking one fact must load to reach it. If the answer is "much they don't need," split; if "only the surrounding thread of the same idea," leave it whole.

**Don't.** Split, or refuse to split, on a line count. "Over N lines" is not a reason to break a file, and "under N lines" is not a reason to keep a mixed-purpose one whole.

## One leaf, one coherent question

**Rule.** A leaf document answers one coherent question: it has one expressible read-trigger, serves one audience, and sits at one level of abstraction. When a leaf's major sections require different read-triggers, switch between audiences (operator vs. implementer), or combine reference, tutorial, migration, and design rationale that a reader could enter independently, it is serving several questions — split it, sending each part to the file that owns its question, or turn the leaf into a hub routing to them.

**Why.** A reader arrives at a leaf with one need and the trigger that matched it. A leaf that also answers three other needs makes that reader carry the other three to reach theirs, and forces the hub's single routing row to promise four things at once — so the row either misleads three readers or swells into a paragraph. One question per leaf keeps the trigger precise and the row a single clause.

**Do.** A command-usage page for the operator running the command; the wire contract for the implementer building against it; the schema for the author configuring it — three triggers, three audiences, three files, each routed from the hub.

**Don't.** One page that opens with operator invocation, pivots to the provider wire protocol, and closes with a migration narrative — three readers, three triggers, bundled so each loads the other two.

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

## Keep hubs pure

**Rule.** A hub `index.md` contains only what every downstream reader needs — the framing required to enter the topic, the navigation back to its parent, and the routing table. It does not carry schemas, procedures, examples, abbreviated reference material, or inventories copied from its children. When a hub starts to hold such detail, that detail belongs in a leaf and the hub points to it. (The routing rows themselves obey §"An index row is a router, not a contents list"; this rule governs everything *between* the rows.)

**Why.** Every agent working anywhere downstream of a hub loads it first, so detail parked in the hub is detail every one of those readers pays for whether or not their branch needs it — and a copy that drifts from the leaf that owns it. A hub holding only framing and routing stays cheap to traverse and has nothing to keep in sync.

**Do.** A hub whose body is a one-line framing, a parent pointer, and a routing table — every fact one click down.

**Don't.** A hub that reproduces a child's schema table or option list "so the reader doesn't have to click" — the schema now lives in two places and every traverser loads it.

## Intermediate hubs for discovery, deep links for exact facts

**Rule.** When the reader's task is *discovery* — finding which file covers a topic — route them through the nearest relevant hub so the sibling branches stay visible and they pick the right one. When the referring sentence instead needs *one already-known fact* — a specific heading, a single field, a named rule — link straight to that leaf or anchor; discovery is not the reader's task and a forced hop through the hub only adds a click. Neither is the universal default: match the link to what the reader is doing.

**Why.** A discovery reference dropped straight onto a deep leaf hides the siblings the reader might actually have needed — they never see the router, so they cannot tell they took the wrong branch. But routing an exact, already-resolved cross-reference through a hub spends a navigation step to show the reader choices they already moved past. The two failure modes are opposite; the fix is to ask whether the reader is still choosing.

**Do.**

- Discovery: *"For the command surface, see the usage hub"* linking to `usage/index.md` — the reader still chooses which command from the router.
- Exact fact: *"…the probe output contract"* linking straight to `configuration/doctor.md#probe-output-contract` — the reader already knows the one fact the sentence needs.

**Don't.**

- Send a reader who is still deciding which sub-topic they need straight to one leaf, bypassing the hub that shows the alternatives.
- Force a sentence that names one exact fact through a hub it does not need, just to honor "always enter at the hub".

**For reviewers.** Flag an accidental hub *bypass* during discovery — but do not force an exact cross-reference through an unnecessary navigation step.

## Tables for a set of options

**Rule.** Present a set of parallel choices — files to route to, commands to pick among, modes to compare — as a table, not as sequential prose, and put the **choice column first**. The leftmost column carries the thing the reader is selecting (the link/destination, the command, the option); the column(s) to its right carry the discriminator that tells the reader which row is theirs. When the choice is a file reference — a routing table — those links form a single scannable left edge the eye runs straight down.

**Why.** A table lets an agent scan one column for the row that matches its need and stop, reading one row instead of the whole block. Sequential prose forces a linear read of every option to find the relevant one, and buries the discriminator that distinguishes them inside sentences. Leading with the choice column is what makes that scan fast: the destinations line up on the left edge, so the reader runs down one column to find their row. Lead with the discriminator instead and the links scatter into a ragged right column the reader has to hunt across, one row at a time — the linear read the table was meant to replace.

**Do.** A routing table whose rows are `| destination | when to read |` (the file link first), or a command table whose rows are `| command | usage | purpose |` — the choice on the left, the reader scanning the discriminator column to its right and descending one row.

**Don't.** Invert the columns — `| when to read | destination |` — stranding the links on the right where they no longer line up. And don't fall back to a paragraph that names each option in turn ("For X, read A. For Y, read B. For Z, read C."), which the reader must consume whole to find their case.

**Scope.** This binds tables that exist **to route** — a choice per row, the row's point being "pick this / go here." It does not bind a table that merely *contains* a link incidentally — a feature matrix, a comparison, a schema table — where the link is one attribute among several and no column is "the choice." When unsure, ask what the table is *for*: if a reader consults it to decide which row to act on or which file to open next, lead with that choice.

## Indexes warrant more scrutiny than leaves

**Rule.** A hub `index.md` is held to a higher bar than the files it routes to. Every agent working anywhere downstream of a hub traverses it first, so a wrong or vague routing row is a fault multiplied by every reader who needed a branch it failed to point at. Review an index row for whether its read-trigger is precise enough that the right agent descends and the wrong one does not.

**Why.** A leaf file is read by the agents that already chose to descend to it; a mistake there costs those readers. A hub is read by every agent traversing the topic; a mistake there — a missing row, a trigger so vague that no one matches it, a row that points at the wrong target — silently blocks discovery of everything beyond it, and the blocked agent has no signal that the fact it needed exists at all. The blast radius of an index defect is the entire sub-tree it gates, which is why the index earns the closer read.

The invariant is **complete, precise routing**: every agent-facing leaf is reachable from its nearest hub, each routing row links its destination and states the condition under which the reader opens it, and any change to the set of leaves keeps the hub in step.

**Do.** Adding, moving, or removing a leaf updates its hub's routing in the **same change** — a new spoke gets a row, a moved spoke's row is repointed, a removed spoke's row is deleted. Check that each trigger is specific enough to be matched by the agent who needs that branch and *not* matched by one whose need is a sibling.

**Don't.** Add a file under a hub without a routing row — an unrouted file is undiscoverable; the hub is the only path to it. Leave a row pointing at a leaf that has moved or no longer exists — a dead route is worse than none, because the reader trusts it.

**See also.** [`./principles.md`](./principles.md) §"Point, don't duplicate" — the reference-shape rule this article's structure exists to serve.
