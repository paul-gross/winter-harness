# Verification — winter

Winter's **verifiability matrix** — the inventory of concrete methods a skill or agent uses to assert a winter change is correct. Instantiates the Canon concept at [`../canon/verifiability-matrix.md`](../canon/verifiability-matrix.md), the way `architecture/` instantiates architecture guidance.

The matrix cuts across languages and surfaces — it holds Python QA commands, CLI probes, and manual orchestration exercises alike — and an agent reads it whenever it plans how a change will be checked, not only at review time. That is why it lives here rather than in the Python-review `standards/` domain.

Parent: `../index.md` (root topology).

| File | When to read |
|------|--------------|
| [`./winter.md`](./winter.md) | Verifying any winter change — the concrete commands, CLI probes, manual methods, and setup tools a skill or agent may run, each with its stable method id |
