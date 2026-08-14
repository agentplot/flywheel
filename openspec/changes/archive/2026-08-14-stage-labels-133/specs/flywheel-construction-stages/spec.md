## MODIFIED Requirements

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

A boundary's label SHALL be written only when that stage actually **ran**.
A stage can fail to happen two ways, and both SHALL write nothing: it can
**fail**, which stops the cycle there, and it can be **skipped**, which the
cycle carries on past. The second is the easier one to get wrong, precisely
because the cycle continues and the stage reports no error — a stage whose
outcome is "skipped" is not a stage whose outcome is "clean", and treating
the two alike writes a label asserting a boundary nobody crossed.

#### Scenario: A batch runs the full sequence

- **WHEN** a batch is specced, built, verified and merged in one cycle
- **THEN** each of its items carries `stage:planned`, then `stage:built`,
  then `stage:verified`, then `stage:merged`, in that order

#### Scenario: A stage that did not happen writes no label

- **WHEN** the spec stage fails and the cycle does not reach build
- **THEN** the batch's items carry `stage:planned` at most, and no
  `stage:built`

#### Scenario: A stage that was skipped writes no label

- **WHEN** a type declares a stage that this bolt's path skips — the
  plan-mode path skipping the stage a spec-driven change would have run —
  and the cycle carries on past it
- **THEN** no label for that stage is written, and the stages that did run
  keep theirs

#### Scenario: A session's report is not the evidence

- **WHEN** a build session settles claiming success but no commit exists on
  the item's branch beyond the bolt branch
- **THEN** no `stage:built` label is written, because the check is
  `git rev-list` and not the report

### Requirement: Built and merged are re-derived from git every cycle

Every cycle, before it works anything, the bolt loop SHALL re-derive
`stage:built` and `stage:merged` for the milestone's open items from the
repository, and reconcile the labels to what it finds:

- an item whose branch is an ancestor of the bolt branch **and holds work of
  its own** SHALL carry `stage:merged`;
- otherwise, an item whose branch holds a commit beyond the bolt branch
  SHALL carry `stage:built`.

**Ancestry alone SHALL NOT be read as merged.** A branch that was cut and
never worked has a tip that is an ancestor of everything it was cut from, so
bare ancestry answers "merged" for a batch on which nothing happened. The
merged test SHALL therefore require, in addition to the ancestry relation,
that the branch exists and that real work stands behind it — the same
strengthened predicate the landing path is already held to, and not a second
implementation of it. Where the repository already carries such a predicate,
the re-derivation SHALL call it rather than re-deriving the weaker test at
its own call site.

The re-derivation SHALL use the same checks the loop makes at those
boundaries, so that the label and the boundary write cannot disagree.

This requirement is stronger than what a reading of "an item whose branch is
an ancestor of the bolt branch is merged" would give, and deliberately so.
The re-derivation guard does not only write a label: at the merged edge it
also **closes** the item with `closed:merged`, and a `closed:merged` item
leaves every open-issue filter. A false merged answer from bare ancestry
therefore does not merely mislabel a batch — it closes the batch out of the
loop's own inbox, and the bolt stops being driven at all. That is a strictly
worse failure than the mis-landing the same weakness caused before, which is
why the guard may not be the one caller left on the weak test.

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

#### Scenario: A branch cut but never worked is not merged

- **WHEN** the guard runs over an item whose branch was created from the
  bolt branch and carries no commit of its own
- **THEN** no `stage:merged` is written and the item is not closed
  `closed:merged`, even though its tip is an ancestor of the bolt branch

#### Scenario: A branch that does not exist is not merged

- **WHEN** the guard runs over an item whose branch is absent from the
  repository
- **THEN** no `stage:merged` is written and the item is not closed

#### Scenario: One predicate answers the merged question

- **WHEN** the repository is searched for the test that decides whether a
  batch's work has reached the bolt branch
- **THEN** the guard and the boundary write are found to consult the same
  strengthened predicate, and no caller is left on bare ancestry

#### Scenario: A label ahead of the tree is corrected

- **WHEN** an item carries `stage:merged` but its branch does not satisfy
  the merged test
- **THEN** the cycle reconciles the label down to what the tree bears out

#### Scenario: The re-derivation is idempotent

- **WHEN** two consecutive cycles run against an unchanged tracker and an
  unchanged tree
- **THEN** the second writes nothing, which is the dry-cycle property the
  loop's guards are already held to
