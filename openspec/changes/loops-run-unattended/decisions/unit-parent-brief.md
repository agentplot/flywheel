# Decision: Compose writes the operator's brief into the unit parent

## Decision

Every compose that births or amends a unit parent marks the parent's
body stale; once per loop cycle that ended with a stale parent, the
loop charges one small headless session (sonnet, effort low) to
rewrite the body as a brief: discoveries grouped by theme, mechanical
vs. risk-carrying, what needs an operator ruling before work starts,
issue numbers as footnotes. The body is the surface because the board
card and the approval click show it; comments scroll away under
bookkeeping. The brief freezes when the operator moves the unit to
Ready — the loop never charges a refresh for a unit at Ready.

Cost ceiling, stated per #69's currency: one short model call per
compose-touched cycle, not per sub-issue; a tracker at rest pays zero.

## Context

- Produced by: `../sessions/2026-08-14-loop-program-decisions/round.md`
  §6, approved by the operator in the plannotator round of 2026-08-16.
- Observed defect: unit #138 reached 19 sub-issues with an empty body —
  the build side gets a cohesive view (the spec stage writes one change
  per batch) while the operator had nothing between the title and all
  19 bodies. Queued as #161.
- Assumptions where this touches open neighbours (#98/#142 on where
  the parent lives, #125 on checkoff — none decided here): the brief
  is written into whatever issue is the parent, and describes the set
  at refresh time; it does not track checkoff.
- A model-free digest was declined: a grouped list of 19 titles is
  still 19 titles.

## Consequences

- The build is #211: the stale-mark in `compose_batch`, the refresh
  charge in the loop, a freeze-at-Ready test.
- #161 closes on the design.
