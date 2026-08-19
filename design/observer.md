# Decision draft: every loop run is observed; the machinery never files issues about itself

Status: RULED by the operator, 2026-08-17 — the change `observer`
(openspec/changes/observer/) carries the build.

## Why

Running the flywheel on its own repo turned the tracker into a hall of
mirrors: sessions testing the machinery filed their findings *into* the
machinery's own bus, and every escalation, retype, and triage note
about the loops became indistinguishable from the work the loops were
supposed to drive. The 2026-08 live fire ended with the tracker
archived wholesale (see `design/field-notes/2026-08-17-tracker-archive.md`).

Two separations fall out of that:

1. **SUT vs machinery.** The tracker is the bus for the system under
   construction. Findings *about the flywheel itself* — bugs in loops,
   prompt problems, dispatch mistakes — are evaluation output, not work
   items, and never enter the tracker the flywheel is driving. When the
   flywheel is eventually pointed at a real target repo (e.g.
   willdan-blueprints), this rule is what keeps its self-knowledge from
   leaking into a client's tracker.
2. **Doing vs judging the run.** The loops do; sessions work; and a
   separate standing observer judges whether the run did what it was
   supposed to. The operator evaluates the flywheel by reading observer
   reports, not by spelunking issues, panes, and server logs.

## The rule

No session, loop, or dispatch writes machinery findings to the tracker.
An agent that notices the machinery misbehaving says so in its report
and stops; the observer carries it to the operator. Tracker writes
remain what they always were: state moves on the SUT's own work items.

## The observer

One observer per loop run, one shared design for both loop kinds — the
intent loop and the bolt loop are different programs but the same shape
(preconditions → trigger → actions → outcome), so they share one
observer implementation, parameterized by the loop's program.

The observer is an agent, but the facts it reports are not gathered by
an agent. The loop already computes everything the report needs — the
tracker snapshot it read, the guard that fired, the session it charged,
the state it expects afterward. The split is:

- **The loop writes the ledger** — a machine-readable run record,
  appended as the pass executes: preconditions as read, each action
  taken, and the expected outcome of each action, in the loop's own
  vocabulary (slugs, stages, batch numbers). Deterministic, testable,
  free.
- **The observer writes the report** — an agent that reads the ledger
  and the session logs, compares expected against actual, and renders
  the operator-facing summary. Narrative and judgment live here;
  facts never originate here.

Live monitoring is optional; reading ledger + logs after (or during)
the run is the baseline and is sufficient.

## The report

Slugs and quick summaries — never issue bodies, never comment threads.
Two editions of the same document:

**Before the run** (the expectation report): preconditions and expected
outcomes only. The operator can catch a logic error by reading this
alone — if the expected column is not what they want to happen, the run
never needs to start.

**After the run**: the same table with the actual column filled in,
expected and actual side by side, mismatches surfaced first.

```markdown
# bolt/stage-labels — run 2026-08-17T09:12
preconditions: #133 state:ready · build/stage-labels absent · gate green on main

| step   | trigger                | expected                        | actual                    |
|--------|------------------------|---------------------------------|---------------------------|
| spec   | #133 ready, no spec    | change validates, commit on br  | ✓ commit ab12f3           |
| build  | spec validated         | commit by pathspec on build/…   | ✓ commit cd45e6           |
| verify | build commit landed    | .flywheel/verify.md = NONE      | ✗ 2 findings → review     |
| review | findings present       | ruling: proceed/refix/escalate  | refix, round 1            |
```

A mismatch is not automatically a failure — the observer states what
diverged and lets the operator judge. The report is the evaluation
surface; commentary on it (not tracker issues) is how fixes get queued.

## Where reports live

`~/.local/state/flywheel/<org>/observations/<milestone-slug>/<run>.md`,
beside the loop logs they interpret — mutable run state, not durable
prose. A finding the operator promotes to durable knowledge gets
written into `design/` or the books by a human-directed session, the
same as any other decision.

## The evaluation loop this enables

Operator reads the expectation report beside the run → reads the
comparison report → comments → a repair agent (an
ordinary interactive session with the operator, not machinery) consumes
report + commentary and fixes the flywheel → next run. Tighter than
live-fire-and-forensics, and the only loop in which machinery fixes
happen.

## Rulings (operator, 2026-08-17)

- R1 — The ledger sits beside the server/loop logs; logs stay raw, the
  ledger is curated.
- R2 (2026-08-19) — The expectation report is a record, never a gate:
  the tracker's own approvals pace the flywheel, and a pass that intends
  actions writes its plan and proceeds.
- R3 — Dispatch is observed too: the server ledgers every nudge it
  sends under `observations/dispatch/`.
