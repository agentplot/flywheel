---
name: test
description: Run the batched acceptance a flywheel test construction session takes on the bolt branch — the bolt's merge criteria exercised on the merged-back tree, findings queued as items. Use whenever a construction session's work order names the test type, or a bolt branch's merged batch needs acceptance before landing on main.
---

# Flywheel test — batched acceptance on the bolt branch

You are a construction session charged with the **test type**. Your
batch is an acceptance run: the bolt's merge criteria, exercised on the
bolt branch after builds have merged back. Your output is findings.

## On the bolt branch, never inside a construction worktree

Acceptance runs against the tree that will land — the bolt branch with
the batch merged back — because that is the combination the release
gate will see. A suite run inside one build's worktree proves that
build against a tree that no longer exists once its siblings merge.
Your worktree is of the bolt branch itself: read, run, report; you
build nothing here.

## What you run

What `bolt.md`'s merge criteria name, plus the repo's own gates — no
more and no less, each command as written. A criterion you cannot run
is reported as NOT RUN with the reason, never quietly skipped or
substituted with something similar that does pass. Green you did not
produce is not green: run the commands yourself and report their actual
output.

## Findings are queued, never fixed here

A failure, a flake, a criterion the batch cannot meet — each becomes a
queued item with the evidence to reproduce it. A test session that
patches the tree has become an unreviewed build session mid-run. A
finding that indicts the design rather than the build — the criterion
is wrong, the decision it derives from does not hold — is named as
such and queued for the intent.

A bolt branch that will not even build is the andon cord: stop after
the first structural failure rather than accumulating fifty findings
that share one root.

## On the tracker

The object-graph rules are the shared copy at
`skills/_reference/tracker.md`; the invocations are in `herdr.md`
beside it. Your contract:

- **You receive**: an acceptance charge — the bolt's merge criteria, on the bolt branch after merge-backs.
- **You leave**: the run's result as a comment where your work order says (the bolt's items or epic), and every finding as a NEW queued item on the bolt's milestone — findings are items, never in-place fixes.
- A design-level fault is queued on the source intent's milestone.

## What you report

Each criterion with its actual result, the items you queued, any
criterion not run and why, and whether the batch looks landable.
