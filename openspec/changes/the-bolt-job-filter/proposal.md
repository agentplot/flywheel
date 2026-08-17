## Why

The planner now owns the bolt milestone: a planning run "creates the
`bolt/<slug>` milestone if it does not exist … and files **one card per
unit on that milestone** at board Backlog"
(`books/flywheel/src/bolt-planning.md`, "From plan to board"), and the
tracker chapter's `plan` row reads "one proposed unit on its bolt's
milestone" (`books/flywheel/src/tracker-protocol.md`, "Milestones and
batches"). The card therefore arrives already knowing where it belongs.

The server's filter still reads a card the old way. The requirement "A
Ready plan card is a bolt job" in
`openspec/specs/flywheel-derived-backlog/spec.md` says the inbox yields
a job "for an open `plan` card at board Status Ready **that has no
milestone**, naming `bolt/<slug>` from the card's title" — a card read
as a bolt waiting to be created. The book states the filter the other
way round: "a plan card at Ready awaiting expansion"
(`books/flywheel/src/tracker-protocol.md`, "Inbox filters"), inside a
list of jobs every other clause of which is a fact about an existing
milestone, and the pass "reads the tracker, computes which milestones
have a job" (`books/flywheel/src/server-and-fleet.md`, "The reconcile
pass"). A name synthesized from a title is not a milestone the tracker
holds, so under the new shape it can name a milestone that does not
exist while the one the card sits on goes unstarted.

The second half is the operator's view. The chapter's CLI table says
`flywheel status` "reports … every milestone with a job, and what waits
on the operator" (`books/flywheel/src/server-and-fleet.md`, "The CLI"),
and the board walk makes an unapproved card the one thing standing
between a planned bolt and its construction: "the operator moves a card
to Ready | the server starts the bolt loop"
(`books/flywheel/src/tracker-protocol.md`, "The board through one
bolt"). A card is now the whole approval surface for construction work,
and today `status` counts only batches — an unexpanded card is
outstanding work on its bolt that the fleet's own report cannot see.

## What Changes

- The server inbox yields the `run` job for the **open `bolt/*`
  milestone the Ready card sits on**, and the job's reason names the
  card awaiting expansion — the reason is what the run record prints
  and what the restart backoff fingerprints, so a milestone that also
  earns a Ready-batch reason on the same pass still reports the card.
- A Ready card whose milestone is closed yields no `run` job; the
  archive job is that milestone's only job.
- **BREAKING** for a card filed under the old shape: a card that names
  no `bolt/*` milestone yields no job at all. The server stops deriving
  a bolt name from a card's title — a card is no longer read as a bolt
  waiting to be created.
- `flywheel status` counts every open unexpanded card as work on its
  bolt: a card at Ready through its milestone's job row, a card at
  Backlog under what waits on the operator, naming the card, its bolt,
  and that the flip to Ready releases it. A card at Backlog still
  starts nothing.
- A Ready card the filter declines to route — no `bolt/*` milestone —
  is reported under what waits on the operator with that defect named,
  so a card the server will not read is visible rather than silent.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `flywheel-derived-backlog`: the requirement "A Ready plan card is a
  bolt job" is restated over the card's own milestone, and one
  requirement is added for the operator-facing count of unexpanded
  cards in `flywheel status`.

## Impact

- `openspec/specs/flywheel-derived-backlog/spec.md` — one modified
  requirement, one added.
- `bin/_flywheel_inbox.py` — the card block in `server_inbox` (today
  "An approved plan card is a job for its bolt"), `PlanCard.bolt`
  (today falling back to "the title slug for a card filed before
  milestones were the planner's"), and the card rows `Tracker.snapshot`
  builds, which carry no milestone state today.
- `bin/flywheel` — `server_rows`, whose "waiting on the operator" list
  is built from board batches at Backlog and so never mentions a card.
- `tests/test_derived_backlog.py` — the filter's tests, which pin the
  Ready and Backlog cases today.
- Read from disk at this writing and to be re-read at build time: the
  bolt loop's two card readers, `_flywheel_bolt_loop.py`'s expansion
  guard and its landing hold, both of which compare `c.bolt ==
  self.params.milestone`. A card carrying its milestone reads the same
  either way, so retiring the title fallback leaves both matching; a
  card without one stops matching, which is this change's intent.
- Out of scope, each its own change in this unit: expansion's own
  behavior (`expansion-makes-a-unit`), the landing's precondition
  (`the-landing-waits-for-the-cards`), and the staleness and
  planning-run triggers, which do not change with the card's shape.
