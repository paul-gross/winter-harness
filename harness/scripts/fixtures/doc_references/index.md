# Doc-references fixture

Routing seed for `lint_doc_references.py`. Pruned from any default repo scan
(it lives under `fixtures/`); the test targets it explicitly.

- A good link: [good](./good.md)
- A routed ai/ doc: [linked](./ai/linked.md)
- A broken link: [missing](./nope.md)
- An external link (skipped): [site](https://example.com)
- A path-notation link (skipped): [ws](workspace:/CLAUDE.md)
