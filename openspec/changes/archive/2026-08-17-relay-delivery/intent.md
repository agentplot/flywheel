# Intent: relay-delivery

## Destination

An escalation raised by an inner-loop actor reaches the operator, or the
fleet says out loud that it did not. Delivery is a fact the loop records
when it happens, not a state inferred from the presence of a
`needs-operator` label and a comment — so the two outcomes that look
identical today, *relayed to a channel the operator reads* and *relayed
into a channel that rejected the message*, are told apart by anyone
reading the tracker or `flywheel status`.

Because delivery is recorded, the fleet's reconcile pass asks dispatch to
relay an item exactly when a relay is owed. An item whose escalation has
already been delivered produces no further nudge; an item whose relay
failed is the one the loop retries, and it retries visibly.

The unreachable channel is the loop's own failure, reported like one. An
operator who is genuinely absent — the case the bridge exists for — is
never the mechanism by which the loop discovers that its bridge is down.

**Books.** This repo carries no `books/` tree, so this intent cites no
chapters. Its prose destinations are `skills/inception/SKILL.md` (the
paragraph beginning "Dispatch is also the inner loop's bridge to a
possibly-absent operator"), `skills/_reference/herdr.md` (the
`needs-operator` block under "The tracker"), and the reconcile and
status prose in `bin/flywheel`.

## Map

This repo carries no `context-map/` tree, so this intent moves no map
nodes. If a context map is established for the flywheel machinery while
this intent is open, the nodes covering the dispatch bridge and the
fleet's reconcile pass are the ones it moves, and this section is
rewritten to name them.

## Scope

**In scope.**

- Where undeliverability becomes visible when a relay's channel rejects
  the message — a comment on the item, a `flywheel status` line, a fleet
  precondition that refuses to run dispatch without a reachable channel,
  or some combination (item #43).
- What counts as "already relayed", and how the reconcile pass in
  `bin/flywheel` selects the items it nudges dispatch about, so a
  delivered relay stops producing turns that write nothing (item #45).
- Whether a relay that sat undelivered is retried, and on what terms —
  the one place the two questions above meet.
- Correcting the loop's own prose where it describes the bridge as
  though delivery were assured.

**Out of scope.**

- The operator's own `/discord:access` pairing. That fixes today's
  instance; this intent is about the instance recurring unnoticed.
- Which chat platform carries a DM, and the wording of an escalation.
  Both are settled; this intent asks only whether the message arrived.
- The `needs-operator` label's own lifecycle — who sets it, who removes
  it — which is unchanged.
- Every other queue the reconcile pass owns, except where a remedy here
  changes how it selects.
- Building the remedy. Construction of whatever this intent settles is
  bolt work.
