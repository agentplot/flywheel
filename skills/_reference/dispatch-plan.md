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
round correcting choices rather than supplying them. **Dispatch runs
every round**: origin actors author and publish payloads, and dispatch —
the standing singleton — assembles everything standing into ONE plan,
runs it (the page and the digest), and applies the word. Rounds are
serialized by dispatch being one session: material arriving mid-round
keeps its standing label and seeds the next round.

| origin | who authors the payload | what stands for the round |
|---|---|---|
| design-session close | the design session, in its own pane | a published payload: marker + `dispatch:standing` on the elaboration parent |
| construction findings | a findings-routing session the bolt loop charges | a published payload: marker + `dispatch:standing` on the anchor item |
| bolt close-ready | the bolt loop itself | the close-ready marker + `dispatch:standing` on the unit parents |
| dispatch triage | dispatch | open unmilestoned issues — its existing inbox |

The operator calls a round with one word — **"dispatch"** — over
Discord or in the pane; the server's triage poke is the other trigger.
If a round is open and unanswered, new material waits for the next.

**Any design session MAY end with a dispatch-plan payload; none must.**
A session with nothing to propose settles as today, and the loop's
compose guard and the operator's ordinary board approval remain the
fallback path. The chain exists so that one approval, given where the
operator already is, closes this round and charges the next — instead
of two gestures on two surfaces with the context carried by memory.

## Publishing a payload

An origin actor with records to propose finishes authoring, then
publishes — three acts, in order:

1. **Commit** the payload files by pathspec in its own worktree (the
   design-session and construction shapes below), and **push the
   branch**: dispatch holds no checkout and reads the files through the
   GitHub contents API at a pinned SHA, so an unpushed payload is
   invisible and a pinned SHA is immutable — the page dispatch renders
   is exactly what the origin committed.
2. **Write the round-payload marker** as a comment on the anchor item —
   the elaboration parent for a design session, the unit parent (or the
   lowest queued finding) for findings-routing:

       <!-- flywheel:round-payload -->
       PAYLOAD: repo=<owner/name> sha=<40-hex> dir=<path to close/>
       ORIGIN: design-session | construction
       <!-- /flywheel:round-payload -->

3. **Add the `dispatch:standing` label** to the same item, and settle.
   The label is only the signal ("dispatch has something to assemble
   here"); the marker is the payload. The actor runs no round and
   applies nothing.

Dispatch's apply, as its last act per payload, writes
`<!-- flywheel:round-consumed -->` on the anchor and removes the label —
consume-last, so a crash mid-apply re-offers only work whose mechanics
are already re-runnable. A republished payload after a send-back
supersedes the earlier address (latest unretired marker wins). A payload
fetch that fails is a reported shortfall in the round, never a guess.

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
`skills/findings-routing/`) that authors this plan's payload over the
whole queued set — the current bolt for work its merge criteria need, a
proposed successor bolt, the source intents for design-level faults,
drop — and publishes it. The loop is already stopped, so nothing
blocks; an operator who never calls a round loses nothing — the payload
stands, and a restarted loop re-proposes. Applying the plan drains the
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

**The round's page** — dispatch holds no repo checkout and writes no
records; the assembled round is one self-contained `plan.html` (every
standing payload's sections plus its own triage rows and the close
section, the payload markdown embedded from the contents-API reads)
under the org folder's untracked scratch, beside `fleet.yaml`:

    <org>/.flywheel/plans/<date>-round/plan.html

An ephemeral surface is not a record — the committed payload files and
the tracker objects the apply writes are the record — and the raw ideas
themselves wait as open unmilestoned issues, dispatch's existing inbox,
so an operator who never calls a round loses nothing.

**The close section** — a bolt loop that finds every item merged and
every card ruled marks its unit parents: the "Ready to land" comment
carries a machine block —

    <!-- flywheel:close-ready -->
    CLOSE-READY: milestone=bolt/<slug> branch=<bolt branch> main=<main>
    <!-- /flywheel:close-ready -->

— beside `needs-operator` and `dispatch:standing`. The round renders one
pre-checked row per close-ready milestone: checked means the apply
closes it (the close releases the landing; the loop and the archive do
the rest). **Unchecking writes nothing** — the milestone stays open, the
labels and marker stand, and the choice reappears in every later round
until the operator closes it or new cards withdraw it (the loop's own
hold, which removes both labels; label off = not offered, and there is
no withdrawn marker). A plan never both files new cards onto a bolt and
closes it: cards on a bolt force its close row unchecked.

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
  "retargets":  { "<row-key>": "<container-key>" },
  "closes":     { "<milestone>": false } }
```

Every field but `decision` is optional, and **an omitted field means
as-proposed** — which is what makes "yes to all" a one-word approval.
`closes` carries only UNCHECKED close rows (keep open); an omitted
milestone closes as seeded.
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
  records it at apply, tracker-first: the operator's answer verbatim as
  a comment on the question item, carrying a bare
  `<!-- flywheel:answered -->` marker line, and the item closed
  `closed:done` — the marker, not the reason, is the machine-readable
  "answered" fact. The item is never filed into a batch. A session
  holding a worktree may still fold an in-pane answer into
  `decisions/<slug>.md`, but nothing new depends on `decisions/*.md`:
  what elaboration should really produce — design documents, context
  maps, ubiquitous language — is the books' job, a standing design
  thread.

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

    Dispatch plan — <date> round
      1. [close] bolt/plan-generalization — every item merged, every
         card ruled; closing releases the landing to main → close
    intent/session-chaining (new) — next elaboration
      2. [writeback] Write the chaining design into the book → approve
      3. [question]  Should the digest thread per round? → awaiting answer
    bolt/next-surface (existing — folding in)
      4. [unit · bolt-default] close-contract-prose · 2 changes → approve
    left out: the map-removal half — that org's tracker owns it

    Reply "yes" or "yes to all" to approve as proposed; corrections by
    number ("4 -> backlog", "4 as bolt-quick", "rename bolt/x to
    bolt/y", "keep bolt/plan-generalization open",
    "answer 3: <text>"); or "send back: <note>".

The reply grammar resolves to the decision contract: `yes` / `yes to
all` is `{"decision": "approve"}` — and it CLOSES every seeded close
row, landing those bolts, which each row states plainly; `row N ->
<route>` edits that row's routing; `N as bolt-<type>` is a unit-type
override; `keep <milestone> open` unchecks a close row; `answer N:
<text>` answers a question row; `send back: <note>` returns the plan.
The digest and the page are the same plan — whichever answer arrives
first is the round's answer, applied identically.

If the page will not open and no channel carries the digest, report the
shortfall and settle without a round: the committed payload still says
what was proposed, and the fallback path carries the work.

## The apply — the operator's word, in a load-bearing order

Dispatch applies every round, and every write is a tracker write: the
payload files were committed at publish, so nothing remains for the
origin actor post-approval. Every Backlog write and `stage:done` comes
before any move to Ready: the loop's cycle runs guards → collect/merge
→ dispatch, so a restart at any point mid-apply either merges the
finished branch before anything newly approved can dispatch, or leaves
a batch at Backlog — the ordinary fallback path, finished by the
operator's board approval. Steps the round lacks are skipped.

1. **Answers** — per answered question row: the operator's answer
   verbatim as a comment carrying the `<!-- flywheel:answered -->`
   marker line on the question item, then close it `closed:done`.
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
4. **`stage:done`** — `flywheel-stage <n> … --stage stage:done` on each
   item a payload names in its `done_items` — the origin session's own
   items, whose completion spec cannot tell who wrote the label. The
   session settled at publish; this is what lets its loop collect.
5. **Ready** — `flywheel-board … --status Ready` on every approved
   elaboration parent and card, immediately after 4 and never before
   it. A card filed onto an open running bolt moves with the rest: the
   round's approval IS the board approval, and the live bolt loop
   expands it mid-flight.
6. **Milestone closes** — close each close row still checked; the close
   releases the landing, and the loop and the archive do the rest. A
   container that filed cards onto a bolt in step 3 forces that bolt's
   close row unchecked — never both in one round.
7. **Consume and settle** — per applied payload, the
   `<!-- flywheel:round-consumed -->` comment on its anchor and the
   `dispatch:standing` label removed. A send-back comments the note on
   the anchor and still consumes: the origin redrafts and republishes.

**The one exception to "you never move an item to `state:ready`"** is
step 5: dispatch applying the operator's explicit approval given in the
round it ran. No other write of yours ever makes anything ready.

**Failure discipline.** A step that fails stops the apply where it is:
comment the partial state on the payload's anchor (or an intake issue
the plan covers), add `needs-operator`, do not settle. A half-applied
plan that settles quietly is the one failure the loop cannot detect. An
apply interrupted before step 5 needs no ceremony: whatever reached
Backlog is finished by the operator's ordinary board approval — the
fallback path is the recovery path — and each container is independent,
so one container's failure strands no other. A crash before step 7
leaves the payload standing; every container mechanic is re-runnable
(amend `--into`, supersede-not-duplicate, move-not-duplicate), so the
next round re-applies safely.

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
