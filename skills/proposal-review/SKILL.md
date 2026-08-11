---
name: proposal-review
description: Run the read a flywheel proposal-review construction session takes across a bolt's batch — the released assertions and their specs checked against the decision records they cite, before anything is built on them. Use whenever a construction session's work order names the proposal-review type, or a persona lens is to be applied before a build.
---

# Flywheel proposal-review — the read across the batch

You are a construction session charged with the **proposal-review
type**. Your batch is a set of released assertions and their specs; your
output is a verdict per assertion, delivered before anything is built.

## The read is across the batch, never one at a time

The defects that occur are relational — two specs that edit the same
file in different directions, a claim one makes about a state another
changes, an enumeration stated twice with different members. A reader
holding one spec cannot see them. Read the whole batch, then judge each.

## What a verdict is

Per assertion: **clear to build**, or **bounced** with the gaps named —
each gap concrete enough for the spec side to close without re-running
your read. Judge against three things only:

- the decision records the assertion cites — does the spec implement
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
closes them. An assertion that looks wrong because its *decision* is
wrong is a design finding, queued for the intent, judged clear-or-
bounced on everything else. A batch incoherent as a whole — the specs
cannot compose no matter how each is fixed — is one finding and the
andon cord, not a bounce per row.

## What you report

The verdict per assertion with its grounds, findings queued, and what
the next batch should work.
