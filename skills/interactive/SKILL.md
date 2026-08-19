---
name: interactive
description: Build the lavish page a flywheel interactive-design session works — one artifact carrying every decision the batch aims to close, with options, trade-offs, and deep links, opened for the operator with `npx -y lavish-axi`. Use whenever a design session's work order names the interactive design type, or a batch needs an option comparison, a report with controls, or diagrams the operator works rather than reads.
---

# Flywheel interactive — the page the operator works

You are a design session charged with the **interactive design type**,
running under `flywheel-interactive-session`. Your batch closes
decisions by building one page the operator works, rather than drafts
they read. The presentation coaching — show the thing, not a
description of it — is in `flywheel:inception`.

## Batch decisions into one artifact

Present **every** decision the batch aims to close in one page —
options, trade-offs, and deep links to the chapters and map nodes each
decision turns on (`system-context-map.html#map=target&sel=<node-id>`).
One page per batch, not one per decision: annotations close decisions
faster when the trade-offs sit beside each other.

Each decision on the page states the decision and its consequences —
the consequences are what you queue as items once the annotations come
back. The page is a real committed file in your
`sessions/<date>-<slug>/` directory, and it stays there.

## Opening it

```bash
npx -y lavish-axi sessions/<date>-<slug>/<name>.html
```

`lavish-axi` **missing from `PATH` is the normal, healthy state** — the
`npx -y` fetch is the install story, and only an opaque `npx` failure
(a restricted sandbox, CI) falls back to an installed copy per the
`lavish` skill. Feedback comes back through `npx -y lavish-axi poll`,
to you and nowhere else.

The steering source for this type is the user-level `lavish` skill
(`~/.claude/skills/lavish/SKILL.md`). If that skill is absent, report
the shortfall and stop — do not half-build the page or substitute a
document; re-charging the batch is the operator's call.

## Close with a round-close plan

A batch with a next round to propose ends with a round-close plan — the
protocol is the shared copy at `skills/_reference/round-close.md`: the
`close/` files, its own lavish page, the exclusive routing, the apply
order, the failure discipline. The close plan is a separate artifact
from the batch's decision page — one carries the decisions, the other
routes their consequences. Nothing reaches GitHub before the operator
approves, and a session with nothing to propose settles as today.

## On the tracker

The object-graph rules are the shared copy at
`skills/_reference/tracker.md`; the invocations are in `herdr.md`
beside it. Your contract:

- **You receive**: item numbers of the coupled decisions the page carries, `type:interactive`, flipped `state:in-progress` by the intent loop.
- **You leave**: one comment per item — what the operator chose, with a pointer to the page in your session directory. The loop closes items on your evidence. The operator's word is the completion signal, and it is one label: told in the pane that an item is done, move that item to `stage:done` — the one call `flywheel-stage <n> --org <org> --repo <tracker> --stage stage:done`, which sweeps whatever stage the item carried, since an item carries exactly one `stage:*` — and settle. The loop reads the label and does the rest.
- New work the round surfaces is a queued item on the milestone.

## What you report

Which decisions the operator's annotations closed, proposed items for
what they opened, and what the next batch should work.
