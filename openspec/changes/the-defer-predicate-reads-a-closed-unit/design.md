## Context

See proposal.md — Why. What the approach turns on is what the pass
already holds when it asks the question, read from the files at writing
time:

- `bin/_flywheel_inbox.py` — `Tracker.snapshot` builds `items` from
  "Open issues **plus** the `closed:merged` ones", filtered to the
  milestone. Nothing else is in there.
- The same method, for every item carrying `unit` or `elaboration`,
  appends a `Batch` whose `sub_issues` is
  `tuple(self.sub_issues(item.number)) if with_edges else ()`. So on the
  live path a blocking unit's **owned** membership is already fetched and
  already in the snapshot, keyed by the blocker's number.
- `bin/_flywheel_bolt_loop.py` — `guard_expand` runs under
  `snapshot(milestone)` with edges on. Its docstring's own words: the
  card's blockers are read because "the one reader of a card's blockers is
  the expansion guard, which runs under `snapshot(milestone)` with edges
  on" (`Tracker.snapshot`, the `blocked_by` gating comment).
- `TrackerSnapshot.batch(number)` returns that row; `Batch.sub_issues` is
  the tuple.
- `Tracker.closed(number)` is one read and answers "closed, whatever the
  reason".

Two facts about the harness shape the tasks. `TrackerSnapshot.from_fixture`
builds `items` from every item in the fixture regardless of state, and
builds `batches` only from a `batches:` key the fixture files do not
carry — so under `FixtureTracker` a `unit`-labelled item produces no
`Batch` row and closed items stay visible. The fixture snapshot is
therefore not the shape the live one has, which is why no existing test
could see this defect. `FixtureTracker.attach_sub_issue` does maintain a
`sub_issues` list on the parent raw, so the fixture can answer ownership
if asked.

## Goals / Non-Goals

**Goals:**

- Ownership answers the "all in" question; visibility never does.
- The common cases stay free: every member visible costs no extra read.
- The two causes of an empty answer — never born, all finished — are
  distinguishable in the run record.

**Non-Goals:**

- Repairing a torn expansion (a card swapped to `unit` before its items
  were created). This design makes that case defer *knowingly* and say so;
  it does not birth the missing items.
- Reshaping `TrackerSnapshot.from_fixture` to mirror the live snapshot.
  That is the fidelity gap named in proposal.md — Impact; it is read here
  and worked around in the tests rather than changed under a defer fix.
- Any change to the close-reason vocabulary, to what the snapshot fetches,
  or to the deferral's contract (a wait, never a refusal, never a pause).

## Decisions

**Membership comes from the blocker's `Batch` row, not from a scan of
`snapshot.items` by `parent_batch`.** The row is the tracker's own answer
to "what does this unit own", fetched per unit by the same snapshot the
guard already holds; the `parent_batch` scan is a reconstruction of it
from whichever items happen to be visible, and `backfill_parentage` fills
that field *from* the very `sub_issues` this row carries. Reading the
source rather than the derived copy is what makes the empty case
meaningful. *Alternative — keep the scan and drop `bool(work)`:* rejected,
because an empty visible set would then read as "all in", and a torn
expansion or a unit whose items were moved off the milestone would let a
dependent expand over work that never happened. The failure would run in
the unsafe direction, which is worse than the one being fixed.

**A member the snapshot cannot answer for gets one `Tracker.closed` read;
a member it carries is answered from the snapshot.** The snapshot's scope
is the whole justification: an open item on this milestone is always in
it, so a missing member is either closed by some reason other than
`closed:merged` or has left the milestone — and only the tracker knows
which. This is the same fallback shape `_predecessor_in` already uses for
a blocker it cannot see, extended one level down to the blocker's members.
*Alternative — read every member from the tracker:* rejected as a per-pass
cost on the common path, where the members are open or `closed:merged` and
the snapshot already has them. *Alternative — treat any invisible member as
closed without reading:* rejected; a member moved to another milestone
while open would read as finished, and the read that settles it is one
call in a case that is already rare.

**Where the snapshot carries no `Batch` row for the blocker, ownership is
one `Tracker.sub_issues` read.** On the live path with edges on, a
`unit`-labelled blocker on this milestone always has a row, so this
fallback never fires there; it exists for the blocker that is off the
milestone and for `FixtureTracker`, whose snapshot builds no rows at all.
`FixtureTracker` gains `sub_issues` over the field `attach_sub_issue`
already maintains — a read method on a class whose reads are the fixture
file, not a new tracker surface. *Alternative — declare the fixture path
unsupported:* rejected, because `ExpansionTest` is the only harness that
drives `guard_expand` end to end.

**Zero owned sub-issues defers.** Deferral is the safe direction: the
alternative expands a dependent over a predecessor that produced nothing.
The cost is that a torn expansion deadlocks its dependent — the same shape
as the bug being fixed, by a different route — which is why it is a named
non-goal and a finding rather than silence.

**The wait's reason is computed and recorded, not inferred by a reader.**
`_expand_card` already notes "expansion deferred — card #N blocked by #M,
whose work is not all in". The predicate now knows which of three states
it found, so it returns that phrase and the note carries it.
`books/flywheel/src/observation.md`'s rule — facts originate in the record
— is the reason this is not left to the log.

**The tracker fallback's docstring is corrected in the same change.** It
currently calls itself "the fallback for the one case the snapshot cannot
answer: a blocker that is not on this milestone at all". A blocker on this
milestone closed off the happy path is the second case, and the comment
denying it is what would license a later reader to narrow the fallback and
restore the deadlock.

## Risks / Trade-offs

- **A blocker whose members are all invisible costs one read per
  member.** → Bounded by the unit's task count and reached only when the
  snapshot cannot answer, which on the live path means the unit's work has
  already finished. The common paths — every member open, every member
  `closed:merged` — add no call.
- **`Batch.sub_issues` is empty when `with_edges=False`, and an empty tuple
  is indistinguishable from a unit owning nothing.** → The expansion guard
  is the only caller and always runs with edges on; the task list requires
  that be re-read from `guard_expand`'s call path and asserted, not
  assumed. If it ever ran edgeless, every blocker would read as owning
  nothing and every dependent would defer — the safe direction, and loudly
  in the run record now that the reason is named.
- **The fixture harness does not reproduce the live snapshot's shape**, so
  a test written only against `FixtureTracker` would prove the fallback
  and not the primary path. → The tasks require both: the fixture path
  through `guard_expand`, and a hand-built `TrackerSnapshot` in the live
  shape (a `Batch` row for the blocker, its finished members absent) that
  asserts the tracker is not consulted for members the snapshot carries.
- **A member moved off the milestone while open reads as closed if the
  fallback is ever dropped.** → The `Tracker.closed` read is what prevents
  it; the requirement states the read rather than the shortcut so a later
  optimization has to argue with the spec.
