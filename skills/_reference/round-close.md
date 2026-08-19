# The round-close plan — a session's close chains the next one

The one shared copy, at the flywheel plugin's
`skills/_reference/round-close.md`; the session profiles and every
design type skill point here rather than restating the protocol. The
object-graph rules are in `tracker.md` beside this file; the
invocations are in `herdr.md`; the unit-card grammar is the
`bolt-planning` skill's and is not repeated here.

**Any design session MAY end with a round-close plan; none must.** A
session with nothing to propose settles as today, and the loop's
compose guard and the operator's board flip remain the fallback path.
The chain exists so that one approval, given in the pane the operator
is already in, closes this round and charges the next — instead of two
gestures on two surfaces with the context carried by memory.

## The close directory

The plan is real files in the session's own directory — the page is a
view over them, never a restatement, because what the operator
annotates IS what lands on the tracker:

    sessions/<date>-<slug>/close/
      plan.html          the surface
      elaboration.md     the batch parent's body + one block per member item
      bolt-summary.md    the bolt milestone's description, verbatim
      units/<slug>.md    the unit-card bodies, in bolt-planning's exact grammar

**Nothing reaches GitHub before approval.** No item, batch, milestone,
or card exists ahead of the apply — a plan is previewed, iterated, or
abandoned without ever leaving a stranded object on the board.

## The page

**The page is the template, filled — never redesigned.** Copy
`round-close-template.html` beside this file into the session's
`close/plan.html` and fill its two marked regions: the payload
markdown blocks (mirroring the committed `close/*.md` exactly) and the
`plan-data` JSON (slug, round numbers, what closed, the member and
unit rows, what is left out). Everything below the template's fill
line is the format and is not edited, which is what makes every
round's page the same page. Opened with
`npx -y lavish-axi sessions/<date>-<slug>/close/plan.html`;
the steering source for the surface is the user-level `lavish` skill.
Four fixed sections, in order:

1. **Results** — what this round closed, one line per decision/item,
   pointing at the records. A send-back control returns the round to
   the session for iteration.
2. **Next elaboration** — the proposed batch, one row per member item
   in dependency order. A question row carries an answer box: an
   answer typed there is recorded as a decision at apply and the item
   is never filed.
3. **Construction** — the proposed bolt: summary line, then one row
   per unit card with its type and price, rendering `units/<slug>.md`.
4. **Left queued** — items proposed for no round, so silence about
   them is never read as approval.

Every row is a proposal with a routing control already set to the
session's default — the round corrects choices, it never supplies
them. The page is built to glance, not to read:

- **One row per proposal**: a type badge with a distinct color per
  type, a bold title, a one-line summary in plain words, and the
  row's control — never a wall of same-weight prose, and never a
  control in a separate list the operator has to match back to its
  proposal by memory.
- **Full text folds away**: the rendered markdown sits behind a
  disclosure on its row; the bolt summary compresses to a stat line
  (units · changes · days) over its unit rows.
- **The payload is always visible**: a fixed bar shows exactly what
  Approve will send, live-updated on every control change, beside the
  Approve and send-back controls. A changed control that could be
  silently lost is a broken page.
- **A row's control offers only the routes that make sense for it**:
  a design item offers next round / hold / drop, and typing an answer
  into a question row takes the `answered` path; a unit offers file
  the card / hold / drop. "This needs more design first" is a
  send-back of the plan with a note, never a routing value.

If `npx -y lavish-axi` fails opaquely and the installed-copy
fallback in the `lavish` skill also fails, report the shortfall and
settle without a round: the committed `close/` files still say what
the session proposed, and the fallback path carries the work.

## Routing

One enumeration, and every control resolves to exactly one value per
outcome:

- `elaboration` — an item in the next elaboration
- `unit card` — a construction card, filed in the bolt-planning grammar
- `hold` — filed `state:queued` on the milestone, out of this round
- `drop` — not filed at all
- `answered` — questions only: the answer becomes a decision record,
  no item is filed

**Routing is exclusive, and the chain carries the sequencing.** No
dependency edge spans the elaboration and construction sections. The
test for carding construction now is the card's `sources` column: cite
what exists — a decision record, this session's own records, a chapter
already written — and the card goes in this plan, the
skip-the-writeback case. An outcome with no source a spec could be
written from routes to a writeback item instead, and that writeback
session's own close round cards it, citing the chapter it just wrote.
`builds on` edges between units stay — that is bolt-planning's own
mechanic, inside the construction section.

## The apply — the operator's word, in a load-bearing order

On approval the session applies the word directly. All file commits
come before any tracker write, and `stage:done` before any Ready flip:
the loop's cycle runs guards → collect/merge → dispatch, so a restart
at any point mid-apply either merges the finished branch before the
released batch can dispatch, or leaves the batch at Backlog — the
ordinary fallback path, finished by one operator board flip. Reversed,
a restart between the Ready flip and `stage:done` dispatches the next
session from a main that lacks this session's records.

1. **Fold answers and commit** — answered questions become
   `decisions/<slug>.md`; commit them and the whole `close/`
   directory. The branch is merge-complete from here; everything below
   writes only the tracker.
2. **Elaboration, at Backlog** — create each member item (`type:*`,
   `state:queued`, on the intent's milestone), then compose with
   `flywheel-batch --kind elaboration`, title
   `Elaboration: <slug> — round N` (N = 1 + the elaborations already
   on the milestone, open or closed). An open Backlog elaboration
   already on the milestone is amended instead — `--into <n>`, keeping
   its number and title.
3. **Construction, at Backlog** — bolt-planning's board mode,
   unchanged: the `bolt/<slug>` milestone with `bolt-summary.md` as
   its description, one `plan`-labelled card per unit with
   `units/<slug>.md` as the body verbatim, `builds on` mirrored as
   blocked-by between cards, stale unapproved cards from earlier runs
   closed `closed:superseded`.
4. **Own items** — `flywheel-stage <n> … --stage stage:done` on each
   item the session carries, per the existing contract.
5. **Ready** — `flywheel-board … --status Ready` on the elaboration
   parent and the approved cards, immediately after 4.
6. **Settle.**

**The one exception to "you never move an item to `state:ready`"** is
step 5: applying the operator's explicit approval given in a round the
session itself ran. No other write of yours ever makes anything ready.

**Failure discipline.** A step that fails stops the apply where it is:
comment the partial state on your item, add `needs-operator`, do not
settle. A half-applied plan that settles quietly is the one failure
the loop cannot detect. An apply interrupted between 4 and 5 needs no
ceremony: the composed batch is at Backlog and the operator's board
flip finishes it — the fallback path is the recovery path.

## Iteration, partial approval, supersession

An annotation striking a row folds: the struck outcome is re-routed or
left unfiled, the approved remainder proceeds. Rejecting the plan
outright is an ordinary round iteration — redraft, re-open. Nothing
becomes Ready by silence.

After an apply, session-proposed elaborations and cards carry the same
staleness mechanic as planned bolt units: an iteration that replaces
one wholesale closes it `closed:superseded` with a successor pointer
in the closing comment; smaller changes amend the open Backlog batch
in place. Nothing an abandoned plan filed stays live, and nothing is
deleted — the superseded parent is the history.
