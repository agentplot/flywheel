# flywheel-dispatch-to-bolt Delta

## ADDED Requirements

### Requirement: Dispatch authors a plan card from the operator's dictation

When the operator states construction work exactly — what to build, where it
lands — dispatch SHALL deliver it as a plan card, the same artifact the bolt
planner files, and nothing else: no loose items, no unit parents, no
`state:*` labels, no board Status.

The card SHALL be titled `Unit: <slug>`, SHALL sit on a `bolt/<slug>`
milestone — created by dispatch when no open bolt milestone fits the work —
SHALL carry the `plan` label, and SHALL be added to the org Project at
Status Backlog with the fleet's Team value. Its body SHALL be a unit
document: a task table with one change per row (change name, what it
delivers, `after` where tasks chain), the unit's type, and its price.
Chapter citations appear when the operator's words named a design source and
are otherwise absent — a dictated card derives from the operator's word, not
from the book.

Approval SHALL remain the operator's own board gesture. Dispatch SHALL NOT
set Status Ready, whatever the operator's phrasing at dictation — the word
that authorizes filing the card is not the gesture that starts the work.

#### Scenario: The operator dictates trivial work

- **WHEN** the operator tells dispatch exactly what to build and no open
  bolt milestone covers it
- **THEN** dispatch creates `bolt/<slug>`, files one `plan`-labeled card
  titled `Unit: <slug>` on it with a unit document as its body, at board
  Backlog with the fleet's Team — and creates no work items and sets no
  Ready status

#### Scenario: The dictated work belongs to a live bolt

- **WHEN** the operator's stated work falls inside an open bolt's delivery
  boundary
- **THEN** dispatch files the card on that bolt's existing milestone, and
  the landing holds for it like any open plan card

### Requirement: Expansion of an approved card is the only birth of work items

Construction work items SHALL be created by exactly one path: the bolt
loop's expansion of a plan card at board Status Ready. The loop SHALL NOT
charge routing sessions for items queued on a bolt milestone, and SHALL NOT
compose queued items into units. A queued item on a bolt milestone is inert
to machinery: it waits until an author — the planner, dispatch, or the
operator — folds its content into a plan card, and the card carries it from
there.

#### Scenario: A queued item on a bolt milestone stays inert

- **WHEN** an open item labelled `state:queued` sits on a `bolt/*` milestone
  with no parent batch
- **THEN** the loop's cycle charges no session about it, creates no unit
  from it, and moves it nowhere

#### Scenario: No unit exists that expansion did not make

- **WHEN** any `unit`-labeled parent exists on a `bolt/*` milestone
- **THEN** it is a former plan card relabeled at expansion, and its
  sub-issues were filed by that expansion
