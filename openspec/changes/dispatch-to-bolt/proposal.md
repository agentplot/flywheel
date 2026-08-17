# dispatch-to-bolt

## Why

Construction work has two births. The bolt planner computes the gap between
the design book and the implemented specs and files plan cards — a unit
document per card, board approval per unit, expansion as the birth of work
items. Beside it survives an older path: items queued on a bolt milestone are
judged one-by-one by charged route sessions (the merge-criteria test) and
bundled by the compose guard into a unit titled "Work the discoveries queued
on bolt/<slug>" — a bare container with no document, no chapter citations, no
provenance, driving the retired assertion-shaped spec path. The route charge
is session spend inside an ungated guard: judgment burning tokens before any
approval. The feeder that justified the path — construction sessions filing
discoveries — is itself retired; what remains queued on a bolt arrives from
the operator or dispatch, whose placement already carries the judgment the
route session re-makes.

What the old path served that the planner does not: work the operator states
exactly — trivial, fully specified, wanted now — should not wait for a book
chapter and a settle window. Retiring the duplicate without replacing that
entry would force every two-line job through design.

## What Changes

One artifact, one birth, many authors. The plan card is the only vehicle that
becomes construction work, and expansion of an approved card is the only
birth of work items — but the planner stops being the card's only author:

- **Dispatch authors a card from the operator's dictation.** When the
  operator states work exactly, dispatch creates the `bolt/<slug>` milestone
  if it does not exist and files one plan card on it — title `Unit: <slug>`,
  body a unit document (task table with a change per row, type, price), at
  board Backlog. Approval stays the operator's own board gesture.
- **The route guard and its sessions retire.** No session is charged to judge
  a queued item's placement; the judgment lives with whoever authored the
  placement.
- **The compose guard retires.** The loop composes no units from queued
  items; an item queued on a bolt milestone is inert until an author folds it
  into a card.
- **The merge close loses its `type:assertion` carve-out.** With discovery
  items retired, every expansion-born work item closes `closed:merged` at
  merge-back — the carve-out is why merged items today sit open at
  `stage:merged` and the unit progress bar never moves.

## Capabilities

### New Capabilities

- `flywheel-dispatch-to-bolt`: dispatch as a second author of plan cards —
  the card it writes from the operator's dictation, the milestone it may
  create, and the one-birth rule: expansion of an approved card is the only
  path that creates construction work items; the loop charges no routing
  sessions and composes no units.

### Modified Capabilities

- `flywheel-release-unit-parent`: the unit parent is born only by expansion
  of an approved plan card; the born-ready operator release and the handoff
  birth no longer exist as creation paths.
- `flywheel-construction-stages`: the merge boundary closes every work item
  `closed:merged`, not only `type:assertion` items; the discovery-item
  carve-out and its scenario retire with the discovery path.

## Impact

- `bin/_flywheel_bolt_loop.py`: `guard_route`, `guard_compose`, the `_ROUTE`
  parser, the route session charge, and `close_merged`'s `is_assertion`
  filter.
- `agents/flywheel-dispatch.md` and `skills/inception`: triage gains the
  card-authoring route in place of the retired quick-bolt route's remains.
- `tests/`: route/compose guard tests retire; card-authoring and
  merge-close tests arrive.
- The live board: queued items on a bolt milestone stop being consumed by
  machinery; existing ones wait for an author.
