---
name: bolt-planning
description: Run a bolt planning session — read a system's design book, the built repo's implemented specs, and the changes in flight; carve the remaining gap into one or more sequenced bolt plans, each a document the operator can approve on the board. Use when a work order charges a planning run.
---

# Bolt planning — one planning run

You compute the system's remaining work and propose how to cut it.
You do not build anything, and you decide nothing the operator has
not asked you to decide: your product is plan documents, and every
plan waits for board approval before anything else exists.

## Inputs — read all three, nothing else

The work order names the design book and the built repo.

1. **The design book, whole.** Every chapter. The destination is
   stated across chapters — synthesize; a single task may draw on
   several. Record the book's subtree commit
   (`git -C <book> log -1 --format=%h -- .`).
2. **The implemented specs** — `openspec/specs/` in the built repo:
   what the repo actually does today. Record the specs subtree commit
   (`git -C <repo> log -1 --format=%h -- openspec/specs`).
3. **The changes in flight** — `openspec/changes/` in the built repo:
   what is already being built. Never plan work a change in flight
   already covers, and never contradict its sequencing.

The gap is destination minus implemented minus in-flight. If the work
order scopes the run ("the smallest useful bolt", "a bolt about X"),
the scope limits which cuts you propose, not how carefully you read.

## Cutting the gap into a bolt of units

Two levels, two different objects:

- A **bolt** is the operator's delivery boundary: one milestone, one
  branch, one landing to main. It lives for days and absorbs several
  units. Propose ONE bolt per run unless the gap genuinely splits
  into independent deliveries — many small bolts is the failure mode
  this shape exists to avoid.
- **Name the bolt for the deliverable the operator wants to see
  working together, never for the work items that build it** — a bolt
  named for its tasks is a to-do list wearing a milestone. This rule is
  every plan author's, not only this run's: dispatch plans and dictated
  cards cite it from here.
- **Read the open `bolt/*` milestones before proposing a new one.**
  Units that serve an open bolt's deliverable fold into it as new
  cards; a related idea splits — the parts the open bolt's deliverable
  needs go in as units on it, the harder or independent parts become a
  proposed successor bolt. A new bolt is for a new deliverable, not for
  new work.
- A **unit** is one coherent batch inside the bolt: buildable in one
  pass of the construction loop, leaving the branch consistent.
  Prefer small units inside one bolt over many bolts.
- Sequence units by dependency and by risk: what unlocks the rest
  comes first. State the order and the reason for each boundary —
  what you left for a later unit, and why.
- A dependency exists on exactly three grounds, and you name which:
  **derivation** (this work's specs derive from specs another task or
  unit advances at its merge), **contention** (two tasks would write
  deltas to the same capability — chain them or fold them into one),
  or **runtime precondition** (the behavior needs an artifact the
  other work produces in the world). Anything else is independent; a
  chain without one of these grounds serializes work for nothing.
- Every task cites the chapter or chapters it derives from, by path
  (`books/<book>/src/<chapter>.md`). A task you cannot tie to a
  chapter does not go in a plan — if the code clearly needs work the
  book never describes, report that as a question for the operator
  instead: the book is silent, and silence is a design gap, not a
  license to invent.
- **A unit is a proposal to a system, written from the user's
  perspective.** Name it and open it as the feature or capability a
  user of the system gains, not as the internal mechanism that
  delivers it. The book's sentences justify the unit; the user's
  story shapes it.
- **Size each change by how much code it actually is, never by how
  many book sentences it serves.** If several claims would be
  implemented together as one small commit, make them one change, not
  several. Every change costs a full loop cycle — a spec session, a
  review, a build session, verify, a merge — so splitting is only
  worth it when a piece has its own tests, a real dependency on
  another piece, or lives in a different repo. Four changes for four
  lines of code is the failure this rule exists to stop. Before
  delivering, reread each unit and ask of every pair of changes:
  would these be one commit in one repo? If yes, merge them into one.
- **Different repos do mean different changes.** A system's book may
  cover several built repos; a unit that touches more than one then
  needs one change per repo, because each repo runs its own
  spec-driven change through its own merge gate. The unit stays whole
  — it is still one user-facing proposal — but the work splits along
  repo lines and nowhere else. A one-repo system gets no such split.

## The chore tier — below the ceremony line

Some of the gap is work with **no new behavior**: deleting dead code,
correcting a docstring or comment that lies, stamping a superseded
draft's header, renaming or moving a file, fixing a label or status.
The agent that finds such work already knows exactly what to do, and
the operator's whole decision is yes or no — so a chore NEVER gets a
unit document. An essay, a mermaid diagram, or destination-voice
framing around a two-line diff is the failure this tier exists to
stop: it spends the operator's minutes decoding ceremony around work
that needed none.

All the chores a run finds for one system collapse into **one chore
card**: title `Unit: chores` (the `chore` LABEL marks the tier — the
title keeps the grammar the loop parses), labels `plan` + `chore`,
filed on the open bolt they tidy (or the run's proposed bolt) exactly
like any card, body in this grammar and nothing more:

```markdown
# Unit: chores

System: <name>
Type: `chore` · Price: <n> changes · ~hours

| # | change | delivers |
|---|--------|----------|
| 1 | <short-name> | <one plain line — the whole instruction> |
```

No sequence line, no mermaid, no Left out, no derivation footer. A
chore needs **no chapter citation** — its justification is that it
makes the code or docs true, not that the book demands it. `chore` is
the type: the loop runs ONE session that applies the card's change
list straight on the batch branch and merges — no openspec change, no
spec session, no plan dialog, no verify; the merge gate is the check.
A chore that needs more than that is not a chore — promote it to a
unit. The round renders a chore card as one row with its changes one
line each, and one approval lands the lot; nothing-before-approval
still holds, the approval just costs the operator ten words of
reading per chore.

The test, per piece of work: would the diff add behavior a user or a
loop could observe? Yes → unit. No → chore.

## The plan documents

One **bolt summary** (it becomes the milestone description, verbatim):

```markdown
<Two or three sentences: what the bolt delivers.>

1. `<unit-slug>` — <one line> · `bolt-<type>` · <n> changes · ~<days>
2. ...

Price: <n> changes · ~<days>.

Derived from: book <sha> · specs <sha> · in flight: <change ids or none>
```

Then one **unit document** per unit (it becomes the unit card's body,
verbatim), written to be approved at a glance and annotated like a
chapter. Plain language throughout — no coined terms; the book's
glossary is the vocabulary.

Every field above is chosen and shown in the FIRST draft the operator
sees — the bolt type per unit, the mode, the price. A plan that makes
the operator ask "which type is this?" or annotate a choice into
existence has not done its job; the round is for correcting choices,
not supplying them.

**What the operator annotates IS what lands on the tracker.** A draft
put in front of the operator — a planner's, or a design session
cutting a direct bolt plan — is the milestone description plus the
unit documents in the exact grammar here, nothing reformatted
between the round and the board. A draft in any other shape gets
approved once and then transcribed, and the transcription is where
plans drift.

**`Type:` is per unit, and it is the whole choice** — a type is a
named loop configuration, and the construction path is part of it:

- `bolt-default` — spec-driven changes, reviews + verify
- `bolt-quick` — spec-driven changes, verify, no reviews
- `bolt-direct` — spec-driven changes, the merge gate as the only check
- `bolt-adversarial` — spec-driven changes, adversarial review
- `bolt-plan` — no spec artifact: the loop opens each build session in
  plan mode and the plan the operator approves in the pane stands as
  the spec, with the merge gate as the check. Right for pages and
  prose; wrong for machinery, because the work never reaches
  `openspec/specs/` and is invisible to future planning runs.

Nothing machine-read lives on the milestone: the summary is prose,
and the loop reads the type from the unit card at drive time. The
card's `System: <name>` line is machine-read the same way: it names
the fleet binding (`fleet.yaml` `books.<name>`), and construction
resolves the unit's BUILT REPO through it — `books.<name>.repo` on the
machine the loop runs on. A card naming no system builds on the
fleet's sole binding; a fleet holding several bindings pauses an
unplaceable card for the operator rather than guessing a repo.

```markdown
# Unit: <slug>

<Two or three sentences: what this unit delivers and why it is next.>

Sequence: <n> of <total> · builds on: <prior unit or none>
Type: `bolt-<type>` · Price: <n> changes · ~<days>

| # | change | delivers | sources | after | why this bolt |
|---|--------|----------|---------|-------|---------------|
| 1 | <change-slug> | <one line> | <chapter or artifact path(s)> | — | <one line> |

The `after` column names the task a task builds on, or `—`. Unmarked
tasks are independent and run concurrently; a marked task waits for
its predecessor's merge. Mark only real dependencies — a chain that
exists to look tidy serializes work for nothing.

<One mermaid diagram: what the cut builds or touches, boxes and
labeled arrows, nothing decorative.>

## Left out

- <what, and why it waits>

Derived from: book <sha> · specs <sha> · in flight: <change ids or none>
```

If the run proposes more than one bolt — the exception — each gets
its own summary and unit set, and one page states why the deliveries
are separate.

## Delivery

The work order says which mode you are in:

- **Files** — write each plan document to the directory the work
  order names. Nothing touches any tracker.
- **Board** — create the `bolt/<slug>` milestone if it does not
  exist, with the bolt summary as its description; then file exactly
  one card per proposed unit ON that milestone: title `Unit: <slug>`,
  label `plan`, the unit document as the card body with a
  `System: <name>` line under the title, the card added to the org
  Project at Status Backlog with the work order's Team, and each
  "builds on" claim mirrored as a blocked-by relationship between the
  unit cards. Supersede any unapproved plan cards from earlier runs
  (close them `closed:superseded`). Nothing else: no `state:*` label
  on any card, no work items, no other issue, comment, or label — the
  items are born at expansion, which is the bolt loop's job, after
  board approval.

A dispatch plan carries construction in this same grammar and applies
it through this same board mode — the summary, the `Unit: <slug>`
cards, the blocked-by mirroring, the supersede rule scoped to cards the
plan itself replaces (`skills/_reference/dispatch-plan.md`). One
format, whoever the author is, so nothing is reformatted between a
round and the board. Two differences are authorized by the round
itself: an approved card is moved to board Ready by the actor
applying the operator's word — including a card folded onto an open
running bolt, which the live loop expands mid-flight — where a planning
run's cards always wait at Backlog; and a plan's bolt container may
reuse an open milestone instead of creating one, per the fold rule
above.

## Boundaries

- You write no code, no specs, no book chapters.
- Findings about the machinery — this skill, the loops, the prompts —
  go in your report to the operator, never onto any tracker.
- If an input is missing or unreadable (no book, no `openspec/specs/`),
  stop and say so; do not plan from partial inputs.
