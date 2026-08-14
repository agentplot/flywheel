# flywheel-stage-labels Specification

## Purpose
The `stage:*` label vocabulary a flywheel tracker carries: the names, what
each one means, who is entitled to write it, and how a repo's tracker
acquires the set. It is the shared half of the two loops' stage behaviour —
what the bolt loop does with these labels is `flywheel-construction-stages`,
and what the intent loop does with them is
`flywheel-design-session-completion`.
## Requirements
### Requirement: The `stage:*` set is exactly seven names

A flywheel tracker SHALL carry exactly these `stage:*` labels and no others:

| label | meaning | written by |
| --- | --- | --- |
| `stage:planned` | the item's spec is validated, or its plan approved | the bolt loop |
| `stage:built` | the change is applied, with a commit on the item's branch | the bolt loop |
| `stage:verified` | verify is clean | the bolt loop |
| `stage:merged` | the work is on the bolt branch | the bolt loop |
| `stage:in-session` | a design session is carrying the item | the intent loop |
| `stage:done` | the operator has marked the item finished | **the operator** |
| `stage:collected` | the item's deliverables are gathered | the intent loop |

Seven names, and the table's seven rows are those names. Six of them are
the loops' — four the bolt loop's, two the intent loop's — and the seventh,
`stage:done`, is the operator's; that split is who WRITES each label and
is not a count of the set.

The rule that keeps the vocabulary small: **a stage exists only if a loop
filter consumes it or the operator's eye needs it.** The rounds inside a
design session — however many plannotator or lavish rounds the operator
takes — are deliberately not stages.

#### Scenario: An eighth stage name is proposed

- **WHEN** a stage is proposed that no loop filter consumes and no operator
  view needs
- **THEN** it is not added, and the span it would name stays inside an
  existing stage

#### Scenario: The stages are readable on a GitHub view

- **WHEN** the operator filters a milestone's open items by a `stage:*`
  label
- **THEN** the items at that stage are exactly those the label names, with
  no second store consulted

### Requirement: `stage:*` refines `state:in-progress` and never replaces a `state:*` label

A `stage:*` label SHALL be additional to the item's `state:*` label, never a
substitute for it. An item carrying any `stage:*` label from the bolt loop's
set SHALL also carry `state:in-progress`, and the state ladder
`queued → ready → in-progress → closed:*` SHALL be unchanged by this
capability.

The reason is that the four inbox filters are built on `state:*` — the
server's filter, the bolt loop's, the intent loop's and dispatch's all read
it — and a stage label that displaced one would make an item invisible to
the loop that owns it.

#### Scenario: An item mid-construction is read by the bolt loop's filter

- **WHEN** an item carries `stage:built` and `state:in-progress`
- **THEN** the bolt loop's filter still sees it as in-progress work on its
  milestone
- **AND** removing `state:in-progress` in favour of the stage label would
  hide it, which is why no writer does so

#### Scenario: The In-flight board view still populates

- **WHEN** the board's In-flight view runs its query `is:open
  label:state:in-progress`
- **THEN** every item at any bolt-loop stage appears in it

### Requirement: An item carries exactly one `stage:*` label, and one writer enforces it for both loops

Writing any `stage:*` label SHALL remove every other `stage:*` label from
that item, so an item's stage names its **leading edge**. This SHALL hold
for every name in the set, whichever loop writes it: the bolt loop's four,
the intent loop's two, and the operator's `stage:done` when a session writes
it on the operator's word.

The rule SHALL have exactly one implementation, living beside the vocabulary
itself, and **every writer SHALL write through it — including the session
that writes `stage:done` from a pane**. A sweep implemented inside one loop
would be a rule about that loop rather than about the set; a sweep copied by
hand into a session's instructions is the same defect in a slower form,
because a copy states the rule for the cases its author had in mind and the
set is what it is for all of them.

Concretely, the one implementation SHALL be reachable from a pane without
importing the loops' internals, so that a session told an item is done runs
the same sweep the loops run rather than a two-label edit naming one
predecessor to remove. Naming a single predecessor is wrong wherever the
item's actual predecessor is a different stage — an item picked up by a
later session while at `stage:collected` keeps that label deliberately, and
a flip that removes only `stage:in-session` leaves it carrying
`stage:collected` and `stage:done` at once, which is the state this
requirement says is unreachable. Any prose that shows a session how to make
the flip SHALL show that one call, and SHALL NOT spell out a hand-built
label edit for it to copy.

**The sweep SHALL run whenever the item's stage set is not already exactly
the target**, and not only on a transition the writer believes is new. An
item that already carries the target and also carries another stage SHALL
end the write carrying the target alone. Skipping the sweep for an item
already at the target assumes every stage label on the tracker was written
through this implementation, and the operator adding a label by hand on
GitHub — which this capability permits — is exactly the case that assumption
does not cover.

The write SHALL be idempotent and SHALL report whether it wrote: an item
already at the target stage **and carrying no other** is left alone and
nothing is recorded, which is what keeps a second cycle over an unchanged
tracker writing nothing.

A label surface that answers "does this item carry X" from a cached snapshot
SHALL NOT report a label removed earlier in the same cycle, or the sweep
would re-remove what it has already taken off. **Symmetrically, it SHALL NOT
report a label added earlier in the cycle once its snapshot has been
re-read**: a re-read is the loop learning what the world now says, and a
cache of the writer's own earlier additions surviving it makes the surface
answer from a state that no longer exists — which sends a removal for a
label the pane has already taken off. Both directions of the cache SHALL be
invalidated together, whenever the snapshot behind them is replaced.

Nothing in this rule SHALL touch a `closed:*` label. `stage:merged` and
`closed:merged` are written at the same boundary and are not the same act.

#### Scenario: A design item reaches the end of its session

- **WHEN** the intent loop has written `stage:in-session`, the operator has
  flipped `stage:done`, and the loop then collects the item
- **THEN** the item carries `stage:collected` and no other `stage:*` label,
  and a reader asking for its leading edge is answered `stage:collected`

#### Scenario: A stage is written twice

- **WHEN** a loop writes the stage an item already carries, and the item
  carries no other stage
- **THEN** no label is added or removed and the cycle records no write

#### Scenario: An item already at the target carries a second stage

- **WHEN** a stage write runs on an item that already carries the target
  stage and also carries another `stage:*` label
- **THEN** the other label is removed and the item ends carrying the target
  alone, rather than the write returning early on the strength of the
  target already being present

#### Scenario: The pane writes the operator's flip

- **WHEN** a design session is told by the operator that an item is done
- **THEN** it makes the flip through the one implementation of this rule,
  and the item ends carrying `stage:done` and no other `stage:*` label —
  whatever stage it carried before

#### Scenario: An item picked up at `stage:collected` is flipped done

- **WHEN** a later session carries an item that is already at
  `stage:collected`, and the operator flips it done
- **THEN** the item ends carrying `stage:done` alone, with `stage:collected`
  removed

#### Scenario: The rule is stated once and copied nowhere

- **WHEN** the skills, profiles and references a session reads are searched
  for how to write `stage:done`
- **THEN** each points at the one call, and none of them spells out a
  hand-built label edit naming which predecessor to remove

#### Scenario: A cached label surface outlives its snapshot

- **WHEN** a cycle writes a stage label, then re-reads its snapshot, then
  asks the same surface whether the item carries that label
- **THEN** the answer comes from the re-read snapshot, so a label the pane
  removed in between is not reported as present and is not removed a second
  time

#### Scenario: The closure labels are untouched by a stage write

- **WHEN** any stage write runs on an item carrying a `closed:*` label
- **THEN** that `closed:*` label is unchanged

### Requirement: The closure vocabulary carries `closed:merged`, and `closed:done` stays the landing's

The `closed:*` set SHALL be exactly `closed:done`, `closed:declined`,
`closed:superseded`, `closed:parked` and `closed:merged`, where
`closed:merged` means **merged to the bolt branch, awaiting the landing**.

`closed:merged` SHALL be defined in the same `bin/flywheel-setup` label
table as the other four and converged by the same `ensure_labels`, so the
closure vocabulary keeps a single enumeration.

`closed:done` SHALL remain the landing's alone, and SHALL carry the landing
SHA in the closing comment as it does today.

No `stage:*` write SHALL add, remove or stand in for a `closed:*` label.
The two are written at the same boundary but are not the same act: at
merge-back the loop writes `stage:merged` **and** closes the item with
`closed:merged`, and a reader of either label alone is never misled about
the other.

This is what lets tracker.md invariant 5 stand verbatim — "whoever holds
the evidence closes, always with one `closed:*` reason" — while GitHub's
native sub-issue bar, which counts closed sub-issues, advances at merge
rather than at the landing. A close with no reason would have bought the
same bar by breaking the invariant every skill points at.

#### Scenario: A merged item before its bolt lands

- **WHEN** an item's branch is an ancestor of the bolt branch but the bolt
  branch has not landed on main
- **THEN** the item is closed, carries `closed:merged` and `stage:merged`,
  and does not carry `closed:done`

#### Scenario: Every closed item carries exactly one reason at every moment

- **WHEN** any item on a bolt milestone is closed, at merge-back or at the
  landing
- **THEN** it carries exactly one `closed:*` label — never none, and never
  both `closed:merged` and `closed:done`

#### Scenario: The landing writes its own signal

- **WHEN** the bolt branch lands on main
- **THEN** each assertion item carries `closed:done` in place of
  `closed:merged`, and a comment naming the landing SHA
- **AND** the Landed board view's query `is:closed label:closed:done` finds
  exactly the landed items, and no merged-but-unlanded one

#### Scenario: A merged item has left the In-flight view

- **WHEN** the board's In-flight view runs its query `is:open
  label:state:in-progress` while a batch is merged and its bolt unlanded
- **THEN** the merged items do not appear in it, which is correct: they
  wait on the landing, not on anyone

### Requirement: `flywheel-setup` converges the `stage:*` set

`bin/flywheel-setup` SHALL define every name in the `stage:*` set in the
one label table it already carries — the enumeration
`bin/_flywheel_inbox.py`'s vocabulary header points at as the single source
— and `ensure_labels` SHALL create the missing ones on a repo whose tracker
does not have them.

Each label SHALL carry a description saying what the stage means, in the
style of the existing entries (`state:in-progress` reads "a session is
working it").

Convergence SHALL stay idempotent: a second run against a converged tracker
creates nothing. `ensure_labels` already skips a name it finds in the
repo's existing labels, and this requirement adds no rewrite of an existing
label's colour or description.

#### Scenario: A tracker that has never seen a stage label

- **WHEN** `flywheel-setup` runs against a repo whose labels include no
  `stage:*` name
- **THEN** it creates every name in the set and reports them as created

#### Scenario: The same run converges the new closure reason

- **WHEN** that run happens on a repo whose labels include no
  `closed:merged`
- **THEN** it creates `closed:merged` too, from the same table, and a
  second run creates nothing

#### Scenario: A converged tracker is re-run

- **WHEN** `flywheel-setup` runs a second time against the same repo
- **THEN** it creates nothing and reports all labels present
- **AND** no existing label's colour or description is rewritten

#### Scenario: The labels exist before any item carries one

- **WHEN** a bolt whose items will carry `stage:*` labels is about to start
- **THEN** the convergence run has already happened, because a loop writing
  a label that does not exist on the repo is a failed `gh issue edit`, not a
  created label

