# Decision: Shared modules stay in bin/

## Decision

The `_`-prefixed shared modules (`_flywheel_gh.py`,
`_flywheel_sessions.py`, `_flywheel_inbox.py`, `_flywheel_bolt_loop.py`,
`_flywheel_intent.py`, `_flywheel_server.py`) stay in `bin/`, beside
the commands that import them. The rule `bin/README.md` states in
place of its "open question" paragraph: a command must be reachable by
name; its logic lives in an importable sibling module when tests need
it or commands share it; `tools/` is for a large command's whole
implementation behind a thin `bin/` entry point, not for shared
libraries.

## Context

- Produced by: `../sessions/2026-08-14-loop-program-decisions/round.md`
  §2, approved by the operator in the plannotator round of 2026-08-16.
- Why not `tools/`: the sibling `sys.path.insert` import only works
  beside the commands; moving the modules churns five commands and the
  test suite for zero user-visible change. The underscore-and-extension
  naming already reads as not-a-command. Queued as #85.
- The item's second defect ("Two commands live here now" vs seven) was
  already fixed on main before this session.

## Consequences

- `bin/README.md`'s open-question paragraph is rewritten into the rule
  above, in this session's branch.
- #85 closes on the ruling.
