# Assertion: A milestone slug cannot be born too long to name its conductor

- **Repo:** agentplot/flywheel
- **Item:** #44
- **Raised by:** `bin/flywheel reconcile`, failing to start
  `intent-machinery-self-description` and surfacing herdr's raw error;
  triaged into this intent by dispatch.

## The claim

Conductor agent names are `intent-<slug>` and `bolt-<slug>`, and herdr
refuses an agent name longer than 32 characters. When this is built the
constraint is enforced at both ends.

At the tool end, `bin/flywheel` refuses to start a wanted conductor
whose derived agent name exceeds herdr's limit, and its refusal names
the fix — the milestone slug to rename and the length it must reach —
rather than passing herdr's error through. The check runs before the
start attempt, so nothing is half-created.

At the practice end, the length rule lands where milestones are born:
`skills/_reference/tracker.md` and dispatch's routing practice state
that an intent slug is at most 25 characters and a bolt slug at most 27
— the two budgets that leave `intent-` and `bolt-` inside 32 — and say
that the rule exists because the slug becomes the conductor's agent
name.

## Why

The failure is this intent's own: the milestone was first born as
`machinery-self-description`, whose conductor name is 33 characters, and
the fleet could not start it. Nothing between the milestone's creation
and the start attempt could have caught it, because the two ends never
mentioned each other. The item body carries the raw error.

## Boundaries

herdr's 32-character limit is not in question and is not being raised —
this is the flywheel side living inside it. Renaming milestones that
already exist is not covered here; this intent's own milestone was
already shortened to `machinery-self-desc` by hand, and any other
over-long slug is a tracker edit, not a code change. The confusing
argument shape `flywheel-batch` accepts is a separate defect, #40.
