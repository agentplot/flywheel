# Design: the observed loop run

## Context

See proposal.md — Why, and `design/observer.md` for the settled shape. Both
loops are stateless per-process programs (`BoltLoop.run` /
`_flywheel_intent.run`) started by the server's 60s reconcile; the guards
write idempotent bookkeeping directly as they check, and the drives (session
launches, merges, landings) happen inside the cycle. Loops already receive
every seam injected (tracker, runner factory, subprocess, clock, log), so the
ledger joins as one more injected seam.

## Goals / Non-Goals

**Goals**

- One ledger implementation shared by both loops and the server.
- Gate the drives; ledger everything.
- Deterministic report rendering — the agent is optional narrative, never a
  fact source.

**Non-Goals**

- Two-phase (plan-then-write) guards. Guards stay write-as-they-check; their
  writes are ledgered around each write, not pre-planned.
- Live pane monitoring. Ledger + logs after the fact is the baseline.
- The narrative observer agent itself — this change ships the hook
  (`FLYWHEEL_OBSERVER`), not the agent.

## Decisions

**D1 — `bin/_flywheel_ledger.py`, one `RunLedger` class.** Constructed from
an observations root, a scope slug (`bolt-<slug>`, `intent-<slug>`,
`dispatch`), and a run id (UTC stamp + pid). Appends JSONL entries of four
kinds: `precondition`, `expect` (step, trigger, expected), `actual` (step,
outcome, ok), `note`. Renders two markdown documents beside the JSONL:
`<run>.plan.md` (preconditions + expected only) and `<run>.report.md`
(the joined table, mismatched rows first). Rendering is pure ledger →
markdown; no tracker read, no agent. Alternative considered: an agent that
scrapes logs — rejected, facts must not originate in an agent.

**D2 — Observations root derives from the tracker owner.** Default
`$FLYWHEEL_STATE_HOME` or `~/.local/state/flywheel`, then
`<org>/observations/<scope>/`, where org is the owner half of the loop's
repo param. The server passes nothing new; a standalone loop invocation
lands in the same place the server's would. Alternative: a `--state-dir`
flag threaded from the server — more plumbing for the same answer.

**D3 — The expectation report is a record, never a gate.** The plan
document renders where the drives begin — bolt loop: after `analyse`
filters the batches, before the drive loop, and again before `land_stage`;
intent loop: before `dispatch_batch` — and the pass proceeds. The approvals
that pace the flywheel are the tracker's own (the board move, the dispatch
plan's round); a loop that paused on a second, file-system approval made
every new milestone stall silently until the operator found the pending
marker. Guard writes were never observed as plans: they are idempotent
repairs, recorded as they happen.

**D6 — Dispatch nudges ledger at the server.** The server appends to
`observations/dispatch/<server-run>.jsonl` around each dispatch prompt it
sends: expect (deliver the nudge) then actual (delivery result). No gate —
relays are the operator's own words moving; vetoing them gates nothing
useful.

**D7 — Observer hook, not observer agent.** After rendering a report, if
`FLYWHEEL_OBSERVER` names a command, the loop runs it with the report path;
whatever it appends must sit under an `## Observer` heading. Ships disabled.

## Risks / Trade-offs

- [Gate stalls unattended runs by design] → that is R2's ruling; `courtesy`
  mode is the relaxation, one env var away, and the plan document tells the
  operator exactly what to approve.
- [Expectation keys churn on incidental detail] → keys hash only step,
  trigger, and expected fields — no run ids, no timestamps.
- [Existing loop tests all start driving without approval] → test params
  construct loops in `courtesy` mode except the gate tests themselves.
- [Ledger write failure must not kill a pass] → ledger writes are
  best-effort: an OSError logs and the pass continues; the report notes the
  gap.

## Migration Plan

Ships in the plugin like any release; no data migrates. First run under the
new version gates every milestone loop until approved — expected, and the
point. Rollback is the previous plugin version; ledgers on disk are inert.

## Open Questions

- Report retention: nothing prunes `observations/` yet; revisit when a week
  of runs shows the volume.
