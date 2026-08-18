## 1. Read the tree before changing it

- [ ] 1.1 Re-read `_predecessor_in` and `_expand_card` in
      `bin/_flywheel_bolt_loop.py`, and `Tracker.snapshot`,
      `Tracker.closed`, `Tracker.sub_issues`, `TrackerSnapshot.batch`,
      `Batch.sub_issues` and `backfill_parentage` in
      `bin/_flywheel_inbox.py`. Done when you can say, from the files,
      which of design.md — Context still holds. Where it does not, say so
      in the report rather than building over it.
- [ ] 1.2 Confirm from `guard_expand`'s call path — `cycle()` and whatever
      builds the snapshot it is handed — that the expansion guard always
      runs under `snapshot(milestone)` with `with_edges=True`, so a
      `unit`-labelled blocker on this milestone always has a `Batch` row
      carrying its sub-issues. Done when the claim is one you read rather
      than one you assumed; if any caller runs it edgeless, stop and
      report before building.
- [ ] 1.3 Re-read `TrackerSnapshot.from_fixture`, `FixtureTracker` and
      `ExpansionTest`'s `snap`, `card_item`, `unit_item` and `work_item`
      helpers. Done when you know why a fixture snapshot carries no `Batch`
      row and shows closed items, and how a test builds each of the two
      shapes the tasks below need.

## 2. The predicate reads what the predecessor owns

- [ ] 2.1 `_predecessor_in` takes the blocker's work items from the
      sub-issues it owns — `snapshot.batch(number).sub_issues` where the
      snapshot has a row, and one `tracker.sub_issues(number)` read where
      it does not — instead of scanning `snapshot.items` by
      `parent_batch`. Done when no reading of the answer depends on which
      items the snapshot happens to carry.
- [ ] 2.2 Each owned sub-issue is answered from the snapshot when the
      snapshot carries it (`is_open`), and by one `tracker.closed(child)`
      read when it does not. Done when a blocker whose members are all
      visible makes no tracker read at all.
- [ ] 2.3 A blocker owning at least one sub-issue is "all in" exactly when
      every one of them is closed; a blocker owning none is not in. Done
      when `bool(work)` as a proxy for "was this expanded" is gone and the
      `unit`-label test above it is the only thing answering that.
- [ ] 2.4 The predicate returns, alongside its verdict, which state it
      found — the blocker not expanded, the blocker owning no work items,
      or how many of its items are still open — and `_expand_card`'s
      deferral note and log line carry that reason instead of the fixed
      phrase "whose work is not all in". Done when a run record
      distinguishes a wait that will end from one that will not.
- [ ] 2.5 Correct `_predecessor_in`'s docstring where it calls the tracker
      fallback "the fallback for the one case the snapshot cannot answer: a
      blocker that is not on this milestone at all". State both cases it
      answers — a blocker off this milestone, and a blocker on it closed by
      any reason other than `closed:merged`, which the snapshot's scope
      excludes — and say why membership is read from ownership rather than
      from visibility.
- [ ] 2.6 `FixtureTracker` gains `sub_issues(number)`, returning the
      parent raw's `sub_issues` list — the field `attach_sub_issue` already
      maintains — and recording no write. Done when the fixture path
      answers ownership the same question the live path answers.

## 3. Tests

- [ ] 3.1 A `TrackerSnapshot` built in the live shape — an open
      `unit`-labelled blocker, a `Batch` row carrying two sub-issue
      numbers, and neither sub-issue among `items` because both closed
      `closed:superseded` — is "all in", and the dependent expands. This
      is the case that reproduces the defect: assert it against a tracker
      whose `closed` answers both children.
- [ ] 3.2 The same shape with one child closed off the happy path and one
      child open and visible: the pass defers and writes nothing.
- [ ] 3.3 A blocker whose members are all visible in the snapshot — every
      one open, then every one `closed:merged` — makes no `closed` and no
      `sub_issues` read on the tracker. Assert on a tracker that raises if
      either is called, so a later change that reads per member fails.
- [ ] 3.4 An expanded blocker owning no sub-issues defers, and the reason
      recorded says it has no work items — distinct from the reason
      recorded for an unexpanded blocker.
- [ ] 3.5 A blocker closed off the happy path is settled: keep the
      existing off-milestone case, and add one for a blocker on this
      milestone closed `closed:declined`, absent from the snapshot for the
      same reason. Both expand the dependent.
- [ ] 3.6 The three existing `ExpansionTest` defer scenarios —
      unexpanded predecessor, half-built predecessor, predecessor whose
      work all merged — stay green unchanged in intent, adjusted only where
      the fixture must now carry the ownership the predicate reads. Say in
      the commit message which helper changed and why.
- [ ] 3.7 The run record carries the reason: assert through the ledger note
      or `guard_expand`'s log line, not on the predicate's return value
      alone, so a reordering that swallows the reason fails.
- [ ] 3.8 `python3 -m unittest discover tests -v` green, and the repo's
      gates — `node scripts/check-paths.mjs`, `node scripts/check-site.mjs`,
      `bash scripts/validate-manifests.sh` — green.

## 4. Record

- [ ] 4.1 `openspec validate the-defer-predicate-reads-a-closed-unit
      --strict` green, and every task above checked off against what the
      files bear out rather than what was edited.
