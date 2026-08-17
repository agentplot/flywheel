## Why

The book now says the bolt is the operator's delivery boundary and the
units are the batches built inside it: "The planner creates the
`bolt/<slug>` milestone if it does not exist, writes the bolt summary
… as the milestone's description, and files **one card per unit on
that milestone** at board Backlog"
(`books/flywheel/src/bolt-planning.md`, "From plan to board"), and the
tracker chapter's `plan` row reads "one proposed unit on its bolt's
milestone … the bolt planner creates the milestone and files one card
per unit, at board Backlog"
(`books/flywheel/src/tracker-protocol.md`).

The repo's record still describes the previous shape. The requirement
"The planner session is hosted by its own profile" in
`openspec/specs/flywheel-derived-backlog/spec.md` says the run's "only
tracker writes are the plan cards — with the card title
`Bolt: <slug>`", names no milestone write at all, and its scenario is
phrased over "two bolts, the second building on the first". The
instruction surfaces the planner actually reads — the Board bullet in
`skills/bolt-planning/SKILL.md` and the "Card conventions" bullet in
`agents/flywheel-bolt-planner.md` — already carry the new shape, so
the record and the instructions disagree today, and nothing in
`tests/` pins either side.

The card's title and its home are what every later part of this bolt
reads: expansion looks for a card already on its milestone, the server
filter reads the card's milestone, and the landing counts open unit
cards on the milestone. Fixing the record first is what lets those
changes be written against a true statement of the planner's writes.

## What Changes

- The planner's requirement states that a planning run creates the
  `bolt/<slug>` milestone when it is missing and writes the bolt
  summary — the delivery, the unit sequence, the price — as that
  milestone's description.
- The planner files **one `plan` card per unit onto that milestone**,
  titled `Unit: <slug>`, with the unit document as the body carrying
  its `System:` line and the input commits, added to the org Project
  at Status Backlog with the work order's Team, and each "builds on"
  claim mirrored as a native blocked-by edge between the unit cards.
- Earlier unapproved plan cards are closed `closed:superseded` — kept
  from the current requirement, restated over units.
- The planner's tracker writes are exactly the milestone and the
  cards; it still creates no work items and sets no `state:*` label.
- **BREAKING** for readers of the old card shape: a filed card now
  carries a milestone and the title prefix `Unit:` rather than
  `Bolt:`. The server's bolt-job filter and the expansion guard are
  the two readers, and each is retired by its own change later in this
  unit (`the-bolt-job-filter`, `expansion-makes-a-unit`); this change
  moves only the planner's side.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `flywheel-derived-backlog`: the requirement "The planner session is
  hosted by its own profile" is restated over the bolt-of-units shape
  — the milestone with its summary is a planner write, the card is a
  unit card on that milestone titled `Unit: <slug>`, and the blocked-by
  edges run between unit cards.

## Impact

- `openspec/specs/flywheel-derived-backlog/spec.md` — one modified
  requirement.
- `skills/bolt-planning/SKILL.md` and `agents/flywheel-bolt-planner.md`
  — the two surfaces a planning run reads. Both already state the new
  shape as of this writing; the change makes them the requirement's
  implementation rather than an undocumented lead, and holds them.
- `tests/test_derived_backlog.py` — the planner is a prose-driven
  session, so a record-consistency check over those two surfaces is
  the only thing that can hold this requirement.
- Out of scope, each its own change in this unit: expansion
  (`expansion-makes-a-unit`), the server's bolt-job filter
  (`the-bolt-job-filter`), the landing's precondition
  (`the-landing-waits-for-the-cards`), and the plan card's body format
  beyond title and Team.
