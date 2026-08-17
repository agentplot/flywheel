# Proposal: the observed loop run

## Why

The 2026-08 live fire proved the flywheel cannot be evaluated through its own
tracker: sessions filed machinery findings into the same bus the machinery was
driving, and the operator had to spelunk issues, panes, and server logs to know
whether a run did what it was supposed to. `design/observer.md` (rulings
applied 2026-08-17: ledger beside logs; expectation report is a gate; dispatch
observed too) settles the replacement: every loop run is observed, and the
machinery never files issues about itself.

## What Changes

- Both loop programs write a **run ledger** — a machine-readable JSONL record
  of preconditions as read, each intended action with its expected outcome, and
  each actual outcome — beside the loop logs under the org state directory.
- A pass that intends actions is **gated**: the loop renders an expectation
  report (preconditions + expected, no actuals) from the ledger and exits
  without acting until the operator approves that exact expectation set;
  an approved set does not re-gate. `flywheel approve` grants the approval.
- At the end of an acting pass the loop renders the **observation report** —
  the same table with the actual column filled, mismatches first — from ledger
  facts alone; an observer agent MAY add narrative, but facts never originate
  in an agent.
- The server writes ledger entries for the **dispatch nudges** it sends, so
  dispatch activity is observable through the same surface.
- Session profiles gain the **finding-routing rule**: machinery findings go in
  the session's report, never to the tracker.

## Capabilities

### New Capabilities
- `flywheel-run-ledger`: what a loop run records, where, and in what vocabulary
  — preconditions, expectation entries before acting, actual entries after,
  dispatch-nudge entries from the server.
- `flywheel-expectation-gate`: the pre-run report, the pause, the approval
  keyed to the expectation set, and the `flywheel approve` grant.
- `flywheel-observation-report`: the operator-facing expected-vs-actual
  report rendered from the ledger, and the optional observer-agent narrative.

### Modified Capabilities
- `flywheel-session-profiles`: profiles must carry the finding-routing rule —
  a session that notices the machinery misbehaving reports it and stops; it
  never files a tracker item about the machinery.

## Impact

- `bin/_flywheel_bolt_loop.py`, `bin/_flywheel_intent.py`: ledger calls at the
  existing guard/stage seams; gate check before the first action of a pass.
- `bin/_flywheel_server.py`: dispatch-nudge ledger entries.
- New `bin/_flywheel_ledger.py`: ledger, gate, and report renderer shared by
  both loops.
- `bin/flywheel`: new `approve` subcommand.
- `agents/flywheel-*.md`: one finding-routing paragraph each.
- `~/.local/state/flywheel/<org>/observations/` becomes a written path.
- Tests: new ledger/gate/report suite plus loop-test updates where passes now
  gate.
