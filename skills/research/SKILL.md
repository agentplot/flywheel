---
name: research
description: Work the investigation a flywheel research-type design session runs — read code, docs, and a tool's actual behavior to answer a factual question, and deliver the answer with its evidence. Use whenever a design session's work order names the research type.
---

# Flywheel research — the investigation that reads rather than builds

You are a design session charged with the **research type**. Your batch
has a factual question, and the answer is already on disk or in a running
system: in code, in docs, in an API's actual behavior, in what a command
actually prints.

## You read; you do not build

That is the boundary between this type and the prototype type: a
prototype builds a throwaway to *make* a fact exist so it can be
measured; research goes and *finds* a fact that already exists. Reading
includes running things to observe them — a command, a script that only
prints, a request against an API you are characterizing. If the question
turns out to need something built to answer it, report that the next
batch should be a prototype.

Most research sessions edit no files and need no worktree: read, comment,
report.

## The finding

Your answer goes in the session report and as a comment on the item, and
it names:

- the question you were sent to answer;
- the answer, plainly, including "no" and "it depends, on this";
- the evidence — the file and anchor, the command and its output, the
  observed behavior — so the next reader can check it rather than trust
  it;
- the decision(s) the answer feeds.

An answer of "not what we assumed" is the finding, not a failed
investigation.

## What you find along the way

Investigations turn up broken things; that is much of what they are for.
A small fix inside your batch's released scope is work — make it, commit
it in your worktree, note it in your report. Anything beyond that scope
is a queued item: write down exactly what the fix would be (that is worth
a lot to whoever lands it), file it, and keep investigating. Neither is a
reason to stop.

## On the tracker

The object-graph rules are the shared copy at
`skills/_reference/tracker.md`; the invocations are in `herdr.md`
beside it. Your contract:

- **You receive**: items whose bodies ask factual questions, `type:research`, flipped `state:in-progress` by your conductor.
- **You leave**: the answer as a comment on each item, evidence as pointers. A small fix inside the batch's ready scope is work, not a finding; discoveries beyond it are queued items.
- The conductor closes items on your evidence; you never close your own.
