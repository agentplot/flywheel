## MODIFIED Requirements

### Requirement: Every release creates exactly one unit parent

A release of assertions to construction SHALL create exactly one issue
labelled `unit`, whose sub-issues are the items the release carries. This
SHALL hold for both release paths, and the two paths SHALL differ in the
parent's milestone and in whether the handoff item is among the sub-issues:

- **the born-ready operator release** — the operator's word at triage is
  itself the approval and the work goes straight to a `bolt/<slug>`
  milestone. The parent SHALL be created **on that bolt milestone**, and its
  sub-issues SHALL be **exactly the released assertions**.
- **handoff birth** — the intent loop's, where a handoff item and its unit
  are born together and the operator's flip to Ready seals the batch. The
  parent SHALL be created **on the intent milestone**, because it is born
  before any assertion has moved to a bolt and the assertions reach
  `bolt/<slug>` later by the handoff session's custody move, staying
  sub-issues across it. Its sub-issues SHALL be **the handoff item together
  with the released assertions**.

The handoff item's membership is load-bearing and not incidental: a second
handoff birth on the same intent SHALL recover the already-open unit through
the handoff item's own parent, so that newcomers join the open Backlog batch
rather than starting a second one. An implementation that attached only the
assertions would have no handle to recover the unit by.

The born-ready path is the one that changes shape from before this
capability. Today it puts a lone item on the board and creates no parent, so
a born-ready bolt has as many board rows as it has items and no progress bar
on any of them.

A release SHALL create exactly one unit however many items it carries, and a
release of a single item SHALL still create one — "born-ready included" is
the whole point, and a special case for one item would put the bolt back to
having no container.

#### Scenario: The operator releases four assertions born ready

- **WHEN** four assertions are released born-ready onto a fresh
  `bolt/<slug>` milestone
- **THEN** one `unit` parent is created on that bolt milestone with the four
  as its sub-issues, and nothing else is attached

#### Scenario: The operator releases a single assertion born ready

- **WHEN** one assertion is released born-ready
- **THEN** a unit parent is still created, with that one item as its sole
  sub-issue

#### Scenario: A handoff release is unchanged in shape

- **WHEN** the intent loop births a handoff and its unit
- **THEN** the release produces exactly one unit parent carrying the whole
  release, which is what it shares with the born-ready path — the two paths
  differing only in that parent's milestone and in whether the handoff item
  is among its sub-issues

#### Scenario: A handoff release names its own milestone and carries its handoff item

- **WHEN** the intent loop births a handoff and its unit for four assertions
- **THEN** the unit parent is created on the `intent/<slug>` milestone, and
  its sub-issues are the handoff item and the four assertions — five in all

#### Scenario: A later wave joins an open handoff unit

- **WHEN** a second settled assertion appears while the handoff's unit still
  sits at Backlog
- **THEN** the open unit is recovered through the handoff item's own parent
  and the newcomer is attached to it, rather than a second unit being created

#### Scenario: The assertions keep their parent across the custody move

- **WHEN** the handoff session moves the released assertions from
  `intent/<slug>` to `bolt/<slug>`
- **THEN** each stays a sub-issue of the same unit parent, which does not
  move with them

### Requirement: A sub-issue checks off at merge-back, not at the landing

A released item SHALL check off on its unit parent's bar when its work
reaches the bolt branch, and SHALL NOT wait for the bolt to land.

Because the bar counts closed sub-issues, this is achieved by the item
being closed at merge-back with `closed:merged`, and by nothing else — no
computed figure, no second store. The landing then upgrades the reason to
`closed:done` with the SHA, which the bar cannot see and does not need to.

The bar's denominator SHALL be read as the parent's sub-issue count on the
path that created it, and the two paths differ. On the born-ready path the
denominator is the number of released assertions, so a full bar and a fully
merged release are the same event. On the handoff path the handoff item is
among the sub-issues, so the denominator is one greater than the number of
assertions — and the handoff item closes at its own design session's collect,
before construction starts, so from the first construction cycle the bar
already counts one closed sub-issue that is not an assertion. Neither the
board nor any tool SHALL correct for this by computing a second figure; the
native bar is the only one, and what it counts is stated here so a reader is
not misled by it.

The board's Landed view SHALL keep filtering `closed:done`, so a
merged-but-unlanded item advances the parent's bar without appearing as
landed.

#### Scenario: Two of four batches have merged

- **WHEN** two of a born-ready release's four items have merged back and the
  bolt has not landed
- **THEN** the parent's native bar reads 2 of 4

#### Scenario: Two of four handoff-released assertions have merged

- **WHEN** two of a handoff release's four assertions have merged back, the
  handoff item having closed at its design session's collect
- **THEN** the parent's native bar reads 3 of 5, counting the closed handoff
  item, and no tool reports a different figure

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

## ADDED Requirements

### Requirement: A landed bolt's unit parent is closed, and stops being a job

A unit parent SHALL be closed once the release it carries is finished, and a
milestone SHALL NOT report a job on account of a unit parent whose work is
done.

Two things follow, and both are needed — the first alone leaves the filter
wrong for any parent the closer has not reached yet, and the second alone
leaves a landed bolt showing an open row on the board forever:

- **the landing closes the parent.** At the landing the parent's bar is full
  and every assertion has been upgraded to `closed:done`, so the release the
  parent carries is finished and there is nothing further it can gate. The
  parent SHALL be closed there, with a `closed:*` reason like any other close
  — the tracker's rule that whoever holds the evidence closes, always with
  one reason, is not relaxed for a container.
- **the server's Ready-batch condition is bounded.** A milestone SHALL report
  a job for a batch at board Status Ready only while that milestone is
  **open**, which is the same test the server's per-item condition already
  makes. Without it a parent left open at Ready keeps its milestone reporting
  a job on every sweep — before the landing, after the landing, and after the
  operator closes the milestone, where it collides with the archive job the
  same sweep adds for that milestone.

The cost of the unbounded condition today is waste rather than damage: the
started loop finds an empty ready set, its guards write nothing, and the
cycle stops without re-landing anything. It is specified because a filter
that names a job forever is indistinguishable, to the operator reading the
fleet, from work that is never getting done.

Closing the parent SHALL NOT close, reopen or relabel any sub-issue: the
assertions' own closes are the merge boundary's and the landing's, and the
parent is a container.

#### Scenario: A bolt lands

- **WHEN** a bolt's branch lands on main and every assertion is upgraded to
  `closed:done`
- **THEN** that release's unit parent is closed, with one `closed:*` reason,
  and no sub-issue's state or reason is altered by that close

#### Scenario: The sweep after a landing

- **WHEN** the server sweeps a milestone whose unit parent has been closed
- **THEN** that milestone reports no job on account of a Ready batch

#### Scenario: A parent still open on a closed milestone

- **WHEN** the operator closes a milestone while a unit parent on it is
  still open at Status Ready
- **THEN** the sweep reports no "run" job for it, and the archive job for
  that milestone is the only one added

#### Scenario: A Ready batch on an open milestone still starts its loop

- **WHEN** the operator flips a unit to Ready on an open milestone
- **THEN** the sweep reports a job for that milestone exactly as it does
  today, because only the closed-milestone case is being excluded
