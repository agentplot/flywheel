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
