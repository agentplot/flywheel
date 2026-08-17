# Decision: The server filter names its sweep in the record

## Decision

`design/loop-programs.md`'s server filter is amended to read as built:
milestones with a job include, besides the ready / in-progress /
Ready-batch / awaiting-landing tests, any open `intent/*` milestone
holding settled unbatched assertions or orphan `state:queued` items —
the guard-only work that previously only the intent loop's own filter
named. The licensing rule is stated beside it: **a server filter may
over-approximate; a loop filter must be exact** — a false positive
costs one process start and a clean exit, a false negative costs work
that never happens. No code changes: this blesses
`_flywheel_inbox.server_inbox(sweep=True)` as built and tested, and
matches the rule `skills/_reference/tracker.md` already carries.

## Context

- Produced by: `../sessions/2026-08-14-loop-program-decisions/round.md`
  §1, approved by the operator in the plannotator round of 2026-08-16
  (`plannotator-result.json`, decision "approved", §1 "Looks good").
- The hole and the sweep are documented at
  `bin/_flywheel_inbox.py:339` (`server_inbox` docstring) with a
  containment property test; found building #76, queued as #81.

## Consequences

- The amendment to `design/loop-programs.md` lands in this session's
  branch (same pass as the guard-list amendment from
  `intent-scaffold-guard.md`).
- #81 closes on the record matching the build.
