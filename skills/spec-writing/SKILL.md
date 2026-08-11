---
name: spec-writing
description: Write the spec-driven change a flywheel spec-writing construction session derives from a released assertion — /opsx:ff in the built repo, from the assertion and its cited chapters and decision records. Use whenever a construction session's work order names the spec-writing type.
---

# Flywheel spec-writing — from the assertion to a spec

You are a construction session charged with the **spec-writing type**.
Your batch holds released assertions — the assertion is the proposal —
and your output is one spec-driven OpenSpec change per assertion in its
built repo, ready for a build session to apply.

## The sources are cited, and you read them from disk

An assertion names the decision records its claim derives from. You spec
from the assertion and those sources read fresh from disk — never from a
paraphrase. Where the assertion and its cited source disagree, stop on
that assertion and report: the disagreement is the finding, and a spec
written over it builds the wrong thing precisely.

## The mechanics

In your worktree, in the built repo the assertion names, run `/opsx:ff`
with the change id your work order names. The artifacts follow the
repo's own OpenSpec config; the schema's artifact instructions
(`openspec instructions <artifact> --change <id>`) are the authoring
contract. Write tasks so a build session can batch them, each stating
what done looks like on disk.

## What a spec may claim about its neighbours

Nothing it has not read. A spec that asserts a neighbouring artifact's
state carries the path it read and holds only what the tree bore out at
writing time — cite by anchor or quoted phrase, never line number. The
build-time re-read is the build session's; your job is to leave claims
that can be re-checked, not claims that must be trusted.

## You spec; you do not build

The agent that specs an assertion is not the agent that builds it. When
the spec implies code you could write in the time it takes to describe,
write the description anyway — the split is what lets the review read
the spec before anything is committed to it. An assertion that cannot be
specced without a decision nobody has made is a design finding to queue,
not a gap to fill with your own judgment.

## What you report

The change id per assertion with its artifact state
(`openspec validate` green before it counts), anything you stopped on
and why, and what the next batch should work.
