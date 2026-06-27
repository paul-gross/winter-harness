# Check Fixture

Deliberate anchor violations for `lint_link_anchors.py`. Pruned from any
default repo scan (it lives under `fixtures/`); the test targets it explicitly.

## Valid anchors — no findings expected

- Same-file anchor: [check-fixture](#check-fixture)
- Other-file anchor: [alpha](./target.md#alpha)
- Duplicate-disambiguated anchor: [beta-1](./target.md#beta-1)
- Code-span heading: [code](./target.md#with-code-span)

## Dangling anchors — fail expected

- Same-file dangling: [nope](#nonexistent-heading)
- Other-file dangling: [nope](./target.md#nonexistent)

## Dead file target — fail expected

- Dead relative link: [gone](./nonexistent.md)

## Skipped by example marker — no findings expected

- Marked as illustration: [bad](#bad-anchor) <!-- winter-lint:example -->
