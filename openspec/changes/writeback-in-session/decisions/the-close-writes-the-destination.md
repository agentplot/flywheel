# Decision: the close writes the records, and chains the destination write

## Decision

A design session that settles something writes the settlement into its
own records as part of its close — the `decisions/<slug>.md` files, the
question closures, the session directory — and proposes every
destination write as a follow-up in its round-close plan. The
destination is an open-ended list — book chapters, context maps, HTML
design docs, research result reports today, extending over time — and
the flywheel specifies the plumbing of the write, never the list. The
write itself is a `type:writeback` item in the next elaboration,
released by the same one approval that closes the round, so it never
waits on a stranger's future batch and never drifts: the chain carries
it, in the very gesture that ends the session that made it due.

Nothing about a settlement is a fait accompli when the operator reviews
the round-close plan. Everything on that plan — the writeback, the
questions, the construction — is a proposal in one grammar, and the
records the session wrote are the only files that exist before
approval.

## Context

- Chapter: the flywheel book at `agentplot/blueprints` (write rides the
  chained writeback this decision defines)
- Produced by: sessions/2026-08-18-close-writes-destination/writeback-in-session-draft.md,
  annotated by the operator 2026-08-18; revised by the operator
  2026-08-18 in the round-close design round — the write moved from the
  settling session's own close to the chained follow-up, so the
  round-close plan holds one grammar where every row is a proposal

## Consequences

- The round-close protocol (`skills/_reference/round-close.md`) carries
  the routing: a settlement's destination write is an elaboration item,
  and the citable-source test decides what is carded for construction
  without one.
- Every design type launches with a worktree — the close writes
  `decisions/` and `close/` files, and an unchanged worktree costs
  nothing at teardown. Research included: flip `worktree=True` in
  `bin/_flywheel_intent.py` TYPES.
- Queued question, closed: where the context-map system code lives —
  see `context-map-code-lives-in-the-plugin.md`.
