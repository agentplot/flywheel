## Purpose

The `stage:*` label vocabulary a flywheel tracker carries: the names, what
each one means, who is entitled to write it, and how a repo's tracker
acquires the set. It is the shared half of the two loops' stage behaviour —
what the bolt loop does with these labels is `flywheel-construction-stages`,
and what the intent loop does with them is
`flywheel-design-session-completion`.

## ADDED Requirements

### Requirement: The `stage:*` set is exactly six names

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

The table names seven rows because `stage:done` is the operator's and the
other six are the loops'; the requirement's count is over the label set,
which SHALL be exactly `planned`, `built`, `verified`, `merged`,
`in-session`, `done`, `collected`.

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
