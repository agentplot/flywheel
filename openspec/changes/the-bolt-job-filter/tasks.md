## 1. The card the filter reads

Everything below turns on one object: `PlanCard` in
`bin/_flywheel_inbox.py`. Re-read it from disk first — this change is
sequenced after `planner-owns-the-milestone` (merged) and beside
`expansion-makes-a-unit`, so parts of this shape may already be there,
and a task is done when the file bears out the claim, not when it was
edited.

- [ ] 1.1 `PlanCard.bolt` answers the card's own `bolt/*` milestone and
      nothing else — the title-slug fallback goes. At this writing the
      property reads "falls back to the title slug for a card filed
      before milestones were the planner's" and returns
      `BOLT_PREFIX + self.slug`; after this task a card whose milestone
      is missing or is not a `bolt/*` milestone answers `None`.
      `PlanCard.slug` stays: it is still the card's parsed unit name,
      just no longer a source of milestones.
- [ ] 1.2 `PlanCard` carries the state of the milestone it sits on, the
      way `Item` already does (`milestone_state: str = "open"`), and
      `Tracker.snapshot` fills it from the same issue row it already
      reads for `milestone=item.milestone` in the `cards.append(
      PlanCard(...))` block. Default `"open"`, so every hand-built
      fixture and test card keeps its current meaning.

## 2. The job

`server_inbox` in `bin/_flywheel_inbox.py`, the block commented "An
approved plan card is a job for its bolt". Note the ordering that
matters: the Ready-batch loop runs before the card loop and `add()` is
`jobs.setdefault(...)`, so today the first reason for a milestone wins
— and a Ready card also arrives as a synthetic Ready `Batch` out of
`Tracker.snapshot` ("a batch may sit on the board without being an open
issue we listed above"), which means the card's own reason is the one
being lost.

- [ ] 2.1 A Ready card yields the `run` job for `card.bolt` only when
      that milestone is open — the same guard the Ready-batch set makes
      with `b.milestone_state == "open"`, and for the same stated
      reason: a job on a closed milestone collides with the `archive`
      job the same pass adds.
- [ ] 2.2 A card with no `bolt/*` milestone yields no job at all. No
      synthesized milestone name reaches the job list.
- [ ] 2.3 The card's reason wins for its milestone: after the pass, a
      milestone with a Ready card reports
      `plan card #<n> at Ready, awaiting expansion` even when a Ready
      batch or a `state:ready` item on that milestone was seen first.
      Whatever mechanism achieves it — running the card loop first, or
      letting the card reason overwrite — leave the job set otherwise
      deduplicated by `(milestone, kind)` exactly as it is now.
- [ ] 2.4 A card at Backlog still yields nothing, and the sweep's other
      clauses are untouched.

## 3. The count the operator sees

`server_rows` in `bin/flywheel`, the "waiting on the operator" block
built today from `flips = [b for b in snap.batches if b.status ==
"Backlog"]` — plan cards are not batches, so no card can appear there.
The snapshot `server_rows` already holds carries `plan_cards`.

- [ ] 3.1 Every open card at Backlog is listed under "waiting on the
      operator" with its number, its `bolt/*` milestone, and that the
      flip to Ready releases it — in the same shape as the existing
      batch line, so the block reads as one list.
- [ ] 3.2 A card at Ready is not listed there: its milestone already
      appears in the job rows, with the card as the reason (task 2.3).
- [ ] 3.3 A card at Ready carrying no `bolt/*` milestone is listed
      under "waiting on the operator" with that defect named — it
      yields no job, so this line is the only place it can surface.
- [ ] 3.4 The block still reads only: no start, no tracker write, and
      an unreadable tracker still returns the reported line rather than
      raising, per the function's own "a report never dies".

## 4. Tests

`tests/test_derived_backlog.py` holds the card filter's tests today —
`test_ready_card_is_a_server_job` and `test_backlog_card_is_not_a_job`,
over the `card()` helper whose default is
`milestone="bolt/observer-rework"`.

- [ ] 4.1 The Ready-card test asserts the job's `why` names the card,
      not only the milestone.
- [ ] 4.2 New: a Ready card with `milestone=None` (title unchanged)
      yields no job — the case that fails before task 1.1 and passes
      after.
- [ ] 4.3 New: a Ready card on a closed milestone yields no `run` job,
      mirroring `test_a_ready_batch_on_a_closed_milestone_is_not_a_run_job`
      in `tests/test_inbox.py`.
- [ ] 4.4 New: a milestone holding both a Ready card and a Ready batch
      yields one `run` job whose reason names the card.
- [ ] 4.5 New: the status surface — cards at Backlog listed as waiting
      on the operator, a Ready card not listed, a Ready card with no
      bolt milestone listed with its defect. Drive it at whatever seam
      `server_rows` already offers the suite; if none exists, keep the
      new seam to a pure function over `(snapshot, jobs)` so the test
      needs no tracker.
- [ ] 4.6 Each new test fails against the pre-change code and passes
      after. A test that is green both ways holds nothing.

## 5. Gates

- [ ] 5.1 `sh scripts/test.sh` green — the whole suite, not just the
      new tests.
- [ ] 5.2 `node scripts/check-paths.mjs` and `node scripts/check-site.mjs`
      green, per the project instructions in `openspec/config.yaml`.
- [ ] 5.3 `openspec validate the-bolt-job-filter --strict` green.
- [ ] 5.4 Commit by pathspec (`git add -- <paths>`,
      `git commit -- <paths>`) — never `-a`, never `add -A`; a sibling
      session may share this tree.
