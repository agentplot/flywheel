# Decision: rounds get numbers

## Decision

The compose guard titles every elaboration
`Elaboration: <slug> — round N`, where N = 1 + the count of
elaborations already on that milestone in the snapshot, open or closed.
The amend-not-rebirth rule is untouched: newcomers join the open
Backlog elaboration, which keeps its number. The board shows distinct
rows per round; nothing else consumes the title.

## Context

- Chapter: the flywheel book at `agentplot/blueprints` (write queued
  with the companion decision's writeback item)
- Produced by: sessions/2026-08-18-close-writes-destination/writeback-in-session-draft.md,
  annotated by the operator 2026-08-18 (annotation 3, "Looks good")

## Consequences

- Assertion: the round number in `apply_compose`'s elaboration title
  (`bin/_flywheel_intent.py`).
