---
name: proposal-writing
description: The exception path a flywheel construction session takes when a released work item is unmineable — the claim too vague to spec, or contradicted by a sibling. The item body is the proposal in the ordinary case; this type exists for the case where it cannot be. Use whenever a construction session's work order names the proposal-writing type.
---

# Flywheel proposal-writing — the exception for unmineable work items

**The item body is the proposal.** In the ordinary case a bolt's spec
sessions work straight from the work item and the sources it
cites, and no proposal-writing session exists. You were charged because
an item arrived unmineable: too vague to state a checkable claim,
contradicted by a sibling, or covering work that is really several.

## The first move is sending it back

An unmineable item is its plan's to fix — the plan came from the
book, a session, or the operator, not from this bolt. Report precisely
what blocks the mining: the
claim that cannot be checked against a tree, the sibling it
contradicts, the seam where it splits. That report, commented on the
item and its unit, is this type's usual whole output.

## When you draft instead

When the work order says the split is yours — one item that is
honestly several buildable claims — draft one proposal per claim, each
carrying:

- the claim — what becomes true in the repo, stated so its absence is
  checkable;
- the repo it lands in, and the decisions it cites;
- what done looks like — the observable state, not the steps;
- which item it serves — the original stays open until all its
  claims land.

Drafts are files in your worktree; you queue an item per claim on the
bolt's unit and wire the dependencies yourself. A decision that looks
wrong is a design finding for the intent, never a thing you fix by
drafting around it.

## On the tracker

The object-graph rules are the shared copy at
`skills/_reference/tracker.md`; the invocations are in `herdr.md`
beside it. Your contract:

- **You receive**: an unmineable work item and a work order saying the split is the bolt's to draft.
- **You leave**: the drafted split as files, one new work item queued on the bolt's unit per claim, and a comment on the original item naming what replaces it — the original closes `closed:superseded` against those replacements.

## What you report

Per item: mineable as split (with the drafts), or blocked (with
exactly what its plan's author must fix).
