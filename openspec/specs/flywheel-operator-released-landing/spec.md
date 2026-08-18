# flywheel-operator-released-landing Specification

## Purpose
A bolt reaches main only on the operator's gesture: the milestone close
releases the landing, the loop tells the operator when that gesture is
due, and the landing's own failure files bounded repair work instead of
pausing forever.

## Requirements

### Requirement: The milestone close releases the landing

The loop SHALL NOT land a bolt while its milestone is open: with every
work item merged, the loop waits. Closing the milestone is the release
gesture. An explicit force from the operator SHALL be the only other
path to a landing.

#### Scenario: All merged, milestone open

- **WHEN** every work item on the bolt is `closed:merged` and the
  milestone is open
- **THEN** no landing runs, and the loop reports it is awaiting the
  operator's close

### Requirement: The close-ready wait reaches the operator

When every work item is merged, no plan card on the bolt remains open,
and the milestone is still open, the loop SHALL mark the open unit
parents `needs-operator` with a comment saying the close releases the
landing — so the wait appears where the operator looks. The mark SHALL
be withdrawn if new cards arrive on the bolt, and removed by the
landing.

#### Scenario: The wait appears when the work is done

- **WHEN** the last work item merges and no open cards remain
- **THEN** the unit parent carries `needs-operator` and the comment
  names the close as the release

#### Scenario: New cards withdraw the wait

- **WHEN** a new plan card lands on the bolt after the mark was written
- **THEN** the mark is withdrawn — the bolt is no longer ready to close

### Requirement: The landing verifies the charter and upgrades the record

The landing SHALL verify the charter's `## Merge criteria` before
merging; a charter with no criteria is nothing to verify and SHALL
pause the bolt rather than let the landing grade itself. After the
merge to main is confirmed, the loop SHALL upgrade every work item from
`closed:merged` to `closed:done` with the landing SHA, and SHALL close
every open unit on the milestone the same way — the unit's close is the
landing's evidence, not the milestone close's paperwork.

#### Scenario: A landed bolt's record

- **WHEN** the landing's merge to main is confirmed
- **THEN** each work item ends `closed:done` naming the landing SHA and
  each unit on the milestone is closed

### Requirement: A failed landing files bounded repair and the server keeps it alive

A landing that fails a merge criterion SHALL file one born-ready fix
item per failing criterion on the bolt's milestone — deduplicated
against the fix items already filed, with a repeat raising the andon
instead of a second item. The server SHALL keep a closed milestone's
loop running while it holds merge-closed items awaiting upgrade or
ready fix items, and SHALL defer the record's archive until the bolt
branch is an ancestor of main.

#### Scenario: The landing refuses a red tree

- **WHEN** the bolt branch is green alone but red rebased onto main
- **THEN** the landing files one fix item, the loop drives it through
  the ordinary stages, and the retried landing merges
