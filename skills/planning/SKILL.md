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
consequences are what get queued as items when the conductor folds them.

When the operator's annotations close a question your work order charged
you with, write the closure yourself: the `decisions/<slug>.md` record,
the pointer on the question record, the closing comment on its item.
Your conductor's merge admits the file writes.

## Your rounds are on files you wrote

A round is opened by the sole writer of the file under review — you are
the sole writer of your session directory, so your rounds are on the
drafts in it and nowhere else. A batch that would have you annotate
another actor's file (the intent record, a spec) goes back to your
conductor instead.

```bash
plannotator annotate sessions/<date>-<slug>/<draft>.md
```

The result comes back to you, and you fold the corrections into your own
drafts. Annotations that concern other changes or other actors' files
travel through your report as proposed items, never as raw relays.

If `plannotator` does not resolve on `PATH`, report the shortfall and
stop — a round the operator never saw produces annotations nobody made.

## On the tracker

The object-graph rules are the shared copy at
`skills/_reference/tracker.md`; the invocations are in `herdr.md`
beside it. Your contract:

- **You receive**: item numbers of the decisions your round closes, `type:planning`, flipped `state:in-progress` by your conductor.
- **You leave**: one comment per item — the round's outcome and a pointer to the annotated draft in your session directory. The conductor closes items on your evidence; you never close your own.
- New work the round surfaces is a queued item on the milestone, filed in a minute.

## What you report

Which decisions closed and the draft each closed on, corrections folded,
proposed items for what the annotations opened, and what the next batch
should work.
