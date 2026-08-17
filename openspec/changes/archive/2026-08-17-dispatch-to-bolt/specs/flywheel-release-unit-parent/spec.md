# flywheel-release-unit-parent Delta

## REMOVED Requirements

### Requirement: Every release creates exactly one unit parent

**Reason**: The born-ready operator release no longer exists — on a bolt
milestone, expansion of an approved plan card is the only birth of a unit
parent, and dispatch delivers dictated work as a plan card rather than a
release. The handoff birth keeps its contract in the replacement
requirement below, unchanged, until its own retirement.

## ADDED Requirements

### Requirement: On a bolt milestone, a unit parent is born only by expansion

On a `bolt/<slug>` milestone, a unit parent SHALL come into being by exactly
one path: the bolt loop's expansion of an approved plan card, which relabels
the card `plan` → `unit` and files the unit's work items as its sub-issues.
No actor creates a `unit`-labeled issue on a bolt milestone directly — not
dispatch, not a session, not the loop outside expansion — and no such
parent exists whose number was not first a plan card's. One card, one unit,
however many items the expansion files; an item joins exactly one unit,
ever.

The intent loop's handoff birth is the one other unit birth and it happens
on the `intent/<slug>` milestone: the handoff item and its unit are born
together, and the release produces exactly one unit parent carrying the
whole release.

#### Scenario: An approved card becomes the unit

- **WHEN** the bolt loop expands a plan card at board Status Ready
- **THEN** that card itself carries the `unit` label, its sub-issues are
  the work items the expansion filed, and no other unit parent was created

#### Scenario: No path but expansion makes a unit on a bolt milestone

- **WHEN** dispatch triages, a session settles, or an operator's word
  arrives outside the board
- **THEN** no `unit`-labeled issue is created on any `bolt/*` milestone by
  any of them

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
