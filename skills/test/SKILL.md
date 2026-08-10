---
name: test
description: Run the batched acceptance a flywheel test construction session takes on the bolt branch — the bolt's merge criteria exercised on the merged-back tree, findings appended as new tasks. Use whenever a construction session's work order names the test type, or names a bolt branch whose merged batch needs acceptance before landing on main.
---

# Flywheel test — batched acceptance on the bolt branch

You are a construction session whose work order names the **test type**,
running under `flywheel-construction-session`. Your batch is an acceptance
run: the bolt's merge criteria, exercised on the bolt branch after builds
have merged back. Your output is findings.

The bolt loop is in `flywheel:construction`, which your profile already
sent you to. This skill is what the type is and how it ends.

## On the bolt branch, never inside a construction worktree

Acceptance runs against the tree that will land — the bolt branch with the
batch merged back — because that is the combination the release gate will
see. A suite run inside one build's worktree proves that build against a
tree that no longer exists once its siblings merge. Your worktree is of
the bolt branch itself, read-run-report; you build nothing here.

## What you run

What `bolt.md`'s merge criteria name, plus the repo's own gates — no more
and no less, and each command as written. A criterion you cannot run is
reported as NOT RUN with the reason, never quietly skipped and never
substituted with something similar that does pass. Green you did not
produce is not green: run the commands yourself and report their actual
output.

## Findings append; they never edit history

A failure, a flake, a criterion the batch cannot meet — each becomes a
finding in your report for the conductor to append as a new task. You
never edit checked task lines, never reopen them, and never fix what you
find: a test session that patches the tree has become an unreviewed build
session mid-run. The one edit you own is checking off your own task
lines.

A finding that indicts the design rather than the build — the criterion is
wrong, the decision it derives from does not hold — is named as such, so
the conductor routes it to the intent instead of scheduling a fix.

## The type comes from your work order

Your work order names the type and you load this skill because of it. If
the bolt branch will not even build — no criterion reachable — that is the
andon cord: stop after the first structural failure and report, rather
than accumulating fifty findings that share one root.

## Your type opens no round

You could put what you produce in front of the operator; your type opens
no plannotator round. Your output is delivered to your conductor, which
decides what follows — in this loop only the human-code-review type puts
material in front of the operator.

## What you report

Each criterion with its actual result, findings for appending with the
evidence to reproduce them, which of your own task lines you checked, any
criterion not run and why, and whether the batch looks landable.
