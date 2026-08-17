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

### Requirement: A card without Team refuses expansion

Expansion SHALL refuse a card carrying no Team: the loop labels the card
`needs-operator` with the reason as a comment — the unit is unroutable —
and pauses, expanding nothing and leaving the bolt's other units
untouched.

#### Scenario: unroutable card

- **WHEN** a Ready card carries no Team
- **THEN** the loop pauses with `needs-operator` and expands nothing

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

