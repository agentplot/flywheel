## 1. Expansion reads the card's milestone and writes none

- [ ] 1.1 In `bin/_flywheel_bolt_loop.py`, narrow `guard_expand`'s
  selection to `c.at_ready and c.milestone == self.params.milestone`, so
  the guard reads the card's own home rather than `PlanCard.bolt`'s
  title fallback. Done when a Ready card carrying no `bolt/*` milestone,
  or another bolt's, is not selected.
- [ ] 1.2 Drop `create_milestone` and the `set_milestone` branch from
  `_expand_card`; the label swap, the `stale` drop, the items, the
  sub-issue attachments and `clear_board_status` stay. Done when
  expansion's writes contain no milestone write.
- [ ] 1.3 Rewrite `guard_expand`'s docstring over the unit shape — the
  approved card becomes a unit on a milestone the planner already wrote,
  one card per approval over the bolt's life, idempotent because an
  expanded card no longer carries `plan`. Done when no sentence in the
  guard claims expansion creates the bolt.
- [ ] 1.4 Update `tests/test_derived_backlog.py::ExpansionTest`:
  `test_expansion_full_path` asserts neither `create_milestone` nor
  `set_milestone` is among the writes (the rest of its assertions hold),
  and a new case expands a second card on the same milestone and asserts
  the first unit and its items are untouched. Done when
  `python3 -m unittest tests.test_derived_backlog -v` is green.
- [ ] 1.5 Add a case for a Ready `plan` card whose milestone is another
  bolt's (or absent): `guard_expand` returns `None` and writes nothing.

## 2. The defer predicate follows the predecessor's merge

- [ ] 2.1 Replace `_expand_card`'s
  `self.tracker.closed_with(blocker, inbox.CLOSED_DONE)` test with the
  merged predicate: a blocker satisfies expansion when it is closed, or
  when it is an open `unit` every one of whose sub-issues is closed. An
  unexpanded blocker, and a unit with an open sub-issue, both defer.
  Done when the wait is still recorded via `self.ledger.note` and the
  guard still returns `None` (a defer is not a pause).
- [ ] 2.2 Read the blocker's state from the snapshot the guard already
  holds where possible, and keep the tracker read the fallback for a
  blocker off the milestone. Done when a defer decision costs no
  per-blocker network call for a sibling unit on this milestone.
- [ ] 2.3 Rewrite the docstring line "a card blocked by an issue not yet
  closed done defers" and state why closure is the wrong predicate under
  bolt-of-units — a unit card closes only after the landing, and the
  landing waits on the cards.
- [ ] 2.4 Replace `test_blocked_by_unlanded_predecessor_defers` and
  `test_blocked_by_landed_predecessor_expands` with the three cases the
  spec names: unexpanded blocker → defer and no writes; expanded blocker
  with an open sub-issue → defer; expanded blocker with every sub-issue
  closed and the blocker itself still open → expands. Done when
  `tests/test_derived_backlog.py` covers all three and is green.
- [ ] 2.5 Check the fixture tracker in `bin/_flywheel_bolt_loop.py`
  (`FixtureTracker`) exposes sub-issue state for a blocker; extend the
  fixture shape only as far as the three cases need.

## 3. The charter carries every expanded unit

- [ ] 3.1 Add `guard_charter` to `BoltLoop`, ordered after
  `guard_topology` in `guards()` so `params.bolt_worktree` names the bolt
  branch's worktree. It compares the `# Unit: <slug>` headings in
  `openspec/changes/<slug>/bolt.md` against the `unit`-labeled issues on
  the milestone and appends each missing unit's card body verbatim under
  its own `# Unit: <slug>` heading, in card-number order, after whatever
  the charter already holds. Done when a bolt whose charter already
  names every unit produces no action.
- [ ] 3.2 Commit the charter write by pathspec on the branch the record
  lives on (`git add -- openspec/changes/<slug>/bolt.md` then
  `git commit -- …` in `params.bolt_worktree`), never `-a` and never
  `add -A`. Done when a charter append is one commit touching one path.
- [ ] 3.3 Record the append in `actions` (so the loop's STOP condition
  stays honest) and in the ledger, naming the unit whose section landed.
- [ ] 3.4 Narrow `guard_scaffold`'s work order line "If the milestone's
  unit parent carries a plan document as its body" to name the unit it
  copies — the lowest-numbered `unit` on the milestone — and note that
  later units' documents are appended by the loop, not by the session.
  Done when the order is unambiguous on a milestone carrying several
  units.
- [ ] 3.5 Add tests: a charter missing a unit's section gains it; a
  second pass writes nothing; a hand-edited existing section is not
  overwritten; a bolt with no unit cards leaves the charter alone.

## 4. The record and the gates

- [ ] 4.1 Confirm the no-Team refusal comment in `_expand_card` says the
  **unit** is unroutable, and that the refusal leaves the bolt's other
  units untouched.
- [ ] 4.2 Run the repo's gates — `sh scripts/test.sh`,
  `node scripts/check-paths.mjs`, `node scripts/check-site.mjs` — and
  `openspec validate expansion-makes-a-unit --strict`. Done when all are
  green.
- [ ] 4.3 Commit by pathspec: the change's artifacts, the loop, and the
  tests, each `git add -- <paths>` and `git commit -- <paths>` on this
  branch. Never `-a`, never `add -A`.
