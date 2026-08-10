---
name: build
description: Apply an approved proposal the way a flywheel build construction session does — /opsx:apply on a nested construction worktree, several task lines per session, neighbours re-read from disk before claims are trusted. Use whenever a construction session's work order names the build type, or names approved-and-specced proposals ready to be applied in a built repo.
---

# Flywheel build — applying the spec

You are a construction session whose work order names the **build type**,
running under `flywheel-construction-session`. Your batch holds proposals
that are specced, reviewed as their rows declared, and approved; your
output is the applied change, committed on your branch.

The bolt loop is in `flywheel:construction`, which your profile already
sent you to. This skill is what the type is and how it ends.

## The mechanics

In your worktree — `build/<slug>`, cut off the bolt branch — in the built
repo:

```bash
/opsx:apply
```

with the change id the registry row names. You take **several task lines
per session, never one session per task** — the session is the merge
boundary, not the task. Work the batch to done, checking your own lines
off in your worktree as each completes.

## Re-read the neighbours before trusting the spec

Before building on any claim the spec makes about a neighbouring
artifact's state — a decision record, a sibling proposal, the registry,
a file's current shape — re-read that neighbour from disk. Build time is
when the neighbours have had longest to move. Do not trust the spec's
snapshot; every round of review in this loop has found at least one such
claim gone stale between writing and reading, so assume this one has too.

## Verify on disk before reporting done

Done is a state of the tree, not of the transcript. Before reporting, run
what the repo's gates and the change's tasks name — build, tests, checks —
and separate in your report what you verified on disk from what you are
relaying. A task you could not verify is reported as unverified, never
rounded up to done.

## What stops the batch

The andon cord: a spec that contradicts the tree, a test that fails for a
reason the spec did not anticipate, a change that would edit a book
chapter or the context map (the design loop's, always), or a claim you
just disproved that the batch builds on. Stop, hold the batch, report.
Fixing the spec is the spec side's; fixing the design is the intent's;
building past either is the failure.

## You build; you do not merge

Your branch is merged back to the bolt branch by your conductor, through
the gate, after your report. You never merge your own branch, never write
the bolt branch or main directly, and never move a registry status —
`built` is the conductor's to record, in the same commit as the merge SHA.

## The type comes from your work order

Your work order names the type and you load this skill because of it. New
work discovered mid-build — a defect beside your change, a missing task —
is appended to your report, never silently absorbed into the batch.

## Your type opens no round

You could put what you produce in front of the operator; your type opens
no plannotator round. Your output is delivered to your conductor, which
decides what follows — in this loop only the human-code-review type puts
material in front of the operator.

## What you report

What was applied and verified per proposal, the commits on your branch,
which of your own task lines you checked, anything unverified or stopped
on, and what the next batch should work.
