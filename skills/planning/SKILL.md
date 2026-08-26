---
name: planning
description: Run the plannotator round a flywheel planning-type design session works — put the decision drafts and plans the session itself wrote in front of the operator, fold what comes back, and report the outcomes. Use whenever a design session's work order names the planning type.
---

# Flywheel planning — the round over your own drafts

You are a design session charged with the **planning type**. Your batch
closes decisions by writing them down and putting the writing in front of
the operator to annotate.

## What you produce

A **decision draft** per decision your batch aims to close, in your own
`sessions/<date>-<slug>/` directory; plans the batch needs live there
too. Each draft states the decision and its consequences — the
consequences are what you queue as items once the round closes.

When the operator's annotations close a question your work order charged
you with, write the closure yourself: the `decisions/<slug>.md` record,
the pointer on the question record, the closing comment on its item.
The loop's merge of your session branch admits the file writes.

## Your rounds are on files you wrote

A round is opened by the sole writer of the file under review — you are
the sole writer of your session directory, so your rounds are on the
drafts in it and nowhere else. A batch that would have you annotate
another actor's file (the intent record, a spec) becomes a queued item
for that file's writer and a line in your report instead.

```bash
plannotator annotate sessions/<date>-<slug>/<draft>.md
```

The result comes back to you, and you fold the corrections into your own
drafts. Annotations that concern other changes or other actors' files
travel through your report as proposed items, never as raw relays.

If `plannotator` does not resolve on `PATH`, report the shortfall and
stop — a round the operator never saw produces annotations nobody made.

## Close with a dispatch-plan payload

A batch with a next round or construction to propose ends with a
dispatch-plan payload — the protocol is the shared copy at
`skills/_reference/dispatch-plan.md`: the `close/` payload drafted as
outcomes settle, the exclusive routing across intent and bolt
containers, then published (commit, push, marker + `dispatch:standing`
on the elaboration parent) and the session settles — dispatch runs the
round and applies, your `stage:done` included. Nothing reaches GitHub
before the operator approves. A session with nothing to propose still
publishes — the closure payload (no containers, the outcome, your items
as `done_items`) — so a dead end reaches the operator as a round row,
never as silence.

## On the tracker

The object-graph rules are the shared copy at
`skills/_reference/tracker.md`; the invocations are in `herdr.md`
beside it. Your contract:

- **You receive**: item numbers of the decisions your round closes, `type:planning`, flipped `state:in-progress` by the intent loop.
- **You leave**: one comment per item — the round's outcome and a pointer to the annotated draft in your session directory. The loop closes items on your evidence; you never close your own. The operator's word is the completion signal, and it is one label: told in the pane that an item is done, move that item to `stage:done` — the one call `flywheel-stage <n> --org <org> --repo <tracker> --stage stage:done`, which sweeps whatever stage the item carried, since an item carries exactly one `stage:*` — and settle. The loop reads the label and does the rest.
- New work the round surfaces is a `state:queued` item on the milestone, filed in a minute — queued and nothing past it: ready is the operator's board approval, sessions are the loop's to charge.

## What you report

Which decisions closed and the draft each closed on, corrections folded,
proposed items for what the annotations opened, and what the next batch
should work.
