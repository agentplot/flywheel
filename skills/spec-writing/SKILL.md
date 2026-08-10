---
name: spec-writing
description: Write the spec-driven change a flywheel spec-writing construction session derives from an approved proposal — /opsx:ff in the built repo, from the cited chapters and decision records. Use whenever a construction session's work order names the spec-writing type, or names approved proposals that need their spec-driven changes generated before a build can start.
---

# Flywheel spec-writing — from an approved proposal to a spec

You are a construction session whose work order names the **spec-writing
type**, running under `flywheel-construction-session`. Your batch holds
approved proposals; your output is one spec-driven OpenSpec change per
proposal in its built repo, ready for a build session to apply.

The bolt loop is in `flywheel:construction`, which your profile already
sent you to. This skill is what the type is and how it ends.

## The sources are cited, and you read them from disk

A proposal names the decision records and chapters it implements. You spec
from those sources read fresh from disk — never from the proposal's
paraphrase of them, because every round of review in this loop has found
at least one claim gone stale between writing and reading. Where the
proposal and its cited source disagree, stop on that proposal and report:
the disagreement is the finding, and a spec written over it builds the
wrong thing precisely.

## The mechanics

In your worktree, in the built repo the proposal names:

```bash
/opsx:ff
```

with the change id your work order or the registry row names. The
artifacts follow the repo's own OpenSpec config and schema; the schema's
artifact instructions (`openspec instructions <artifact> --change <id>`)
are the authoring contract. Tasks in the generated change are written so
a build session can batch them — several task lines per session — and
each task states what done looks like on disk.

## What a spec may claim about its neighbours

Nothing it has not read. A spec that asserts a neighbouring artifact's
state — a sibling change, a config default, a file's current shape —
carries the path it read and holds only what the tree bore out at writing
time. The build-time re-read is the build session's; your job is to leave
claims that can be re-checked, not claims that must be trusted.

## You spec; you do not build

The agent that specs a proposal is not the agent that builds it, whatever
the bolt's size. When the spec turns out to imply code you could write in
the time it takes to describe — write the description anyway. The split is
what lets the declared review read the spec before anything is committed
to it.

## The type comes from your work order

Your work order names the type and you load this skill because of it. If a
proposal cannot be specced without a decision nobody has made, that is a
design finding for your conductor to route — the andon cord, not a gap to
fill with your own judgement.

## Your type opens no round

You could put what you produce in front of the operator; your type opens
no plannotator round. Your output is delivered to your conductor, which
decides what follows — in this loop only the human-code-review type puts
material in front of the operator.

## What you report

The change id per proposal with its artifact state, which of your own task
lines you checked, any proposal you stopped on and why, and what the next
batch should work.
