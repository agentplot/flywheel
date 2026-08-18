## MODIFIED Requirements

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

A blocking issue that IS closed is settled whatever its close reason —
`closed:done`, `closed:declined`, `closed:superseded`, `closed:parked`,
or a close carrying no reason at all. The pass's milestone snapshot
carries open issues and `closed:merged` ones only, so a blocker closed by
any other route is absent from it; absence SHALL be resolved by reading
that issue's state, never read as evidence that its work is outstanding.

Which work items an expanded unit has SHALL be decided from the
sub-issues that unit owns, never from which issues the pass's snapshot
happens to carry. Every owned sub-issue the snapshot cannot answer for
SHALL have its state read; a sub-issue the snapshot carries SHALL be
answered from the snapshot and cost no read. An expanded unit owning no
sub-issues at all is a unit whose work was never born: its dependent
defers.

The run record's wait SHALL name which state it found — the blocker not
expanded, the blocker owning no work items, or a count of its items still
open — so a wait that a later pass will end is distinguishable from one
that will not.

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

#### Scenario: the predecessor's work closed off the happy path

- **WHEN** card B is Ready and blocked by unit A, A is still open, and
  every work item A owns is closed by a reason other than `closed:merged`
  — so none of them appears in the pass's snapshot
- **THEN** B expands on that pass, because A owns work items and every one
  of them is closed

#### Scenario: some of the predecessor's items are invisible and one is open

- **WHEN** card B is Ready and blocked by unit A, one item A owns is
  closed off the happy path and another is open
- **THEN** the pass defers and writes nothing

#### Scenario: an expanded predecessor that owns no work items

- **WHEN** card B is Ready and blocked by unit A, A carries `unit` and
  owns no sub-issues
- **THEN** the pass defers, writes nothing, and the wait it records says A
  has no work items rather than that its items are unfinished

#### Scenario: a blocker closed off the happy path

- **WHEN** card B is Ready and blocked by issue A, and A is closed with a
  reason other than `closed:merged` — whether A sits on this bolt's
  milestone or on none
- **THEN** B expands on that pass, a closed blocker being settled whatever
  the reason
