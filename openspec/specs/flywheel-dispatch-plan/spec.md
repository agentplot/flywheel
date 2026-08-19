# flywheel-dispatch-plan Specification

## Purpose
The dispatch plan — the one routing surface put before the operator
wherever a batch of outcomes needs routing: a design session's close,
dispatch's triage of raw ideas. One approval places every outcome, with
nothing on GitHub until the word is given. The protocol's one shared
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
others, never the plan's definition; the Discord digest SHALL render the
same payload as text, and both SHALL resolve to the same decision
contract.

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

For a design-session origin the payload SHALL be real committed files in
the session's own `close/` directory — the page a view over them, never
a restatement — with unit documents in bolt-planning's exact card
grammar, posted verbatim at apply. For the dispatch origin the payload
SHALL be embedded in one self-contained surface under the org folder's
untracked scratch, because dispatch holds no checkout and writes no
records; the tracker objects the apply writes are the record.

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
`answered` path. A reply the applying actor cannot resolve into exactly
one contract SHALL be asked again, never guessed.

#### Scenario: The operator replies "yes to all" over Discord

- **WHEN** the digest's reply is "yes to all"
- **THEN** the apply runs with every route, type, and name exactly as
  the payload seeded them

#### Scenario: A correction by number

- **WHEN** the reply is "3 -> hold, 2 as bolt-quick"
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

Every row SHALL resolve to exactly one route: for an intent row `next
round`, `hold` (filed `state:queued`, out of this round), `drop` (not
filed), or `answered` (questions only — the answer becomes a decision
record and no item is filed); for a bolt row `file the card`, `hold`, or
`drop`, with the unit's bolt type seeded and overridable. A retarget
re-files a row under another container of the same kind and is not a
route.

The test for `file the card` SHALL be the card's sources: it cites what
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

On approval the actor SHALL apply the operator's word in this order: (1)
fold answered questions into `decisions/` and commit every payload file,
so the branch is merge-complete before any tracker write — the dispatch
origin, which commits nothing, starts at (2); (2) per intent container
in plan order, at Backlog: create the milestone and originating item
when new, create member items — a triage row that is an intake issue is
moved onto the milestone, never duplicated — and compose the elaboration
(`--into` an open Backlog elaboration instead of creating a second); (3)
per bolt container, at Backlog: reuse the open bolt's milestone or
create the new one with the summary as its description, then
bolt-planning's board mode, superseding only cards this plan explicitly
replaces; (4) write `stage:done` on the items the session carries —
dispatch carries none; (5) flip every approved elaboration parent and
card to board Ready, including cards folded onto an open running bolt,
which the live loop expands mid-flight; (6) settle. `stage:done` SHALL
precede every Ready flip; an apply interrupted before its Ready flips
leaves batches at Backlog, which the operator's ordinary board flip
finishes, per container independently.

Step 5 is the one exception to an actor never moving an item to
`state:ready`: applying the operator's explicit approval given in a
round the actor itself ran.

#### Scenario: The loop restarts between the flips

- **WHEN** a loop process restarts after the apply's `stage:done` writes
  and before its Ready flips
- **THEN** the loop collects and merges the session's finished branch
  before anything newly released could dispatch, and the batches wait at
  Backlog for a board flip

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
settles as today, and the compose guard and board flip remain the
release path for whatever no plan proposed.

#### Scenario: A later round replaces an applied plan's batch

- **WHEN** an iteration replaces a filed elaboration wholesale
- **THEN** the replaced parent closes `closed:superseded` pointing at its
  successor, and nothing the abandoned plan filed stays live on the
  board
