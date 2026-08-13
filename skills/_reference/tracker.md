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
- **batch** — a parent issue whose sub-issues are the batch, sitting
  on the org Project at Status **Backlog** (proposed) or **Ready**
  (approved). Its kind is what approving it authorizes: a **unit**
  (label `unit`) releases construction work — AI-DLC's unit of work;
  an **elaboration** (label `elaboration`) authorizes design sessions
  on an intent.
- **milestone** — the change-sized container, exactly two forms:
  `intent/<slug>` and `bolt/<slug>`. A due date puts it on the
  roadmap.
- **the board** — the org Project: Status lanes, Team = host, roadmap
  fields. A view, never a second store. **Whatever carries the
  approval sits on the board**: units and elaborations — at Backlog,
  flipped to Ready by the operator, except a born-ready release's unit
  parent, which is at Ready from birth (via `flywheel-board`) because
  the operator's word at triage is itself the approval. Sub-issues do
  not appear beside their parent: one row per bolt is what the parent
  buys, and the progress on that row is GitHub's own sub-issue "n of
  m", never a figure the flywheel computes or stores.
  Status is the batch-approval surface and holds no other state — the
  per-item state of a running session lives in `stage:*` labels, with
  every other signal the loops read.

## The invariants

1. **An issue holds exactly one milestone**, and the milestone answers
   "which change owns this work now." Moving an assertion item from
   `intent/<slug>` to `bolt/<slug>` IS the release to construction —
   no other act bolts it, and the milestone field is the test for
   whether it happened. A discovery made during construction joins the
   bolt's milestone only when the bolt's merge criteria need it;
   otherwise it goes to the intent that owns its subject, or
   unmilestoned for dispatch to triage.
2. **An item joins exactly one batch, ever** (GitHub enforces this —
   attaching a parented sub-issue is a 422). Which batch:
   design-work items — questions, prototypes, writebacks, handoff
   items — join an elaboration on their intent; an assertion item
   joins only the unit that releases it; work queued fresh on a live
   bolt joins a bolt-side unit. Sub-issue links are independent of
   milestones and survive the custody move.
3. **Batches group by thread, not by type** — a prototype, the
   questions it answers, and the writeback of its findings are one
   approval. The loop partitions a batch's sub-issues into typed sessions at
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
   makes ready — the flip to Ready on the board for a batch, or
   born-ready at triage when the work IS the operator's word; the
   loop flips `in-progress` as a session starts; whoever holds
   the evidence closes, always with one `closed:*` reason.
   **`stage:*` refines `in-progress` and never replaces a `state:*`
   label.** An item being worked carries its `state:*` and exactly one
   `stage:*` naming its leading edge, and writing a stage removes the
   previous one. The bolt loop writes `stage:planned` (its spec
   validates, or its plan is approved), `stage:built` (a commit on the
   item's branch), `stage:verified` (verify clean — never on a
   `bolt-direct` item, whose type runs no verify stage) and
   `stage:merged` (on the bolt branch), and re-derives the last two
   from git every cycle so they survive a restart. The intent loop
   writes `stage:in-session` at launch and `stage:collected` once an
   item's deliverables are gathered; between them the **operator**
   writes `stage:done`, which is the one signal that loop's completion
   filter consumes. No `stage:*` write touches a `closed:*` label:
   `stage:merged` (on the bolt branch) and `closed:done` (landed on
   main) are two different facts, written at the same boundary but not
   the same act.
   **A construction assertion closes at the merge-back, with
   `closed:merged`**, because GitHub's native sub-issue bar counts
   closed sub-issues and `#98` puts the check-off at merge; the
   landing then **upgrades** that reason to `closed:done` with the
   landing SHA in its closing comment, on an item that is already
   closed. The one-reason rule above holds at every moment — never
   both, never neither — which is why the check-off is a new reason
   rather than a close with none. A `closed:merged` item is still in
   flight: its bolt has not landed, the loop's picture of its
   milestone carries it, and the server counts its milestone as a job
   until the landing.
6. **The handoff birth condition is computable.** An assertion is
   settled and unbolted when its item is open on `intent/<slug>`, has
   no parent batch, and has no open blockers. Whenever such assertions
   exist at the queue, the intent loop births one `type:handoff` item
   naming exactly that set, or extends the open unstarted one — and
   while that handoff's unit still sits at Backlog, newcomers join it:
   the item's set amended, the assertions attached as sub-issues. The
   flip seals the batch; the next settled wave births the next handoff.
7. **Blocked on the operator's word**: comment the one-line question
   on the item, add `needs-operator`, keep working what it does not
   gate. Whoever applies the answer removes the label. The label marks
   a LIVE wait, applied at the moment of blocking — never at birth: an
   operator step scheduled for later is an ordinary item until its
   moment comes, or it pollutes the operator's waiting-on-me view.
8. **Board fields default aggressively — automation first.** Whatever
   goes on the board gets Start and Target of that day, a new
   milestone is due the day it is created, Team defaults to the
   field's first option (the org's default flywheel host — Team is
   what routes a milestone's loop to a host through fleet.yaml's
   `teams:` map), and Quarter defaults to the current quarter (the
   tools do all of this). An agent that judges differently overrides
   with a stated reason; nothing ever waits for a field to be assigned.
   There is no Iteration field: the flywheel is continuous delivery,
   not sprint cadence.
9. **The lifecycle ends at the milestone, not the process.** When a
   milestone's items are all closed, its loop proposes closure and
   stops; the operator closes the milestone on GitHub — the archive
   signal — and the server's next pass runs a one-shot session to
   `openspec archive` the change. A bolt milestone is **not** finished
   while any of its items sits at `closed:merged`: those items are
   closed and still in flight, and the landing is what finishes them.
   A loop process stops whenever its
   milestone has no job, and a fresh one starts when a job appears and
   re-reads the tracker and the records; no process is ever the memory.
10. Sub-issues and dependency relations take the **database id**, not
    the issue number — invocations and gotchas in `herdr.md`.

## The inbox filters — the tracker is the only bus

No session, loop, or server ever messages another. Everything moves
through GitHub issues, and each consumer has an exact filter:

- **server** — milestones with a job: any open `intent/*` or `bolt/*`
  milestone holding an open item labelled `state:ready` or
  `state:in-progress`, or a `closed:merged` item still awaiting its
  landing, or a batch at board Status **Ready**; plus closed
  milestones whose change still sits in `openspec/changes/` (archive).
- **bolt loop for `bolt/<slug>`** — open items on that milestone
  labelled `state:ready`, plus that bolt's units at board Status Ready
  (their `state:queued` sub-issues are relabelled first).
- **intent loop for `intent/<slug>`** — the same filter on its
  milestone, plus the guard sweeps: settled unbatched assertions
  (handoff birth, invariant 6) and orphan `state:queued` items
  (compose).
- **dispatch** — open issues with no milestone (triage), and open
  issues labelled `needs-operator` (relay). The relay half has no
  milestone condition: an escalation from a running bolt has one and
  still needs relaying.

**These filters are the whole coordination model.** A discovery is an
issue; an escalation is a label; a completion is item state. Anything
not expressible in the filters is a design smell — and nothing edits
without an item either: a CLAUDE.md fix, an ADR, a machinery tweak are
GitHub issues like all work.

They are implemented once, as pure functions over a snapshot, in the
plugin's `bin/_flywheel_inbox.py`; the loops import them rather than
each re-deriving a query. Two properties hold across them and are worth
knowing when reading a loop's behaviour:

- **A server filter may over-approximate; a loop filter must be
  exact.** The server starting a loop that finds nothing costs one
  clean exit — the loop STOPs when nothing is ready and the guards
  wrote nothing — while a milestone the server never starts is work
  that never happens. So the server sweeps a little wider than the list
  above, and the loop does the exact test.
- **A filter never writes.** Flip-consume, handoff birth and compose
  are guards, and guards write; the filters name what the guard should
  write and the guard writes it. Applying a guard's plan empties it,
  which is what makes a second cycle against an unchanged tracker write
  nothing.

## The andon cord — the marker the loop reads

A **session** raises the andon: when it finds the work wrong in a way
no further round will fix — the spec contradicts the decision it cites,
the tree contradicts the claim — it writes the stop **as this marker**
in its item comment, and settles.

    <!-- flywheel:andon -->
    ANDON: <what is wrong, and why no further round fixes it — one line>
    <!-- /flywheel:andon -->

Both delimiters start their own lines, the closing one is required, and
the `ANDON:` line carries the reason. The loop recognizes it as **code,
not judgment**: prose that merely mentions the andon cord is not an
andon, and half a marker is not a stop signal. Write the marker, or the
loop will not see it — "stopping and saying so plainly" is a report,
and a report is for the operator, not for the program.

**The marker is the payload; the signal is the label and the state.** A
comment body is not expressible in any of the four filters above, so no
loop sweeps comments hunting for stops. The loop pauses the batch and
sets `needs-operator` — invariant 7 — and reads the marker on the item
it is already working to find out why. Raising the cord is therefore
both things at once: the marker in the comment, and the item left in a
state the filters can see.

## The literal graph — one assertion, birth to landing

An intent `auth-hardening` needs a forgot-password flow; one question
gates it:

    #101  Decide the reset-token delivery channel      type:research · queued
    #102  The auth page offers a forgot-password flow  type:assertion · queued
          body → assertions/forgot-password.md · blocked-by #101
    #103  [elaboration] Settle password-reset design   sub-issues: #101

The elaboration batches the *deciding*; the assertion joins no
elaboration. #101 closes → #102 is settled and unbolted (invariant 6)
→ the intent loop births the handoff item and its unit:

    #104  Plan the bolt for the forgot-password assertion  type:handoff · queued
    #105  [unit] Handoff: forgot-password to construction  sub-issues: #104, #102

The operator moves #105 to Ready — the checklist they flip is the list
of assertions being released. The handoff session works #104: drafts
`bolt-plan.md` on the standard template, runs one plannotator round,
then makes the custody move:

    #102  milestone intent/auth-hardening → bolt/forgot-password · state:ready

The server starts the bolt loop; construction accrues on
#102 as comments and as its one `stage:*` label. When its branch reaches
the bolt branch the loop closes it `closed:merged` with the merge SHA —
which is what checks it off on #105's bar — and the landing upgrades that
to `closed:done` with the landing SHA. #105's
checklist keeps tracking it across the move (invariant 2), and
`intent/auth-hardening` is free to close when design and writebacks
are done.

## The quick bolt — and the no-spec path

The operator, at triage: "rename the gateway's env var everywhere."
Small, fully defined, no intent behind it. Dispatch creates:

    milestone bolt/rename-gateway-env
    #40  Rename GATEWAY_URL to GATEWAY_BASE_URL across the built repos
         type:assertion · state:ready — born ready on the operator's word
    #41  [unit] Rename the gateway env var   sub-issues: #40
         on the board at Status Ready from birth — the parent carries the
         approval, and its native sub-issue bar is the bolt's progress

Every release creates one unit parent, this one included: a release of a
single item still gets one, because a special case for one item would put
the bolt back to having no container and no bar. #40 is not added to the
board itself — the parent is the row.

There is no assertion record file — with no intent, the item body IS
the claim. The server sees a `bolt/*` milestone with a ready item and
no loop process on it, starts one for `bolt/rename-gateway-env`, and
the loop's scaffold guard writes the change binding the member the work
warrants (`bolt-quick` here — no review step).

**`bolt-no-spec` is deliberately not a schema: plan mode replaces the
spec step, inside a quick bolt only.** For work too small to warrant a
spec-driven change in the built repo, the bolt declares the plan-mode
path — the phrase the release writes into the milestone description, or
`plan_mode:` in the change's binding — and the build session is started
in plan mode (`--permission-mode plan`): every edit is blocked
mechanically until the plan is approved. Approval is a judgment, so the
loop asks an approver session whether the plan does what the item's
claim says and drives the plan dialog on the one line it answers with;
two returns on one batch pause it with `needs-operator`. The plan-mode
call rides the bolt type: it exists only where the
operator already chose `bolt-quick` — on `bolt-direct`, `bolt-default`
and
`bolt-adversarial` every item is specced through a spec-driven change,
because the bolt type is the scrutiny the release approved, and a
declaration against those types is refused rather than honoured
quietly. The same rule runs the other way for `bolt-direct`'s missing
verify stage: it is that type's alone, and a bolt on another type
cannot declare its way out of verify. Everything else is unchanged:
the item's comments and its one `stage:*` label carry the stages, the
merge gate runs unweakened, the merge-back closes the item
`closed:merged` with the merge SHA, and the landing upgrades it to
`closed:done` with the landing SHA.
