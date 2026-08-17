# Decision: The restart sweep — re-attach where alive, escalate where dead

## Decision

The intent loop gains a resume sweep, run each cycle before dispatch
(beside `resume_collect`), over items `state:in-progress` without
`stage:done`/`stage:collected` on its milestone:

1. Group by the session name in the dispatch marker
   (`<!-- flywheel:dispatch name=… origin=… notified=… -->`).
2. Ask the runner whether an agent is alive under that name (the same
   roster `HerdrRunner.launch` consults).
3. **Alive** → rehydrate supervision only — `supervise(…,
   origin=<marker>, notified=<marker>)` — then the normal land/collect
   path. Never `launch` on a live name: it would re-send the work
   order into a running session.
4. **Dead** → never auto-relaunch. Comment what was found (session
   gone, work state unknown), set `needs-operator`; the operator flips
   `stage:done` (collect path) or back to `state:ready` (fresh
   dispatch, on their word).

## Context

- Produced by: `../sessions/2026-08-14-loop-program-decisions/round.md`
  §5, approved by the operator in the plannotator round of 2026-08-16.
- The dispatch marker carries `origin`/`notified` precisely so
  supervision can be rehydrated without handing a hung session a fresh
  four-hour budget (`_flywheel_sessions.supervise` docstring). The R1
  coupling is discharged: `stage:done` is the completion signal and
  `resume_collect` consumes it; this sweep covers the complement.
- Auto-relaunch on a dead name was declined: only a judgment can say
  whether a dead session's tree is resumable, and judgment belongs to
  sessions and the operator. Queued as #89.

## Consequences

- The build is #210: the sweep in `_flywheel_intent`, a roster fake in
  the suite, fixtures for restart-with-live-pane and
  restart-with-dead-pane.
- #89 closes on the design.
