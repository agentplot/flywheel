## 1. Re-read the neighbours from disk before trusting a claim

Every path and quoted phrase below was read on `bolt/stage-labels` at
`553c7e3`. Siblings on this bolt are live and `main` moves under it; locate
every site by heading, function name or quoted phrase, never by line number.

- [x] 1.1 Re-read `bin/flywheel-setup`'s `LABELS` table and confirm it still
      defines only `type:*`, `state:*`, `closed:*`, `unit`, `elaboration` and
      `needs-operator`, with no `stage:*` name. If a `stage:*` name is
      already there, stop — someone else has moved it.
- [x] 1.2 Re-read `bin/_flywheel_inbox.py`'s vocabulary block and confirm
      its header comment still reads "The vocabulary. One enumeration,
      bin/flywheel-setup:57-90."
- [x] 1.3 Re-read `bin/_flywheel_bolt_loop.py` and confirm `guards` still
      runs `guard_scaffold`, `guard_flip_consume`, `guard_route` and returns
      `(actions, failure)`; that `change_validates`, `branch_has_commits` and
      `branch_merged` are unchanged; and that `cycle` still runs
      `spec_stage → build_stage → verify_stage → merge_stage`.
- [x] 1.4 Re-read `bin/_flywheel_intent.py` and confirm `is_complete` still
      returns `None` for an unconfigured signal, that `COMPLETION_SIGNALS`
      still holds `closed`/`label`/`board`, and that `land` still tests
      completion batch-wide.
- [x] 1.5 Re-read `design/loop-programs.md`'s `## Open questions (three)`
      section and confirm R1 is still an open bullet reading "a state label
      the operator sets, a board Status, or closing the items — pick one so
      the loop has one filter."
- [x] 1.6 Re-read `skills/_reference/tracker.md` invariant 5 (the state
      ladder) and the board bullet naming "a quick bolt's lone born-ready
      item (at Ready from birth, via `flywheel-board`)".
- [x] 1.7 Confirm `openspec/changes/stage-labels/bolt.md` is present on this
      branch and that its Merge criteria still name the `flywheel-setup`
      label convergence.

## 2. The label set — before any loop writes one

- [x] 2.1 Add every name in the `stage:*` set — `stage:planned`,
      `stage:built`, `stage:verified`, `stage:merged`, `stage:in-session`,
      `stage:done`, `stage:collected` — to `bin/flywheel-setup`'s `LABELS`,
      each with a colour and a description in the style of the existing
      entries. Do not touch any existing entry.
- [x] 2.2 Add the matching constants to `bin/_flywheel_inbox.py`'s
      vocabulary block, beside `READY`/`IN_PROGRESS`/`QUEUED`, so the loops
      compare against names rather than string literals.
- [x] 2.3 Confirm `ensure_labels` needs no change: it skips a name already
      on the repo and rewrites nothing. Run it in a way that shows the
      idempotence (a second run reports all present) and record what you ran.
- [x] 2.4 Run the convergence against `agentplot/flywheel` and record the
      created names in your item comment. This is a merge criterion of the
      bolt and must be green before any item carries a stage label.

## 3. The bolt loop — the four construction stages (#96)

- [x] 3.1 Give `LoopConfig` a declared stage set, defaulting to
      `spec, build, verify, merge, land` so the three existing types are
      unchanged, and read a `stages:` key from the `loop:` block in
      `read_schema_config`. `parse_loop_block` already handles flow lists;
      confirm that on the real `schema.yaml` text rather than assuming it.
- [x] 3.2 Write `stage:planned` on each item of the batch when `spec_stage`
      returns ok — and on the plan-mode path when the plan is approved,
      which is where `plan_mode_build` leaves the loop after an `APPROVED`
      verdict.
- [x] 3.3 Write `stage:built` when `build_stage` returns ok and its
      deliverables check has passed, `stage:verified` when `verify_stage`
      returns clean, and `stage:merged` when `merge_stage` confirms ancestry.
      Each write follows the objective check already made at that boundary;
      none is taken from a session's report.
- [x] 3.4 Make each stage write remove any earlier `stage:*` label from the
      same item, so an item carries exactly one.
- [x] 3.5 Add a stage-reconciliation guard to `guards`, running before any
      work, that re-derives `stage:built` and `stage:merged` for the
      milestone's open items using `branch_has_commits` and `branch_merged`
      against `build/<slug>` branch names taken from `analyse`. It records
      its writes in `actions` like every other guard.
- [x] 3.6 Leave `stage:planned` and `stage:verified` out of the
      reconciliation, and say why in the guard's docstring — neither has a
      witness the tree can answer.
- [x] 3.7 Confirm no stage write touches a `closed:*` label and that
      `land_stage` still closes with `closed:done` and the landing SHA.

## 4. The intent loop — completion (#97)

- [x] 4.1 Write `stage:in-session` on each item of a batch in
      `dispatch_batch`, alongside the existing `state:ready` →
      `state:in-progress` relabel.
- [x] 4.2 Replace `is_complete` and `COMPLETION_SIGNALS` with a single
      per-item test on `stage:done`. Delete `_done_closed`, `_done_board`,
      `R1_UNRESOLVED`, and the unknown/`None` third value.
- [x] 4.3 **BREAKING** — remove `--completion-signal`, `--done-label` and
      `--done-status` from `bin/flywheel-intent-loop`, the matching `Config`
      fields, and their `config_fault` checks. Nothing else in the repo
      passes them; confirm that with a grep and record it.
- [x] 4.4 Rework `land` so each item carrying `stage:done` is collected,
      marked `stage:collected`, and closed independently of its siblings.
      An item already carrying `stage:collected` is skipped.
- [x] 4.5 Keep `merge_session` and `runner.close(handle)` session-scoped:
      they run once every item the session carries has reached
      `stage:collected`. The stalled path and the andon path still leave the
      pane open and merge and close nothing.
- [x] 4.6 Give the design-session skills the pane half of the flip: a
      session told by the operator that an item is done writes `stage:done`
      to that item and settles, and does not collect, merge or close
      anything itself.
- [x] 4.7 Update `design/loop-programs.md` — record R1 as resolved by the
      operator-set `stage:done` label, and remove it from the open-questions
      section rather than leaving the three candidates offered as a choice.
      Do not annotate what changed; the record reads as current state.

## 5. Every release creates a unit parent (#98)

- [x] 5.1 Make the born-ready release path create one `unit` parent on the
      bolt's milestone with the released items as its sub-issues.
      `bin/flywheel-batch --kind unit` already does the composing, the
      sub-issue attachment, the project add and the field defaults; prefer
      calling it over reimplementing any of that.
- [x] 5.2 Put the born-ready unit parent at Status **Ready** from birth —
      the operator's word at triage is the approval. `flywheel-batch` sets
      Backlog and states it never sets Ready, so the Ready move belongs to
      the release path, not inside that tool.
- [x] 5.3 Confirm the handoff birth path already produces the same shape and
      leave it at Backlog. If it does not, make it, and say in your item
      comment which it was.
- [x] 5.4 Stop adding the released items themselves to the board on the
      born-ready path; the parent is the row.
- [x] 5.5 Confirm an already-batched item is skipped rather than fatal —
      `flywheel-batch` prints "already in batch" and continues — and that
      running the release twice creates no second parent.
- [x] 5.6 Update `skills/_reference/tracker.md`'s board bullet, which today
      names "a quick bolt's lone born-ready item (at Ready from birth, via
      `flywheel-board`)", and the worked example under `## The quick bolt`,
      which shows a lone `#40` on the board with no parent.
- [x] 5.7 Sub-issue check-off timing was out of scope when sections 1–8 were
      built, and was not implemented. The operator has since ruled on
      `agentplot/flywheel#118`; section 9 carries it.

## 6. `bolt-direct` (#99)

- [x] 6.1 Add `schemas/bolt-direct/schema.yaml`, modelled on
      `schemas/bolt-quick/schema.yaml`: `loop:` declaring strategy `ff`, the
      stage set `spec, build, merge, land`, empty extensions, and hooks
      naming only boundaries these stages create — `post-verify` is not
      among them.
- [x] 6.2 Carry the same warning comment the sibling schemas carry about
      openspec 1.8.0 stripping the `loop:` block, since it applies verbatim
      to this file.
- [x] 6.3 Write the type's `artifacts` and `apply` instruction blocks in the
      shape its siblings use, stating that this type runs no verify stage
      and that the repo's merge gate is unaffected by the type.
- [x] 6.4 Make `cycle` run the stages the bound config names, so a
      `bolt-direct` bolt goes spec → build → merge with no verify session
      launched, and no `stage:verified` written.
- [x] 6.5 Confirm `bin/install-schemas` publishes the new directory with no
      change — it copies the tree — and record what you checked.
- [x] 6.6 Add `bolt-direct` to `schemas/README.md`'s list of construction
      types and to `design/loop-programs.md`'s `## The bolt types` section.
- [x] 6.7 Confirm the merge and landing paths are untouched: `merge_stage`
      and `land_stage` run `wt merge` through the repo's hooks whatever the
      type, and no new flag can suppress them.

## 7. Tests

- [x] 7.1 `tests/test_bolt_loop.py` — the four boundary writes; exactly one
      `stage:*` per item; reconciliation supplying `stage:built` for a commit
      the loop never saw written; reconciliation walking a too-far label
      back; the dry-cycle property holding with the new guard (two cycles
      against an unchanged tracker and tree, the second writing nothing).
- [x] 7.2 `tests/test_bolt_loop.py` — a `bolt-direct` config runs no verify
      stage and its items never carry `stage:verified`.
- [x] 7.3 `tests/test_intent_loop.py` — `stage:in-session` at dispatch;
      `stage:done` on two of three items collects and closes exactly those
      two; the `sess/*` merge and the pane close waiting for the third;
      `stage:collected` making a second collect a no-op.
- [x] 7.4 `tests/test_intent_loop.py` — remove
      `test_no_signal_configured_is_unknown_rather_than_incomplete` and
      `test_the_r1_note_is_on_every_run_that_names_no_signal` with the
      behaviour they pin. Keep
      `test_a_settled_session_is_not_a_finished_one`: a settled pane is
      still not a finished session, and it is now `stage:done` that decides.
- [x] 7.5 `tests/test_inbox.py` — the stage constants exist and every one is
      defined in `flywheel-setup`'s `LABELS`, so the two enumerations cannot
      drift.

## 8. The gates, on the tree that lands

- [x] 8.1 `sh scripts/validate-manifests.sh` green.
- [x] 8.2 `node scripts/check-paths.mjs` green.
- [x] 8.3 `node scripts/check-site.mjs` green.
- [x] 8.4 The repo's Python tests green.
- [x] 8.5 `openspec validate stage-labels-96 --strict` green.
- [x] 8.6 Commit by pathspec — `git add -- <your paths>`, then
      `git commit -- <your paths>`. Never `-a`, never `add -A`. Do not merge
      and do not push; the loop merges.

## 9. The merge-time check-off (#98, per the ruling on #118)

Sections 1–8 are built and committed at `3621c3f`; this section is the half
`#98` left open, ruled on `agentplot/flywheel#118` after that build ran.
Re-read each site on this branch before editing it — the tree has moved
since sections 1–8 were written.

- [x] 9.1 Add `closed:merged` to `bin/flywheel-setup`'s `LABELS`, beside the
      other four `closed:*` entries, with a colour and a description saying
      it means merged to the bolt branch and awaiting the landing. Add the
      matching `CLOSED_MERGED` constant to `bin/_flywheel_inbox.py`'s
      vocabulary block beside `CLOSED_DONE`.
- [x] 9.2 Run the convergence against `agentplot/flywheel` and record the
      created name — same merge criterion as 2.4, and the loop cannot write
      a label the repo does not define.
- [x] 9.3 Close each assertion item of a batch with `closed:merged` at the
      merge boundary in `cycle`, where `set_stage(batch.numbers,
      STAGE_MERGED)` already runs on git-confirmed ancestry, and comment the
      merge SHA. Non-assertion items on the milestone are untouched.
      `Tracker.close` hard-codes `closed:done` today — check every caller
      before changing its signature, and prefer a reason argument over a
      second closing method.
- [x] 9.4 Correct the merge session's work order, which reads "Comment the
      merge SHA on each item; do not close them — they close at the
      landing." The loop closes; the session does not. Keep the rest of that
      order — the gate language above all — exactly as it is.
- [x] 9.5 Make `land_stage` upgrade rather than close: remove
      `closed:merged`, add `closed:done`, comment the landing SHA, on an
      item that is already closed. Confirm on disk what `gh issue close`
      does against an already-closed issue and do not depend on it
      succeeding; an item that arrives without `closed:merged` still ends at
      `closed:done`.
- [x] 9.6 Carry `closed:merged` items in the picture the bolt loop works
      from. `Tracker.snapshot` is built from `open_issues()`; whatever you
      change there, the ready set must stay exactly what it is today, and
      the intent loop's and dispatch's filters must not acquire closed items
      they do not want.
- [x] 9.7 Make `landing_wanted` count a `closed:merged` item as something to
      land — its `open_items` test returns False on an empty list with the
      comment "nothing to close, nothing to land" — and `land_stage`'s item
      set include them. Without both, a bolt whose last batch merged never
      lands.
- [x] 9.8 Make `server_inbox` treat a bolt milestone holding a
      `closed:merged` item as a milestone with a job, so a loop killed
      between the last merge and the landing is restarted. The filter may
      over-approximate; a loop filter may not.
- [x] 9.9 Extend `guard_stages` to reconcile both halves of the merged edge:
      an item whose branch is an ancestor of the bolt branch ends the guard
      at `stage:merged` and `closed:merged`. Widen its scope to the
      milestone's `closed:merged` items as well as its open
      `state:in-progress` ones, and never walk a `closed:done` item back.
- [x] 9.10 Update `skills/_reference/tracker.md` invariant 5's closing
      sentence, which today reads "the landing stays the sole writer of the
      second, with the SHA in its closing comment", and the `## The literal
      graph` and `## The quick bolt` examples where an item closes
      `closed:done` at the landing. State the merge-back close, the upgrade,
      and that invariant 5's one-reason rule holds at every moment. Read as
      current state; do not annotate the change.
- [x] 9.11 Check whether any other skill or agent profile tells a session
      that construction items close only at the landing — grep for
      `closed:done` across `skills/`, `agents/` and `design/` — and correct
      what you find.

## 10. Tests and gates for section 9

- [x] 10.1 `tests/test_bolt_loop.py` — a merged batch's assertion items are
      closed with `closed:merged` and carry the merge SHA; a non-assertion
      item on the milestone is untouched.
- [x] 10.2 `tests/test_bolt_loop.py` — the landing upgrades `closed:merged`
      to `closed:done` with the SHA, leaves neither both labels nor none,
      and works on an item that is already closed.
- [x] 10.3 `tests/test_bolt_loop.py` — a bolt whose every item is
      `closed:merged` still lands: `landing_wanted` is true and the landing
      runs.
- [x] 10.4 `tests/test_bolt_loop.py` — reconciliation closes an open
      `stage:merged` item whose branch is merged, writes `stage:merged` on a
      `closed:merged` item that lacks it, leaves a `closed:done` item alone,
      and the dry-cycle property still holds with merged closed items on the
      milestone.
- [x] 10.5 `tests/test_inbox.py` — a bolt milestone holding only
      `closed:merged` items is a milestone with a job in `server_inbox`; the
      bolt loop's ready set on that milestone is empty; every `closed:*`
      constant is defined in `flywheel-setup`'s `LABELS`.
- [x] 10.6 The three repo gates, the Python tests, and `openspec validate
      stage-labels-96 --strict` — all green on the tree that lands.
- [x] 10.7 Commit by pathspec — `git add -- <your paths>`, then
      `git commit -- <your paths>`. Never `-a`, never `add -A`. Do not merge
      and do not push; the loop merges.

## 11. The two rules the vocabulary owns, and the escalation surfaces

These requirements state behaviour that already stands on this branch; each
task is the on-disk witness for one of them. Confirm by reading, and fix
only what the reading contradicts.

- [x] 11.1 `bin/_flywheel_inbox.py` — `set_stage(tracker, number, stage)`
      sweeps every other `stage:*` off before writing, returns whether it
      wrote, and touches no `closed:*` label. It is the one implementation
      of the rule and it sits beside the vocabulary.
- [x] 11.2 Both loops write through it: `BoltLoop.set_stage` delegates to
      `inbox.set_stage` and holds no sweep of its own; the intent loop's two
      writes — `stage:in-session` at dispatch, `stage:collected` at collect —
      call it too.
- [x] 11.3 The intent loop's `Writer` tracks removals beside additions, so
      `has_label` cannot report a label the same cycle removed and the
      shared sweep cannot re-remove it.
- [x] 11.4 `land_stage`'s item set is every unlanded item on the milestone —
      `i.is_open or i.merge_closed` — and the numbers taken from it drive the
      launch marker, the stall notify, the failure pause and the andon read.
- [x] 11.5 `dispatch_inbox`'s relay half reads unlanded items, open or
      `closed:merged`; its triage half stays open-issues-only.
- [x] 11.6 `tests/test_bolt_loop.py`, `tests/test_inbox.py` and
      `tests/test_intent_loop.py` pin all five: the shared sweep's label
      order, a no-op move writing nothing, a collected design item holding
      exactly one stage label, the landing pausing and reading an andon on an
      all-merge-closed milestone, and the relay carrying a merge-closed
      escalation while dropping a landed one.
- [x] 11.7 The three repo gates, the Python tests, and `openspec validate
      stage-labels-96 --strict` — all green on the tree that lands.
