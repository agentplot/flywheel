---
name: handoff
description: Plan a bolt for a flywheel handoff-type design session — draft the bolt plan from the settled assertions on the standard template, run one plannotator round with the operator, then move custody to construction. Use whenever a design session's work order names the handoff type.
---

# Flywheel handoff — bolt planning

You are a design session charged with the **handoff type**. Your item
names a set of settled assertions — open items on `intent/<slug>` with
no open blockers — and your job is to plan their construction and move
custody. The handoff epic's move to Ready charged you; the plan itself
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
different depths. Each section carries: the bolt (`bolt/<slug>`, new
milestone or a live bolt joined), the **member** — `bolt-default`,
`bolt-quick`, `bolt-deep`, because the member picked at creation IS the
review depth — the **owner** read from the items' assignee, the repos,
the assertions by item number and record path, the sequencing to wire,
and any ADR the bolt conductor should write directly.

## The plannotator round

`plannotator annotate bolt-plan.md` — one blocking round. Fold what
comes back by rewriting the plan to its new current state, and proceed
on approval. The operator approved the handoff epic to charge you; this
round approves the plan.

## The custody move

Execute each approved section on the tracker (invocations in the
plugin's `skills/_reference/herdr.md`): ensure the milestone, move each
assertion item onto it (`gh issue edit <n> --milestone "bolt/<slug>"`),
relabel them `state:ready`, wire the sequencing, and comment the plan
on the handoff epic. If the bolt conductor is running, prompt it; if
not, report that — the fleet layer starts `bolt-<slug>`, and it
scaffolds its change from the milestone and your plan.

## The receipt is custody, not completion

Custody has transferred when the items sit on the bolt's milestone;
say so in a comment on the handoff epic. It does not say the work is
done: an assertion records its landing ref only when evidence lands on
main — and the assertion items stay sub-issues of the handoff epic
across the move, so its checklist keeps tracking the batch to landing.
Anything held back goes in your report with the reason, never quietly
dropped.

## The literal graph — one assertion, birth to landing

An intent `auth-hardening` needs a forgot-password flow; one question
gates it:

    #101  Decide the reset-token delivery channel     type:research · queued
    #102  The auth page offers a forgot-password flow  type:assertion · queued
          body → assertions/forgot-password.md · blocked-by #101
    #103  [epic] Settle password-reset design          sub-issues: #101

The design epic batches the *deciding*; the assertion joins no design
epic. #101 closes → #102 is settled and unbolted → the conductor
births the handoff item and the handoff epic:

    #104  Plan the bolt for the forgot-password assertion  type:handoff · queued
    #105  [epic] Handoff: forgot-password to construction  sub-issues: #104, #102

The operator moves #105 to Ready. The handoff session works #104:
drafts `bolt-plan.md` (one section: `bolt/forgot-password`,
member bolt-quick, owner from #102's assignee), runs the plannotator
round, then moves custody:

    #102  milestone intent/auth-hardening → bolt/forgot-password · state:ready

The fleet layer starts `bolt-forgot-password`; construction accrues on
#102 as comments; it closes `closed:done` with the landing SHA, #105's
checklist completes, and the intent milestone is free to close when
design and writebacks are done.

## What you report

The plan as approved and executed — bolts, members, owners, item
numbers moved — and anything held back.
