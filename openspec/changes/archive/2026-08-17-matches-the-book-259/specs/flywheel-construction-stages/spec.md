## ADDED Requirements

### Requirement: The operator's milestone close releases the landing, and the card hold is asked first

The bolt loop SHALL NOT reach for a landing on its own initiative while
the bolt's milestone is **open**. The operator's close of that milestone
is the release gesture: merged work never reaches the main branch on the
machinery's own initiative, and every item merged and every card ruled
is necessary but never sufficient. The condition SHALL be read from the
milestone state the unlanded items carry, so it holds for a milestone
whose every assertion is already `closed:merged`.

A landing the operator or the server **forces** SHALL pass this
condition. A forced landing is a claim about what this process knows —
the operator landing deliberately, or the server resuming a run that
died between the last merge and its landing — and the close it stands in
for has, in that case, already been made or is being made by the same
hand.

**Two release conditions stand, and neither subsumes the other.** The
open-unit-card hold specified in `flywheel-derived-backlog` ("The
landing is the bolt's boundary, held by any open unit card") and this
milestone-close condition answer different questions and SHALL both be
enforced:

- an open unit card means the **bolt is still being planned** — the
  operator has a card left to rule, so what would land is not yet the
  whole bolt;
- an open milestone means the operator **has not released** what is
  built — the work may be complete and still not theirs to land yet.

The milestone-close condition is one of the "existing preconditions"
that the card-hold requirement defers to when it says the landing
proceeds under them and gains no new ones. Adding the card hold SHALL
NOT be read as having replaced this one, and this requirement SHALL NOT
be read as weakening the card hold.

**The card hold is asked first, and its answer is final.** When both
conditions are outstanding, the run's landing line SHALL report the
hold and name the holding card — not the milestone — because the card
is the gesture the operator can act on next and the hold is the more
specific fact. The two conditions differ in one further way, which the
loop SHALL preserve: a forced landing passes the milestone-close
condition and SHALL NOT pass the card hold, since a card is the
operator's own unfinished gesture and the way past it is to rule it.

#### Scenario: An open milestone declines an automatic landing

- **WHEN** every unlanded assertion on `bolt/<slug>` is `closed:merged`,
  no unit card is open on the milestone, and the milestone itself is
  still open
- **THEN** no landing session runs, nothing reaches the main branch, and
  no item is upgraded to `closed:done`

#### Scenario: The operator's close releases it

- **WHEN** the same bolt's milestone is closed and the loop runs again
- **THEN** the landing proceeds under its remaining preconditions, and
  the units on the milestone are closed at that one landing

#### Scenario: Both conditions outstanding

- **WHEN** the milestone is open **and** an open unit card sits on it
- **THEN** the run's landing line reports the hold and names that card by
  number, rather than naming the milestone or reading "not attempted"

#### Scenario: A forced landing on an open milestone whose cards are all ruled

- **WHEN** a landing is forced on a bolt whose assertions have all merged
  and whose milestone is still open, with no open unit card on it
- **THEN** the landing runs — the force passes the milestone-close
  condition

#### Scenario: A forced landing with a card still open

- **WHEN** a landing is forced on a bolt that still holds an open unit
  card
- **THEN** it is held exactly as an automatic landing would be, and the
  landing line names the card
