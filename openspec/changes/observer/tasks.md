# Tasks: the observed loop run

## 1. The ledger

- [x] 1.1 Write `bin/_flywheel_ledger.py`: `RunLedger` with `precondition`,
      `expect`, `actual`, `note`, JSONL append under
      `<state-home>/<org>/observations/<scope>/<run>.jsonl`, best-effort
      writes (OSError logs, never raises)
- [x] 1.2 Add plan rendering (`<run>.plan.md`: preconditions + expected) and
      report rendering (`<run>.report.md`: joined table, mismatches first,
      clean-run line when nothing diverged)
- [x] 1.3 Add the gate helpers: canonical expectation-set key (SHA-256 over
      step/trigger/expected of drive entries), `pending.json` write,
      `approved/<key>` check, approve() that moves pending to approved
- [x] 1.4 Tests: `tests/test_ledger.py` — entry shapes, plan/report
      rendering, mismatch ordering, key stability across runs, approve flow,
      best-effort write failure

## 2. The bolt loop

- [x] 2.1 Construct a `RunLedger` in `BoltLoop.run`; record preconditions
      (ready set, batches) and a no-action outcome on empty passes
- [x] 2.2 Ledger guard writes: wrap each guard action append with
      expect/actual entries
- [x] 2.3 Gate the drive: after batches are analysed, build drive
      expectations (per batch: stages the type runs), check approval per D3;
      unapproved → write plan, stop pass with "gated — awaiting flywheel
      approve"; `courtesy` mode writes the plan and drives
- [x] 2.4 Ledger each stage drive (expect before, actual after: spec, build,
      verify, review, merge) and gate + ledger the landing before
      `land_stage`
- [x] 2.5 Render the report at end of an acting pass; run `FLYWHEEL_OBSERVER`
      hook when set
- [x] 2.6 Wire `gate` mode into loop params from `FLYWHEEL_GATE` in
      `bin/flywheel-bolt-loop`; default `gate`
- [x] 2.7 Tests: gated pass stops with plan written; approved key drives;
      changed plan re-gates; courtesy drives; report renders with actuals;
      existing tests updated to construct courtesy-mode loops

## 3. The intent loop

- [x] 3.1 Construct a `RunLedger` in `_flywheel_intent.run`; preconditions +
      no-action outcome
- [x] 3.2 Ledger guard writes (handoff birth, compose) with expect/actual
- [x] 3.3 Gate `dispatch_batch`: expectation per batch (number, session
      type); same approval mechanics; ledger the dispatch actual
- [x] 3.4 Render the report at end of an acting pass
- [x] 3.5 Tests: mirror 2.7 for the intent loop

## 4. The server and the CLI

- [x] 4.1 Server: append expect/actual entries to
      `observations/dispatch/<server-run>.jsonl` around each dispatch nudge
- [x] 4.2 `flywheel approve <milestone-slug>`: resolve the scope, print the
      pending plan summary, approve it; "nothing to approve" when no pending
- [x] 4.3 Tests: server nudge entries; approve CLI happy path and
      nothing-pending path

## 5. The profiles

- [x] 5.1 Add the finding-routing paragraph to every `agents/flywheel-*.md`
      profile body: machinery findings go in the session's report, never to
      the tracker

## 6. Close out

- [x] 6.1 Update `design/observer.md` status line: rulings applied, change
      `observer` carries the build
- [x] 6.2 `openspec validate observer --strict` green; full test suite green
