# flywheel-construction-stages Specification

## Purpose
How a construction item's progress becomes visible on the tracker: which
`stage:*` label the bolt loop writes at each boundary it already drives, and
the rule that the labels are re-derived from observable git state every
cycle rather than remembered, so they survive the loop's stateless restart.
## Requirements
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

### Requirement: An item carries exactly one `stage:*` label at a time

Writing a stage SHALL remove any earlier `stage:*` label from the same item,
so that an item's stage label names its **leading edge** and a filter for
one stage returns one answer.

This follows the shape the tracker already uses for `state:*` — an item
holds exactly one — and it is what makes "the items at `stage:built`" a
question with an answer rather than a set that also contains everything
further along.

The rule belongs to the vocabulary rather than to this loop:
`flywheel-stage-labels` states it over the whole `stage:*` set and names the
single writer both loops call. This capability's four boundary writes SHALL
go through that writer, so the bolt loop implements no sweep of its own.

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

### Requirement: The landing keeps a tracker surface when every assertion is merge-closed

The landing stage's item set SHALL be every **unlanded** item on the
milestone — open or `closed:merged` — and not the open ones alone.

That set is not "what the landing session is told to work": the work order
names the bolt, not items. It is the loop's own tracker surface for the
stage, and four things ride on it — the launch marker the stall budget is
recovered from across a restart, the stall notify, the failure pause that
writes `needs-operator`, and the andon marker the landing session may raise
and the loop reads back. Where a unit parent sits on the
intent milestone, so once the merge boundary has closed every assertion an
open-items-only set is **empty** and all four write nowhere. The landing is
the last boundary, with no session downstream to catch what it drops.

For the same reason, dispatch's relay filter SHALL read `closed:merged`
items as well as open ones. A `needs-operator` that nobody relays is the
same silence as one never written. The filter stays bounded because the
landing's upgrade to `closed:done` drops the item from it for good, and the
triage half of that filter SHALL stay open-issues-only — a closed item is
not untriaged work.

#### Scenario: The landing fails twice on an all-merge-closed milestone

- **WHEN** every assertion on the bolt is `closed:merged` and the landing's
  merge criteria fail on the second attempt
- **THEN** `needs-operator` is written on the milestone's unlanded items and
  the batch pauses, exactly as it would with those items still open

#### Scenario: A landing session raises the andon

- **WHEN** the landing session writes the andon marker on an item that is
  `closed:merged`
- **THEN** the loop reads that marker, pauses, and sets `needs-operator` —
  rather than reporting a plain failure with nothing written

#### Scenario: The escalation reaches the operator

- **WHEN** a `closed:merged` item carries `needs-operator`
- **THEN** dispatch's relay includes it
- **AND** once the landing upgrades that item to `closed:done`, the relay no
  longer includes it

### Requirement: The operator's milestone close releases the landing, and the card hold is asked first

The bolt loop SHALL NOT reach for a landing on its own initiative while
the bolt's milestone is **open**. The operator's close of that milestone
is the release gesture: merged work never reaches the main branch on the
machinery's own initiative, and every item merged and every card ruled
is necessary but never sufficient. The condition SHALL be read from the
milestone state the unlanded items carry, so it holds for a milestone
whose every assertion is already `closed:merged`.

A landing the operator or the server **forces** SHALL pass this
condition. A forced landing is a claim about what this process knows —
the operator landing deliberately, or the server resuming a run that
died between the last merge and its landing — and the close it stands in
for has, in that case, already been made or is being made by the same
hand.

**Two release conditions stand, and neither subsumes the other.** The
open-unit-card hold specified in `flywheel-derived-backlog` ("The
landing is the bolt's boundary, held by any open unit card") and this
milestone-close condition answer different questions and SHALL both be
enforced:

- an open unit card means the **bolt is still being planned** — the
  operator has a card left to rule, so what would land is not yet the
  whole bolt;
- an open milestone means the operator **has not released** what is
  built — the work may be complete and still not theirs to land yet.

The milestone-close condition is one of the "existing preconditions"
that the card-hold requirement defers to when it says the landing
proceeds under them and gains no new ones. Adding the card hold SHALL
NOT be read as having replaced this one, and this requirement SHALL NOT
be read as weakening the card hold.

**The card hold is asked first, and its answer is final.** When both
conditions are outstanding, the run's landing line SHALL report the
hold and name the holding card — not the milestone — because the card
is the gesture the operator can act on next and the hold is the more
specific fact. The two conditions differ in one further way, which the
loop SHALL preserve: a forced landing passes the milestone-close
condition and SHALL NOT pass the card hold, since a card is the
operator's own unfinished gesture and the way past it is to rule it.

#### Scenario: An open milestone declines an automatic landing

- **WHEN** every unlanded assertion on `bolt/<slug>` is `closed:merged`,
  no unit card is open on the milestone, and the milestone itself is
  still open
- **THEN** no landing session runs, nothing reaches the main branch, and
  no item is upgraded to `closed:done`

#### Scenario: The operator's close releases it

- **WHEN** the same bolt's milestone is closed and the loop runs again
- **THEN** the landing proceeds under its remaining preconditions, and
  the units on the milestone are closed at that one landing

#### Scenario: Both conditions outstanding

- **WHEN** the milestone is open **and** an open unit card sits on it
- **THEN** the run's landing line reports the hold and names that card by
  number, rather than naming the milestone or reading "not attempted"

#### Scenario: A forced landing on an open milestone whose cards are all ruled

- **WHEN** a landing is forced on a bolt whose assertions have all merged
  and whose milestone is still open, with no open unit card on it
- **THEN** the landing runs — the force passes the milestone-close
  condition

#### Scenario: A forced landing with a card still open

- **WHEN** a landing is forced on a bolt that still holds an open unit
  card
- **THEN** it is held exactly as an automatic landing would be, and the
  landing line names the card

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

### Requirement: A charter with no readable merge criteria is not landable

The landing verifies the bolt's merge criteria by running them, so a
charter that states none gives it nothing to verify. The bolt loop SHALL
refuse the landing when the bolt's `bolt.md` states no merge criteria —
no such section in the charter's own region, a section whose body is
empty, or no `bolt.md` at all. The refusal SHALL come ahead of any
landing session and ahead of anything reaching the main branch: nothing
is verified, no item is closed, and no item is upgraded to
`closed:done`.

The refusal SHALL name the charter's path and say that its merge criteria
could not be read, so the operator's next act is obvious. A landing
refused this way SHALL be legible as refused wherever the run reports its
landing, and SHALL NOT read as a landing that was never reached for.

**A forced landing does not pass this refusal.** Forcing is a claim about
the operator's release — that the milestone close has been made or is
being made by the same hand — and it says nothing about whether the
charter states criteria. An empty criteria list is not a green landing
under any flag.

This is a refusal within the landing, not a third release condition: it
is asked after the open-unit-card hold and the milestone-close condition
have been satisfied, alongside the landing's existing refusals — a live
operator wait on any item, and a bolt branch that carries no work beyond
its cut point. Unlike a release condition it cannot be answered on the
board; the charter is what has to change.

#### Scenario: a charter that states no merge criteria

- **WHEN** every release condition is satisfied and the bolt's `bolt.md`
  states no merge criteria in the charter's own region
- **THEN** no landing session runs, nothing reaches the main branch, no
  item is closed or upgraded, and the run's landing line names the
  charter and says its merge criteria could not be read

#### Scenario: an empty merge criteria section

- **WHEN** the charter carries the merge criteria heading with no body
  under it
- **THEN** the landing is refused exactly as for a charter that carries
  no such section at all

#### Scenario: a forced landing over an unreadable charter

- **WHEN** a landing is forced on a bolt whose charter states no merge
  criteria
- **THEN** it is refused exactly as an automatic landing would be

#### Scenario: a charter that states its criteria

- **WHEN** the charter carries a merge criteria section with a body
- **THEN** the landing proceeds under its existing preconditions and
  gains nothing from this requirement


### Requirement: Batches fan out; the merge is the one serialized stage

The bolt loop SHALL drive up to its configured `parallel` batches
concurrently — each batch's spec, build and verify sessions running
while its siblings' run, every batch isolated on its own
`build/<slug>` branch and worktree — and SHALL admit exactly one batch
at a time into the merge stage, the lowest batch number first when more
than one is waiting, because the bolt branch is the only state batches
share. Each session's notify and stall budgets SHALL measure that
session alone, however the waits interleave. `parallel: 1` SHALL be
the strictly serial drive. A batch's type SHALL be read per batch:
interleaved batches of different types never see each other's stage
set or plan mode.

#### Scenario: A slow batch does not hold its siblings back

- **WHEN** two unblocked batches are driven and the first's session
  keeps working while the second's settles
- **THEN** the second batch proceeds through its stages and merges
  while the first is still being supervised

#### Scenario: Two batches reach the merge together

- **WHEN** two pipelines are waiting to merge at the same moment
- **THEN** the lower batch number merges first and the other starts its
  merge only after the first's merge stage has finished

#### Scenario: An andon pauses only its own batch

- **WHEN** one of several concurrent batches carries an unanswered andon
- **THEN** that batch alone pauses with `needs-operator` and its
  siblings drive on to the bolt branch

#### Scenario: A mid-flight merge releases a held sibling into the running set

- **WHEN** a batch merges while `after:`-held siblings wait and slots
  are free under the cap
- **THEN** the released siblings are admitted to the same cycle's
  running set rather than waiting for the next planning pass
