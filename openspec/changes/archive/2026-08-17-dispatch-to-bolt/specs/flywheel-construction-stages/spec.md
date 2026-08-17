# flywheel-construction-stages Delta

## REMOVED Requirements

### Requirement: The merge boundary closes the item with `closed:merged`

**Reason**: The requirement carved `type:assertion` items out for closing
and left discovery items open on their own evidence. The discovery path is
retired, and the carve-out is why expansion-born items — which carry no
`type:*` label — sit open at `stage:merged` and never advance the unit
parent's progress bar. The replacement below closes every item of a merged
batch.

## ADDED Requirements

### Requirement: The merge boundary closes every item of the batch

At the same boundary at which it writes `stage:merged` — ancestry confirmed
by git, never a session's report — the loop SHALL close each work item of
the batch with `closed:merged`, and SHALL comment the merge SHA on it. The
close SHALL apply to every item expansion filed into the batch, whatever
labels it carries beyond its state: no type carve-out exempts an item from
its merge close.

Closing SHALL be the loop's, not the merge session's, for the reason the
landing already gives: closing is bookkeeping, not judgment. The merge
session's work order SHALL NOT instruct the session to close or to defer
closing — the session and the loop do not race for the same act.

#### Scenario: A batch reaches the bolt branch

- **WHEN** `merge_stage` confirms the batch's branch is an ancestor of the
  bolt branch
- **THEN** each item of that batch carries `stage:merged`, is closed,
  carries `closed:merged`, and has the merge SHA in a comment

#### Scenario: The merge session does not close anything

- **WHEN** a merge session settles
- **THEN** it has closed no item, and the close that follows is the loop's,
  made against git's ancestry answer

#### Scenario: An expansion-born item closes at merge-back

- **WHEN** a batch whose items carry no `type:*` label merges to the bolt
  branch
- **THEN** those items are closed `closed:merged` the same as any others,
  and the unit parent's progress bar advances
