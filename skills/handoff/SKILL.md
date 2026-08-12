---
name: handoff
description: Plan a bolt for a flywheel handoff-type design session — read the settled assertions the work order names, compose the bolt milestone and its release, pick the member that sets review depth, and move custody to construction. Use whenever a design session's work order names the handoff type.
---

# Flywheel handoff — bolt planning

You are a design session charged with the **handoff type**. Your item
names a set of settled assertions — open items on `intent/<slug>` with
no open blockers — and your job is to turn them into a bolt's plan.
The epic that released your item covers everything you do here; no
further approval is needed.

## Where handoff items come from

The conductor births one at the queue whenever settled assertions are
**unbolted** — still on the intent's milestone, because bolting IS the
milestone move to `bolt/<slug>`. Assertions settle in waves, so
handoffs recur: each wave gets its own item, and an intent that settles
in three waves hands off in three, either as later batches on a live
bolt or as the next bolt. Nothing waits for the whole intent to close.

## The plan, composed from the records

Read the assertion records themselves — never re-derive from memory.
The plan is:

- **The bolt**: `bolt/<slug>` — a new milestone, or the live bolt these
  assertions join.
- **The member** — `bolt-default`, `bolt-quick`, `bolt-deep` — because
  the member picked at creation IS the review depth. Recommend from
  what the assertions touch, not from their count.
- **The owner** — the developer whose word settles the bolt's
  decisions, read from the items' assignee.
- **Sequencing** — blocked-by relations between the assertion items
  where build order matters, wired now while you hold the context.
- Any architecture decision record the batch warrants: repo, decision,
  sources. The bolt conductor writes it directly.

## The custody move

Execute the plan on the tracker (invocations in the plugin's
`skills/_reference/herdr.md`): ensure the milestone, move each
assertion item onto it (`gh issue edit <n> --milestone "bolt/<slug>"`),
relabel them `state:ready` — the release that covers you covers them —
and comment the plan (member, owner, sequencing) on the milestone's
first item and on the epic that released you. If the bolt conductor is
running, prompt it; if not, report that — the fleet layer starts
`bolt-<slug>`, and it scaffolds its change from the milestone and your
plan.

## The receipt is custody, not completion

Custody has transferred when the items sit on the bolt's milestone;
say so in a comment on the releasing epic. It does not say the work is
done: an assertion records its landing ref only when evidence lands on
main. Anything you judged not ready to hand off goes back in your
report with the reason, never quietly dropped.

## What you report

The plan as executed — milestone, member, owner, item numbers moved —
and anything held back.
