## Purpose

How a construction item's progress becomes visible on the tracker: which
`stage:*` label the bolt loop writes at each boundary it already drives, and
the rule that the labels are re-derived from observable git state every
cycle rather than remembered, so they survive the loop's stateless restart.

## ADDED Requirements

### Requirement: The bolt loop writes a stage label at each boundary it drives

The bolt loop SHALL write, on each item of the batch it is working:

- `stage:planned` when the batch's spec is validated — or, on the plan-mode
  path, when the plan is approved;
- `stage:built` when the change has been applied and a commit exists on the
  item's own branch beyond the bolt branch;
- `stage:verified` when verify is clean;
- `stage:merged` when the item's branch is an ancestor of the bolt branch.

These are the four boundaries the loop already drives, in the order its
cycle runs them. The loop SHALL NOT write a stage label from a session's
prose: each write follows the same objective check the loop already makes
at that boundary, and a session saying "green" is not evidence.

#### Scenario: A batch runs the full sequence

- **WHEN** a batch is specced, built, verified and merged in one cycle
- **THEN** each of its items carries `stage:planned`, then `stage:built`,
  then `stage:verified`, then `stage:merged`, in that order

#### Scenario: A stage that did not happen writes no label

- **WHEN** the spec stage fails and the cycle does not reach build
- **THEN** the batch's items carry `stage:planned` at most, and no
  `stage:built`

#### Scenario: A session's report is not the evidence

- **WHEN** a build session settles claiming success but no commit exists on
  the item's branch beyond the bolt branch
- **THEN** no `stage:built` label is written, because the check is
  `git rev-list` and not the report

### Requirement: An item carries exactly one `stage:*` label at a time

Writing a stage SHALL remove any earlier `stage:*` label from the same item,
so that an item's stage label names its **leading edge** and a filter for
one stage returns one answer.

This follows the shape the tracker already uses for `state:*` — an item
holds exactly one — and it is what makes "the items at `stage:built`" a
question with an answer rather than a set that also contains everything
further along.

#### Scenario: An item advances from built to verified

- **WHEN** verify comes back clean on an item carrying `stage:built`
- **THEN** the item carries `stage:verified` and no longer carries
  `stage:built`

#### Scenario: The operator filters for one stage

- **WHEN** the operator lists a milestone's items labelled `stage:built`
- **THEN** the result holds only items whose leading edge is built, and not
  items already merged

### Requirement: Built and merged are re-derived from git every cycle

Every cycle, before it works anything, the bolt loop SHALL re-derive
`stage:built` and `stage:merged` for the milestone's open items from the
repository, and reconcile the labels to what it finds:

- an item whose branch is an ancestor of the bolt branch SHALL carry
  `stage:merged`;
- otherwise, an item whose branch holds a commit beyond the bolt branch
  SHALL carry `stage:built`.

The re-derivation SHALL use the same two checks the loop already makes at
those boundaries — the ancestry test and the commit count against the bolt
branch — so that the label and the boundary write cannot disagree.

This is what makes the labels **self-heal**: the loop is stateless by
construction, every cycle re-reads the tracker and the records, and a
process killed between an apply and its label write leaves an item whose
git state is built and whose label is not. The next cycle repairs it
without knowing anything about the process that died.

#### Scenario: The loop is killed between the apply and the label write

- **WHEN** a loop process dies after a build session commits to the item's
  branch but before the label is written, and a fresh process starts on the
  same milestone
- **THEN** the first cycle of the new process writes `stage:built` from the
  commit it finds, with no record of the earlier run consulted

#### Scenario: A label ahead of the tree is corrected

- **WHEN** an item carries `stage:merged` but its branch is not an ancestor
  of the bolt branch
- **THEN** the cycle reconciles the label down to what the tree bears out

#### Scenario: The re-derivation is idempotent

- **WHEN** two consecutive cycles run against an unchanged tracker and an
  unchanged tree
- **THEN** the second writes nothing, which is the dry-cycle property the
  loop's guards are already held to

### Requirement: Planned and verified are written at their boundary and not re-derived

`stage:planned` and `stage:verified` SHALL be written when the loop reaches
those boundaries, and SHALL NOT be reconciled from the repository each
cycle.

Neither has a witness in git. A validated spec is a property of a change
that survives, but a plan approval is an event in a pane; verify being
clean is a session's finding, and the only thing a later cycle could do
with it is re-run verify, which is a stage and not a reconciliation. The
re-derivation covers exactly what the tree can answer, and claims nothing
it cannot.

#### Scenario: A restart mid-verify does not invent a verdict

- **WHEN** a loop process dies during a verify stage and a new one starts
- **THEN** no `stage:verified` label appears from re-derivation, and the
  item's stage stays where the tree puts it

#### Scenario: A merged item is not walked back to planned

- **WHEN** re-derivation finds an item merged
- **THEN** it writes `stage:merged`, and the absence of a re-derivable
  witness for the earlier stages does not remove it

### Requirement: `stage:verified` never appears on a `bolt-direct` item

On a bolt whose type declares no verify stage, the loop SHALL neither run
verify nor write `stage:verified`, and such an item SHALL go from
`stage:built` to `stage:merged` directly.

The absence of the label is the honest record of a stage that did not run.
Writing it anyway would make a `bolt-direct` item indistinguishable from a
verified one on every view that reads the label.

#### Scenario: A bolt-direct item reaches the bolt branch

- **WHEN** an item on a `bolt-direct` bolt is built and then merged
- **THEN** its stage labels are `stage:planned`, `stage:built`,
  `stage:merged`, and `stage:verified` never appears on it

#### Scenario: The operator audits which items were verified

- **WHEN** the operator lists items that carry or have carried
  `stage:verified`
- **THEN** no `bolt-direct` item is among them

### Requirement: The merge boundary closes the item with `closed:merged`

At the same boundary at which it writes `stage:merged` — ancestry confirmed
by git, never a session's report — the loop SHALL close each assertion item
of the batch with `closed:merged`, and SHALL comment the merge SHA on it.

Closing SHALL be the loop's, not the merge session's, for the reason the
landing already gives: closing is bookkeeping, not judgment. The merge
session's work order, which today reads "Comment the merge SHA on each
item; do not close them — they close at the landing", SHALL be corrected to
match, so the session and the loop do not race for the same act.

Only `type:assertion` items SHALL be closed this way. A discovery item
queued on the bolt closes on its own evidence, as it does today.

#### Scenario: A batch reaches the bolt branch

- **WHEN** `merge_stage` confirms the batch's branch is an ancestor of the
  bolt branch
- **THEN** each assertion item of that batch carries `stage:merged`, is
  closed, carries `closed:merged`, and has the merge SHA in a comment

#### Scenario: The merge session does not close anything

- **WHEN** a merge session settles
- **THEN** it has closed no item, and the close that follows is the loop's,
  made against git's ancestry answer

#### Scenario: A discovery item on the bolt is untouched by the merge

- **WHEN** a batch merges while a `type:assertion`-less discovery item is
  open on the same milestone
- **THEN** that item is neither closed nor labelled `closed:merged`

### Requirement: The landing upgrades `closed:merged` to `closed:done`

At the landing the loop SHALL replace each assertion item's `closed:merged`
with `closed:done` and comment the landing SHA, leaving the item closed
throughout. It SHALL NOT depend on the item being open at that moment, and
SHALL NOT leave an item carrying both labels or neither.

An item that reaches the landing without `closed:merged` — a bolt landed by
a path that never merged it back, or an item closed by hand — SHALL still
be brought to `closed:done` with the SHA. The landing's job is the end
state, not a transition it must have witnessed.

#### Scenario: A bolt lands with every item merge-closed

- **WHEN** the bolt branch lands on main
- **THEN** each assertion item carries `closed:done`, no longer carries
  `closed:merged`, and has the landing SHA in a comment

#### Scenario: The landing is not blocked by an already-closed item

- **WHEN** the landing runs over items that are already closed with
  `closed:merged`
- **THEN** the upgrade succeeds on each, and no step fails because the item
  was not open

#### Scenario: A pull-request landing closes nothing early

- **WHEN** the bolt's Landing line reads `pr` and the pull request is not
  yet merged
- **THEN** the items stay at `closed:merged`, and nothing is upgraded

### Requirement: A merge-closed item is still in flight until the bolt lands

An item closed with `closed:merged` SHALL count as work in flight on its
bolt milestone until the landing. Specifically:

- the picture the bolt loop works from SHALL include the milestone's
  `closed:merged` items, which the snapshot — built today from
  `open_issues()` alone — does not;
- the landing SHALL run over them: `landing_wanted`'s "nothing to close,
  nothing to land" test SHALL count a `closed:merged` item as something to
  land, and `land_stage`'s item set SHALL include them;
- the server's job filter SHALL treat a bolt milestone holding a
  `closed:merged` item as a milestone with a job, so a loop killed between
  the last merge and the landing is started again;
- a bolt milestone SHALL NOT be read as finished while any of its items is
  at `closed:merged`; the landing is what finishes it.

This requirement exists because closing at merge removes an item from every
filter that reads open issues, and those filters are what start the loop
and trigger the landing. Without it the last batch of a bolt would merge,
the milestone would look empty, and the bolt would never land.

The filters that read `state:ready` SHALL be unaffected: a closed item is
not ready, and the ready set stays exactly what it is today.

#### Scenario: The last batch of a bolt merges

- **WHEN** every assertion on a bolt has merged and closed with
  `closed:merged`
- **THEN** the landing still runs in that same run, rather than the loop
  concluding there is nothing to land

#### Scenario: The loop process dies between the last merge and the landing

- **WHEN** the server sweeps for milestones with a job and the bolt's items
  are all `closed:merged`
- **THEN** that milestone has a job, a loop is started for it, and it lands

#### Scenario: The ready set is unchanged

- **WHEN** the bolt loop computes its ready set on a milestone holding
  `closed:merged` items
- **THEN** none of them is in it, and no closed item is ever worked

### Requirement: Re-derivation repairs the merge-close as well as the label

The re-derivation guard SHALL treat the merged edge as one fact with two
writes. An item whose branch is an ancestor of the bolt branch SHALL end
the guard carrying `stage:merged` **and** closed with `closed:merged`,
whichever of the two a dead process left undone.

The guard's scope SHALL therefore reach the milestone's open
`state:in-progress` items — as it does today, for the item whose close did
not happen — and the milestone's `closed:merged` items, for the item whose
label did not.

An item already at `closed:done` SHALL NOT be walked back to
`closed:merged`. The landing is downstream of the merge, and re-derivation
never reverses it.

#### Scenario: A process dies after the stage label and before the close

- **WHEN** a new loop process runs its guards over an item carrying
  `stage:merged`, open, whose branch is an ancestor of the bolt branch
- **THEN** the guard closes it with `closed:merged` and records the write in
  its actions

#### Scenario: A process dies after the close and before the label

- **WHEN** a new loop process runs its guards over a `closed:merged` item
  carrying no `stage:merged`
- **THEN** the guard writes `stage:merged` on it

#### Scenario: A landed item is never walked back

- **WHEN** re-derivation runs over an item carrying `closed:done`
- **THEN** it is left exactly as it is, and no `closed:merged` is written

#### Scenario: The dry cycle still holds

- **WHEN** two consecutive cycles run against an unchanged tracker and tree
  that include merged, closed items
- **THEN** the second cycle writes nothing
