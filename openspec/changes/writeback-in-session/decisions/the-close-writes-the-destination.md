# Decision: the close writes the destination

## Decision

A design session that settles something writes the settlement into its
destination as part of its own close, before it settles. The
destination is an open-ended list — plans, book chapters, context maps,
HTML design docs, research result reports today, extending over time —
and the flywheel specifies the plumbing of the write, never the list. A
book chapter is rewritten in full, in destination voice, gates green,
by the session that made it stale; a settlement about the intent itself
lands in the intent's records. No session queues a writeback item for
what it itself settled; a consequence item is queued only when the
settlement obligates work beyond the writer's own close — a chapter in
a repo the session holds no worktree for, or a contradiction the write
reveals. Every design type launches with a worktree so the write always
has somewhere to land; an unchanged worktree costs nothing at teardown.

## Context

- Chapter: the flywheel book at `agentplot/blueprints` (write queued —
  see Consequences)
- Produced by: sessions/2026-08-18-close-writes-destination/writeback-in-session-draft.md,
  annotated by the operator 2026-08-18 (annotation 1 amended the
  destination list to open-ended with the context map first-class;
  no objection to the core)

## Consequences

- Assertion: flip research to `worktree=True` in
  `bin/_flywheel_intent.py` TYPES.
- Writeback item: write this decision into the flywheel book at
  `agentplot/blueprints` — beyond this session's worktree.
- Queued question: where the context-map system code lives (out of
  willdan-blueprints; into flywheel or a new agentplot project; map
  JSON stays with the repo it describes).
- Skill and profile prose (type skills, session profiles,
  `skills/inception/SKILL.md`, decision template) waits on the
  session-chaining DX design before its final shape.
