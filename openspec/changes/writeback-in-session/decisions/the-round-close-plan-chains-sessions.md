# Decision: the round-close plan chains sessions

## Decision

A design session with a next round to propose ends with a **round-close
plan**: one lavish page over real markdown files in the session's
`close/` directory, carrying what the round closed, the elaboration it
proposes next, the construction it proposes directly as unit cards in
the bolt planner's exact grammar, and what it deliberately leaves
queued. Every row is a proposal with a routing control set to the
session's default; **nothing reaches GitHub until the operator
approves** — no item, batch, milestone, or card exists ahead of the
apply, so a plan is previewed rather than discovered on the board.

Routing is exclusive — `elaboration` · `unit card` · `hold` · `drop` ·
`answered` — and the chain carries the sequencing the plan does not:
an outcome whose card can cite a source that exists (a decision
record, a chapter already written) is carded now, the skip-the-
writeback case; an outcome with no source a spec could be written from
routes to a writeback, and that writeback session's own close round
cards it. No dependency edge spans the elaboration and construction
sections.

Approval is one operator gesture, and the session applies the word
directly, in an order that is load-bearing: all file commits first (the
branch merge-complete before any tracker write), then the elaboration
and cards at Backlog, then `stage:done` on its own items, then the
board Ready flips, then settle. The loop's cycle runs guards →
collect/merge → dispatch, so a restart at any point mid-apply either
merges the finished branch before the released batch can dispatch, or
leaves the batch at Backlog — the ordinary fallback path, finished by
one operator board flip. A step that fails stops the apply where it is:
comment the partial state, add `needs-operator`, never settle
half-applied.

Partial approval folds: struck items stay unfiled or at Backlog per the
annotation; outright rejection is an ordinary round iteration.
Session-proposed elaborations and cards that an iteration replaces
wholesale after an apply close `closed:superseded` with a successor
pointer; smaller changes amend the open Backlog batch in place. The
chain is an option, never an obligation — any design type MAY run a
close round, a session with nothing to propose settles as today, and
the loop's compose guard and board flip remain the fallback path. The
loop itself changes not at all: `stage:done` items and a Ready batch
are exactly what it consumes today.

## Context

- Chapter: the flywheel book at `agentplot/blueprints` (write rides
  this intent's chained writeback)
- Produced by: sessions/2026-08-18-chaining-and-map-home/session-chaining-dx-draft.md,
  annotated by the operator 2026-08-18; revised by the operator
  2026-08-18 in the round-close design round — the surface moved from
  a plannotator round to a lavish page, composing moved from before
  the round to the apply, and the writeback-then-card sequencing moved
  off blocked-by edges and onto the chain itself

## Consequences

- The protocol lands as `skills/_reference/round-close.md`, cited by
  the session profiles and every design type skill; the one exception
  to "never move an item to `state:ready`" — applying the operator's
  explicit approval given in a round the session itself ran — lands in
  the profiles and `tracker.md`.
- Every design type becomes an operator-round, worktree-carrying type
  in `bin/_flywheel_intent.py` TYPES.
- The unit cards and elaboration bodies are files the page renders,
  posted verbatim at apply — the bolt-planning grammar, nothing
  reformatted between the round and the board.
