## 1. Re-read the neighbours from disk before trusting a claim

Every path and quoted phrase below was read on `bolt/stage-labels` at
`553c7e3`. Siblings on this bolt are live and `main` moves under it; locate
every site by heading, function name or quoted phrase, never by line number.

- [ ] 1.1 Re-read `bin/flywheel-setup`'s `LABELS` table and confirm it still
      defines only `type:*`, `state:*`, `closed:*`, `unit`, `elaboration` and
      `needs-operator`, with no `stage:*` name. If a `stage:*` name is
      already there, stop — someone else has moved it.
- [ ] 1.2 Re-read `bin/_flywheel_inbox.py`'s vocabulary block and confirm
      its header comment still reads "The vocabulary. One enumeration,
      bin/flywheel-setup:57-90."
- [ ] 1.3 Re-read `bin/_flywheel_bolt_loop.py` and confirm `guards` still
      runs `guard_scaffold`, `guard_flip_consume`, `guard_route` and returns
      `(actions, failure)`; that `change_validates`, `branch_has_commits` and
      `branch_merged` are unchanged; and that `cycle` still runs
      `spec_stage → build_stage → verify_stage → merge_stage`.
- [ ] 1.4 Re-read `bin/_flywheel_intent.py` and confirm `is_complete` still
      returns `None` for an unconfigured signal, that `COMPLETION_SIGNALS`
      still holds `closed`/`label`/`board`, and that `land` still tests
      completion batch-wide.
- [ ] 1.5 Re-read `design/loop-programs.md`'s `## Open questions (three)`
      section and confirm R1 is still an open bullet reading "a state label
      the operator sets, a board Status, or closing the items — pick one so
      the loop has one filter."
- [ ] 1.6 Re-read `skills/_reference/tracker.md` invariant 5 (the state
      ladder) and the board bullet naming "a quick bolt's lone born-ready
      item (at Ready from birth, via `flywheel-board`)".
- [ ] 1.7 Confirm `openspec/changes/stage-labels/bolt.md` is present on this
      branch and that its Merge criteria still name the `flywheel-setup`
      label convergence.

## 2. The label set — before any loop writes one

- [ ] 2.1 Add every name in the `stage:*` set — `stage:planned`,
      `stage:built`, `stage:verified`, `stage:merged`, `stage:in-session`,
      `stage:done`, `stage:collected` — to `bin/flywheel-setup`'s `LABELS`,
      each with a colour and a description in the style of the existing
      entries. Do not touch any existing entry.
- [ ] 2.2 Add the matching constants to `bin/_flywheel_inbox.py`'s
      vocabulary block, beside `READY`/`IN_PROGRESS`/`QUEUED`, so the loops
      compare against names rather than string literals.
- [ ] 2.3 Confirm `ensure_labels` needs no change: it skips a name already
      on the repo and rewrites nothing. Run it in a way that shows the
      idempotence (a second run reports all present) and record what you ran.
- [ ] 2.4 Run the convergence against `agentplot/flywheel` and record the
      created names in your item comment. This is a merge criterion of the
      bolt and must be green before any item carries a stage label.

## 3. The bolt loop — the four construction stages (#96)

- [ ] 3.1 Give `LoopConfig` a declared stage set, defaulting to
      `spec, build, verify, merge, land` so the three existing types are
      unchanged, and read a `stages:` key from the `loop:` block in
      `read_schema_config`. `parse_loop_block` already handles flow lists;
      confirm that on the real `schema.yaml` text rather than assuming it.
- [ ] 3.2 Write `stage:planned` on each item of the batch when `spec_stage`
      returns ok — and on the plan-mode path when the plan is approved,
      which is where `plan_mode_build` leaves the loop after an `APPROVED`
      verdict.
- [ ] 3.3 Write `stage:built` when `build_stage` returns ok and its
      deliverables check has passed, `stage:verified` when `verify_stage`
      returns clean, and `stage:merged` when `merge_stage` confirms ancestry.
      Each write follows the objective check already made at that boundary;
      none is taken from a session's report.
- [ ] 3.4 Make each stage write remove any earlier `stage:*` label from the
      same item, so an item carries exactly one.
- [ ] 3.5 Add a stage-reconciliation guard to `guards`, running before any
      work, that re-derives `stage:built` and `stage:merged` for the
      milestone's open items using `branch_has_commits` and `branch_merged`
      against `build/<slug>` branch names taken from `analyse`. It records
      its writes in `actions` like every other guard.
- [ ] 3.6 Leave `stage:planned` and `stage:verified` out of the
      reconciliation, and say why in the guard's docstring — neither has a
      witness the tree can answer.
- [ ] 3.7 Confirm no stage write touches a `closed:*` label and that
      `land_stage` still closes with `closed:done` and the landing SHA.

## 4. The intent loop — completion (#97)

- [ ] 4.1 Write `stage:in-session` on each item of a batch in
      `dispatch_batch`, alongside the existing `state:ready` →
      `state:in-progress` relabel.
- [ ] 4.2 Replace `is_complete` and `COMPLETION_SIGNALS` with a single
      per-item test on `stage:done`. Delete `_done_closed`, `_done_board`,
      `R1_UNRESOLVED`, and the unknown/`None` third value.
- [ ] 4.3 **BREAKING** — remove `--completion-signal`, `--done-label` and
      `--done-status` from `bin/flywheel-intent-loop`, the matching `Config`
      fields, and their `config_fault` checks. Nothing else in the repo
      passes them; confirm that with a grep and record it.
- [ ] 4.4 Rework `land` so each item carrying `stage:done` is collected,
      marked `stage:collected`, and closed independently of its siblings.
      An item already carrying `stage:collected` is skipped.
- [ ] 4.5 Keep `merge_session` and `runner.close(handle)` session-scoped:
      they run once every item the session carries has reached
      `stage:collected`. The stalled path and the andon path still leave the
      pane open and merge and close nothing.
- [ ] 4.6 Give the design-session skills the pane half of the flip: a
      session told by the operator that an item is done writes `stage:done`
      to that item and settles, and does not collect, merge or close
      anything itself.
- [ ] 4.7 Update `design/loop-programs.md` — record R1 as resolved by the
      operator-set `stage:done` label, and remove it from the open-questions
      section rather than leaving the three candidates offered as a choice.
      Do not annotate what changed; the record reads as current state.

## 5. Every release creates a unit parent (#98)

- [ ] 5.1 Make the born-ready release path create one `unit` parent on the
      bolt's milestone with the released items as its sub-issues.
      `bin/flywheel-batch --kind unit` already does the composing, the
      sub-issue attachment, the project add and the field defaults; prefer
      calling it over reimplementing any of that.
- [ ] 5.2 Put the born-ready unit parent at Status **Ready** from birth —
      the operator's word at triage is the approval. `flywheel-batch` sets
      Backlog and states it never sets Ready, so the Ready move belongs to
      the release path, not inside that tool.
- [ ] 5.3 Confirm the handoff birth path already produces the same shape and
      leave it at Backlog. If it does not, make it, and say in your item
      comment which it was.
- [ ] 5.4 Stop adding the released items themselves to the board on the
      born-ready path; the parent is the row.
- [ ] 5.5 Confirm an already-batched item is skipped rather than fatal —
      `flywheel-batch` prints "already in batch" and continues — and that
      running the release twice creates no second parent.
- [ ] 5.6 Update `skills/_reference/tracker.md`'s board bullet, which today
      names "a quick bolt's lone born-ready item (at Ready from birth, via
      `flywheel-board`)", and the worked example under `## The quick bolt`,
      which shows a lone `#40` on the board with no parent.
- [ ] 5.7 Do **not** implement sub-issue check-off timing. It is out of
      scope for the reason `design.md` gives, and a queued tracker item owns
      the decision.

## 6. `bolt-direct` (#99)

- [ ] 6.1 Add `schemas/bolt-direct/schema.yaml`, modelled on
      `schemas/bolt-quick/schema.yaml`: `loop:` declaring strategy `ff`, the
      stage set `spec, build, merge, land`, empty extensions, and hooks
      naming only boundaries these stages create — `post-verify` is not
      among them.
- [ ] 6.2 Carry the same warning comment the sibling schemas carry about
      openspec 1.8.0 stripping the `loop:` block, since it applies verbatim
      to this file.
- [ ] 6.3 Write the type's `artifacts` and `apply` instruction blocks in the
      shape its siblings use, stating that this type runs no verify stage
      and that the repo's merge gate is unaffected by the type.
- [ ] 6.4 Make `cycle` run the stages the bound config names, so a
      `bolt-direct` bolt goes spec → build → merge with no verify session
      launched, and no `stage:verified` written.
- [ ] 6.5 Confirm `bin/install-schemas` publishes the new directory with no
      change — it copies the tree — and record what you checked.
- [ ] 6.6 Add `bolt-direct` to `schemas/README.md`'s list of construction
      types and to `design/loop-programs.md`'s `## The bolt types` section.
- [ ] 6.7 Confirm the merge and landing paths are untouched: `merge_stage`
      and `land_stage` run `wt merge` through the repo's hooks whatever the
      type, and no new flag can suppress them.

## 7. Tests

- [ ] 7.1 `tests/test_bolt_loop.py` — the four boundary writes; exactly one
      `stage:*` per item; reconciliation supplying `stage:built` for a commit
      the loop never saw written; reconciliation walking a too-far label
      back; the dry-cycle property holding with the new guard (two cycles
      against an unchanged tracker and tree, the second writing nothing).
- [ ] 7.2 `tests/test_bolt_loop.py` — a `bolt-direct` config runs no verify
      stage and its items never carry `stage:verified`.
- [ ] 7.3 `tests/test_intent_loop.py` — `stage:in-session` at dispatch;
      `stage:done` on two of three items collects and closes exactly those
      two; the `sess/*` merge and the pane close waiting for the third;
      `stage:collected` making a second collect a no-op.
- [ ] 7.4 `tests/test_intent_loop.py` — remove
      `test_no_signal_configured_is_unknown_rather_than_incomplete` and
      `test_the_r1_note_is_on_every_run_that_names_no_signal` with the
      behaviour they pin. Keep
      `test_a_settled_session_is_not_a_finished_one`: a settled pane is
      still not a finished session, and it is now `stage:done` that decides.
- [ ] 7.5 `tests/test_inbox.py` — the stage constants exist and every one is
      defined in `flywheel-setup`'s `LABELS`, so the two enumerations cannot
      drift.

## 8. The gates, on the tree that lands

- [ ] 8.1 `sh scripts/validate-manifests.sh` green.
- [ ] 8.2 `node scripts/check-paths.mjs` green.
- [ ] 8.3 `node scripts/check-site.mjs` green.
- [ ] 8.4 The repo's Python tests green.
- [ ] 8.5 `openspec validate stage-labels-96 --strict` green.
- [ ] 8.6 Commit by pathspec — `git add -- <your paths>`, then
      `git commit -- <your paths>`. Never `-a`, never `add -A`. Do not merge
      and do not push; the loop merges.
