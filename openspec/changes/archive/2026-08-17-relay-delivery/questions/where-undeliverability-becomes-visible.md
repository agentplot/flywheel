# Question: where does a relay the channel refused become visible?

- **Item:** #43
- **Raised by:** dispatch, relaying #33 on 2026-08-12

## The question

When dispatch DMs an escalation and the channel rejects the message, the
loop currently records nothing outside that one transcript: the item
carries `needs-operator` and a comment either way, so a delivered relay
and a refused one are indistinguishable to every later reader. The
question is which artifact is made to carry the failure — a comment on
the item stating the channel refused, a `flywheel status` line reporting
the relay channel unreachable, a fleet precondition that refuses to
start dispatch into an org whose channel is not reachable, or some
combination — and, whichever is chosen, what an actor does next when it
holds an escalation it cannot deliver.

## What turns on it

Whether an absent operator is a case the bridge handles or the case that
breaks it silently. The bridge exists precisely for the operator who is
not watching the terminal; if the only witness to a failed DM is a
transcript nobody reads, then the one condition the mechanism was built
for is the condition under which it fails without saying so. It also
decides where the check lives — inside dispatch's own relay step, in the
fleet layer's periodic read, or as a precondition at `flywheel up` — and
therefore who is responsible for noticing.

The answer is coupled to #45: a relay whose failure is a recorded fact
is also the relay a retry can select, so making delivery recordable is
the shared half of both questions.

## What is already known

Measured on this machine on 2026-08-12; re-check against the tree and
machine you read this on.

- **The observed failure** is `reply failed: Unknown Channel`. The
  Discord access config allows the operator's user id for DMs under
  `dmPolicy: pairing`, but nothing is paired, so there is no `chat_id`
  to send to. Dispatch fell back to a GitHub `@mention` comment, which
  `skills/inception/SKILL.md` names as the sanctioned fallback — so the
  fallback fired correctly and still left no durable trace of *why*.
- **`flywheel status` reports nothing about the relay channel.** Its
  read (`bin/flywheel`, `status`) covers actors against the manifest
  roster; the channel is not part of what it knows.
- **The reconcile pass neither knows nor asks.** `bin/flywheel` step 5
  builds its dispatch nudge from tracker labels alone and prompts
  dispatch to "DM each item's assignee"; nothing in that path reads or
  reports a delivery outcome.
- **The defect shape is the one `intent/gated-merge-guarantee` names**:
  a green-looking result that silently did not do the thing. That
  intent's remedy was to make the check fail closed
  (`../../gated-merge-guarantee/decisions/gate-runs-under-pre-merge.md`),
  and whether the same posture is right here is part of this question.
- The operator's own `/discord:access` pairing repairs today's instance
  and is deliberately not this question, per this intent's scope.
