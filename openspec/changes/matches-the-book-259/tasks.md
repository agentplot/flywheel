## 1. The guard-order test, against the guards that exist

- [x] 1.1 In `tests/test_derived_backlog.py`,
  `CharterTest.test_the_charter_guard_runs_after_topology_names_the_worktree`:
  replace the watch tuple with exactly the guards `BoltLoop.guards` calls
  — `guard_expand`, `guard_scaffold`, `guard_topology`, `guard_charter`,
  `guard_flip_consume`, `guard_stages` — dropping `guard_route`, which
  `main` removed. Keep the `seen[:4]` assertion unchanged: the
  proposition is that the charter guard runs after topology has named the
  worktree.
  *Done when* `python3 -m unittest tests.test_derived_backlog -k charter_guard`
  passes and the `AttributeError` is gone.
- [x] 1.2 In `bin/_flywheel_bolt_loop.py`, correct the comment in the
  defer predicate that reads "the same field `guard_route` keys on" so it
  names the derivation it meant — `backfill_parentage`'s `parent_batch`
  from the batches' sub-issues — without naming a method that no longer
  exists.
  *Done when* `grep -rn "guard_route" bin/ tests/` returns nothing.

## 2. The landing's two release conditions, written down

- [x] 2.1 Add the requirement "The operator's milestone close releases
  the landing, and the card hold is asked first" to
  `openspec/specs/flywheel-construction-stages/spec.md`, placed with the
  landing's other requirements (after "The landing keeps a tracker
  surface when every assertion is merge-closed"), with the five scenarios
  from this change's delta spec verbatim.
  *Done when* the requirement and its five `####` scenarios are in the
  main spec and `openspec validate --specs --strict` is green.
- [x] 2.2 Bring `landing_wanted`'s comment in `bin/_flywheel_bolt_loop.py`
  into line with the written requirement: it states the milestone-close
  condition and that a forced landing passes it, and names the
  `flywheel-construction-stages` requirement as the place that condition
  is specified. No behavior change — the test at the milestone-state
  branch and the `land != "force"` guard around it stay exactly as they
  are.
  *Done when* the comment cites the requirement by name and
  `sh scripts/test.sh` is unchanged in outcome by this task alone.
- [x] 2.3 In `holding_cards`'s docstring, keep "Asked before
  `landing_wanted`, and blind to `land`" and add the one fact the
  docstring does not yet carry: that the milestone-close condition
  survives beside the card hold, so a later reader does not take the card
  hold for the whole of the operator's release.
  *Done when* the docstring names both conditions and says which is asked
  first.

## 3. The fixtures that predate `main`'s gate

- [x] 3.1 In `tests/test_bolt_loop.py`, `LandingHoldTest.merged`: build
  the item with `milestone_state="closed"`, matching the fixtures
  elsewhere in this file that already carry the operator's close. Update
  the `at_the_landing` docstring so it says what the fixture now is — the
  operator's close made, so anything declining the landing here is the
  card hold and nothing else.
  *Done when* `test_a_held_run_lands_nothing_and_says_so_by_card_number`,
  `test_the_last_card_ruled_lets_the_landing_run` and
  `test_a_second_unit_expanded_later_does_not_buy_a_second_landing` pass.
- [x] 3.2 In `test_a_second_unit_expanded_later_does_not_buy_a_second_landing`,
  the two `item(3, ...)` / `item(4, ...)` released-work items and the
  second snapshot's items go the same way: the assertion under test is
  that released work declines the landing and that one landing then
  serves both units, not that an open milestone declines it.
  *Done when* the test's own `landing_wanted` assertion still fails for
  the released-work reason with the milestone closed.
- [x] 3.3 Leave
  `test_a_hold_is_reported_while_released_work_is_still_in_flight` as it
  is unless it fails: it builds its own snapshot and asserts
  `landing_wanted` is False for the released-work reason, which the
  milestone state does not reach.
  *Done when* it passes with no edit, or, if edited, its comment says why.

## 4. Coverage for the condition this change writes down

- [x] 4.1 Add a test to `tests/test_bolt_loop.py` covering the first
  scenario of the new requirement: every unlanded assertion
  `closed:merged`, no open unit card, milestone **open** — the run
  launches no landing session, writes no close or reclose, and reports no
  `done` landing.
  *Done when* the test fails if the `milestone_state == "open"` branch of
  `landing_wanted` is deleted.
- [x] 4.2 Add a test covering the forced-landing asymmetry: with the
  milestone open and no open card, `land="force"` lands; with an open
  card, `land="force"` is held and the landing line names the card. The
  second half may reuse the existing
  `test_a_forced_landing_is_held_by_the_same_card` if it already asserts
  it — check on disk before adding a duplicate.
  *Done when* both halves are asserted somewhere in the file and neither
  duplicates an existing test.
- [x] 4.3 Add a test covering the "both conditions outstanding" scenario:
  milestone open **and** an open unit card — the landing line reports the
  hold and names the card by number rather than naming the milestone.
  *Done when* the test asserts `report.landing.startswith("held")` and
  the card number in the line.

## 5. Green on the tree that would land

- [x] 5.1 `sh scripts/test.sh` green in this worktree — which is
  `bolt/matches-the-book` as rebased onto `main`, the only tree the
  landing cares about. Not a green run in isolation.
  *Done when* the run reports 0 failures and 0 errors.
- [x] 5.2 The three repo gates green: `sh scripts/validate-manifests.sh`,
  `node scripts/check-paths.mjs`, `node scripts/check-site.mjs`.
  *Done when* all three exit 0.
- [x] 5.3 `openspec validate matches-the-book-259 --strict` green, and
  the change's specs synced into `openspec/specs/` per task 2.1.
  *Done when* both `openspec validate matches-the-book-259 --strict` and
  `openspec validate --specs --strict` report valid.
