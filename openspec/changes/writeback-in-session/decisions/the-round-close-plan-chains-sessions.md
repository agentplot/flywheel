# Decision: the round-close plan chains sessions

## Decision

A design session with a next round to propose ends with a round-close
plan through a plannotator round: what this round closed, the next
elaboration (a batch the session composed at Backlog before the round),
direct bolt plan cards where the records already say everything a spec
needs, and what is deliberately left queued. Approval is one operator
gesture, and the session applies the word directly: `stage:done` on its
own items, board Ready on the approved elaboration and cards, then
settle — the loop is unchanged, doing with `stage:done` items and a
Ready batch exactly what it does today. Partial approval folds: struck
items stay at Backlog; outright rejection is an ordinary round
iteration. Session-defined elaborations and bolt cards carry the
planned-bolt-unit staleness mechanic: an iteration that replaces one
wholesale closes it `closed:superseded` with a successor pointer, and
smaller changes amend the open Backlog batch in place. The chain is an
option, never an obligation — sessions with nothing to propose settle
as today, and the loop's compose guard and board flip remain the
fallback path.

## Context

- Chapter: the flywheel book at `agentplot/blueprints` (write rides
  #320's writeback)
- Produced by: sessions/2026-08-18-chaining-and-map-home/session-chaining-dx-draft.md,
  annotated by the operator 2026-08-18 ("this all looks good" plus the
  supersession caveat, folded)

## Consequences

- Assertions to queue: the contract edits — round-close plan and
  approval-application in the session profiles and round-type skills,
  with the one exception to "never move an item to state:ready";
  compose-guard and state-ladder prose in inception/tracker references;
  the session-run `flywheel-board` Ready flip in herdr.md; the
  stale/supersede mechanic for session-defined elaborations and cards.
