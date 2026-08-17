# flywheel-derived-backlog Delta

## RENAMED Requirements

- FROM: `### Requirement: Expansion turns the approved card into the bolt`
- TO: `### Requirement: Expansion turns the approved card into a unit on its bolt`

- FROM: `### Requirement: A card blocked by an unlanded predecessor defers`
- TO: `### Requirement: A card whose predecessor unit has not merged defers`

## MODIFIED Requirements

### Requirement: Expansion turns the approved card into a unit on its bolt

The bolt loop SHALL expand, on any pass, an open `plan`-labeled card at
board Status Ready **on this bolt's milestone**: swap its `plan` label
for `unit`, drop `stale` if present, consume its Ready status, and file
one work item per plan task at `state:ready` on the same milestone —
title from the task's change, body carrying its deliverable, chapter
citations, and `after` — each attached as a sub-issue of that unit.

Expansion SHALL NOT create the bolt milestone and SHALL NOT set a
milestone on the card: the milestone and the card's home are the
planner's writes, and a Ready card that is not on this bolt's milestone
is not this bolt's to expand.

A bolt expands one card per approval, over its whole life, not once:
each approved card becomes its own unit beside the units already there,
and expanding one SHALL leave every other unit and its items untouched.
Expansion is idempotent: a second pass against an expanded card writes
nothing.

#### Scenario: expansion

- **WHEN** a pass finds an open `plan` card at Ready on this bolt's
  milestone
- **THEN** the card carries `unit` and not `plan`, its board status is
  consumed, one `state:ready` work item per plan task sits on the same
  milestone as its sub-issue, and no milestone was created or written
  onto the card

#### Scenario: a second unit is approved later

- **WHEN** a second card on the same milestone is moved to Ready while
  the first unit's items are already being driven
- **THEN** that card expands into its own unit with its own items, and
  the first unit, its items, and their labels are unchanged

#### Scenario: expansion is idempotent

- **WHEN** a later pass runs against a card already carrying `unit`
- **THEN** nothing is written

#### Scenario: a card belonging to another bolt

- **WHEN** a Ready `plan` card carries a different `bolt/*` milestone,
  or none
- **THEN** this bolt's expansion leaves it alone and writes nothing

### Requirement: A card whose predecessor unit has not merged defers

When a Ready card is blocked by an issue whose work is not all in,
expansion SHALL defer — the pass records the wait in the run record and
stops without refusing or altering the card, and a later pass retries.
Work is "all in" when the blocking issue is closed, or when it is an
expanded unit every one of whose work items is closed.

The predicate SHALL NOT be the blocker's own close: a unit card is
closed `closed:done` only after the bolt lands, and the landing waits on
the milestone's cards, so a card blocked by a sibling unit would
otherwise never expand and the bolt would never land.

#### Scenario: approved out of order

- **WHEN** card B is Ready and blocked by card A, and A has not been
  expanded
- **THEN** the pass defers, writes nothing, and records the wait

#### Scenario: the predecessor's work merged

- **WHEN** card B is Ready and blocked by unit A, A's every work item is
  closed, and A itself is still open awaiting the landing
- **THEN** B expands on that pass

#### Scenario: the predecessor is half built

- **WHEN** card B is Ready and blocked by unit A, and one of A's work
  items is still open
- **THEN** the pass defers and writes nothing

### Requirement: A card without Team refuses expansion

Expansion SHALL refuse a card carrying no Team: the loop labels the card
`needs-operator` with the reason as a comment — the unit is unroutable —
and pauses, expanding nothing and leaving the bolt's other units
untouched.

#### Scenario: unroutable card

- **WHEN** a Ready card carries no Team
- **THEN** the loop pauses with `needs-operator` and expands nothing

## ADDED Requirements

### Requirement: The bolt's charter carries every expanded unit's plan

The plan document behind an approved card is mutable state on the
tracker until expansion; expansion is what makes it durable prose in
git. The loop SHALL ensure that `openspec/changes/<slug>/bolt.md` holds
the plan document of every unit expanded on the bolt's milestone, each
as its own `# Unit: <slug>` section, in expansion order, verbatim from
the card's body. The write SHALL be committed to the bolt's change
directory on the branch that carries the bolt's record — main only
before the bolt branch is cut, the bolt branch after.

The charter is not written from the milestone's "unit parent": a bolt
carries as many units as the operator approves, and each one's document
belongs in the charter. A unit whose section is already present SHALL
NOT be written again, so a pass with nothing newly expanded makes no
commit.

#### Scenario: the first unit

- **WHEN** the first card on a bolt's milestone is expanded and the
  bolt's change directory does not yet exist
- **THEN** the directory is scaffolded and `bolt.md` carries that unit's
  plan document under its `# Unit: <slug>` heading

#### Scenario: a second unit expands into an existing charter

- **WHEN** a second card on the same milestone is expanded and the
  bolt's change directory already exists
- **THEN** `bolt.md` gains that unit's document as a second
  `# Unit: <slug>` section, committed on the bolt branch, and the first
  unit's section is unchanged

#### Scenario: nothing newly expanded

- **WHEN** a pass expands no card and every unit on the milestone
  already has its section
- **THEN** no charter write and no commit happen
