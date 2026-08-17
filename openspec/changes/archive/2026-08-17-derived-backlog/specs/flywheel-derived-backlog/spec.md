# flywheel-derived-backlog

## ADDED Requirements

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

The server inbox SHALL yield a bolt job for an open `plan` card at
board Status Ready that has no milestone, naming `bolt/<slug>` from
the card's title, so the bolt loop starts and expands it.

#### Scenario: card approved

- **WHEN** a plan card sits at Status Ready with no milestone
- **THEN** the server starts a bolt loop for the card's slug

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
changes in flight, and its only tracker writes are the plan cards —
with the card title `Bolt: <slug>`, a `System:` line and the input
commits in the body, Team set at filing, builds-on mirrored as
blocked-by, and earlier unapproved cards closed `closed:superseded`.

#### Scenario: run files cards

- **WHEN** a planning run proposes two bolts, the second building on
  the first
- **THEN** two cards exist at Backlog, the second blocked by the
  first, and any earlier unapproved cards are closed superseded
