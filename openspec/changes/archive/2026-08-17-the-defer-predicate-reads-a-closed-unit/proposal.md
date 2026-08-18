## Why

`_predecessor_in` decides whether a Ready card may expand behind the unit
it builds on. Its last line reads:

```python
work = [i for i in snapshot.items if i.parent_batch == number]
return bool(work) and all(not i.is_open for i in work)
```

`snapshot.items` is not every item the blocker owns. `Tracker.snapshot`
builds it from "Open issues **plus** the `closed:merged` ones, which are
closed and still in flight" — so a work item closed any other way
(`closed:done`, `closed:declined`, `closed:superseded`, `closed:parked`,
or closed by hand with no reason at all) is simply absent. When *every*
one of a unit's items closed off that happy path, the list the predicate
computes is empty, `bool(work)` is false, and the predecessor reads as
work that has not been born.

The empty list is not evidence. It has two causes and the predicate
collapses them: a unit whose items were never created, and a unit whose
items are all finished and out of the snapshot's window. Reading it as
the first is the deadlocking direction, and the deadlock is total —
verified against the tree at `bin/_flywheel_bolt_loop.py`,
`_predecessor_in`:

```
unit #11: `unit`, open, on the milestone; its two work items closed
          `closed:superseded`, so the snapshot cannot see them
_predecessor_in(11, snapshot) -> False   # and the tracker is never asked
```

The dependent card defers on every pass, forever. Nothing escalates: a
defer is "never a refusal", so no `needs-operator` is written, the run
record notes a wait that will not end, and the card stays open — which
holds the landing too, since `holding_cards` refuses a landing while an
open card sits on the milestone. One bolt, stopped, with no pause and no
gesture that clears it. `books/flywheel/src/construction-loop.md` reserves
that state for judgment running out: "The loop pauses — never guesses."
This is a guess — the guess that absence means unborn — made where
nobody can see it.

The same absence is what a closed *unit* relies on to be read correctly,
and the code comment denies it. `_predecessor_in` calls its tracker
fallback "the fallback for the one case the snapshot cannot answer: a
blocker that is not on this milestone at all." That is false about the
tree as it stands: a unit on this milestone closed off the happy path is
equally invisible, and the same fallback is the only thing answering for
it. Behaviour that is right by accident, and documented as something
else, is a load-bearing line one tidy-up away from the same deadlock.

## What Changes

- **The predecessor's membership is read, not inferred from what is
  visible.** The blocker unit's work items are the sub-issues it owns —
  the set the snapshot already carries on the blocker's `Batch` row,
  fetched per unit by `Tracker.snapshot` when edges are on, which is how
  the expansion guard always runs. The predicate asks that set what it
  contains instead of asking `snapshot.items` who claims the blocker as a
  parent.
- **A member the snapshot cannot see is resolved against the tracker, one
  read each.** By the snapshot's own scope, a sub-issue missing from it is
  not an open item on this milestone; whether it is finished is a fact
  only the tracker holds, and `Tracker.closed` — "Is this item closed,
  whatever the reason?" — is the question. Members the snapshot carries
  are answered from the snapshot and cost nothing, so the common cases —
  every item open, every item `closed:merged` — make no extra call at all.
- **An expanded unit that owns no work items defers, and says which.**
  Zero sub-issues means nothing was born — a torn expansion, not a
  finished unit — and deferral stays the safe direction. What changes is
  that this is now the answer to a question that was asked, rather than
  the accident of an empty filter.
- **A blocking unit that is itself closed is settled, however it was
  closed.** The requirement names the reasons rather than implying
  `closed:done`, and the tracker fallback's comment is corrected to state
  both cases it actually answers: a blocker off this milestone, and a
  blocker on it whose close took it out of the snapshot's window.
- **The run record names the real reason for each wait.** A deferral notes
  which of "not expanded", "no work items were born", or "n of m items
  still open" it computed, so the operator reading the run report can tell
  a wait that will end from one that will not.
- **No new close vocabulary and no new tracker surface.** `Tracker.closed`
  and `Tracker.sub_issues` already exist and are already what the live
  path calls; `FixtureTracker` gains `sub_issues` over the field
  `attach_sub_issue` already maintains, so the fixture path answers the
  same question the live one does.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `flywheel-derived-backlog`: the defer requirement gains what "every one
  of whose work items is closed" is decided from — the blocker's owned
  sub-issues rather than the items a milestone-scoped snapshot happens to
  carry — states that a unit owning no work items defers, and names that a
  closed blocker is settled whatever its close reason.

## Impact

- `bin/_flywheel_bolt_loop.py` — `_predecessor_in`: the membership source,
  the per-member resolution, and the docstring's claim about the tracker
  fallback. `_expand_card`'s deferral note gains the computed reason.
  `FixtureTracker` gains `sub_issues`.
- `bin/_flywheel_inbox.py` — `Tracker.snapshot`, `Tracker.closed`,
  `Tracker.sub_issues`, `TrackerSnapshot.batch` and `Batch.sub_issues` are
  read, not changed.
- `tests/test_derived_backlog.py` — `ExpansionTest`, its `unit_item` and
  `work_item` helpers, and a snapshot built in the live shape (a `Batch`
  row for the blocker, closed-off-the-happy-path members absent) so the
  test exercises the path the live snapshot produces rather than the
  fixture's all-items view.
- **Out of scope**, recorded as findings rather than fixed here:
  `TrackerSnapshot.from_fixture` derives no `Batch` from a `unit`-labelled
  item and carries items in every state, so the fixture snapshot is not
  the shape the live one has — the fidelity gap that let this survive; and
  a torn expansion (a card swapped to `unit` before its items were
  created) has no repair, so its dependent defers forever by a route this
  change does not close.
