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

Most research batches edit no files: read, comment, report. The worktree
you launch with is for the close — folded answers and a dispatch plan,
if you have one — and costs nothing at teardown if unchanged.

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

## Close with a dispatch plan

A batch with a next round or construction to propose ends with a
dispatch plan — the protocol is the shared copy at
`skills/_reference/dispatch-plan.md`: the `close/` payload drafted as
outcomes settle, the lavish page, the exclusive routing across intent
and bolt containers, the apply order, the failure discipline. Nothing
reaches GitHub before the operator approves, and a session with nothing
to propose settles as today.

## On the tracker

The object-graph rules are the shared copy at
`skills/_reference/tracker.md`; the invocations are in `herdr.md`
beside it. Your contract:

- **You receive**: items whose bodies ask factual questions, `type:research`, flipped `state:in-progress` by the intent loop.
- **You leave**: the answer as a comment on each item, evidence as pointers. A small fix inside the batch's ready scope is work, not a finding; discoveries beyond it are queued items.
- The loop closes items on your evidence; you never close your own. The operator's word is the completion signal, and it is one label: told in the pane that an item is done, move that item to `stage:done` — the one call `flywheel-stage <n> --org <org> --repo <tracker> --stage stage:done`, which sweeps whatever stage the item carried, since an item carries exactly one `stage:*` — and settle. The loop reads the label and does the rest.
