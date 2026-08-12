# Question: what counts as "already relayed", and what does the fleet do about one that was not?

- **Item:** #45
- **Raised by:** dispatch, nudged a second time for #33 on 2026-08-12
  having relayed it on the first pass

## The question

The fleet's reconcile pass asks dispatch to relay every open item
carrying `needs-operator`, and the label correctly stays set until the
operator's word is applied — which may be hours or days. So the pass
re-asks for the same item on every run, and dispatch's only correct
answer after the first pass is silence, because an escalation is never
re-asked. The question is what predicate the pass selects on instead:
the newest comment on the item being the app's rather than a human's; a
`relayed` label dispatch adds and whoever applies the answer removes;
or a deliberate but rate-limited re-nudge, on the theory that a relay
sitting unanswered for a day deserves a second attempt down a different
channel.

## What turns on it

Every reconcile pass over a waiting escalation currently burns a
dispatch turn to produce no tracker write, so the loop's cost of an
absent operator grows with the length of their absence. The answer also
fixes where the fact of a relay lives — inferred from comment authorship
(no new state, but a guess), or written down as a label (explicit, and
one more thing that can be left stale) — and whether the loop retries at
all.

The third option is where this meets #43: a relay that *failed* to
deliver is exactly the one that should be retried, which argues for
delivery being a recorded fact rather than something inferred. Both
questions therefore want answering together; either one answered alone
constrains the other's remaining room.

## What is already known

Read on this tree on 2026-08-12; re-check against the tree you read this
on.

- **The selection is purely the label.** `bin/flywheel`'s tracker read
  collects every open issue whose labels contain `needs-operator` into
  `needs_operator`, and step 5 prompts dispatch with that list whenever
  it is non-empty and dispatch is settled. There is no test for whether
  a relay was already sent.
- **The nudge is one prompt for two queues** — waiting relays and
  unmilestoned items awaiting triage — so a change to the relay
  predicate touches a prompt dispatch also reads for triage work.
- **A relay leaves its evidence as a comment.** That is what makes the
  comment-authorship predicate available at all, and it is the same
  evidence #43 may make carry a delivery outcome.
- **`skills/inception/SKILL.md` states the invariant the predicate must
  preserve**: an escalation is one line of question with its evidence
  pointer, relayed once; whoever applies the operator's word removes the
  label.
