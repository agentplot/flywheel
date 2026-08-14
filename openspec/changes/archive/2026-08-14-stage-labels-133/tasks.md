## 1. Re-read the neighbours from disk before trusting a claim

Every path and quoted phrase below was read on `build/stage-labels-133` at
`eae4984`, which holds `stage-labels-96` merged and archived. Siblings on this
bolt are live and `main` moves under it; locate every site by heading,
function name or quoted phrase, **never by line number**. The items this
change serves cite paths under `openspec/changes/stage-labels-96/specs/`,
which no longer exist — the same content is under `openspec/specs/`.

- [x] 1.1 Confirm `openspec/specs/` holds `flywheel-stage-labels`,
      `flywheel-construction-stages`, `flywheel-release-unit-parent`,
      `flywheel-bolt-direct` and `flywheel-design-session-completion`. If any
      is missing, stop — this change is written against a tree that has
      `stage-labels-96` merged, and a tree without it is not that tree.
- [x] 1.2 Confirm `bin/_flywheel_bolt_loop.py` still has `guard_stages`
      calling `self.branch_merged(branch)`, and that `batch_merged`,
      `branch_advanced` and `refs/flywheel/base` are still **absent** from
      `bin/`. If they are present, the rebase has happened — go to task 2.
- [x] 1.3 Confirm `bin/flywheel-bolt-loop` still resolves the type as
      `args.type_name or binding.get("schema") or "bolt-quick"` and passes
      only the binding to `refuse_stage_declaration`.
- [x] 1.4 Confirm `set_stage` in `bin/_flywheel_inbox.py` still returns
      before its sweep when the item carries the target, and that its
      docstring still justifies that with "an item already at the target
      carries no other stage by this function's own invariant".
- [x] 1.5 Confirm `Writer` in `bin/_flywheel_intent.py` still keeps `_added`
      and `_removed`, and that reassigning `writer.snapshot` after a re-read
      clears neither.
- [x] 1.6 Confirm `skills/_reference/herdr.md` still gives the flip as a
      literal `gh issue edit … --remove-label stage:in-session --add-label
      stage:done`, and that `bin/` holds no stage command.
- [x] 1.7 Confirm `compose_unit` in `bin/_flywheel_intent.py` is still called
      with the intent loop's own milestone and with the handoff item
      prepended to the released numbers, and that
      `tests/test_intent_loop.py` still pins "the handoff item and the
      released assertions".
- [x] 1.8 Confirm `server_inbox` in `bin/_flywheel_inbox.py` still adds a
      "run" job for every `ready_batch_milestones` entry with no
      milestone-state test, while the per-item loop above it tests
      `item.milestone_state != "open"`.

## 2. The re-derivation guard, and the rebase it waits on

**Ordering matters and is the whole content of D3.** `main` fixed `#164` by
adding a stronger predicate beside the weak one, not by hardening the weak
one, so the rebase resolves cleanly and silently leaves `guard_stages` on
bare ancestry. Do not write a second predicate here; port the call.

- [x] 2.1 Establish that this branch has `main`'s `#164` fix available —
      `main` an ancestor of `HEAD`, and `batch_merged` / `branch_advanced` /
      `refs/flywheel/base` present in `bin/_flywheel_bolt_loop.py`. If the
      rebase has not happened, **stop and raise the andon**: writing the
      predicate here creates the conflicting duplicate the finding warns
      against, and no further round inside this batch fixes that.
- [x] 2.2 Point `guard_stages`' merged test at that predicate. It already
      iterates the batches `analyse(...)` returns, so the object the
      predicate takes is in hand at the call site.
- [x] 2.3 Re-word `guard_stages`' docstring, which says an item whose branch
      is an ancestor of the bolt branch is merged. Say what the guard now
      asks, and say why bare ancestry is not it — an untouched branch's tip
      is an ancestor of everything it was cut from.
- [x] 2.4 Check the boundary write in `cycle` against the same question. It
      is downstream of real merge work so it is likely already sound;
      confirm it rather than assume it, and record which it was.
- [x] 2.5 Pin it: a batch whose branch exists, is an ancestor of the bolt
      branch, and carries no work of its own gets **no** `stage:merged` and
      is **not** closed `closed:merged`. Add the absent-branch case beside
      it. Done when both fail against the pre-2.2 code.

## 3. The command-line type is refused when it disagrees with the binding

- [x] 3.1 In `bin/flywheel-bolt-loop`, refuse a `--type` that disagrees with
      the type the binding on disk records. Name both types in the message,
      and name the rule the way `refuse_stage_declaration` does — the bolt
      type is the scrutiny the release approved.
- [x] 3.2 Keep `--type` working where the binding records no schema: there
      is no approval for it to contradict, and refusing would leave an
      unbound bolt unable to run.
- [x] 3.3 Pin all three: disagreement raises, agreement runs, no binding
      runs. Done when the first fails against today's precedence.

## 4. The shipped types' declarations are held on disk

- [x] 4.1 Add `bolt-direct` to `tests/test_bolt_loop.py`'s
      `test_each_shipped_type_declares_the_strategy_its_stages_run`, with
      the strategy and invocations `schemas/bolt-direct/schema.yaml`
      declares.
- [x] 4.2 Make the cycle test that proves `bolt-direct` runs no verify load
      the real schema through `load_type` instead of building a
      `LoopConfig` by hand. A config built in a test asserts what its author
      believed; the point is to hold what the plugin ships.
- [x] 4.3 Confirm the shipped stage set is covered too, not only strategy
      and invocations — a schema edited to add `verify` back to
      `bolt-direct` must fail something.

## 5. The one-stage rule reaches the pane

- [x] 5.1 Narrow `set_stage`'s early return to "already at the target **and**
      carrying no other stage". An item carrying the target plus another
      ends carrying the target alone. Keep the idempotent no-write for the
      clean case — the dry-cycle property depends on it.
- [x] 5.2 Invalidate `Writer._added` wherever `_removed` is invalidated, so
      neither outlives the snapshot behind it. Reassigning
      `writer.snapshot` is the moment.
- [x] 5.3 Add the command that makes the flip from a pane — one item, one
      stage, the same sweep `set_stage` holds, no import of the loops'
      internals. It goes in `bin/`, which an installed plugin puts on a
      user's PATH; that bar is met, and the implementation belongs under
      `tools/` per this repo's split.
- [x] 5.4 Replace the hand-built recipe in `skills/_reference/herdr.md` with
      that call, keeping the sentence that says a stage move replaces the
      previous one.
- [x] 5.5 Follow the recipe's echoes: both agent profiles
      (`agents/flywheel-design-session.md`,
      `agents/flywheel-interactive-session.md`) and all six design-session
      skills (`planning`, `research`, `writeback`, `interactive`,
      `prototype`, `handoff`). Each points at the call; none spells out
      which predecessor to remove.
- [x] 5.6 Pin the case the hard-coded recipe got wrong: an item at
      `stage:collected` flipped done ends carrying `stage:done` alone. Pin
      the sweep-on-target case from 5.1. Extend
      `RecordConsistencyTest`'s prose check so it holds the *call* being
      named rather than only that a removal is mentioned.

## 6. The unit parent's spec is corrected to the two shapes that exist

No `bin/` change — the tree is the considered choice in each case.

- [x] 6.1 Apply the `flywheel-release-unit-parent` delta: the born-ready
      path on the bolt milestone with exactly the assertions; the handoff
      path on the intent milestone with the handoff item among the
      sub-issues, and the reason it must be there — the amend path recovers
      the open unit through it.
- [x] 6.2 Apply the bar-denominator correction. State what the bar counts on
      each path; do not compute a corrected figure, which the same
      capability forbids in "No second progress figure exists".
- [x] 6.3 Confirm no neighbour is left disagreeing: the sibling requirement
      in `flywheel-construction-stages` about the landing's tracker surface,
      and `skills/_reference/tracker.md`'s literal graph, both already
      describe the handoff shape. Read both and record that they agree.

## 7. A unit parent is closed, and a Ready one stops being a job

- [x] 7.1 Close the release's unit parent at the landing, with one
      `closed:*` reason. The bar is full by then and every assertion has
      been upgraded, so there is nothing left for the container to gate.
- [x] 7.2 Touch no sub-issue while doing it: the assertions' closes belong
      to the merge boundary and the landing.
- [x] 7.3 Give `server_inbox`'s Ready-batch branch the milestone-state test
      the per-item loop above it already makes, so a closed milestone adds
      no "run" job to collide with the `archive` job the same sweep adds.
- [x] 7.4 Pin both: a landed bolt's parent is closed and its milestone
      reports no job; a Ready unit on an **open** milestone still starts its
      loop exactly as today.

## 8. The skipped-stage scenario

- [x] 8.1 Apply the `flywheel-construction-stages` delta's skipped-stage
      scenario. The code is already right — the four boundary writes test
      whether the stage `ran`, fixed at `ecad0e5` — so this is the spec
      catching up, not a behaviour change.
- [x] 8.2 Confirm on disk that the boundary writes still test `ran` rather
      than `ok`, and that the two tests pinning it are still present. If
      they are not, this is a behaviour change and the task is bigger than
      stated — say so rather than widening it silently.

## 9. Test hygiene

- [x] 9.1 Move `tests/test_inbox.py`'s `if __name__ == "__main__":` block to
      the end of the file, below `RecordConsistencyTest`. Measure before and
      after: `python3 tests/test_inbox.py` should report the same count as
      the class list implies, and `sh scripts/test.sh` should be unchanged.
- [x] 9.2 Check every other file under `tests/` for the same misplacement
      and fix any found.
- [x] 9.3 Add one `LandingTest` case on a **worktree-bearing** type
      asserting the session-teardown merge fires exactly once when the last
      item reaches `stage:collected`. `land`'s completion tests all use
      `research`, whose type has no worktree, so `merge_session` is never
      reached on that path; the resume path is already covered.

## 10. Verify the thirteen already answered, and record the evidence

These were filed against `build/stage-labels-96` and answered by that
change's own go-fix rounds before merge-back. Each was re-read at `eae4984`
while this change was written. Re-check each on the tree you are building
against — a claim about a neighbour is only as good as its last read — and
comment the evidence on the item. **A gap found here is filed as a new item,
not absorbed into this change.**

- [x] 10.1 `#133` — `land_stage`'s item set is `[i for i in on_milestone if
      i.is_open or i.merge_closed]` and its `numbers` covers all of them, so
      the pause, the andon read, the notify and the launch marker survive an
      all-merge-closed milestone.
- [x] 10.2 `#134` — the intent loop's two stage writes go through
      `set_stage`, so it moves the leading edge rather than accumulating.
- [x] 10.3 `#135` — no `STUB` prose survives in `schemas/`, and all four
      bolt schemas' `apply.instruction` describe the landing as upgrading
      `closed:merged` to `closed:done`.
- [x] 10.4 `#136` — `refuse_stage_declaration` exists and is wired into
      `bin/flywheel-bolt-loop` ahead of `resolve_plan_mode`; and
      `server_inbox`'s `closed:merged` branch is bolt-milestones-only.
- [x] 10.5 `#143` — `design/loop-programs.md` and
      `skills/construction/SKILL.md` state the merge-back close and the
      landing's upgrade, pinned by `RecordConsistencyTest`.
- [x] 10.6 `#144` and `#145` — both agent profiles and all six
      design-session skills name `stage:done` **and** the removal, and
      `skills/_reference/herdr.md` carries the recipe. (The residual — that
      the recipe hard-codes one predecessor — is this change's task 5.)
- [x] 10.7 `#146` — `read_binding` reads dash lists as well as scalars and
      flow lists, so a block-style `stages:` is refused rather than ignored.
- [x] 10.8 `#148` and `#158` — `collect_plan` excludes an item carrying
      `needs-operator`, and `land` marks **every** item of the batch on both
      the stall path and the andon path, so no flipped sibling is
      collectable under a pause.
- [x] 10.9 `#149` and `#157` — `dispatch_batch` records the session name per
      item and `session_named` reads it back, so the teardown is keyed on
      the session; `resume_collect` merges the branch and closes the pane
      when the last sibling lands.
- [x] 10.10 `#150` — `flywheel-stage-labels`' first requirement heading
      reads seven, its table has seven rows, and `bin/flywheel-setup`'s
      `LABELS` and `bin/_flywheel_inbox.py`'s `STAGE_LABELS` both hold
      seven. The two miscounts the item also names are in
      `stage-labels-96`'s own `design.md` and `proposal.md`, now under
      `openspec/changes/archive/`; **leave them.** An archived change is the
      record of what was decided then, not a document kept current.
- [x] 10.11 `#151`'s second half and `#154`'s framing — `LoopConfig.validate`
      raises on an unknown stage name and is called at the entry point.
- [x] 10.12 Comment the evidence on each of the thirteen items, naming the
      symbol or quoted phrase read and the commit read at. Do not close
      them — the loop closes on evidence, and this is the evidence.

## 11. Gates and the record

- [x] 11.1 `openspec validate stage-labels-133 --strict` green.
- [x] 11.2 `sh scripts/test.sh` green, and the count higher than before by
      the cases this change adds. A green suite with an unchanged count
      means the new tests are not being collected — check task 9.1 first.
- [x] 11.3 `devenv shell -- gates` green: `sh scripts/validate-manifests.sh`,
      `node scripts/check-paths.mjs`, `node scripts/check-site.mjs`. The
      second is the one task 5.3's new command can break, by referencing a
      plugin path other than `${CLAUDE_PLUGIN_ROOT}/<path>`.
- [x] 11.4 Commit by pathspec — `git add -- <paths>` then
      `git commit -- <paths>`, flags before the `--`. Never `-a`, never
      `add -A`: this worktree shares a git index with siblings on this bolt.
- [x] 11.5 Footer-reference every item the commit serves (`Refs: #133 …`) and
      never a closing keyword. Items close through the loop, with evidence
      and a `closed:*` reason.
