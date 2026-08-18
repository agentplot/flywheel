## 1. Read the tree before changing it

- [ ] 1.1 Re-read `guard_charter`'s unit scan and its `--dry-run`,
      fixture-tracker, write and commit-failure branches in
      `bin/_flywheel_bolt_loop.py`, and `PlanCard.slug` in
      `bin/_flywheel_inbox.py`. Done when you can name, from the files,
      which of design.md — Context still holds. Where it does not, say so
      in the report rather than building over it.
- [ ] 1.2 Confirm from `guards()`, `cycle()` and `run()` that a reason
      string returned by `guard_charter` becomes `result.halted`, reaches
      `ledger.note("HALTED — …")`, and is printed by
      `bin/flywheel-bolt-loop`. Done when the pause path this change uses
      is the one the files bear out, and nothing new has to be plumbed.
- [ ] 1.3 Re-read `CharterTest`, `FakeGit`, `NotTheFixtureTracker` and the
      `unit_item` helper in `tests/test_derived_backlog.py`. Done when you
      know how to build a unit item whose title parses no slug without
      changing `unit_item`'s default.

## 2. The guard reports the unnameable unit

- [ ] 2.1 The unit scan collects, alongside the units it will write, every
      `unit`-labeled item on the milestone whose title parses no slug —
      in item order, keeping each item's number and its title exactly as
      the tracker carries it. The parse stays `PlanCard.slug`; no second
      regex is introduced. Done when the scan holds both lists.
- [ ] 2.2 `guard_charter` returns a reason naming every such unit — each by
      number and by its verbatim title — and stating in prose what a unit
      title must carry for a file to be named from it. One reason for all
      of them, not one pass per card. Done when a milestone with two bad
      cards produces one string naming both.
- [ ] 2.3 The reason is returned on a pass that writes nothing of its own
      as well as on one that writes: the `--dry-run` branch reports the
      pause and its reason among its actions and returns it, and the
      fixture-tracker branch returns it while still writing no tree. Done
      when neither branch can report "nothing to write" over an unnameable
      unit.
- [ ] 2.4 On a pass that has nameable units to write, those files are
      written and committed first and the reason is returned after — and
      where that commit failed, the commit-failure reason is the one
      returned. Done when a milestone carrying one good and one bad unit
      ends the pass with the good unit's file at HEAD and the cycle halted
      on the bad one.
- [ ] 2.5 A milestone whose unit titles all parse is untouched: the guard's
      dry-cycle property, its idempotency keyed on HEAD, and its
      torn-write repair all behave exactly as before. Done when nothing in
      the existing `CharterTest` needed changing to stay green.
- [ ] 2.6 Replace the scan's "left alone here" comment with what the code
      now does, and say why a pause rather than a log: the record, not the
      loop log, is where facts originate.

## 3. Tests

- [ ] 3.1 A unit whose title parses no slug: the cycle halts, and the
      reason names that unit's number and its title verbatim and says what
      a unit title must carry. Cover at least a title with a capital
      letter and one with no `Unit:` prefix at all.
- [ ] 3.2 Two unnameable units on one milestone: one reason names both, in
      item order.
- [ ] 3.3 One nameable unit beside an unnameable one: the nameable unit's
      file is written, committed by pathspec, and reaches HEAD, and the
      guard then returns the reason naming the other.
- [ ] 3.4 A failed commit on the same pass: the commit-failure reason is
      what comes back, and the pass after the commit succeeds returns the
      unnameable unit's reason.
- [ ] 3.5 `--dry-run` over an unnameable unit: the reason is among the
      reported actions and is returned, and no file is written and no
      commit is made.
- [ ] 3.6 A fixture-tracker run over an unnameable unit: the reason is
      returned, and no `git add` or `git commit` runs against anyone's
      checkout.
- [ ] 3.7 The pause reaches the operator: a guard reason returned from
      `guard_charter` shows up as the cycle's `halted`. Assert it through
      `guards()` or `cycle()` rather than on the returned string alone, so
      a reordering that swallowed the reason fails.
- [ ] 3.8 `python3 -m unittest discover tests -v` green, and the repo's
      gates — `node scripts/check-paths.mjs`, `node scripts/check-site.mjs`,
      `bash scripts/validate-manifests.sh` — green.

## 4. Record

- [ ] 4.1 `openspec validate an-unparseable-unit-title-says-so --strict`
      green, and every task above checked off against what the files bear
      out rather than what was edited.
