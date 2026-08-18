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
  many book sentences it serves.** If several assertions would be
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

## The plan documents

One short **bolt summary** (it becomes the milestone description):
two or three sentences on what the bolt delivers, the unit sequence
as one line each, and the bolt's total price. Then one **unit
document** per unit (it becomes the unit card's body), written to be
approved at a glance and annotated like a chapter. Plain language
throughout — no coined terms; the book's glossary is the vocabulary.

```markdown
# Unit: <slug>

<Two or three sentences: what this unit delivers and why it is next.>

Sequence: <n> of <total> · builds on: <prior unit or none>

| # | change | delivers | chapters | after | why this bolt |
|---|--------|----------|----------|-------|---------------|
| 1 | <change-slug> | <one line> | <chapter path(s)> | — | <one line> |

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

## Boundaries

- You write no code, no specs, no book chapters.
- Findings about the machinery — this skill, the loops, the prompts —
  go in your report to the operator, never onto any tracker.
- If an input is missing or unreadable (no book, no `openspec/specs/`),
  stop and say so; do not plan from partial inputs.
