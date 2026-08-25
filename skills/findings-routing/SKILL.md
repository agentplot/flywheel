---
name: findings-routing
description: Author the dispatch-plan payload a flywheel findings-routing session builds over a bolt's queued findings — the whole findings inbox seeded for one operator round (dispatch runs it) into the current bolt, a successor bolt, the source intents, or drop. Use whenever a work order charges a findings-routing run on a bolt's queue.
---

# Flywheel findings-routing — the round over a bolt's queue

You are a one-shot session charged by the bolt loop when it stops at a
non-empty queue. Test and code-review sessions wrote each finding as a
`state:queued` item at birth — the bolt's **findings inbox**, durable
but inert. Your whole job is one dispatch plan over that inbox: the
shared protocol at `skills/_reference/dispatch-plan.md` is the practice,
and this skill only says what its construction origin pins down.

## The rows are the queued items

Read every open `state:queued` non-container item on the bolt's
milestone, plus the finding comments they carry. Each becomes one row,
seeded with your judgment — like dispatch's intake issues, they pre-exist
as the inbox and are the subject of proposals: the apply moves, cards,
or closes them, and never duplicates one.

The containers you may propose, and what each route does at apply:

- **this bolt** — work its merge criteria need: a unit card on the open
  milestone, in bolt-planning's exact grammar, citing the finding item;
  the finding closes `closed:superseded` with the card as its successor
  pointer, because the card is now the tracked object and expansion
  births the work items.
- **a successor bolt** — related work this delivery does not need: a
  new `bolt/<slug>` container, named per bolt-planning's rule (the
  deliverable, never the task list), its cards filed the same way.
- **a source intent** — a finding that indicts the design rather than
  the build: the item moves onto that intent's milestone with the
  `type:*` of the session that will work it, and joins the elaboration
  your plan composes there.
- **backlog** — stays queued on the bolt, explicitly out of this round.
- **drop** — closed `closed:declined`, with the reason as the closing
  comment.

## The payload is real files on the bolt change

You run on the repo that owns the bolt change. Write the payload under
the bolt's own change directory —

    openspec/changes/bolt-<slug>/sessions/<date>-findings-routing/close/

— the same file shapes the protocol names, and commit it by pathspec
before any tracker write, pushing what you commit: your directory is a
shared checkout, so the standing staging rule binds you — never `-a`,
never `add -A`.

## Publish — you run no round

You author and publish; dispatch assembles every standing payload into
the one round and applies the operator's word (the protocol's
"Publishing a payload"). Three acts, then settle:

1. Commit the `close/` payload by pathspec and **push your branch** —
   dispatch has no checkout and reads the files through the contents
   API at your commit's SHA.
2. Write the round-payload marker as a comment on the anchor item — the
   bolt's unit parent, or its lowest queued finding — with
   `ORIGIN: construction` and the pushed SHA.
3. Add the `dispatch:standing` label to the same item.

No lavish page, no digest, no apply, no Ready, and no `needs-operator`:
the payload stands until a round consumes it. The loop that charged you
is already stopped, so nothing blocks; an operator who never calls a
round loses nothing — the inbox waits, and a send-back comes back to a
fresh session as the note on the anchor. Applying the plan (dispatch's
act) drains the inbox the way applying a guard's plan empties the
guard: a later run against an unrouted queue proposes again; against an
empty one, the loop charges nothing. Nothing the plan proposes reaches
GitHub before the approval.

## What you never do

You never fix a finding, build anything, or edit the built repo — you
route. A finding that needs no routing decision does not exist: backlog
is a decision too. Machinery findings follow the finding-routing rule: your
report, never the tracker.

## What you report

One line per row with its seeded route, the payload's anchor item and
SHA, and anything you left out of the plan and why.
