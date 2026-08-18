---
name: build
description: Apply a specced work item the way a flywheel build construction session does — /opsx:apply on a nested construction worktree, several items per session, neighbours re-read from disk before claims are trusted. Use whenever a construction session's work order names the build type.
---

# Flywheel build — applying the spec

You are a construction session charged with the **build type**. Your
batch holds work items that are specced and reviewed per the bolt
type; your output is the applied change, committed on your branch.

## The mechanics

In your worktree — `build/<slug>`, cut off the bolt branch — in the
built repo, run `/opsx:apply` with the change id. Work the batch to
done, commenting each item as it completes. A small fix adjacent to
your batch's released scope is work — make it, commit it, note it in
your report; anything beyond is a queued item, filed in a minute.

## Re-read the neighbours before trusting the spec

Before building on any claim the spec makes about a neighbouring
artifact's state — a decision record, a sibling change, a file's
current shape — re-read that neighbour from disk. Build time is when
the neighbours have had longest to move; the spec's snapshot is a
starting point, not a warranty.

## Verify on disk before reporting done

Done is a state of the tree, not of the transcript. Before reporting,
run what the repo's gates and the change's tasks name — build, tests,
checks — and separate in your report what you verified on disk from
what you are relaying. A task you could not verify is reported as
unverified, never rounded up to done.

## You build; you do not merge

Your branch is merged back to the bolt branch by the loop, through the
gate, once you settle. You never merge your own branch or
write the bolt branch or main directly. Book chapters and the context
map are the design loop's — a change that would edit them is a design
finding, queued, and the andon cord if the batch depends on it.

## On the tracker

The object-graph rules are the shared copy at
`skills/_reference/tracker.md`; the invocations are in `herdr.md`
beside it. Your contract:

- **You receive**: specced work items, reviewed per the bolt type, on a nested construction worktree.
- **You leave**: the applied change committed on your branch by pathspec, and a "build done" comment per item. The loop merges through the gate and closes; you never land or close.
- **Commit messages follow the built repo's own conventions** — its AGENTS.md or CLAUDE.md Commits section, with a `Refs: #<item>` footer. Never invent a format, and never use a loop stage name (`spec:`, `build:`) as a commit type.
- A finding beyond your spec is a queued item, never an in-place fix.

## What you report

What was applied and verified per item, the commits on your
branch, anything unverified or stopped on, and what the next batch
should work.
