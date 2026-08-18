# flywheel-proven-work-resume Specification

## Purpose
A restarted bolt loop re-buys no proven work: each stage names a witness
the tree itself carries, and a stage whose witness holds is skipped, not
re-run. Judgment is re-bought only where no record of it survives.

## Requirements

### Requirement: The spec stage skips when the change validates

The spec stage SHALL be skipped for a batch whose change already exists
and passes `openspec validate` in the tree that holds it. A validated
change is the spec stage's whole deliverable; re-deriving it burns a
session to produce what the tree already proves.

#### Scenario: A restart finds the spec already landed

- **WHEN** the loop restarts and a batch's change validates on its branch
- **THEN** the spec stage reports done without charging a session

### Requirement: The build stage's witness is the task list, not a commit

The build stage SHALL be skipped only when the change's deliverables are
met AND its `tasks.md` carries no unchecked task (`- [ ]`). A commit on
the branch alone SHALL NOT satisfy the build: a spec session's planning
commit satisfies any commit-existence test with zero implementation, and
verify then fails against work that was never done — observed live as a
build skipped on a spec commit with 0 of 15 tasks applied.

#### Scenario: A spec commit does not prove a build

- **WHEN** a batch's branch carries only the spec session's commits and
  `tasks.md` holds unchecked tasks
- **THEN** the build stage runs rather than reporting done

#### Scenario: A finished build is not repeated

- **WHEN** deliverables are met and `tasks.md` holds no unchecked task
- **THEN** the build stage reports done — the tree proves it

### Requirement: A verify verdict binds to the branch head and is spent by the next commit

A clean verify SHALL be recorded on the batch's items as a marker naming
the branch head SHA it judged. On a later pass the verify stage SHALL be
skipped while the branch head still matches the marker, and SHALL run
again the moment any commit moves the head — the verdict is spent, never
carried forward onto a tree it did not see. An operator's explicit
proceed over a verify finding SHALL be recorded the same way, so a
restart does not re-open what the operator already ruled.

#### Scenario: A restart honors a standing verdict

- **WHEN** the loop restarts and an item's verify marker names the
  branch's current head
- **THEN** the verify stage reports done without charging a session

#### Scenario: A new commit spends the verdict

- **WHEN** any commit lands on the branch after the marker was written
- **THEN** the next pass runs verify again
