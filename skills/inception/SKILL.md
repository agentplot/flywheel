---
name: inception
description: Run the flywheel design loop — dispatch raw ideas into intent changes and tracker items, run design sessions that close decisions and write the books and the context map, hand work to construction as the operator moves batches to Ready. Use when the operator files or discusses a new idea or intent, asks where an idea should go, asks to work an intent's design items, or asks "what's in design".
---

# Flywheel inception — the design loop

One intent = one OpenSpec change bound to the `flywheel-intent` schema
(shipped in this plugin's `schemas/`), plus one tracker milestone
(`intent/<slug>`) holding its work items. The change holds the durable
prose — `intent.md`, `decisions/`, `questions/`, `assertions/`,
`sessions/` — and the tracker holds every mutable fact: item state,
dependencies, the queue, the narrative in comments. Nothing is recorded
in both places; a file keeps only terminal facts.

Two roles load this skill: **dispatch** and **design sessions** under
either session profile. The **intent loop** — `bin/flywheel-intent-loop`,
one process per milestone — is a program rather than a reader; what it
does is written down here so the actors around it can count on it.

## The tracker

GitHub Issues on the org's tracker repo — the `tracker:` line in the
org's `fleet.yaml`. Every machinery write runs as the app:
`GH_TOKEN=$("${CLAUDE_PLUGIN_ROOT}"/bin/flywheel-token --org <org>) gh …`
— the plugin's `bin/` is not on `PATH`; `${CLAUDE_PLUGIN_ROOT}` is
substituted into this skill at load and is the `<plugin-root>` the
references speak of. The invocations, label
set, and batch queries are in the plugin's `skills/_reference/herdr.md`;
the object-graph rules and two worked examples are the shared copy at
`skills/_reference/tracker.md` — when a situation is not covered there
or by a work order, queue a question rather than inventing structure.

- **An item** is an issue: title imperative, body one to three sentences
  plus pointers to the record it serves, milestone from birth, labels
  `type:*` and exactly one `state:*`. The type is the session type that
  works it — a question borrows the type of the session that will answer
  it — except `type:assertion`: the released claim itself, whose
  construction stages live in its comments, never as items of their own.
- **The lifecycle** is `state:queued → state:ready → state:in-progress`,
  ending closed with a `closed:*` reason — done, declined, superseded,
  parked. Anyone queues; only the operator's word makes an item ready;
  an item's progress is its comment history.
- **A batch** is a parent issue whose sub-issues are the batch,
  composed with `flywheel-batch`, sitting in the Project at Status
  **Backlog**. Its kind is what approving it authorizes: a **unit**
  releases construction work — AI-DLC's unit of work; an
  **elaboration** authorizes design sessions. The operator approves by
  moving the batch to **Ready** on the board — one move per batch,
  never per item. Batches group by **thread**, not by type: a
  prototype, the questions it answers, and the writeback of its findings
  are one approval; the loop partitions the types into sessions at
  work time.
- **Milestones** are the change-sized containers, exactly two forms:
  `intent/<slug>` and `bolt/<slug>`. Everything an intent owns —
  questions, assertions, prototypes, writebacks — sits on its one
  milestone, distinguished by `type:*`. Dependencies are the items'
  native blocked-by relations, declared best-effort by whoever files an
  item; the loop computes readiness from the field and never reasons
  about it.

**Routing is creating the item where it belongs.** A finding for another
change is queued on that change's milestone, and the open item is the
obligation — nothing needs a second ledger to avoid being lost.

## Running agents

Supervised sessions run on herdr; names are the addressing scheme. The
loop launches, waits on, collects and closes them through the session
runner (`bin/_flywheel_sessions.py`), which reuses any agent already
running under the name — so a restarted loop process never puts two
sessions on the same work. Check `test "${HERDR_ENV:-}" = 1` before
starting anything yourself — if it fails you cannot address standing
agents; say so and stop rather than reaching for the `Agent` tool, whose
subagents are invisible to the operator.

The herdr and worktrunk invocations — starting an agent, the
rename-then-confirm protocol, cutting worktrees, merging through the
gate, teardown — are in `skills/_reference/herdr.md`, the one shared
copy. Read it before doing any of them.

## What lives where

- **A design session** writes the change's records: its own
  `sessions/<date>-<slug>/` directory, the decision, question and
  assertion records its work order charged it to close, and the books and
  map for writeback batches — all inside its own worktree.
- **The intent loop** writes no records. Its merge of a session's branch
  is what admits that session's file writes to main.
- **Anyone** writes the tracker: items, comments, queued discoveries.
- Construction — every other file edit, in any repo, the loop's own
  machinery included — reaches a repo through a released bolt.

## Sessions

A work order is the change id, the session type, the item numbers, and
one or two plain sentences of goal. Worktree, session directory, and
model are launch mechanics the loop sets, not work order content.

- **Batch generously, partition by judgment.** Type is the hard
  boundary — a session loads one type skill. Within a type: related
  topics share a session, unrelated ones split even at the same type,
  and prototypes ride alone by default — each is its own experiment. A
  session costs a pane, a worktree, and its reading — spend it on a
  real batch, and never split just to make sessions smaller.
- **A session that edits no files gets no worktree.** Most research
  reads, comments its answer, and reports — no branch, no merge, no
  teardown.
- **Sessions run with their own judgment.** A small fix inside the
  batch's ready scope is work, not a finding. Discoveries beyond the
  batch are queued items, filed in a minute. Escalation is for being
  blocked, not for noticing things.
- **A report is comment-sized**: what happened, evidence as pointers,
  what it asks the operator to decide. A report that is genuinely a
  document is a file in the session directory the comment points at. It
  goes on the item and into the pane; there is nobody to prompt.
- The six design types and their skills: `flywheel:planning`,
  `flywheel:interactive`, `flywheel:prototype`, `flywheel:research`,
  `flywheel:writeback`, `flywheel:handoff`. An item's `type:*` label
  picks the type and the loop batches by it. Interactive runs under
  `flywheel-interactive-session`; the other five under
  `flywheel-design-session`.

## Which channel carries which question

The outer loop is high-touch: design sessions reach the operator
directly, and dispatch relays nothing for them.

| the answer is | channel | blocking? |
|---|---|---|
| a sentence | an inline question | no — keep working on what it does not gate |
| margin notes on a document that exists | `plannotator annotate <file>` | yes |
| a choice across coupled decisions | a lavish page | yes |

Escalation runs one way: take the cheapest channel that can carry the
answer, and never demote a question back down or re-ask it. **The sole
writer of a file under review opens its round**, and feedback returns to
the invoker alone — annotations concerning another actor's files travel
as queued items or your report, never as raw relays.

## State claims

A claim about a neighbouring artifact's state decays silently while
batches run, so: prefer a CONTENT claim the tree can be checked against;
where state is unavoidable, name the mechanism rather than its current
output; give every measurement the tree it was taken on, and cite by
anchor or quoted phrase, never by line number. A decision record is
authoritative on its decision and provisional on its measurements. ONE
ANSWER PER RECORD: when a decision moves, rewrite every statement of it
in that record, and state each enumeration once, marked as the one to
copy.

## Dispatch

The standing singleton, and a pure GitHub-and-relay actor: no repo
checkout, no file writes — everything dispatch produces lands on the
tracker, and the records are written from it there. Five routes for a
raw idea — say which you chose:

1. **New intent** — dedupe against the open `intent/*` milestones, then
   create the milestone and its originating item, assigned to the
   developer whose word settles it.
2. **Assertion on an existing intent** — an idea that arrives
   work-shaped becomes a queued item on that intent's milestone; a design
   session writes the assertion record from it.
3. **Item on a running bolt** — construction-scoped work a live bolt
   covers: queue it on the bolt's milestone.
4. **Quick bolt** — small, fully defined work gets a `bolt/<slug>`
   milestone and one ready item on the operator's word at triage, put
   on the board at Status Ready (`flywheel-board`) — the lone item
   carries the approval where a batch would. Something that is
   genuinely one shell command is still one shell command; run it and
   say so.
5. **Dropped** — say so; record nothing.

Loops are started by `flywheel server`, never by dispatch.

**The operator's word is applied directly**, by whoever holds it:
edit the record or item it names, comment the change, and the loop sees
it on its next cycle. No relay ceremony exists for the operator's
own word.

Dispatch is also the inner loop's bridge to a possibly-absent operator.
An inner-loop actor blocked on the operator's word comments the
question on its item and adds `needs-operator`; dispatch DMs the item's
assignee on Discord with the line and the link — GitHub `@mention` in
the comment as the fallback — relays the answer back as a comment, and
whoever applies the word removes the label. An escalation is one line
of question, options if any, and a pointer to evidence.

## The intent loop

`bin/flywheel-intent-loop` — one stateless process per `intent/<slug>`
milestone, started and stopped by `flywheel server`. It works the ready
set to empty, then stops at the queue. It reads state and enforces
contracts and does nothing else: every judgment it might have wanted
belongs to a session or to the operator.

- **Ready items get sessions**, batched one type per batch — prototypes
  alone — and run in parallel where batches are disjoint. Items flip
  `state:in-progress` as their session launches, and a batch runs only
  once every `blocked_by` of every item in it is closed.
- **Completion is the operator's.** A session settling is not
  completion — the operator may iterate a plannotator or lavish round as
  often as they like — so the loop waits for the operator's mark on the
  tracker and reacts to that: it collects the deliverables (session
  directory, drafts, item comments), merges the session branch through
  the merge gate (`wt merge --no-remove -C <worktree>`) — books, mermaid
  and map are exactly what a documentation session should pass — closes
  the batch's items with the session's report, and closes its pane.
- **At the queue**, two guards, then wait. First, birth the handoff when
  it is due: an assertion is **settled and unbolted** when its item is
  open on `intent/<slug>` (bolting IS the milestone move to
  `bolt/<slug>`), has no parent batch, and has no open blockers — when
  any exist, one `type:handoff` item names exactly that set, born or
  amended to match. Second, compose the orphan queued items into a
  proposed batch (`flywheel-batch`) at Status **Backlog** — composing is
  not releasing — and report one line per batch and unbatched item.
  Moving a batch to Ready is the approval; the handoff session inside a
  released unit plans the bolt and moves its assertions to
  `bolt/<slug>`; the server then starts that milestone's bolt loop,
  which scaffolds its own change — an intent loop never writes a bolt
  change's artifacts.
- **Stop honestly**: nothing ready and the guards wrote nothing → the
  run stops with its report, and a second cycle against an unchanged
  tracker writes nothing. The operator closes the milestone on GitHub —
  that is the archive signal, and the server runs `openspec archive` and
  commits it. A milestone with no job has no process; a later job starts
  a fresh one that re-reads the tracker and the records.
- **The andon cord** is a session's, not the loop's: a session that
  finds the work wrong in a way no fixing will help writes the stop as a
  structured marker in its item comment and settles. The loop
  recognises the marker as code, pauses the batch — nothing merged,
  nothing closed — and sets `needs-operator`.

## Design session

Read your type's skill. What every session owes the operator when it
puts material in front of them: **show the thing, not a description of
it** — the configuration that would change, the sample each option
produces, the diagram (`branch-topology-diagram` for topology) beside
each option. If the material is a document the operator reads rather
than choices they work, run a plannotator round instead of building a
page. **Prototype when talk stalls**: the criterion is a fact a
throwaway can prove faster than an argument can settle.
