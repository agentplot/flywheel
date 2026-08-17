# Bolt sequence — flywheel, 2026-08-17

Eight bolts carry the flywheel repo from what its specs record today to
what `books/flywheel` describes. The book's central mechanism — the
backlog as a measurement, derived by a bolt planner and approved as one
card per bolt — does not exist in the repo at all, and most of the rest
of the sequence is the design loop and the two schemas letting go of the
stored work lists that mechanism replaces.

| # | slug | goal | size |
|---|------|------|------|
| 1 | `board-surface` | the org Project carries the fields and views the loops and the operator read | small |
| 2 | `derived-backlog` | the bolt planner exists: it derives the cut, files plan cards, and the bolt loop expands an approved one | large |
| 3 | `design-loop-ends-at-the-book` | the intent stops handing work to construction; an approved plan card is the only way a bolt is born | medium |
| 4 | `records-not-registries` | the two schemas hold records, not work lists — no `tasks.md`, no `design.md`, no `proposals.md` | medium |
| 5 | `session-types-match-the-loops` | the session types are the ones the two loop chapters name, and no others | medium |
| 6 | `fleet-across-hosts` | Team routes a milestone to a host, and the server's remaining verbs and timers land | medium |
| 7 | `schema-distribution` | the installer owns the names it wrote, and a schema version is immutable | small |
| 8 | `verification-stages` | the fake tracker, the golden records, and the harnesses every change docks onto | large |

## The shape of the cut

The order is a dependency chain for the first five and a matter of risk
for the last three. `board-surface` comes first because the planner sets
a plan card's Team when it files it and expansion refuses a card without
one, so the field has to exist before either behavior can. `derived-backlog`
is next because everything else in the book's construction path assumes a
plan card: it is the largest bolt in the sequence and the one that makes
commitment 2 in `books/flywheel/src/commitments.md` true — direction lives
in the book and the backlog is computed. The two births of a bolt coexist
for exactly one bolt — the release
path the repo has today and the plan card — and
`design-loop-ends-at-the-book` closes the older one. `records-not-registries`
then removes the stored work lists that only the release path needed, and
`session-types-match-the-loops` retires the types that die with them.

The last three are independent of each other and of the chain above.
`fleet-across-hosts` needs only the Team field. `schema-distribution`
touches the installer alone. `verification-stages` is last because stage 2
diffs a run against a golden run record, and the run record is being built
now by the `observer` change in flight.

## Two things the operator settles before bolt 2 and bolt 4 start

**The planner has no host profile and no book binding.** The book says
four profiles cover every session — dispatch, design session, interactive
session, construction session — and describes the bolt planner as a
session the server charges the way it nudges dispatch. No profile hosts
it, and nothing in `fleet.yaml` says which design book belongs to which
built repo or where that book is checked out. Both are inputs
`derived-backlog` cannot derive.

**The vocabulary is settled two ways.** `work-object-vocabulary` is in
flight with three assertions (#30, #31, #32) that rename *proposal* to
*assertion* across identifiers, prose and all of `openspec/specs/**` —
119 occurrences including five requirement headings. The book retires the
word: `books/flywheel/CLAUDE.md` names *assertion*, *handoff*,
*conductor* and *andon* as retired vocabulary, and the book has no claim
object at all, since a work item is born from a plan task at expansion.
Landing that pass and then landing bolts 2 through 5 renames the same
surfaces twice. No bolt here plans a vocabulary pass; which direction it
runs is the operator's call.

Derived from: book 2243c39f · specs aa1debe · in flight: add-flywheel-loops,
gated-merge-guarantee, loops-run-unattended, machinery-self-desc, observer,
relay-delivery, work-object-vocabulary
