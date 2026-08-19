# flywheel-design-session-completion Specification

## Purpose
How a design session finishes: the stage labels the intent loop writes
around it, the operator's `stage:done` flip as the one signal that a session
is complete, and what the loop does when it sees that flip. This is the
answer to R1 in `design/loop-programs.md` — "the exact GitHub signal for
'operator marks a design session done'".
## Requirements
### Requirement: The operator's `stage:done` flip is the completion signal

The intent loop SHALL treat the `stage:done` label on an item as the signal
that the operator has marked that item finished, and SHALL have no other
completion signal.

This resolves R1 by taking the first of its three named options — "a state
label the operator sets" — over a board Status and over closing the items.
The loop SHALL have one filter and SHALL NOT require an operator or a
configuration to name which of several signals is in use; the state in which
no signal is configured, and completion is therefore *unknown* rather than
false, SHALL cease to exist.

Completion SHALL NOT be inferred from a session settling. The operator may
iterate a plannotator or lavish round, or a dispatch plan, as many
times as they want, and a settled pane is not a finished session. Every
design type is an operator-round session for this reason: any may end
with a dispatch plan, so none auto-stalls.

#### Scenario: A session settles and the operator has not flipped

- **WHEN** a design session settles with no `stage:done` on its items
- **THEN** nothing is collected, merged or closed, and the pane stays open
  for the next round

#### Scenario: The loop needs no configuration to know what done means

- **WHEN** the intent loop runs against a milestone with no completion
  signal named anywhere in its parameters
- **THEN** it consumes `stage:done` and reports no unresolved-signal note

#### Scenario: The board is not consulted for completion

- **WHEN** an item's board row sits at any Status
- **THEN** that Status does not make the item complete or incomplete

### Requirement: The flip is the same signal from the pane or from GitHub

The operator SHALL be able to produce `stage:done` two ways, and the loop
SHALL NOT distinguish them:

- **by word in the pane** — the operator tells the session it is done, and
  the session writes `stage:done` to its own item and settles;
- **directly on GitHub** — the operator adds the label to the item.

There is one flip and one filter. A session that is told it is done SHALL
write the label to the items it carries and settle rather than doing
anything further with the deliverables: the collect, the merge and the
closes are the loop's.

When the word arrives as approval of a dispatch plan, the session
SHALL apply the protocol's ordered steps
(`skills/_reference/dispatch-plan.md`) before settling — commits first,
the composed batches and cards at Backlog per container, `stage:done`,
then the board Ready flips, which are the one exception to a session
never moving an item to `state:ready`. The collect, the merge and the
closes remain the loop's, and `stage:done` SHALL precede any Ready flip
so a loop restart mid-apply merges the finished branch before any
released batch can dispatch.

#### Scenario: The operator approves a dispatch plan

- **WHEN** the operator approves a session's dispatch plan
- **THEN** the session commits its close files, files the elaborations
  and cards at Backlog, writes `stage:done` on its own items, flips the
  approved batches and cards to board Ready, and settles
- **AND** the loop consumes the `stage:done` items and the Ready batch
  exactly as it would had the operator produced them on GitHub

#### Scenario: The operator says so in the pane

- **WHEN** the operator tells a running design session that an item is done
- **THEN** the session adds `stage:done` to that item and settles
- **AND** the loop's next pass acts on the label exactly as it would on one
  the operator added on GitHub

#### Scenario: The operator flips on GitHub while the pane is open

- **WHEN** the operator adds `stage:done` on GitHub to an item whose session
  is still running
- **THEN** the loop consumes the flip on its next pass, with no message
  passing between the operator and the session

### Requirement: The loop writes `stage:in-session` at launch and `stage:collected` once gathered

The intent loop SHALL write `stage:in-session` on each item of a batch as
that batch's session is launched, alongside the `state:ready` →
`state:in-progress` relabel it already makes.

The intent loop SHALL write `stage:collected` on an item once that item's
deliverables have been gathered.

`stage:in-session` names the whole span in which the operator iterates,
however many rounds it holds; the rounds themselves are not stages.

#### Scenario: A batch is dispatched

- **WHEN** the loop launches a design session carrying three items
- **THEN** all three carry `stage:in-session` and `state:in-progress`

#### Scenario: Deliverables are gathered for an item

- **WHEN** the loop collects an item's deliverables after its `stage:done`
- **THEN** that item carries `stage:collected`

### Requirement: Each item's stages advance and flip independently

A design session MAY carry several items, and each item's stage SHALL
advance on its own. The loop SHALL act on every item that carries
`stage:done` whether or not its siblings in the same session do.

Today's all-or-nothing predicate is the behaviour this replaces: an
operator who marks two of three items done gets nothing collected, nothing
merged and nothing closed, because the completion test returns false on the
first item that is not done.

For an item at `stage:done` the loop SHALL collect that item's deliverables,
mark it `stage:collected`, and close it.

#### Scenario: Two of three items are flipped

- **WHEN** the operator flips `stage:done` on two of a session's three items
- **THEN** those two are collected, marked `stage:collected` and closed
- **AND** the third stays at `stage:in-session` with its work untouched

#### Scenario: The last item is flipped later

- **WHEN** the operator flips the remaining item on a later pass
- **THEN** it is collected, marked `stage:collected` and closed, and the
  two already handled are not handled again

### Requirement: The session-scoped acts wait for the whole session

Merging the session's `sess/*` branch and closing its pane are properties of
the session, not of an item, and SHALL happen once every item the session
carries has reached `stage:collected`.

A branch merged while the session is still working the remaining items would
merge a half-finished tree, and a pane closed under a running session
destroys the work in it. The per-item independence above is about the
tracker; the session's own resources have one lifetime.

#### Scenario: A partially-flipped session keeps its pane

- **WHEN** some but not all of a session's items are collected
- **THEN** the `sess/*` branch is not merged and the pane is not closed

#### Scenario: The last item completes the session

- **WHEN** the final item of a session reaches `stage:collected`
- **THEN** the `sess/*` branch is merged through the gate and the pane is
  closed

#### Scenario: A stalled or andon-raising session is untouched

- **WHEN** a session stalls, or an item carries the andon marker
- **THEN** its pane is left open and nothing is merged or closed, as it is
  today — a stalled session is evidence, and a raised andon is a pause

### Requirement: Board Status stays batch-approval only

No Status option SHALL be added to the org Project for design-session
completion, and the board's Status field SHALL keep its existing meaning:
the operator's batch-approval surface, where a unit or an elaboration moves
from Backlog to Ready.

Per-item session state lives in labels, with every other signal the loops
read. That is the reason the label option was taken over the board option
in R1, and adding a Status later would reintroduce the second store the
decision exists to avoid.

#### Scenario: The board's Status options after this change

- **WHEN** the org Project's Status field is read
- **THEN** its options are the batch-approval ones and hold no
  session-completion state

#### Scenario: An operator looks for where per-item state lives

- **WHEN** the operator wants to know which items of a running session are
  done
- **THEN** the answer is the items' `stage:*` labels, not a board column

### Requirement: R1 is recorded as resolved in the record that raised it

`design/loop-programs.md` SHALL record R1 as resolved by this decision,
naming `stage:done` as the signal and the operator as its writer, rather
than continuing to list it among the open questions.

The record is the one that raised the question, and a question answered in
code and left open in the record is how the next reader re-opens it.

#### Scenario: The record is read after this change

- **WHEN** a reader looks up R1 in `design/loop-programs.md`
- **THEN** it names the operator-set `stage:done` label as the answer
- **AND** the record's open-questions section no longer offers the three
  candidates as an undecided choice

