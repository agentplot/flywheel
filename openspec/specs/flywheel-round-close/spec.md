# flywheel-round-close Specification

## Purpose
The round-close plan — how a design session with a next round to propose
ends: one operator approval that closes this round and charges the next,
with nothing on GitHub until the word is given. The protocol's one
shared statement is `skills/_reference/round-close.md`; this spec is the
contract that statement and the code around it must satisfy.

## Requirements

### Requirement: The plan is files, and the page is a view over them

A round-close plan SHALL be real committed files in the session's own
directory — `close/plan.html`, `close/elaboration.md`,
`close/bolt-summary.md`, `close/units/<slug>.md` — and the lavish page
SHALL render the markdown files rather than restate them. The unit
documents SHALL use the bolt-planning skill's exact card grammar, and
the apply SHALL post each file's content verbatim: the summary as the
milestone description, each unit document as its card body. Nothing is
reformatted between the round and the board.

#### Scenario: A card lands on the tracker

- **WHEN** an approved plan's unit card is filed
- **THEN** its body is byte-identical to the `close/units/<slug>.md` the
  operator annotated, plus the `System:` line the board mode adds

### Requirement: Nothing reaches GitHub before approval

A session preparing a round-close plan SHALL create no issue, batch,
milestone, or card ahead of the operator's approval. Every tracker
object the plan describes SHALL be born in the apply, so an iterated or
abandoned plan strands nothing on the board and races nothing the
loop's compose guard does.

#### Scenario: The operator abandons a plan

- **WHEN** a round-close plan is rejected outright and the session
  redrafts
- **THEN** no tracker object exists from the rejected draft — the only
  trace is the files in the session directory

### Requirement: Routing is exclusive and the chain carries the sequencing

Every outcome on the plan SHALL resolve to exactly one routing value:
`elaboration`, `unit card`, `hold` (filed `state:queued`, out of this
round), `drop` (not filed), or `answered` (questions only — the answer
becomes a decision record and no item is filed). No dependency edge
SHALL span the elaboration and construction sections.

The test for `unit card` SHALL be the card's sources: it cites what
exists — a decision record, the session's own records, a chapter
already written. An outcome with no source a spec could be written from
SHALL route to a writeback item instead, and that writeback session's
own close round cards it. `builds on` edges between units inside the
construction section remain bolt-planning's mechanic and are unaffected.

#### Scenario: The records already say everything a spec needs

- **WHEN** an outcome's construction can cite the session's decision
  records as its sources
- **THEN** it is carded in this plan with no writeback ahead of it

#### Scenario: The book does not say it yet

- **WHEN** an outcome's construction has no citable source
- **THEN** the plan routes it to a writeback item, files no card for it,
  and writes no blocked-by edge — the writeback session's close round
  is where the card is born, citing the chapter it just wrote

### Requirement: The apply order is load-bearing

On approval the session SHALL apply the operator's word in this order:
(1) fold answered questions into `decisions/` and commit every close
file, so the branch is merge-complete before any tracker write; (2)
create the elaboration's items and compose the batch at Backlog —
titled `Elaboration: <slug> — round N`, amending an open Backlog
elaboration via `--into` instead of creating a second; (3) file the
construction through bolt-planning's board mode at Backlog; (4) write
`stage:done` on its own items; (5) flip the elaboration parent and the
approved cards to board Ready; (6) settle. `stage:done` SHALL precede
every Ready flip, so a loop restart mid-apply merges the finished
branch before the released batch can dispatch; an apply interrupted
before the Ready flip leaves the batch at Backlog, which the operator's
ordinary board flip finishes.

Step 5 is the one exception to a session never moving an item to
`state:ready`: applying the operator's explicit approval given in a
round the session itself ran.

#### Scenario: The loop restarts between the flips

- **WHEN** a loop process restarts after the apply's `stage:done` writes
  and before its Ready flips
- **THEN** the loop collects and merges the session's finished branch
  before anything newly released could dispatch, and the batch waits at
  Backlog for a board flip

#### Scenario: An apply step fails

- **WHEN** any apply step fails
- **THEN** the session stops the apply where it is, comments the partial
  state on its item, adds `needs-operator`, and does not settle

### Requirement: Iteration supersedes, and the fallback path stays

Partial approval SHALL fold: a struck row is re-routed or left unfiled
and the approved remainder proceeds; nothing becomes Ready by silence.
After an apply, a session-proposed elaboration or card that a later
iteration replaces wholesale SHALL close `closed:superseded` with a
successor pointer, and smaller changes SHALL amend the open Backlog
batch in place. The chain is an option: a session with nothing to
propose settles as today, and the compose guard and board flip remain
the release path for whatever no session proposed.

#### Scenario: A later round replaces an applied plan's batch

- **WHEN** an iteration replaces a filed elaboration wholesale
- **THEN** the replaced parent closes `closed:superseded` pointing at its
  successor, and nothing the abandoned plan filed stays live on the
  board
