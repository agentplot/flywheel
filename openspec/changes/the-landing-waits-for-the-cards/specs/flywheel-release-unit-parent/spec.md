# flywheel-release-unit-parent Delta

## MODIFIED Requirements

### Requirement: A landed bolt's unit parent is closed, and stops being a job

Every unit a landed bolt carries SHALL be closed once the release it
carries is finished, and a milestone SHALL NOT report a job on account
of a unit whose work is done.

A bolt milestone holds as many units as the operator has approved cards
on it, and one landing serves them all. The close at the landing SHALL
therefore reach **every** open unit on the bolt's milestone — not one —
together with a unit parent that sits off the milestone and is reachable
only through a landed item's own parentage, which is where the handoff
release path puts it.

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
