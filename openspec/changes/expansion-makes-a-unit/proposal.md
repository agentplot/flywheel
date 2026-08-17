## Why

The book now says an approved card becomes a **unit inside a bolt**, not
a bolt of its own: "Moving a unit card to Ready is board approval … On
its next pass the bolt loop expands the approved card: the card becomes
the unit, and one work item per task is filed beside it on the
milestone, each citing its chapters"
(`books/flywheel/src/bolt-planning.md`, "Board approval and expansion"),
and the lifecycle chapter states the writes exactly: "Expansion — the
bolt loop's next pass after approval — relabels the card `unit`,
consumes its Ready status, and files the work items beside it as its
sub-issues" (`books/flywheel/src/lifecycles.md`, "The plan card and its
bolt").

The record still describes the previous shape. The requirement
"Expansion turns the approved card into the bolt" in
`openspec/specs/flywheel-derived-backlog/spec.md` opens "On its first
pass for an unexpanded Ready card, the bolt loop SHALL: create the
`bolt/<slug>` milestone; move the card onto it" — but
`planner-owns-the-milestone` (archived, this unit's task 1) made the
milestone and the card's home the *planner's* writes, so expansion now
runs against a card that is already where it belongs, and a bolt sees
expansion once per approved unit rather than once in its life.

Two consequences of the unit shape are live defects rather than
wording:

- **The charter never gains the second unit's plan.** The plan document
  reaches git only through the scaffold guard's work order — "If the
  milestone's unit parent carries a plan document as its body, copy it
  into `bolt.md` verbatim" (`bin/_flywheel_bolt_loop.py`,
  `guard_scaffold`) — and that guard's whole test is
  `if self.params.change_dir.exists(): return None`. A bolt's second
  approved unit finds the directory there and its plan is never written
  down, while the book has expansion copying the plan "into the bolt's
  charter, where it becomes durable prose in git"
  (`books/flywheel/src/bolt-planning.md`, "The planning run"). "The
  milestone's unit parent" is also no longer a unique referent once a
  milestone carries several.
- **The defer predicate deadlocks.** `_expand_card` defers while a
  blocker is not `closed_with(blocker, inbox.CLOSED_DONE)`, which was
  right when a card was a whole bolt and `closed:done` meant that bolt
  had landed. Under bolt-of-units the blocker is a sibling unit card on
  the same milestone; the loop closes units `closed:done` only *after*
  the landing (`books/flywheel/src/lifecycles.md`), and the landing
  itself waits on the cards — so a card blocked by a sibling could
  never expand before the landing, and the landing could never run. The
  book's predicate is the merge, not the landing: "a card approved
  before its named predecessor merges waits, and the run record says
  so" (`books/flywheel/src/bolt-planning.md`, "Board approval and
  expansion"). This bolt is already in it: on the tracker at writing,
  `Unit: one-birth-for-construction` (#221) is blocked by
  `Unit: bolt-of-units` (#220), which is open and stays open until
  `bolt/matches-the-book` lands.

## What Changes

- Expansion is restated over the unit shape: it runs on **any** pass, on
  an open `plan` card at board Ready **already on this bolt's
  milestone**, and relabels it `unit`, drops `stale`, consumes its Ready
  status, and files one `state:ready` work item per plan task on the
  same milestone as sub-issues of that unit. It stays idempotent, and
  several units expand over one bolt's life, one per approval.
- Expansion no longer creates the bolt milestone and no longer moves the
  card onto one: the milestone and the card's home are the planner's
  writes, and a card that is not on this bolt's milestone is not this
  bolt's card to expand.
- The bolt's charter carries **every** expanded unit's plan document —
  one `# Unit: <slug>` section per unit, appended as each is expanded,
  committed on the bolt branch after the branch and its worktree exist.
  Idempotent: a unit whose section is already there is not written
  again.
- The defer predicate becomes the predecessor's **merge**: a Ready card
  defers while any issue blocking it is open and its work is not all in
  — a blocking unit card that is unexpanded, or that still has an open
  sub-issue. A closed blocker, or an expanded one whose every work item
  is closed, satisfies it. The wait is recorded in the run record, and a
  defer is still neither a refusal nor a write.
- The no-Team refusal is unchanged in substance and restated over the
  unit: the unroutable thing is the unit, not the bolt.
- **BREAKING** for a plan card filed before the planner owned the
  milestone: such a card carries no `bolt/*` milestone, and expansion no
  longer creates one for it. `PlanCard.bolt`'s title-slug fallback in
  `bin/_flywheel_inbox.py` is what such a card still rides on, and it is
  the server filter's to retire in `the-bolt-job-filter`; this change
  makes the loop's expansion read `card.milestone` and nothing else.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `flywheel-derived-backlog`: "Expansion turns the approved card into
  the bolt" is restated as expansion making a unit on a milestone the
  planner already wrote, and gains the charter write for every expanded
  unit; "A card blocked by an unlanded predecessor defers" is restated
  over the predecessor's merge; the no-Team refusal is restated over the
  unit.

## Impact

- `bin/_flywheel_bolt_loop.py` — `guard_expand`'s card selection,
  `_expand_card`'s milestone writes and blocker predicate, and the
  charter write (today a line of `guard_scaffold`'s work order, gated on
  the change directory being absent).
- `openspec/specs/flywheel-derived-backlog/spec.md` — three modified
  requirements.
- `tests/test_derived_backlog.py` — `ExpansionTest` pins the current
  shape and moves with it: `test_expansion_full_path` asserts
  `create_milestone` is among the writes, and
  `test_blocked_by_landed_predecessor_expands` builds its predecessor as
  a `closed:done` card.
- Out of scope, each its own task in this unit: the server's bolt-job
  filter and `PlanCard.bolt`'s fallback (`the-bolt-job-filter`), and the
  landing's precondition over open unit cards
  (`the-landing-waits-for-the-cards`). The plan card's body format
  beyond the task table is out of scope for the whole unit.
