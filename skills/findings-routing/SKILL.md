---
name: findings-routing
description: Run the dispatch plan a flywheel findings-routing session builds over a bolt's queued findings — the whole findings inbox routed in one operator approval into the current bolt, a successor bolt, the source intents, or drop. Use whenever a work order charges a findings-routing run on a bolt's queue.
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

## The round, and the apply

Fill the template beside the protocol into `close/plan.html`, open it
with `npx -y lavish-axi`, and post the digest form as a comment on the
bolt's unit parent (or its first queued item) with `needs-operator`, so
dispatch relays it to an operator who is not at the page. Whichever
answer arrives first is the round's answer. Apply it in the protocol's
order — commit, containers at Backlog, Ready last; a card approved onto
this open bolt goes to Ready with the rest and the live loop expands it
mid-flight — then clear `needs-operator` and settle. Applying the plan drains the
inbox the way applying a guard's plan empties the guard: a later run
against an unrouted queue proposes again; against an empty one, the loop
charges nothing.

The loop that charged you is already stopped, so your round blocks
nothing. An operator who never takes it loses nothing — the inbox waits,
and you settle without applying if they send the plan back with nothing
to redraft. Nothing the plan proposes reaches GitHub before the
approval.

## What you never do

You never fix a finding, build anything, or edit the built repo — you
route. A finding that needs no routing decision does not exist: backlog
is a decision too. Machinery findings follow the finding-routing rule: your
report, never the tracker.

## What you report

One line per row with its applied route and link, what stayed backlogged
and why, and whether the inbox is empty.
