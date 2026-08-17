# flywheel-derived-backlog Delta

## MODIFIED Requirements

### Requirement: The planner session is hosted by its own profile

A `flywheel-bolt-planner` profile SHALL host planning runs: it loads
the bolt-planning skill, reads only the work order's book, specs, and
changes in flight, and its only tracker writes are the bolt milestone
and the unit cards on it.

A run in board mode SHALL create the `bolt/<slug>` milestone if it
does not already exist and SHALL write the bolt summary — what the
bolt delivers, the unit sequence one line each, and the bolt's total
price — as that milestone's description. It SHALL then file exactly
one `plan`-labeled card per proposed unit **on that milestone**, each
with the title `Unit: <slug>`, the unit document as the body carrying
a `System:` line and the input commits, the card added to the org
Project at Status Backlog with the work order's Team, and every
"builds on" claim mirrored as a native blocked-by relationship
between the unit cards. Unapproved plan cards from earlier runs SHALL
be closed `closed:superseded`.

The run SHALL write nothing else on the tracker: no work items, no
`state:*` label on any card, no other issue, comment, or label — a
unit is born only when the operator approves its card and the bolt
loop expands it.

The surfaces a planning run reads — the bolt-planning skill's
delivery section and the planner profile's card conventions — SHALL
state these conventions, since the run is driven by prose and nothing
else enforces them.

#### Scenario: run files cards

- **WHEN** a planning run in board mode proposes one bolt of two
  units, the second building on the first
- **THEN** the `bolt/<slug>` milestone exists carrying the bolt
  summary as its description, and two cards titled `Unit: <slug>` sit
  on that milestone at Backlog with the work order's Team, the second
  blocked by the first

#### Scenario: a later run replaces what nobody approved

- **WHEN** a planning run files its cards and unapproved plan cards
  from an earlier run are still open
- **THEN** those earlier cards are closed `closed:superseded`, and no
  approved card is touched

#### Scenario: the milestone already exists

- **WHEN** a planning run's `bolt/<slug>` milestone was created by an
  earlier run
- **THEN** the run files its cards onto the existing milestone rather
  than creating a second one

#### Scenario: the run writes no work

- **WHEN** a planning run finishes filing its cards
- **THEN** no work item exists on the milestone and no card carries a
  `state:*` label
