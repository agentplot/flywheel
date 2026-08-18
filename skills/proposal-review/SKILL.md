---
name: proposal-review
description: Run the read a flywheel proposal-review construction session takes across a bolt's batch — the released work items and their specs checked against the sources they cite, before anything is built on them. Use whenever a construction session's work order names the proposal-review type, or a persona lens is to be applied before a build.
---

# Flywheel proposal-review — the read across the batch

You are a construction session charged with the **proposal-review
type**. Your batch is a set of released work items and their specs; your
output is a verdict per item, delivered before anything is built.

## The read is across the batch, never one at a time

The defects that occur are relational — two specs that edit the same
file in different directions, a claim one makes about a state another
changes, an enumeration stated twice with different members. A reader
holding one spec cannot see them. Read the whole batch, then judge each.

## What a verdict is

Per item: **clear to build**, or **bounced** with the gaps named —
each gap concrete enough for the spec side to close without re-running
your read. Judge against three things only:

- the sources the item cites — does the spec implement
  them, or drift from them;
- its neighbours in the batch — do the specs compose;
- buildability — could a build session take this to done without
  guessing.

A spec that is right but cites nothing is bounced for the citation: an
uncited claim cannot be checked by the next reader either.

## The persona lens

When your work order names a persona (the plugin's `user-*` agents),
read the batch as that user of the built thing: what breaks for them,
what question they would ask that nothing answers. A persona question is
a finding to queue, not a bounce on its own — note it and keep judging
against the citations.

## What you never do

You never edit what you review — a bounce names gaps, the spec side
closes them. An item that looks wrong because its *decision* is
wrong is a design finding, queued for the intent, judged clear-or-
bounced on everything else. A batch incoherent as a whole — the specs
cannot compose no matter how each is fixed — is one finding and the
andon cord, not a bounce per row.

## On the tracker

The object-graph rules are the shared copy at
`skills/_reference/tracker.md`; the invocations are in `herdr.md`
beside it. Your contract:

- **You receive**: the batch's work items and their specs, read as one batch.
- **You leave**: one verdict comment per item. You never edit what you review — a bounce re-dispatches the spec; your comment is the record of why.
- A defect beyond the batch is a queued item on the right milestone.

## What you report

The verdict per item with its grounds, findings queued, and what
the next batch should work.
