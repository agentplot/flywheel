## Purpose

What a release to construction creates on the tracker: one unit parent issue
per release, whose sub-issues are the released items, so that every bolt has
exactly one row on the board carrying GitHub's native sub-issue progress bar
— including the born-ready release, which today produces loose items and no
container at all.

## ADDED Requirements

### Requirement: Every release creates exactly one unit parent

A release of assertions to construction SHALL create one issue labelled
`unit`, on the bolt's milestone, whose sub-issues are exactly the items
being released. This SHALL hold for both release paths:

- **handoff birth** — the intent loop's, where a handoff item and its unit
  are born together and the operator's flip to Ready seals the batch;
- **the born-ready operator release** — where the operator's word at triage
  is itself the approval and the work goes straight to a `bolt/<slug>`
  milestone.

The born-ready path is the one that changes. Today it puts a lone item on
the board and creates no parent, so a born-ready bolt has as many board rows
as it has items and no progress bar on any of them.

A release SHALL create exactly one unit however many items it carries, and a
release of a single item SHALL still create one — "born-ready included" is
the whole point, and a special case for one item would put the bolt back to
having no container.

#### Scenario: The operator releases four assertions born ready

- **WHEN** four assertions are released born-ready onto a fresh
  `bolt/<slug>` milestone
- **THEN** one `unit` parent is created on that milestone with the four as
  its sub-issues

#### Scenario: The operator releases a single assertion born ready

- **WHEN** one assertion is released born-ready
- **THEN** a unit parent is still created, with that one item as its sole
  sub-issue

#### Scenario: A handoff release is unchanged in shape

- **WHEN** the intent loop births a handoff and its unit
- **THEN** the result is the same shape as the born-ready release: one unit
  parent, the released assertions as its sub-issues

### Requirement: The unit parent is the board row and the approval carrier

The unit parent SHALL sit on the org Project, and it SHALL be what carries
the release's approval on the board — the rule that whatever carries the
approval sits on the board, applied to the born-ready path.

On a born-ready release the parent SHALL be at Status **Ready** from birth,
because the operator's word at triage is the approval and there is nothing
left to approve. On a handoff release the parent SHALL be at Status
**Backlog** and the operator's flip to Ready SHALL remain the approval, as
it is today.

The released items themselves SHALL NOT each be added to the board. One row
per bolt is what this requirement buys, and it is lost if the sub-issues
appear beside their parent.

#### Scenario: A born-ready bolt on the board

- **WHEN** the operator looks at the board after a born-ready release of
  four items
- **THEN** there is one row for that bolt, at Ready, and not four

#### Scenario: The handoff approval still gates

- **WHEN** a handoff's unit parent is created
- **THEN** it is at Backlog, and construction does not start until the
  operator moves it to Ready

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

The board's Landed view SHALL keep filtering `closed:done`, so a
merged-but-unlanded item advances the parent's bar without appearing as
landed.

#### Scenario: Two of four batches have merged

- **WHEN** two of a release's four items have merged back and the bolt has
  not landed
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
