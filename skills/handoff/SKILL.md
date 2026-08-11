---
name: handoff
description: Work the transfer a flywheel handoff-type design session runs — compose the release request from the released assertion records, deliver it to the bolt conductor, and bring back the receipt. Use whenever a design session's work order names the handoff type.
---

# Flywheel handoff — the transfer to construction

You are a design session charged with the **handoff type**. The operator
has released a handoff epic; your batch turns that release into a bolt's
work: compose the release request, deliver it, bring back the receipt.

## What the release request carries

One request per released epic, composed from the released assertion
records themselves — never re-derived from memory:

- the assertions being released, by change-relative path, with their
  item numbers;
- the built repos they land in;
- the bolt member the work warrants (`bolt-default`, `bolt-quick`,
  `bolt-deep`), because the member picked at creation IS the review
  depth;
- the bolt's owner — the developer whose word settles its decisions,
  read from the released items' assignee;
- any architecture decision record the batch names: repo, decision to
  record, sources. The bolt conductor writes it directly.

## How it travels

To the bolt conductor by herdr prompt when it runs, as a comment on
the released epic when it does not — the invocations are in the
plugin's `skills/_reference/herdr.md`. If no bolt conductor exists yet,
report that: the fleet layer starts it, and it scaffolds its change on
first start.

## The receipt is custody, not completion

The receipt says the released items now sit in the bolt's milestone —
custody has transferred, and you comment it on the epic. It does not say
the work is done: an assertion records its landing ref only when
evidence lands on main. Anything the bolt declined or deferred goes back
in your report as an open item, never quietly dropped.

## What you report

The request as sent, the receipt as received, and anything declined or
deferred.
