---
name: handoff
description: Plan a bolt for a flywheel handoff-type design session — draft the bolt plan from the settled assertions on the standard template, run one plannotator round with the operator, then move custody to construction. Use whenever a design session's work order names the handoff type.
---

# Flywheel handoff — bolt planning

You are a design session charged with the **handoff type**. Your item
names a set of settled assertions — open items on `intent/<slug>` with
no open blockers — and your job is to plan their construction and move
custody. The unit's move to Ready charged you; the plan itself
still gets the operator's eyes, in one plannotator round, before
anything moves.

## Where handoff items come from

The conductor births one at the queue whenever settled assertions are
**unbolted** — still on the intent's milestone, because bolting IS the
milestone move to `bolt/<slug>`. Assertions settle in waves, so
handoffs recur: each wave gets its own item, and an intent that settles
in three waves hands off in three, either as later batches on a live
bolt or as the next bolt. Nothing waits for the whole intent to close.

## The plan, on the standard template

Copy `plan-template.md` (beside this skill) into your session directory
as `bolt-plan.md` and fill it from the assertion records themselves —
never re-derived from memory. One section per bolt — a handoff cuts
more than one when assertions land in unrelated repos or warrant
different bolt types. Each section carries: the bolt (`bolt/<slug>`,
new milestone or a live bolt joined), the **bolt type** — `bolt-quick`,
`bolt-default`, `bolt-adversarial`, the `bolt-*` schema member the
change will bind, which is what sets the review steps the bolt's loop
schedules —
the **landing mode** (merge to main, or a pull request), the
**owner** read from the items' assignee, the repos,
the assertions by item number and record path, the sequencing to wire,
and any ADR the bolt owes — as its own born-ready item on the bolt, never
as a direct edit. Nothing edits without an item, ADRs included.

## The plannotator round

`plannotator annotate bolt-plan.md` — one blocking round. Fold what
comes back by rewriting the plan to its new current state, and proceed
on approval. The operator approved the unit to charge you; this
round approves the plan.

## The custody move

Execute each approved section on the tracker (invocations in the
plugin's `skills/_reference/herdr.md`): ensure the milestone, move each
assertion item onto it (`gh issue edit <n> --milestone "bolt/<slug>"`),
relabel them `state:ready`, wire the sequencing, and comment the plan
on the unit. If the bolt conductor is running, prompt it; if
not, report that — the fleet layer starts `bolt-<slug>`, and it
scaffolds its change from the milestone and your plan.

## The receipt is custody, not completion

Custody has transferred when the items sit on the bolt's milestone;
say so in a comment on the unit. It does not say the work is
done: an assertion records its landing ref only when evidence lands on
main — and the assertion items stay sub-issues of the unit
across the move, so its checklist keeps tracking the batch to landing.
Anything held back goes in your report with the reason, never quietly
dropped.

## On the tracker

The object-graph rules — one milestone per issue, one batch per item
ever, which batches parent what, who moves which state — are the shared
copy at `skills/_reference/tracker.md`, which also walks this flow
issue by issue as the literal forgot-password graph. Read it before
your first tracker write; when a situation is not covered there or by
your work order, queue a question — never invent tracker structure.

## What you report

The plan as approved and executed — bolts, types, owners, item
numbers moved — and anything held back.
