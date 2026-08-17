# flywheel-derived-backlog Delta

## ADDED Requirements

### Requirement: The landing is the bolt's boundary, held by any open unit card

A bolt SHALL land once, for its milestone, however many units that
milestone carries. The landing is the bolt's boundary and not a unit's:
items merge to the bolt branch as they finish, and one landing carries
the branch to main for all of them.

The bolt loop SHALL NOT reach for a landing while an **open unit card
sits on this bolt's milestone** — an open `plan`-labelled card whose own
`bolt/*` milestone is this bolt's, whatever its board Status and whether
or not it is stale. The hold SHALL come before the landing's expectation
gate and before any landing session: while a card is open nothing is
verified against the bolt branch, nothing reaches the main branch, and
no item's `closed:merged` is upgraded.

A card that expansion has already turned into a unit SHALL NOT hold the
landing. The `unit` label is what ends the card's holding life: an
expanded unit stays open across the landing precisely so the landing can
close it, and reading it as a card still open would make the hold
unsatisfiable and the bolt unlandable.

The hold SHALL apply to a forced landing exactly as to an automatic one.
The way past it is the operator's ruling of the card, never a flag:
approving it, which the next pass expands into a unit, or closing it as
declined or superseded. A card the operator has closed holds nothing. A
card that is not on this bolt's milestone holds nothing here — including
a card that names no `bolt/*` milestone at all, which is no bolt's card
to hold.

A held run SHALL be legible as held wherever the run reports its
landing. The landing line of the run report — the line
`flywheel bolt-loop` prints and carries in its `--json` — SHALL state
that the landing was held and name each holding card by number, rather
than the "not attempted" it reports for a run that never had a landing
to reach for; the run record SHALL carry the same statement.

Once no open card remains on the milestone, the landing SHALL proceed
under its existing preconditions and gain no new ones from this
requirement: released work still declines it, and every unlanded
assertion must have reached the bolt branch.

A unit expanded after an earlier unit's items have merged SHALL NOT buy
a second landing: its items are released work, which declines the
landing until they too are merged, and the single landing that follows
serves every unit on the milestone.

#### Scenario: An unapproved card holds the landing

- **WHEN** every unlanded assertion on `bolt/<slug>` is `closed:merged`
  and an open `plan` card at board Status Backlog sits on that milestone
- **THEN** no landing session runs, nothing reaches the main branch, no
  item is upgraded to `closed:done`, and the run's landing line says the
  landing was held and names that card

#### Scenario: An approved card that has not been expanded yet holds it

- **WHEN** the only card left on the milestone sits at Status Ready and
  has not been expanded — deferred behind its predecessor, or approved
  after the last merge
- **THEN** the landing is held exactly as for a Backlog card

#### Scenario: The operator rules the last card

- **WHEN** the operator closes the card they decline, or approves it and
  the loop expands it and its items merge, leaving no open `plan` card
  on the milestone
- **THEN** the landing runs on the next pass that finds the bolt's other
  preconditions met

#### Scenario: An expanded unit does not hold the landing

- **WHEN** every card on the milestone has been expanded, the units are
  open, and every item is merged
- **THEN** the landing runs, and the open units are not read as cards
  holding it

#### Scenario: A forced landing is held too

- **WHEN** a landing is forced on a bolt whose milestone still holds an
  open card
- **THEN** it is held, and the run says so rather than landing

#### Scenario: A card elsewhere holds nothing

- **WHEN** an open `plan` card sits on another bolt's milestone, or names
  no `bolt/*` milestone at all
- **THEN** it does not hold this bolt's landing

#### Scenario: A second unit does not buy a second landing

- **WHEN** one unit's items are all merged and the operator approves a
  second card on the same milestone
- **THEN** expansion files that unit's items as released work, the
  landing is declined while they run, and the bolt lands once after they
  merge
