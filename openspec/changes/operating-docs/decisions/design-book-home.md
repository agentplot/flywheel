# Decision — flywheel's design book's home

Closed 2026-08-18 across two plannotator rounds on
`../sessions/2026-08-18-docs-set/design-book.md` (item #275; inherits
#183). Round 1 redirected the draft to a new org repo; round 2
confirmed the state already stands.

**Flywheel's book lives in `agentplot/blueprints` (public) at
`books/flywheel/`** — the org's one book-carrying repo, holding every
agentplot system's book with the shared tooling at the root. The
plugin repo carries no book. Verified standing state: the 13 chapters
are in the repo, fleet.yaml's `books:` entry points at the checkout,
and the moved chapters scan clean of client-private references.

What writes into it: writeback sessions on flywheel's own intents,
under the ordinary books contract — destination voice, chapters
rewritten in full, gates green, never a record that work happened.
Field notes and gap audits stay in the plugin repo's `design/`.

Ownership split with `intent/machinery-self-desc`: the location and
write path are settled here; the content backfill (the 2026-08-17
book-gap audit's findings) remains that intent's work. Full rationale
in the session draft.
