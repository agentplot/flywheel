# The tracker graph — objects, invariants, worked examples

The one shared copy, at the flywheel plugin's
`skills/_reference/tracker.md`; every skill that touches the tracker
points here rather than restating the rules. `herdr.md` beside this
file holds the invocations; this file holds what the objects must look
like. **When a situation is not covered here or by your work order,
queue a question — never invent tracker structure.**

## The objects

- **item** — one unit of work, as an issue: imperative title · 1–3
  sentences of body plus a pointer to the record it serves · milestone
  from birth · `type:*` and exactly one `state:*` · assignee = whose
  word settles it · native blocked-by dependencies · comments as its
  narrative.
- **epic** — one release batch: a parent issue, label `epic`, the
  batch as sub-issues, sitting on the org Project at Status
  **Backlog** (proposed) or **Ready** (approved).
- **milestone** — the change-sized container, exactly two forms:
  `intent/<slug>` and `bolt/<slug>`. A due date puts it on the
  roadmap.
- **the board** — the org Project: Status lanes, Team = host, roadmap
  fields. A view, never a second store. **Whatever carries the
  approval sits on the board**: epics (at Backlog, flipped to Ready by
  the operator), and a quick bolt's lone born-ready item (at Ready
  from birth, via `flywheel-board`).

## The invariants

1. **An issue holds exactly one milestone**, and the milestone answers
   "which change owns this work now." Moving an assertion item from
   `intent/<slug>` to `bolt/<slug>` IS the release to construction —
   no other act bolts it, and the milestone field is the test for
   whether it happened.
2. **An item joins exactly one epic, ever** (GitHub enforces this —
   attaching a parented sub-issue is a 422). Which epic:
   design-work items — questions, prototypes, writebacks, handoff
   items — join a design epic on their intent; an assertion item joins
   only the handoff epic that releases it; work queued fresh on a live
   bolt joins a bolt-side epic. Sub-issue links are independent of
   milestones and survive the custody move.
3. **Epics group by thread, not by type** — a prototype, the questions
   it answers, and the writeback of its findings are one approval. The
   conductor partitions an epic's sub-issues into typed sessions at
   work time: type is the hard boundary, relatedness decides within a
   type, prototypes ride alone.
4. **`type:*` is the session type that works the item.** A question
   borrows the type of the session that will answer it. The exception
   is `type:assertion` — the released claim itself: its construction
   stages (spec, review verdict, build, merge SHA) are comments on the
   one item, never items of their own. Only discoveries become new
   items.
5. **The state ladder is `queued → ready → in-progress → closed:*`**,
   and each move has an owner: anyone queues; only the operator's word
   makes ready — the epic flip to Ready on the board for a batch, or
   born-ready at triage when the work IS the operator's word; the
   conductor flips `in-progress` as a session starts; whoever holds
   the evidence closes, always with one `closed:*` reason.
6. **The handoff birth condition is computable.** An assertion is
   settled and unbolted when its item is open on `intent/<slug>`, has
   no parent epic, and has no open blockers. Whenever such assertions
   exist at the queue, the conductor births one `type:handoff` item
   naming exactly that set, or extends the open unstarted one.
7. **Blocked on the operator's word**: comment the one-line question
   on the item, add `needs-operator`, keep working what it does not
   gate. Whoever applies the answer removes the label.
8. Sub-issues and dependency relations take the **database id**, not
   the issue number — invocations and gotchas in `herdr.md`.

## The literal graph — one assertion, birth to landing

An intent `auth-hardening` needs a forgot-password flow; one question
gates it:

    #101  Decide the reset-token delivery channel      type:research · queued
    #102  The auth page offers a forgot-password flow  type:assertion · queued
          body → assertions/forgot-password.md · blocked-by #101
    #103  [epic] Settle password-reset design          sub-issues: #101

The design epic batches the *deciding*; the assertion joins no design
epic. #101 closes → #102 is settled and unbolted (invariant 6) → the
conductor births the handoff item and its epic:

    #104  Plan the bolt for the forgot-password assertion  type:handoff · queued
    #105  [epic] Handoff: forgot-password to construction  sub-issues: #104, #102

The operator moves #105 to Ready — the checklist they flip is the list
of assertions being released. The handoff session works #104: drafts
`bolt-plan.md` on the standard template, runs one plannotator round,
then makes the custody move:

    #102  milestone intent/auth-hardening → bolt/forgot-password · state:ready

The fleet layer starts `bolt-forgot-password`; construction accrues on
#102 as comments; it closes `closed:done` with the landing SHA. #105's
checklist keeps tracking it across the move (invariant 2), and
`intent/auth-hardening` is free to close when design and writebacks
are done.

## The quick bolt — and the no-spec path

The operator, at triage: "rename the gateway's env var everywhere."
Small, fully defined, no intent behind it. Dispatch creates:

    milestone bolt/rename-gateway-env
    #40  Rename GATEWAY_URL to GATEWAY_BASE_URL across the built repos
         type:assertion · state:ready — born ready on the operator's word
         on the board at Status Ready — the lone item carries the approval

There is no assertion record file — with no intent, the item body IS
the claim. The reconciler sees a `bolt/*` milestone with a ready item
and no conductor, starts `bolt-rename-gateway-env`, and the conductor
scaffolds the change binding the member the work warrants
(`bolt-quick` here — no review step).

**`bolt-no-spec` is deliberately not a schema: plan mode replaces the
spec step.** For work too small to warrant a spec-driven change in the
built repo, the conductor's work order says so, and the build session
opens in plan mode: its plan — checked against the item's claim — is
the spec surrogate, approved by the conductor before any edit. The
choice is per batch, made by the conductor; everything else is
unchanged: the item's comments carry the stages, the merge gate runs
unweakened, the landing SHA closes the item `closed:done`.
