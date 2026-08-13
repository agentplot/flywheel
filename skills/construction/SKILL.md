---
name: construction
description: Run the flywheel construction loop — the bolt loop drives released assertions through spec, build, verify, merge and landing across built-repo bolt branches, tracked as items on the org's tracker. Use when a bolt is created or amended, when the operator asks to check on or land construction work, or when construction findings need routing.
---

# Flywheel construction — the bolt loop

One bolt = one construction iteration = one OpenSpec change bound to a
bolt schema member — `bolt-direct`, `bolt-default`, `bolt-quick`,
`bolt-adversarial`,
where **the member picked at creation IS the bolt type**, setting the
review steps the loop schedules and the stages it runs (`bolt-direct`
declares spec, build, merge, land — no verify) — plus the tracker
milestone `bolt/<slug>` holding its items. The items are the released
assertions, moved there at release; **the assertion is the proposal**,
and every spec derives from the assertion record and the decisions it
cites, never from a restatement. A bolt exists only past the operator's
release, so the server starts its loop the moment the milestone has a
job, and the release that created a bolt covers every wave of agents
inside it.

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
are invisible to the operator. The loop itself launches through the
session runner — `launch`/`wait`/`collect`/`close` — which gives a pane
to anything the operator might watch or answer and runs only
unsupervised stages headless.

Before first construction in a repo, audit its readiness: `.config/wt.toml`
gates, named verification commands, reset path, OpenSpec root. Queue
gaps as items rather than improvising around them.

## What lives where

- **The bolt loop** — `bin/flywheel-bolt-loop`, one stateless process
  per bolt milestone, started and stopped by `flywheel server` — drives
  the items: it scaffolds the bolt change's artifacts (`bolt.md`), and
  it merges every construction branch and lands every landing. It reads
  state and enforces contracts; every judgment it needs is asked of a
  session or of the operator.
- **Sessions** write the built repo inside their own worktrees, and their
  own spec-driven changes there. Book chapters and the context map are
  the design loop's; a design-level finding — the design is wrong, not
  the build — is queued on the source intent's milestone, never fixed
  from here.
- **Nothing edits without an item**, however small: a repo's CLAUDE.md,
  an architecture decision record (into the built repo's log4brains
  layout — the bolt is where the material for one exists), a tweak to
  the loop's own machinery. Each is a GitHub issue like all other work,
  and everything the bolt lands is carried by an item.

## Topology

One bolt branch + worktree per involved built repo (`bolt/<slug>`),
alive for the bolt's lifetime. Sessions build on nested worktrees off
the bolt branch — concurrent when items are independent, serial when
they share contracts. Building directly on the bolt branch is legal only
for a bolt with a single small item. Batch acceptance after 2–3
merge-backs by default; a batch of one for high-risk changes.

Agents sharing a worktree share a git index: every session commits its
own artifacts by pathspec — never `-a`, never `add -A` — so a sibling's
staged work is never swept into a commit that did not mean it.

## The item flow

A released assertion carries `type:assertion`, and it is the one
tracked object for its whole construction: the stages below create no
items of their own — the dynamic workflow decides those moves, and the
item's comments record them. Each item's progress is its comment
history — spec landed, review verdict, build done, merge SHA — plus the
one `stage:*` label naming its leading edge. Its
label stays `state:in-progress` from first spec work until the
merge-back, where the loop closes it `closed:merged` with the merge SHA
so the unit parent's native bar advances there; the landing then
upgrades that reason to `closed:done` with the landing SHA in the
closing comment. A closed item carries exactly one `closed:*` reason at
every moment. Only
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
- **The plan-mode path — quick bolts only**: where a `bolt-quick`
  declares it, the build session starts in plan mode
  (`--permission-mode plan`); approval is a judgment, so an approver
  session checks the plan against the item's claim and the loop drives
  the plan dialog on the verdict it answers with, pausing the batch
  after two returns rather than bouncing again. On other types every item is
  specced — the bolt type is the scrutiny the operator chose at
  release, and a declaration against those types is refused rather than
  honoured quietly.
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

The inner loop assumes the operator is absent. A session blocked on the
operator's word posts the question as a comment on its item — one line
of question, options if any, a pointer to evidence — and adds the
`needs-operator` label, and the loop does the same whenever it pauses an
item; the tracker is the channel of record. Dispatch DMs the item's
assignee on Discord with the line and the item link, falling back to a
GitHub `@mention` in the comment when no DM route exists; its own
filter is every open `needs-operator` item, so one sitting unanswered
keeps coming back round. The operator's answer lands as a comment —
directly or relayed by dispatch — and whoever applies the word removes
the label. Work on everything the question does not gate continues
meanwhile.

## The posture at the queue

Work the ready set to empty, then stop. Every released item with an
unblocked next action is dispatched; when all are waiting on running
sessions, park on them (`herdr agent wait`); and when the ready set is
empty and the guards wrote nothing, report this bolt's queue —
`state:queued` items and Backlog units, one line each — and STOP, which
is a finished pass and not a failure. New work pushed into a live bolt
joins as queued items; scope that belongs elsewhere is queued
elsewhere.

**Cleanup is mechanical and immediate; archive is the operator's.**
At the merge, a merged-back session's pane, worktree and branch go — no
word needed, it is all reproducible — and the bolt branch is
reclaimed the moment it lands on main. When the milestone's items are
all closed, the loop proposes closure and stops; the operator closes
the milestone on GitHub (directly, or through dispatch), and the
server's next pass runs the archive itself — `openspec archive <slug>
--yes --json`, committed by pathspec. It needs no session because it
needs no judgment: JSON mode never prompts, and the one case it cannot
decide alone comes back as a diagnostic the server routes to the
operator with `needs-operator`. The server also stops a loop whose
milestone has no job — state lives on the tracker and in git, so a
later job starts a fresh, stateless process that re-reads the records.
