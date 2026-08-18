# flywheel-board-surface Specification

## Purpose
TBD - created by archiving change board-surface. Update Purpose after archive.
## Requirements
### Requirement: The label table carries the three batch kinds

`flywheel-setup` SHALL converge a `plan` label alongside `unit` and
`elaboration`, described as one proposed bolt awaiting approval whose
plan document is the card body, so a loop or planner writing the
label performs a label move, never a failed edit against a label the
repo does not carry.

#### Scenario: plan label converges

- **WHEN** `flywheel-setup` runs against a repo without a `plan` label
- **THEN** the label is created with its color and description, and a
  second run changes nothing

### Requirement: stage:planned means the spec validates

The `stage:planned` label's description SHALL state only that the
item's spec validates. No clause references plan approval: board
approval is a batch event on the plan card, not an item stage.

#### Scenario: description carries no approval clause

- **WHEN** `flywheel-setup` converges labels
- **THEN** `stage:planned`'s description is "its spec validates"

### Requirement: The org Project carries the fields batch parents use

`flywheel-setup` SHALL converge the org Project with fields Status
(single select: Backlog, Ready), Team (single select, default host
first), Quarter (single select), and Start and Target (dates). Batch
parents carry the fields; sub-issues carry none.

#### Scenario: fields converge idempotently

- **WHEN** `flywheel-setup` runs against a Project missing any field
- **THEN** the missing fields are created and present fields are left
  unchanged

### Requirement: Views arrive by template copy

Because Project views cannot be created through the API,
`flywheel-setup` SHALL copy the org Project from a hand-built
template project (default title "Flywheel Template") carrying the six
views — Kanban, Roadmap, Triage, Waiting On Me, In Flight, Landed —
and SHALL warn when no template exists and a bare Project is created
whose views need one-time hand configuration.

#### Scenario: no template

- **WHEN** the org has no project titled "Flywheel Template"
- **THEN** setup creates a bare Project and prints the one-time
  hand-configuration warning


### Requirement: A spent approval leaves the board

A batch at board Status Ready whose sub-issues are all released or done
is a spent approval, and the loop SHALL clear its board status on the
pass after the release — the Ready column shows only approvals not yet
consumed.

#### Scenario: An approved elaboration is consumed

- **WHEN** an elaboration at Ready has no `state:queued` sub-issue left
- **THEN** the next pass clears its board status and writes nothing more

### Requirement: The operator's Ready flip wakes a held loop

The server's hold on a quiet loop SHALL release the moment a batch on
that loop's milestone reaches board Status Ready: the approval is the
job's reason, and a changed reason releases the hold. The operator's
flip SHALL take effect within one server pass, never waiting out a
backoff that predates it.

#### Scenario: An approval lands mid-hold

- **WHEN** a loop is held on a quiet-milestone reason and the operator
  flips its elaboration to Ready
- **THEN** the next server pass starts the loop
