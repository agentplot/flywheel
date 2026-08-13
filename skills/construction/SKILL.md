---
name: construction
description: Run the flywheel construction loop — a bolt conductor drives released assertions through spec, review, build, test, and merge across built-repo bolt branches, tracked as items on the org's tracker. Use when a bolt is created or amended, when the operator asks to check on or land construction work, or when construction findings need routing.
---

# Flywheel construction — the bolt loop

One bolt = one construction iteration = one OpenSpec change bound to a
bolt schema member — `bolt-default`, `bolt-quick`, `bolt-deep`, where
**the member picked at creation IS the bolt type**, setting the review
steps the loop schedules — plus the tracker
milestone `bolt/<slug>` holding its items. The items are the released
assertions, moved there at release; **the assertion is the proposal**,
and every spec derives from the assertion record and the decisions it
cites, never from a restatement. A bolt exists only past the operator's
release, so bolt conductors auto-start on request, and the release that
created a bolt covers every wave of agents inside it.

The tracker practice — labels, lifecycle, batches, comments as narrative,
routing as item creation — is stated once in `flywheel:inception` and
reads the same here. The invocations are in the plugin's
`skills/_reference/herdr.md`; the object-graph rules and the quick-bolt
worked example are `skills/_reference/tracker.md` — when a situation is
not covered there or by a work order, queue a question rather than
inventing structure.

## Running agents

Construction runs on herdr; names are the addressing scheme. Check
`test "${HERDR_ENV:-}" = 1` before starting anything — if it fails, say
so and stop rather than reaching for the `Agent` tool, whose subagents
are invisible to the operator. The one exception: inside the conductor's
own `/opsx:apply` loop run, the sessions the loop launches are
permitted, each isolated in its own worktree, with the run ID reported.

Before first construction in a repo, audit its readiness: `.config/wt.toml`
gates, named verification commands, reset path, OpenSpec root. Queue
gaps as items rather than improvising around them.

## What lives where

- **The bolt conductor** writes the bolt change's artifacts (`bolt.md`)
  and drives the items; it merges every construction branch and lands
  every landing.
- **Sessions** write the built repo inside their own worktrees, and their
  own spec-driven changes there. Book chapters and the context map are
  the design loop's; a design-level finding — the design is wrong, not
  the build — is queued on the source intent's milestone, never fixed
  from here.
- **Three edits the conductor makes directly, with no item**: a repo's
  CLAUDE.md, an architecture decision record (into the built repo's
  log4brains layout — the bolt is where the material for one exists),
  and the loop's own machinery where the change is small and
  self-evident. Everything else the bolt lands is carried by an item.

## Topology

One bolt branch + worktree per involved built repo (`bolt/<slug>`),
alive for the bolt's lifetime. Sessions build on nested worktrees off
the bolt branch — concurrent when items are independent, serial when
they share contracts. Building directly on the bolt branch is legal only
for a bolt with a single small item. Batch acceptance after 2–3
merge-backs by default; a batch of one for high-risk changes.

Agents sharing a worktree share a git index: commit by pathspec, and the
conductor lands a spec agent's artifacts itself when agents share a
tree.

## The item flow

A released assertion carries `type:assertion`, and it is the one
tracked object for its whole construction: the stages below create no
items of their own — the dynamic workflow decides those moves, and the
item's comments record them. Each item's progress is its comment
history — spec landed, review verdict, build done, merge SHA — and its
label stays `state:in-progress` from first spec work until it closes
`closed:done` with the landing SHA in the closing comment. Only
discoveries become new items: findings, readiness gaps, design-level
faults queued to the source intent.

**WHICH STAGES EXIST IS THE BOLT TYPE'S FACT, NOT THIS SKILL'S.** The
loop — its stages, their order, whether any review runs — is defined
solely by the change's schema (`openspec instructions` shows it), and
is compiled from that instruction into the change's own
`openspec/changes/<slug>/workflow.js`, mechanics taken verbatim from
`workflows/reference-loop.js`. This skill never adds a stage the loop
did not schedule: no review, no re-review, no bounce round exists
unless the bolt type's own instruction names it. What this skill holds
is the practice shared by every stage the loop does run:

- **One spec-driven change per assertion** (`/opsx:ff` each); the
  assertion's record binds one change id and one landing ref. `openspec validate --strict` green before a spec
  counts; cite by anchor or quoted phrase, never line number; re-read
  every neighbour a spec claims something about from disk at build
  time.
- **The no-spec path — quick bolts only**: inside a `bolt-quick`, the
  build session starts in plan mode (`--permission-mode plan`) and
  the conductor approves the plan against the item's claim through
  the plan dialog. On other types every item is specced — the bolt
  type is the scrutiny the operator chose at release, and the
  conductor never downgrades it.
- **Merging**: session branch to bolt branch through the gate
  (`wt merge <bolt-branch> --no-remove -C <worktree>`, never
  `--yes`); bolt branch to main through the merge gate, one
  writer at a time, when `bolt.md`'s merge criteria hold. Comment the
  SHA, close the item, archive the built repo's spec-driven change,
  and comment the source intent's assertion item so the intent
  records the landing.

## State claims

Stated in full in `flywheel:inception`; it binds every spec and charge
written here. The short form: content over state, mechanism over
snapshot, every measurement named with the tree it was taken on, cite by
anchor never line number — and state a constraint only as strongly as
you verified it, never at remembered or feared strength, because an
agent told to expect a failure that cannot happen learns to discount
constraints.

## Reaching the operator

The inner loop assumes the operator is absent. A conductor or session
blocked on the operator's word posts the question as a comment on its
item — one line of question, options if any, a pointer to evidence —
and adds the `needs-operator` label; the tracker is the channel of
record. Dispatch DMs the item's assignee on Discord with the line and
the item link, falling back to a GitHub `@mention` in the comment when
no DM route exists; the fleet layer's reconcile pass nudges dispatch
whenever a `needs-operator` item is sitting unanswered. The operator's
answer lands as a comment — directly or relayed by dispatch — and
whoever applies the word removes the label. Work on everything the
question does not gate continues meanwhile.

## The long-lived posture

Work the ready set to empty, then stop at the queue. Every released
item with an unblocked next action is dispatched; when all are waiting
on running sessions, park on them (`herdr agent wait`), and when the
ready set is empty, present this bolt's queue — `state:queued` items
and Backlog units, one line each — and wait for the operator to move
one to Ready.
New work pushed into a live bolt joins as queued items; scope that
belongs elsewhere is queued elsewhere.

**Cleanup is mechanical and immediate; archive is the operator's.**
At the merge, a merged-back session's pane, worktree and branch go — no
word needed, it is all reproducible — and the bolt branch is
reclaimed the moment it lands on main. When the milestone's items are
all closed, report that and stop; the operator closes the milestone
on GitHub (directly, or through dispatch), and the fleet layer then
charges a fresh conductor session with the archive: `openspec
archive <slug>`, committed. The fleet layer also stops a settled
conductor whose milestone has no job — state lives on the tracker and
in git, so a later job rehydrates a fresh session from the records.
