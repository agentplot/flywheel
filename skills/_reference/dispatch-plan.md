# The dispatch plan — one routing surface, one approval

The one shared copy, at the flywheel plugin's
`skills/_reference/dispatch-plan.md`; the session profiles, the dispatch
profile, and every design type skill point here rather than restating
the protocol. The object-graph rules are in `tracker.md` beside this
file; the invocations are in `herdr.md`; the unit-card grammar and the
bolt-selection guidance are the `bolt-planning` skill's and are not
repeated here.

A dispatch plan is a batch of routed outcomes facing the operator as one
approval — every proposal already placed, every choice already made, the
round correcting choices rather than supplying them. Three origins build
one, and each origin's actor runs its own round:

| origin | who builds and applies it | when |
|---|---|---|
| design-session close | the design session, in its own pane | a batch with a next round or construction to propose |
| dispatch triage | dispatch | accumulated raw ideas need routing |
| construction findings | a findings-routing session the bolt loop charges | the loop stops at a non-empty queue |

**Any design session MAY end with a dispatch plan; none must.** A
session with nothing to propose settles as today, and the loop's compose
guard and the operator's ordinary board approval remain the fallback
path.
The chain exists so that one approval, given where the operator already
is, closes this round and charges the next — instead of two gestures on
two surfaces with the context carried by memory.

**Nothing the plan proposes reaches GitHub before approval.** No item
placement, batch, milestone, or card exists ahead of the apply — a plan
is previewed, iterated, or abandoned without ever leaving a stranded
object on the board. The intake issues a triage plan routes pre-exist
as dispatch's inbox; they are the subject of proposals, never proposals
themselves.

The operator's own dictation never takes this path: an idea arriving as
the operator's word is applied directly by whoever holds it —
dispatch's born-ready unit, a session applying the word in its pane —
because the word at the moment of stating is itself the approval, and a
plan would be a second gesture for the same word.

Construction findings take the same intake/routing split as dispatch.
Test and code-review sessions write each finding as a `state:queued`
item at birth — the bolt's **findings inbox**, durable while the
operator is away, and never routed work: nothing in it is built, carded,
or composed until a plan routes it. When the bolt loop stops at a
non-empty queue (including the pass where it proposes closure), it
charges a one-shot findings-routing session (the type skill at
`skills/findings-routing/`) that builds this plan over the whole queued
set — the current bolt for work its merge criteria need, a proposed
successor bolt, the source intents for design-level faults, drop — and
runs the round. The loop is already stopped, so the round blocks
nothing; an operator who never takes it loses nothing — the inbox
waits, and a restarted loop re-proposes. Applying the plan drains the
inbox the way applying a guard's plan empties the guard.

## The three layers

A plan is three separable things, and keeping them separate is what lets
the same plan reach the operator through more than one channel:

1. **The payload** — the plan as data: the committed markdown files and
   the `plan-data` JSON, every proposal placed in a container with its
   choice seeded.
2. **The decision contract** — what comes back: a route per row,
   corrections to the seeded choices, inline answers, or a send-back
   with a note. Defined independently of any page, so "yes to all" over
   Discord and an Approve click on the lavish page resolve to the same
   structure.
3. **A surface** — one renderer of the payload that collects the
   contract. The lavish page is one surface; the Discord digest is
   another. No surface defines the plan.

## Containers and rows

A plan proposes zero or more **containers**, and places each outcome as
a **row** under exactly one of them:

- an **intent** container — its next elaboration, and the intent itself
  when `status` is `new`: the plan's apply creates the milestone and
  originating item, and the intent loop scaffolds the change from the
  tracker.
- a **bolt** container — an existing open bolt the rows fold into, or a
  new one the apply creates. Its `deliverable` line states what the
  operator sees working, and its `alternates` list the open bolts the
  units could fold into instead — the naming choice on the surface,
  where one control corrects it.

Multiple intents and multiple bolts in one plan are ordinary — a triage
of several raw ideas splitting into several new intents is the shape the
container model exists for. **No dependency edge spans containers.**
`builds on` edges between units stay — bolt-planning's mechanic, inside
one bolt container.

**Choosing the bolt is part of authoring the payload**, and the rule is
bolt-planning's, stated there and only pointed to here: the bolt is
named for the deliverable the operator wants to see working together,
never for the work items; read the open `bolt/*` milestones first and
fold units into the open bolt whose deliverable they serve; a related
idea splits — easy parts into the open bolt, harder parts into a
proposed successor.

## The payload

**Design-session origin** — real files in the session's own directory,
drafted incrementally as outcomes settle so the close is assembly, not
authoring. The page is a view over them, never a restatement, because
what the operator annotates IS what lands on the tracker:

    sessions/<date>-<slug>/close/
      plan.html            the surface
      elaboration.md       the session's own intent: the batch parent's
                           body + one block per member item
      intents/<slug>.md    a proposed NEW intent: its originating item's
                           body + one block per member item
      bolt-summary.md      the bolt milestone's description, verbatim
      bolts/<slug>.md      per-bolt summaries, replacing bolt-summary.md
                           when the plan proposes more than one bolt
      units/<slug>.md      the unit-card bodies, in bolt-planning's
                           exact grammar

**Dispatch origin** — dispatch holds no repo checkout and writes no
records; its plan is one self-contained `plan.html` (the payload
embedded, as the template already does) under the org folder's untracked
scratch, beside `fleet.yaml`:

    <org>/.flywheel/plans/<date>-triage/plan.html

An ephemeral surface is not a record — the tracker objects the apply
writes are the record — and the raw ideas themselves wait as open
unmilestoned issues, dispatch's existing inbox, so an operator who never
takes the round loses nothing.

**Construction origin** — the findings-routing session runs on a
worktree of the repo that owns the bolt change, and its plan is real
files like a design session's, under the bolt's own change directory:

    openspec/changes/bolt-<slug>/sessions/<date>-findings-routing/close/

with the same file shapes as above. The rows it routes are the queued
items themselves — like dispatch's intake, they pre-exist as the inbox
and are moved, carded, or closed by the apply, never duplicated.

## The decision contract

What any surface sends back, one canonical shape:

```json
{ "decision": "approve" | "sendback",
  "note": "…",
  "routing":    { "<row-key>": "<route>" },
  "answers":    { "<row-key>": "<the answer, verbatim>" },
  "unit_types": { "<row-key>": "bolt-<type>" },
  "renames":    { "<container-key>": "<new-slug>" },
  "retargets":  { "<row-key>": "<container-key>" } }
```

Every field but `decision` is optional, and **an omitted field means
as-proposed** — which is what makes "yes to all" a one-word approval.
`note` rides a send-back; `renames` corrects a proposed container's
slug; `retargets` moves a row to another container of the same kind. An
answer typed for a question row takes the `answered` path below. A
reply the actor cannot resolve into exactly one contract is asked
again, never guessed.

## Routing

One enum, aligned with the board's own words, on every surface and
every control. Per row, one route:

- **approve** — file the row under its container: an item in an intent
  container's elaboration, or a unit card on a bolt container in
  bolt-planning's grammar. On a bolt row the unit's type is a seeded,
  overridable control — an override is written into the card's `Type:`
  line before filing. The row's system rides beside it — seeded in the
  payload, rendered on the row, written into the card's `System:` line
  at filing (how construction resolves the unit's built repo); a wrong
  system is corrected by annotation or send-back.
- **backlog** — filed `state:queued` on the container's milestone, out
  of this round; the board's word for parked work.
- **drop** — not filed at all.
- **answered** — questions only: typing an answer into a question row
  records it as a decision at apply, and the item is never filed.

A **retarget** re-files a row under another container of the same kind.
"This needs more design first" is a send-back of the plan with a note,
never a routing value.

**Routing is exclusive, and the chain carries the sequencing.** The
test for carding construction now is the card's sources: cite what
exists — a decision record, the session's own records, a chapter
already written — and the card goes in this plan, the
skip-the-writeback case. An outcome with no source a spec could be
written from routes to a writeback item instead, and that writeback
session's own close cards it, citing the chapter it just wrote.

## Surfaces

**The lavish page** is the primary surface, and it is the template,
filled — never redesigned. Copy `dispatch-plan-template.html` beside
this file into the plan's `plan.html` and fill its two marked regions:
the payload markdown blocks (mirroring the committed payload files
exactly, where files exist) and the `plan-data` JSON. Everything below
the template's fill line is the format and is not edited, which is what
makes every plan's page the same page. Opened with
`npx -y lavish-axi <path>/plan.html`; the steering source for the
surface is the user-level `lavish` skill. The page renders the context
list, one section per container, and the left-out list — one row per
proposal: a type badge, a bold title, a one-line summary, the row's
seeded control, the full text behind a disclosure, and a fixed payload
bar showing exactly what Approve will send, live-updated on every
control change. A changed control that could be silently lost is a
broken page.

**The Discord digest** is the same payload as text — the surface for an
operator who is not at a page. One numbered row per proposal with its
seeded route, container headers between them, the left-out list last:

    Dispatch plan: <slug>
    intent/session-chaining (new) — next elaboration
      1. [writeback] Write the chaining design into the book → approve
      2. [research]  Confirm poll values survive the relay → approve
    bolt/plan-generalization (existing — folding in)
      3. [unit · bolt-default] close-contract-prose · 2 changes → approve
    left out: the map-removal half — that org's tracker owns it

    Reply "yes" or "yes to all" to approve as proposed; corrections by
    number ("3 -> backlog", "3 as bolt-quick", "rename bolt/x to
    bolt/y"); or "send back: <note>".

The reply grammar resolves to the decision contract: `yes` / `yes to
all` is `{"decision": "approve"}`; `row N -> <route>` edits that row's
routing; `N as bolt-<type>` is a unit-type override; `send back: <note>`
returns the plan. The digest and the page are the same plan — whichever
answer arrives first is the round's answer, applied identically.

If the page will not open and no channel carries the digest, report the
shortfall and settle without a round: the committed payload still says
what was proposed, and the fallback path carries the work.

## The apply — the operator's word, in a load-bearing order

All file commits come before any tracker write, and every Backlog write
and `stage:done` before any move to Ready: the loop's cycle runs guards
→ collect/merge → dispatch, so a restart at any point mid-apply either
merges the finished branch before anything newly approved can dispatch,
or leaves a batch at Backlog — the ordinary fallback path, finished by
the operator's board approval. Steps an origin lacks are skipped.

1. **Fold answers and commit** (design-session and construction
   origins) — answered questions become `decisions/<slug>.md`; commit
   them and the whole `close/` directory. The branch is merge-complete
   from here; everything below writes only the tracker. The dispatch
   origin has no commits — the tracker objects its apply writes are the
   durable record.
2. **Per intent container, in plan order, at Backlog** — when `status`
   is `new`, create the `intent/<slug>` milestone and its originating
   item first, assigned to the developer whose word settles it. Create
   each member item (`type:*`, `state:queued`, on the milestone) — a
   triage row that IS an intake issue is moved onto the milestone and
   normalized, never duplicated — then compose with
   `flywheel-batch --kind elaboration`, title
   `Elaboration: <slug> — round N` (N = 1 + the elaborations already on
   the milestone, open or closed). An open Backlog elaboration already
   on the milestone is amended instead — `--into <n>`, keeping its
   number and title.
3. **Per bolt container, at Backlog** — `status: existing` files the
   approved cards on the open bolt's milestone; `status: new` creates
   `bolt/<slug>` with the summary body as its description first. Then
   bolt-planning's board mode, unchanged: one `plan`-labelled card per
   unit with its `units/<slug>.md` body verbatim, `builds on` mirrored
   as blocked-by between cards, and cards this plan explicitly replaces
   closed `closed:superseded` — never other unapproved cards that
   happen to share the milestone. Every card body carries its two
   machine-read lines before filing: `System: <name>` under the title
   (the fleet binding the bolt loop resolves the unit's built repo
   through) and the `Type:` line, with any round override written in —
   a card missing either builds on the fleet's sole binding and the
   bolt's bound type, which is a fallback, not a filing convention.
4. **Own items** — `flywheel-stage <n> … --stage stage:done` on each
   item the session carries, per the existing contract. Dispatch
   carries none; its triage plan skips this step.
5. **Ready** — `flywheel-board … --status Ready` on every approved
   elaboration parent and card, immediately after 4 and never before
   it. A card filed onto an open running bolt moves with the rest: the
   round's approval IS the board approval, and the live bolt loop
   expands it mid-flight.
6. **Settle.**

**The one exception to "you never move an item to `state:ready`"** is
step 5: applying the operator's explicit approval given in a round the
actor itself ran. No other write of yours ever makes anything ready.

**Failure discipline.** A step that fails stops the apply where it is:
comment the partial state on your item (dispatch: on an intake issue the
plan covers), add `needs-operator`, do not settle. A half-applied plan
that settles quietly is the one failure the loop cannot detect. An apply
interrupted before step 5 needs no ceremony: whatever reached Backlog is
finished by the operator's ordinary board approval — the fallback path
is the recovery path — and each container is independent, so one
container's failure strands no other.

## Iteration, partial approval, supersession

An annotation striking a row folds: the struck outcome is re-routed or
left unfiled, the approved remainder proceeds. Rejecting the plan
outright is an ordinary iteration — redraft, re-open. Nothing becomes
Ready by silence.

After an apply, plan-proposed elaborations and cards carry the same
staleness mechanic as planned bolt units: an iteration that replaces one
wholesale closes it `closed:superseded` with a successor pointer in the
closing comment; smaller changes amend the open Backlog batch in place.
Nothing an abandoned plan filed stays live, and nothing is deleted — the
superseded parent is the history.
