# flywheel-dispatch-plan Specification

## Purpose
The dispatch plan — the one routing surface put before the operator
wherever a batch of outcomes needs routing: a design session's close,
a bolt's routed findings, dispatch's triage of raw ideas, a
close-ready milestone. Origins author and publish payloads; dispatch
runs every round and applies the one approval that places every
outcome, with nothing on GitHub until the word is given. The protocol's one shared
statement is `skills/_reference/dispatch-plan.md`; this spec is the
contract that statement and the code around it must satisfy.

## Requirements

### Requirement: The plan is three separable layers

A dispatch plan SHALL consist of three layers, each defined
independently of the others: the **payload** (the plan as data — the
markdown bodies and the `plan-data` JSON, every proposal placed in a
container with its choice seeded), the **decision contract** (what any
surface sends back), and a **surface** (a renderer of the payload that
collects the contract). The lavish page SHALL be one surface among
others, never the plan's definition; the Discord digest SHALL carry the
page's link and one line per row — no caveats, no per-row prose, every
URL embed-suppressed — and both SHALL resolve to the same decision
contract.

#### Scenario: A chore card costs one approval and ten words per chore

- **WHEN** a plan carries a `chore`-labeled card
- **THEN** the page renders it as one row whose change list — one plain
  line per chore — is the full text, the digest renders it as a single
  `N chores · bolt/<slug>` line, and one approval releases every chore
  on the card

#### Scenario: The digest is a link and a blurb

- **WHEN** a round's Discord message is composed
- **THEN** it opens with the served page URL, carries one line of at
  most 80 characters per row and the reply grammar, wraps every URL in
  `<...>`, and repeats nothing the page already says

#### Scenario: The same plan is answered from two surfaces

- **WHEN** a plan's page is open and its digest has been relayed
- **THEN** whichever answer arrives first is the round's answer, and
  applying it produces the same tracker writes regardless of which
  surface carried it

### Requirement: The payload is placed proposals in containers

A payload SHALL place each proposed outcome as a row under exactly one
container — an intent (its next elaboration, plus the intent itself when
`status` is `new`) or a bolt (an existing open bolt the rows fold into,
or a new one). A plan MAY hold multiple intent and multiple bolt
containers. No dependency edge SHALL span containers; `builds on` edges
between units remain bolt-planning's mechanic inside one bolt container.

A bolt container SHALL carry a `deliverable` line stating what the
operator sees working, and MAY carry `alternates` naming the open bolts
its units could fold into instead — the bolt-selection choice made
visible and correctable on the surface. The selection rule itself is
bolt-planning's: named for the operator's deliverable, folded into an
open bolt whose deliverable the units serve, split easy-into-open /
hard-into-successor.

For a session origin (design-session close, findings-routing) the
payload SHALL be real committed files in the session's own `close/`
directory — the page a view over them, never a restatement — with unit
documents in bolt-planning's exact card grammar, posted verbatim at
apply. Dispatch's own triage rows need no files: the intake issues are
the inbox, and the round's one self-contained surface lives under the
org folder's untracked scratch, because dispatch holds no checkout and
writes no records; the committed payloads and the tracker objects the
apply writes are the record.

### Requirement: Every design-session close publishes — the dead end included

A design session SHALL end by publishing a payload proposing one of
three things: a next round (elaboration rows), construction (cards), or
**closure** — no containers, the session's outcome and its items as
`done_items`. An elaboration SHALL NOT end silently: either the
operator was in the session, or its close is a row in the next round.
The round renders closure payloads as finished-elaboration rows, seeded
approve; approving writes `stage:done` on the `done_items`, and a note
typed on the row is instead commented on each of those items with no
`stage:done`, so the loop's next pass charges a fresh session carrying
the steer. Either way the payload is consumed.

#### Scenario: A dead-end elaboration reaches the operator

- **WHEN** a design session finds nothing to propose and settles
- **THEN** its closure payload stands for the round, whose row carries
  the outcome — and "yes to all" signs it off while a typed note sends
  a fresh session after it

### Requirement: Origins publish; dispatch assembles and runs every round

A session origin SHALL end by publishing, not by running a round:
commit the payload files by pathspec, push the branch, write the
round-payload marker (repo, a 40-hex commit SHA, the payload
directory, the origin) as a comment on the payload's anchor item, and
add the `dispatch:standing` label there. Dispatch SHALL enumerate
everything standing — `dispatch:standing` items (published payloads,
close-ready unit parents) plus its own unmilestoned intake — assemble
ONE plan, run its surfaces, and apply the approval. Payload files SHALL
be read at the pinned SHA (an actor with no checkout reads them through
the API); a fetch that fails is a reported shortfall in the round,
never a guess. Rounds are serialized: one at a time, material arriving
mid-round seeding the next. As its last act per applied payload,
dispatch SHALL write the round-consumed marker on the anchor and remove
the label; a consumed payload is never re-offered, and a republish
after a send-back supersedes the earlier address. A standing item SHALL
NOT also be relayed as a DM — one wait, one surface.

#### Scenario: A settled session's payload reaches the next round

- **WHEN** a design session publishes its payload and settles, and the
  operator later says "dispatch"
- **THEN** the round dispatch assembles carries that payload's sections
  beside whatever else stands, and the session's pane is not consulted

#### Scenario: A crash between apply and consume

- **WHEN** dispatch dies after applying a payload's containers and
  before writing the consumed marker
- **THEN** the payload still stands and the next round re-applies it —
  every container mechanic is re-runnable, so nothing duplicates

#### Scenario: A batch with nothing left to release is not offered

- **WHEN** a Backlog batch's known members hold nothing queued — every
  member already released, or every member closed
- **THEN** the round derives no approvals row for it, and the loop
  closes a finished elaboration container (every member closed, no
  standing payload, no operator hold) so no later round re-derives it

#### Scenario: A triage splits raw ideas into new intents

- **WHEN** dispatch builds a triage plan over four unmilestoned intake
  issues
- **THEN** the plan may propose two new-intent containers, a row on an
  existing bolt, and a drop — one plan, one approval

#### Scenario: A card lands on the tracker

- **WHEN** an approved plan's unit card is filed
- **THEN** its body is byte-identical to the unit document the operator
  annotated, plus the `System:` line the board mode adds

### Requirement: The decision contract defaults to as-proposed

The decision contract SHALL be
`{decision, note?, routing?, answers?, unit_types?, renames?,
retargets?}`, and an omitted field SHALL mean as-proposed — so
`{"decision": "approve"}` (a "yes to all") approves every seeded choice.
`renames` corrects a proposed container's slug or re-aims a bolt
container at an alternate open bolt; `retargets` moves a row to another
container of the same kind; an inline answer takes the question's
`answered` path; `closes` carries only UNCHECKED close rows (keep that
milestone open — a choice that writes nothing and stands again next
round), so an omitted milestone closes as seeded. A reply the applying
actor cannot resolve into exactly one contract SHALL be asked again,
never guessed.

#### Scenario: The operator replies "yes to all" over Discord

- **WHEN** the digest's reply is "yes to all"
- **THEN** the apply runs with every route, type, and name exactly as
  the payload seeded them

#### Scenario: A correction by number

- **WHEN** the reply is "3 -> backlog, 2 as bolt-quick"
- **THEN** row 3 files `state:queued` out of the round, row 2's card is
  filed with `Type: bolt-quick` written before filing, and everything
  else applies as seeded

### Requirement: Nothing the plan proposes reaches GitHub before approval

An actor preparing a dispatch plan SHALL create no issue, batch,
milestone, card, or item placement ahead of the operator's approval.
Every tracker object the plan proposes SHALL be born in the apply, so an
iterated or abandoned plan strands nothing on the board. The intake
issues a triage plan routes pre-exist as dispatch's inbox and are the
subject of proposals, not proposals; an operator who never takes the
round loses nothing, because unrouted ideas wait unmilestoned.

#### Scenario: The operator abandons a plan

- **WHEN** a dispatch plan is rejected outright and the actor redrafts
- **THEN** no tracker object exists from the rejected draft — the only
  trace is the payload (the session's `close/` files, or the scratch
  surface and the untouched intake issues)

### Requirement: Routing is exclusive and the chain carries the sequencing

Every row SHALL resolve to exactly one route from the one enum, aligned
with the board's own words: `approve` (filed under the row's container —
an item in an intent container's elaboration, or a unit card on a bolt
container), `backlog` (filed `state:queued` on the container's
milestone, out of this round), `drop` (not filed), or `answered`
(questions only — the operator's answer verbatim as a comment carrying
the `<!-- flywheel:answered -->` marker line on the question item,
which closes `closed:done`; the marker, not the reason, is the
machine-readable fact, and no item is filed. A session holding a
worktree may still fold an in-pane answer into `decisions/`, but
nothing new SHALL depend on `decisions/*.md`). On a bolt row the
unit's bolt type is seeded and overridable. A
retarget re-files a row under another container of the same kind and is
not a route.

The test for approving a bolt row SHALL be the card's sources: it cites what
exists — a decision record, the session's own records, a chapter already
written. An outcome with no source a spec could be written from SHALL
route to a writeback item instead, and that writeback session's own
close cards it.

#### Scenario: The records already say everything a spec needs

- **WHEN** an outcome's construction can cite the session's decision
  records as its sources
- **THEN** it is carded in this plan with no writeback ahead of it

#### Scenario: The book does not say it yet

- **WHEN** an outcome's construction has no citable source
- **THEN** the plan routes it to a writeback item, files no card for it,
  and writes no blocked-by edge — the writeback session's close is where
  the card is born, citing the chapter it just wrote

### Requirement: The apply order is load-bearing

On approval dispatch SHALL apply the operator's word — every write a
tracker write, the payload files having been committed at publish — in
this order: (1) answers: the marked comment and `closed:done` close on
each answered question item; (2) per intent container in plan order, at
Backlog: create the milestone and originating item when new, create
member items — a triage row that is an intake issue is moved onto the
milestone, never duplicated — and compose the elaboration (`--into` an
open Backlog elaboration instead of creating a second); (3) per bolt
container, at Backlog: reuse the open bolt's milestone or create the
new one with the summary as its description, then bolt-planning's board
mode, superseding only cards this plan explicitly replaces; (4) write
`stage:done` on each payload's `done_items` — the origin session's own
items; (5) move every approved elaboration parent and card to board
Ready, including cards folded onto an open running bolt, which the live
loop expands mid-flight; (6) close each close row still checked — the
close releases that bolt's landing; a container that filed cards onto a
bolt forces its close row unchecked, never both in one round; (7)
consume each payload and settle. `stage:done` SHALL precede every move
to Ready; an apply interrupted before step 5 leaves batches at Backlog,
which the operator's ordinary board approval finishes, per container
independently.

Step 5 is the one exception to an actor never moving an item to
`state:ready`: dispatch applying the operator's explicit approval given
in the round it ran.

#### Scenario: An elaboration batch is released by Approve-as-seeded

- **WHEN** a round's approvals container carries an elaboration batch at
  Backlog and the operator approves the plan without touching its row
- **THEN** the row applies as `ready` — the elaboration's seed — and
  step 5 moves the batch to board Status Ready; only a `stale` card or
  other non-elaboration row seeds `leave`

#### Scenario: The loop restarts mid-apply

- **WHEN** a loop process restarts after the apply's `stage:done` writes
  and before its moves to Ready
- **THEN** the loop collects and merges the session's finished branch
  before anything newly approved could dispatch, and the batches wait at
  Backlog for the operator's board approval

#### Scenario: An apply step fails

- **WHEN** any apply step fails
- **THEN** the actor stops the apply where it is, comments the partial
  state, adds `needs-operator`, and does not settle — and no other
  container's filed Backlog objects are disturbed

### Requirement: Iteration supersedes, and the fallback path stays

Partial approval SHALL fold: a struck row is re-routed or left unfiled
and the approved remainder proceeds; nothing becomes Ready by silence. A
send-back within the payload's scope is the plan's author's to redraft
and re-open. After an apply, a plan-proposed elaboration or card that a
later iteration replaces wholesale SHALL close `closed:superseded` with
a successor pointer, and smaller changes SHALL amend the open Backlog
batch in place. The plan is an option: a session with nothing to propose
settles as today, and the compose guard and the operator's board
approval remain the path for whatever no plan proposed.

#### Scenario: A later round replaces an applied plan's batch

- **WHEN** an iteration replaces a filed elaboration wholesale
- **THEN** the replaced parent closes `closed:superseded` pointing at its
  successor, and nothing the abandoned plan filed stays live on the
  board
