# Decision: the writeback type carries the destination write

## Decision

`type:writeback` is the standard destination-write type. A settlement's
chapter, map move, or other destination write is a writeback item in
the settling session's next elaboration — proposed on its round-close
plan, released by the round's one approval — and book work that is
itself the work rides the same type: repairing a contradiction the
books already hold, restructuring chapters, catch-up writes for
settlements that predate the chain. The type keeps its skill's chapter
discipline. What it never is is a stranded tail: no settlement's write
waits on a future batch nobody has composed, because the close that
made the write due is the close that proposes it.

## Context

- Chapter: the flywheel book at `agentplot/blueprints` (write rides
  this intent's chained writeback)
- Produced by: sessions/2026-08-18-chaining-and-map-home/session-chaining-dx-draft.md,
  annotated by the operator 2026-08-18; revised by the operator
  2026-08-18 in the round-close design round — the destination write
  moved out of the settling session's close and back onto this type,
  so the narrowing to repair-only was revised away with it

## Consequences

- `skills/writeback/SKILL.md` keeps its destination-write frame and
  gains the close-round section every design type carries.
- The decision template's default consequence line keeps naming the
  writeback item a settlement queues.
