# flywheel-release-unit-parent Specification

## Purpose
What a release to construction creates on the tracker: one unit parent issue
per release, whose sub-issues are the released items, so that every bolt has
exactly one row on the board carrying GitHub's native sub-issue progress bar
— including the born-ready release, which today produces loose items and no
container at all.
## Requirements
### Requirement: The unit parent is the board row and the approval carrier

The unit parent SHALL sit on the org Project, and it SHALL be what carries
the release's approval on the board — the rule that whatever carries the
approval sits on the board, applied to the born-ready path.

On a born-ready release the parent SHALL be at Status **Ready** from birth,
because the operator's word at triage is the approval and there is nothing
left to approve. On every other path the parent SHALL be at Status
**Backlog** and the operator's flip to Ready SHALL remain the approval.

The released items themselves SHALL NOT each be added to the board. One row
per bolt is what this requirement buys, and it is lost if the sub-issues
appear beside their parent.

#### Scenario: A born-ready bolt on the board

- **WHEN** the operator looks at the board after a born-ready release of
  four items
- **THEN** there is one row for that bolt, at Ready, and not four

#### Scenario: A Backlog-born parent still gates

- **WHEN** a unit parent is born at Backlog
- **THEN** construction does not start until the operator moves it to Ready

#### Scenario: The reconciler's Ready query sees the release

- **WHEN** the server sweeps for milestones with a job
- **THEN** the born-ready release's unit parent is found by the same Ready
  query that finds any released batch

### Requirement: The progress bar is GitHub's own, on the parent

The board SHALL show the release's progress as GitHub's native sub-issue
progress on the unit parent — the "n of m" the platform derives from the
parent's sub-issues — and SHALL NOT compute a second progress figure
anywhere.

The board is a view and never a second store. A progress number the flywheel
maintained itself would be exactly that.

#### Scenario: A bolt part-way through construction

- **WHEN** the operator reads a bolt's row on the board
- **THEN** the progress shown is GitHub's own sub-issue count on the unit
  parent

#### Scenario: No second progress figure exists

- **WHEN** the flywheel's tools are searched for a stored or computed
  progress figure for a bolt
- **THEN** none is found, and the parent's native bar is the only one

### Requirement: A sub-issue checks off at merge-back, not at the landing

A released item SHALL check off on its unit parent's bar when its work
reaches the bolt branch, and SHALL NOT wait for the bolt to land.

Because the bar counts closed sub-issues, this is achieved by the item
being closed at merge-back with `closed:merged`, and by nothing else — no
computed figure, no second store. The landing then upgrades the reason to
`closed:done` with the SHA, which the bar cannot see and does not need to.

The bar's denominator SHALL be read as the parent's sub-issue count: the
number of work items the expansion filed, so a full bar and a fully merged
release are the same event. Neither the board nor any tool SHALL compute a
second figure; the native bar is the only one.

The board's Landed view SHALL keep filtering `closed:done`, so a
merged-but-unlanded item advances the parent's bar without appearing as
landed.

#### Scenario: Two of four batches have merged

- **WHEN** two of a born-ready release's four items have merged back and the
  bolt has not landed
- **THEN** the parent's native bar reads 2 of 4

#### Scenario: The bar is full before the bolt lands

- **WHEN** every item of a release has merged back and the bolt has not yet
  landed
- **THEN** the parent's bar is complete, and the Landed view still shows
  none of them

#### Scenario: The landing does not change the bar

- **WHEN** the bolt lands and each item's reason is upgraded to
  `closed:done`
- **THEN** the parent's bar is unchanged, because the items were already
  closed

### Requirement: An item still joins exactly one batch

Creating a unit parent SHALL NOT attach an item that already belongs to a
batch, and encountering one SHALL be skipped rather than fatal.

An item joins exactly one batch ever — GitHub enforces it, returning 422 on
an attempt to attach a parented sub-issue — and the release path is a guard
like the others: applying it twice must converge rather than crash.

#### Scenario: A release is attempted twice

- **WHEN** the release path runs a second time over items that are already
  sub-issues of a unit
- **THEN** the already-batched items are skipped and no second unit parent
  is created for them

#### Scenario: One item of a release is already batched

- **WHEN** a release names four items and one of them already belongs to a
  batch on another milestone
- **THEN** that item is skipped with a note, and the release proceeds for
  the other three

### Requirement: A landed bolt's unit parent is closed, and stops being a job

Every unit a landed bolt carries SHALL be closed once the release it
carries is finished, and a milestone SHALL NOT report a job on account
of a unit whose work is done.

A bolt milestone holds as many units as the operator has approved cards
on it, and one landing serves them all. The close at the landing SHALL
therefore reach **every** open unit on the bolt's milestone — not one —
together with any unit parent that sits off the milestone and is
reachable only through a landed item's own parentage.

Two things follow, and both are needed — the first alone leaves the
filter wrong for any unit the closer has not reached yet, and the second
alone leaves a landed bolt showing open rows on the board forever:

- **the landing closes the units.** At the landing every unit's bar is
  full and every assertion has been upgraded to `closed:done`, so the
  release each unit carries is finished and there is nothing further it
  can gate. Each SHALL be closed there, with a `closed:*` reason like any
  other close — the tracker's rule that whoever holds the evidence
  closes, always with one reason, is not relaxed for a container — and
  the closing comment SHALL carry the landing SHA.
- **the server's Ready-batch condition is bounded.** A milestone SHALL
  report a job for a batch at board Status Ready only while that
  milestone is **open**, which is the same test the server's per-item
  condition already makes. Without it a unit left open at Ready keeps its
  milestone reporting a job on every sweep — before the landing, after
  the landing, and after the operator closes the milestone, where it
  collides with the archive job the same sweep adds for that milestone.

The cost of the unbounded condition today is waste rather than damage:
the started loop finds an empty ready set, its guards write nothing, and
the cycle stops without re-landing anything. It is specified because a
filter that names a job forever is indistinguishable, to the operator
reading the fleet, from work that is never getting done.

Closing a unit SHALL NOT close, reopen or relabel any sub-issue: the
assertions' own closes are the merge boundary's and the landing's, and
the unit is a container. An elaboration on the milestone SHALL NOT be
closed by a landing — it authorizes design work, not this release — and
a unit already closed SHALL NOT be closed a second time.

#### Scenario: A bolt lands

- **WHEN** a bolt's branch lands on main and every assertion is upgraded
  to `closed:done`
- **THEN** that release's unit is closed, with one `closed:*` reason and
  the landing SHA in its closing comment, and no sub-issue's state or
  reason is altered by that close

#### Scenario: A bolt carrying several units lands

- **WHEN** the milestone holds two expanded units, each with its own
  merged sub-issues, and the bolt lands
- **THEN** both units are closed at that one landing, each with the
  landing SHA, and neither is left open for a later run to find

#### Scenario: The sweep after a landing

- **WHEN** the server sweeps a milestone whose units have been closed
- **THEN** that milestone reports no job on account of a Ready batch

#### Scenario: A parent still open on a closed milestone

- **WHEN** the operator closes a milestone while a unit on it is still
  open at Status Ready
- **THEN** the sweep reports no "run" job for it, and the archive job for
  that milestone is the only one added

#### Scenario: A Ready batch on an open milestone still starts its loop

- **WHEN** the operator flips a unit to Ready on an open milestone
- **THEN** the sweep reports a job for that milestone exactly as it does
  today, because only the closed-milestone case is being excluded

### Requirement: On a bolt milestone, a unit parent is born only by expansion

On a `bolt/<slug>` milestone, a unit parent SHALL come into being by exactly
one path: the bolt loop's expansion of an approved plan card, which relabels
the card `plan` → `unit` and files the unit's work items as its sub-issues.
No actor creates a `unit`-labeled issue on a bolt milestone directly — not
dispatch, not a session, not the loop outside expansion — and no such
parent exists whose number was not first a plan card's. One card, one unit,
however many items the expansion files; an item joins exactly one unit,
ever.

The intent loop births no units: a settled assertion sits on its
milestone until the planner cards its work, and the operator's approval
expands the card.

#### Scenario: An approved card becomes the unit

- **WHEN** the bolt loop expands a plan card at board Status Ready
- **THEN** that card itself carries the `unit` label, its sub-issues are
  the work items the expansion filed, and no other unit parent was created

#### Scenario: No path but expansion makes a unit on a bolt milestone

- **WHEN** dispatch triages, a session settles, or an operator's word
  arrives outside the board
- **THEN** no `unit`-labeled issue is created on any `bolt/*` milestone by
  any of them

#### Scenario: A settled assertion births nothing

- **WHEN** an assertion settles on an `intent/<slug>` milestone
- **THEN** the intent loop creates no item and no unit for it, and it sits
  queued until the planner's card for its work is approved and expanded

