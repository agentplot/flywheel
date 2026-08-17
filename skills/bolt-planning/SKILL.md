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
   several. Record the book's current commit.
2. **The implemented specs** — `openspec/specs/` in the built repo:
   what the repo actually does today. Record the specs commit.
3. **The changes in flight** — `openspec/changes/` in the built repo:
   what is already being built. Never plan work a change in flight
   already covers, and never contradict its sequencing.

The gap is destination minus implemented minus in-flight. If the work
order scopes the run ("the smallest useful bolt", "a bolt about X"),
the scope limits which cuts you propose, not how carefully you read.

## Cutting the gap into bolts

- A bolt is one coherent construction iteration: buildable in one
  pass of the construction loop, leaving the repo consistent. Prefer
  the smallest cut that delivers something whole.
- Sequence bolts by dependency and by risk: what unlocks the rest
  comes first. State the order and the reason for each boundary —
  what you left for a later bolt, and why.
- A dependency exists on exactly three grounds, and you name which:
  **derivation** (this work's specs derive from specs another task or
  bolt advances at its merge), **contention** (two tasks would write
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

## The plan document

One document per proposed bolt, written to be approved at a glance
and annotated like a chapter. Plain language throughout — no coined
terms; the book's glossary is the vocabulary.

```markdown
# Bolt: <slug>

<Two or three sentences: what this bolt delivers and why it is next.>

Sequence: <n> of <total> · builds on: <prior bolt or none>

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

If the run proposes more than one bolt, also write a one-page summary:
a table of the sequence (order, slug, goal, size) and one paragraph on
the shape of the whole cut.

## Delivery

The work order says which mode you are in:

- **Files** — write each plan document to the directory the work
  order names. Nothing touches any tracker.
- **Board** — file exactly one card per proposed bolt on the tracker
  the work order names: label `plan`, no milestone, board Status
  Backlog, the plan document as the card body, and each "builds on"
  claim mirrored as a blocked-by relationship between the cards,
  superseding any unapproved plan cards from earlier runs (close them
  `closed:superseded`). No milestones, no work items, no other issue,
  comment, or label — expansion is the bolt loop's job, after board
  approval.

## Boundaries

- You write no code, no specs, no book chapters.
- Findings about the machinery — this skill, the loops, the prompts —
  go in your report to the operator, never onto any tracker.
- If an input is missing or unreadable (no book, no `openspec/specs/`),
  stop and say so; do not plan from partial inputs.
