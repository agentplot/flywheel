# flywheel-derived-backlog Specification

## Purpose
TBD - created by archiving change derived-backlog. Update Purpose after archive.
## Requirements
### Requirement: The fleet manifest binds books to built repos

`fleet.yaml` SHALL carry a `books:` block — one entry per system the
fleet homes — naming the design book's checkout path, the built
repo's checkout path, the Team a filed plan card carries, and
optionally the settle window in minutes (default 90). The server
reads the bindings at start; a system without a binding gets no
planning runs.

#### Scenario: binding read

- **WHEN** the manifest carries `books: {flywheel: {book: B, repo: R, team: T}}`
- **THEN** the server's config holds the binding and the reconcile
  pass evaluates it

### Requirement: Unapproved plan cards are marked stale

Every plan card records the book and spec commits it derived from.
The reconcile pass SHALL compare those against the current heads and
add the `stale` label to an unapproved card whose inputs have moved —
once, idempotently. The marker is information, never a lock: a stale
card remains approvable.

#### Scenario: book moves under a card

- **WHEN** the book's head no longer matches a card's recorded commit
- **THEN** the pass adds `stale` to the card and a second pass adds
  nothing

### Requirement: A planning run is charged when cards are missing or stale on a settled book

The reconcile pass SHALL charge one planning-run session per system
when the system has no open plan cards or only stale ones, and the
book has been quiet — no commit touching it — for the settle window.
The charge carries the work order the bolt-planning skill defines
(book, repo, board mode, tracker, team) and lands in the run record.
A charge is retried on backoff, never repeated while a run is live.

#### Scenario: first quiet pass on a fresh system

- **WHEN** a bound system has a book, no plan cards, and the book's
  last commit is older than the settle window
- **THEN** the pass charges a planning run

#### Scenario: heavy design day

- **WHEN** the book's last commit is younger than the settle window
- **THEN** no run is charged, whatever the cards' state

### Requirement: A Ready plan card is a bolt job

The server inbox SHALL yield a `run` job for the `bolt/*` milestone an
open `plan` card at board Status Ready sits on, so the bolt loop starts
and expands the card. The milestone the card names is the milestone the
job carries: the server SHALL NOT derive a bolt name from a card's
title, and a card that names no `bolt/*` milestone SHALL yield no job.

The job's reason SHALL name the card and that it awaits expansion, and
SHALL be the reason reported for that milestone even when the same pass
finds another reason for it — the reason is what the run record prints
and what the restart backoff fingerprints, so the card must be legible
as the thing the loop was started for.

The milestone SHALL be open. A Ready card sitting on a closed milestone
SHALL yield no `run` job, leaving that milestone's archive job as its
only job.

A card at board Status Backlog SHALL yield no job: approval is the
operator's flip to Ready, and nothing starts before it.

#### Scenario: card approved

- **WHEN** an open `plan` card at Status Ready sits on the open
  milestone `bolt/<slug>`
- **THEN** the server starts a bolt loop for `bolt/<slug>`, and the
  job's reason names that card as awaiting expansion

#### Scenario: the milestone has another reason too

- **WHEN** a Ready card's milestone also holds a batch at Status Ready
  or an item at `state:ready` on the same pass
- **THEN** one `run` job is reported for that milestone and its reason
  names the card awaiting expansion

#### Scenario: a card naming no bolt milestone

- **WHEN** an open `plan` card sits at Status Ready with no `bolt/*`
  milestone, whatever its title says
- **THEN** the server starts nothing for it and no job names a
  milestone the tracker does not hold

#### Scenario: a card on a closed milestone

- **WHEN** a Ready card sits on a `bolt/*` milestone the operator has
  closed
- **THEN** no `run` job is yielded for that milestone, and its archive
  job — if its change still sits in `openspec/changes/` — is unchanged

#### Scenario: card awaiting approval

- **WHEN** an open `plan` card sits at Status Backlog on its milestone
- **THEN** the server starts nothing for it

### Requirement: Expansion turns the approved card into the bolt

On its first pass for an unexpanded Ready card, the bolt loop SHALL:
create the `bolt/<slug>` milestone; move the card onto it and swap
its `plan` label for `unit`; consume the card's Ready status; file
one work item per plan task at `state:ready` — title from the task's
change, body carrying its deliverable, chapter citations, and
`after` — each a sub-issue of the unit; and write the plan document
into the bolt's charter in the change directory. Expansion is
idempotent: a second pass against an expanded card writes nothing.

#### Scenario: expansion

- **WHEN** the loop's first pass finds its Ready, unexpanded card
- **THEN** milestone, unit, items, consumed status, and charter all
  exist, and the next pass drives the items

### Requirement: A card without Team refuses expansion

Expansion SHALL refuse a card carrying no Team: the loop labels the
card `needs-operator` with the reason as a comment and pauses.

#### Scenario: unroutable card

- **WHEN** a Ready card carries no Team
- **THEN** the loop pauses with `needs-operator` and expands nothing

### Requirement: A card blocked by an unlanded predecessor defers

When a Ready card is blocked by an issue that is not closed
`closed:done`, expansion SHALL defer — the pass records the wait in
the run record and stops without refusing or altering the card.

#### Scenario: approved out of order

- **WHEN** card B is Ready and blocked by card A, and A is not closed
  done
- **THEN** the loop defers, and expands B on a later pass once A is
  closed done

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

### Requirement: Unexpanded cards count as outstanding work

`flywheel status` SHALL report every open, unexpanded `plan` card as
outstanding work on its bolt, so a planned bolt is never invisible
between the planning run and expansion.

A card at Status Ready SHALL appear through its milestone's job row. A
card at Status Backlog SHALL appear under what waits on the operator,
naming the card, the `bolt/*` milestone it sits on, and that the flip
to Ready releases it — the report SHALL NOT treat a milestone holding
only unapproved cards as quiet.

A card at Status Ready that names no `bolt/*` milestone SHALL appear
under what waits on the operator with that defect named, since the
server yields no job for it: a card the filter declines to read is
reported, never silently dropped.

`status` SHALL start nothing on account of any card, and a tracker it
cannot read SHALL remain a reported line rather than a failure.

#### Scenario: a bolt awaiting its first approval

- **WHEN** a planning run has filed cards on `bolt/<slug>` and none has
  been moved to Ready
- **THEN** `flywheel status` lists each card under what waits on the
  operator, naming its number, `bolt/<slug>`, and the flip to Ready

#### Scenario: an approved card is already counted

- **WHEN** a card on `bolt/<slug>` sits at Ready
- **THEN** the milestone appears in the job rows with the card as its
  reason, and the card is not also listed as waiting on the operator

#### Scenario: an unroutable card is visible

- **WHEN** a card at Ready carries no `bolt/*` milestone
- **THEN** `flywheel status` lists it under what waits on the operator
  and says it names no bolt milestone

#### Scenario: status starts nothing

- **WHEN** `flywheel status` runs against a tracker holding cards in
  any state
- **THEN** no loop process is started and no tracker write is made

