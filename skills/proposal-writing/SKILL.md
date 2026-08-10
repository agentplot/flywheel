---
name: proposal-writing
description: Draft the proposals a flywheel proposal-writing construction session mines from released assertions — one buildable claim per proposal, citing the decisions it implements, docked into the bolt's registry by the conductor. Use whenever a construction session's work order names the proposal-writing type, or names a batch of released assertions that need mining into buildable units.
---

# Flywheel proposal-writing — mining assertions into buildable units

You are a construction session whose work order names the
**proposal-writing type**, running under `flywheel-construction-session`.
Your batch holds released assertions; your output is proposal drafts — one
buildable claim each — for your conductor to dock into the registry.

The bolt loop is in `flywheel:construction`, which your profile already
sent you to. This skill is what the type is and how it ends.

## One assertion may mine into several proposals

The unit is buildability, not the assertion. A proposal is one thing a
build session can take to done: one repo, one coherent change, one
statement of what done looks like. When an assertion needs three of those,
draft three proposals and say which assertion each serves — the assertion
stays open until all of them land.

## A proposal cites, it does not re-open

Every proposal cites the decision records it implements, by
change-relative path, and derives its content from them. A decision that
looks wrong is a design finding routed to your conductor — never a thing
you fix by drafting around it. The spec agents that follow you will turn
your proposal into a spec-driven change; what you owe them is a claim
precise enough to spec without guessing.

## What each draft carries

- the claim — what becomes true in the repo, stated so its absence is
  checkable;
- the repo it lands in, and the decisions it cites;
- the review the row should declare (`agent` or `human`), with one line of
  why that depth;
- what done looks like — the observable state, not the steps;
- what it waits on, when it waits on anything.

## Where the drafts land

In your worktree, as files your work order names — the conductor docks
them into the registry and owns every status thereafter. You never write
`bolt.md` or the registry yourself, and you never assign a status: a
proposal has no status until the conductor gives it one.

## The type comes from your work order

Your work order names the type and you load this skill because of it. If
mid-batch an assertion turns out unmineable — too vague to state a
checkable claim, or contradicted by a sibling — stop on that assertion and
report it; drafting a vague proposal moves the vagueness downstream to a
spec agent with less context than you have now.

## Your type opens no round

You could put what you produce in front of the operator; your type opens
no plannotator round. Your output is delivered to your conductor, which
decides what follows — in this loop only the human-code-review type puts
material in front of the operator.

## What you report

The drafts and the assertion each serves, which of your own task lines you
checked, any assertion you could not mine and why, and what the next batch
should work.
