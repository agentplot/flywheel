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

### Requirement: The bolt's charter is the bolt's own statement

`openspec/changes/<slug>/bolt.md` is the bolt's charter and carries the
bolt-level statement alone: the delivery, the unit sequence and price,
and the merge criteria the landing verifies. It SHALL carry the sections
the bound `bolt-*` schema's `bolt.md` template names — scope, sources,
repos, and merge criteria with the landing mode stated on its `Landing:`
line — and SHALL carry no unit's plan document. The record mirrors the
board one-to-one: one charter per bolt.

**The charter is born at scaffold, from the milestone's description.**
The description the planner authored — the delivery in three sentences,
the unit sequence, the total price — SHALL be carried to the session that
writes the charter, so the sections are written from it rather than
re-derived or guessed. This SHALL hold for a planner-born bolt exactly as
for one the operator dictated: a milestone carrying unit cards is not a
reason to write a unit and skip the bolt. A bolt whose milestone carries
no description SHALL still get its sections, written from what the
milestone and its items say; an absent description is a thinner charter,
never a missing one.

**A charter that is absent is written, never assumed present.** The test
that decides whether a charter is owed SHALL be `bolt.md` itself, not the
change directory that holds it: a change directory that exists carrying
no `bolt.md` SHALL be driven to a charter on the same pass that finds it,
and SHALL NOT be read as a bolt whose charter is already written. This
covers the record whose directory was created and whose charter was not —
a scaffold that settled without writing one, or a change made by any
other hand — and it holds on every pass after the first, so a record that
was charterless when the stages began does not stay charterless because a
directory was there.

**A charter owed to an existing change is asked for as an addition to
it.** Where the change directory is already present, the session SHALL be
ordered through the invocation that adds a missing artifact to an
existing change, not the one that creates a change: an order to create a
change that exists cannot be obeyed, and a session that cannot obey its
order writes nothing while reading as settled. What the order asks for
SHALL be the same on both paths — the four sections, the `Landing:` line
stated, the milestone's description as the charter's stated source, and
no unit's plan document — so the charter a record gets does not depend on
which path wrote it.

**A charter that is present is left exactly as it stands.** Where
`bolt.md` exists, this guard SHALL drive no session and write nothing,
whether or not the charter reads back merge criteria. A charter that has
lost its sections, or never carried them, is named by the landing's
refusal; rewriting it here would put a guard over committed prose, which
outranks the state it came from. A pass over a record whose charter is
present SHALL record no action, which is the loop's dry-cycle property.

**The charter is checked, not assumed.** After the session that writes
the charter settles, the loop SHALL read `bolt.md` and confirm it carries
a merge-criteria section with a body. A charter that does not SHALL stop
the cycle with a reason naming the change directory and what is missing:
a settle is not the whole post-condition. The check SHALL use the same
reader the landing reads the criteria through, so "the guard passed" and
"the landing can read it" cannot disagree, and it SHALL read the file, so
a later pass over a charter that has since gained its sections passes
without re-driving anything. The check SHALL apply to every path that
drives a charter session, so a charter written into an existing change is
held to what a charter written with its directory is held to.

**The bolt's merge criteria are read from the charter's own region.**
The region ends at the first `# `-level heading that opens a unit
section, so prose left in an older `bolt.md` under a `# Unit: <slug>`
heading SHALL NOT be read as this bolt's merge criteria however it is
subdivided. A charter with no such heading is its own region entire.

**A landing mode that was defaulted is not a mode that was declared.**
Because the charter states its `Landing:` line, the reader that picks
merge or pull request finds a declaration rather than falling through to
its default on a charter that said nothing.

#### Scenario: a planner-born charter

- **WHEN** a bolt's change directory is scaffolded on a milestone that
  carries unit cards and a description the planner authored
- **THEN** `bolt.md` carries the scope, sources, repos and merge criteria
  written from that description, with the `Landing:` line stated, and no
  unit's plan document anywhere in the file

#### Scenario: a bolt whose milestone carries no description

- **WHEN** the milestone has no description — a bolt born at triage, or
  one whose description was never written
- **THEN** the charter still carries all four sections, written from what
  the milestone and its items say, and the scaffold does not pass on a
  charter that carries none of them

#### Scenario: a change directory that exists without a charter

- **WHEN** a pass finds `openspec/changes/<slug>/` present and
  `openspec/changes/<slug>/bolt.md` absent
- **THEN** a session is driven to write the charter into that change,
  ordered through the invocation that adds an artifact to an existing
  change and asked for the same four sections, `Landing:` line and
  description-borne content as a charter written with its directory

#### Scenario: the scaffold that settled without writing one

- **WHEN** a scaffold session created the change directory and settled
  without a `bolt.md`, stopping that cycle, and a later pass runs over
  the record it left
- **THEN** the later pass drives the charter again rather than reading
  the directory as evidence that the charter was written, and the record
  does not reach the stages carrying no charter

#### Scenario: the charter comes back without its sections

- **WHEN** the session that was driven to write the charter settles and
  `bolt.md` carries no merge-criteria section, or carries an empty one
- **THEN** the cycle stops with a reason naming the change directory and
  the missing sections, and the run does not proceed to the stages —
  whichever path drove that session

#### Scenario: a charter already present is not this guard's business

- **WHEN** a pass finds `bolt.md` present, whether it reads back merge
  criteria or not
- **THEN** no session is driven, nothing is written, no action is
  recorded, and a charter that reads back nothing is left for the
  landing's refusal to name

#### Scenario: a dry run over a charterless record

- **WHEN** the loop runs without writing and finds a change directory
  carrying no `bolt.md`
- **THEN** it reports the charter it would write into that change,
  launches no session and leaves the tree untouched

#### Scenario: a leftover unit section cannot supply the criteria

- **WHEN** a `bolt.md` written under the older shape carries a
  `# Unit: <slug>` section whose plan document contains its own
  `## Merge criteria` subsection, and no merge criteria above it
- **THEN** this bolt's merge criteria read as absent, and the unit's
  prose is never read as the bolt's criteria

### Requirement: Each approved unit's document is its own artifact

A plan document is mutable state on the tracker while its card is
unapproved. The operator's approval freezes it, and expansion is what
makes it durable prose in git. The loop SHALL write each expanded unit's
plan document to `openspec/changes/<slug>/units/<unit-slug>.md` —
verbatim from the body of the card the operator approved, one file per
approved unit, named by the slug the card's title carries. The write
SHALL be committed to the bolt's change directory on the branch that
carries the bolt's record — main only before the bolt branch is cut, the
bolt branch after.

The unit artifacts are not written into the charter. `bolt.md` is the
bolt's statement and a unit file is the approval's, and neither is
appended to the other.

**A unit whose file is already present SHALL NOT be written again**, so a
pass with nothing newly expanded makes no commit and the loop keeps its
dry-cycle property. The test SHALL be the committed state of the record,
not a stored flag and not the working tree alone: a pass following an
interrupted commit SHALL re-run the commit rather than read the file it
already wrote as evidence that the write is done.

A unit file already on disk SHALL NOT be overwritten, whether the loop
wrote it or a hand did: durable prose in git outranks the mutable tracker
state it came from.

#### Scenario: the first unit

- **WHEN** the first card on a bolt's milestone is expanded
- **THEN** `units/<unit-slug>.md` is written with that card's body
  verbatim and committed, and `bolt.md` is unchanged by it

#### Scenario: a second unit expands

- **WHEN** a second card on the same milestone is expanded
- **THEN** a second file appears under `units/`, committed on the bolt
  branch, and the first unit's file and the charter are both unchanged

#### Scenario: nothing newly expanded

- **WHEN** a pass expands no card and every unit on the milestone already
  has its file at HEAD
- **THEN** no unit write and no commit happen

#### Scenario: a torn write is repaired, not read as done

- **WHEN** a previous pass wrote a unit's file but its commit did not
  land
- **THEN** the next pass leaves the file's content alone and re-runs the
  commit, so the record ends carrying it

