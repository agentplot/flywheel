# Decision draft: the session-chaining DX (item #316)

The dictation, from the round on #312: chained design sessions should
close one and charge the next in a single DX action — (a) present the
next elaboration plan to the operator to approve, and upon approval
(b) close the current session and charge the next. The plan may carry
direct bolt plans alongside book writebacks. The standalone writeback
type's fate folds into this design.

## Today's flow costs the operator two gestures on two surfaces

1. The session settles; the operator rules items done (word in the
   pane, or `stage:done` on GitHub) — **surface 1, per item**.
2. The loop collects, closes, merges the branch, closes the pane.
3. The loop's compose guard batches the orphan queued items into an
   `Elaboration: <slug> — round N` at board **Backlog**.
4. The operator flips the batch to **Ready** — **surface 2, the
   board**.
5. The loop charges the next session.

Between 1 and 4 the chain stalls twice, and the operator carries the
round's context from the pane to the board by memory.

## Proposed design — the closing round carries the whole gesture

### The round-close plan

A session that has a next round to propose ends not with a bare report
but with a **round-close plan**, one document in its session directory,
put through the channel the operator is already in — a plannotator
round. The plan holds, in order:

1. **What this round closed** — one line per decision/item, pointing at
   the records.
2. **The next elaboration** — the queued items it batches, one line
   each, in dependency order. The session composes this batch itself
   (`flywheel-batch`, at Backlog) *before* the round, so the plan
   describes a batch that exists and approval has a concrete object to
   act on.
3. **Direct bolt plans, where construction is the right next step** —
   full plan cards (`Unit: <slug>` documents), filed at Backlog, listed
   in the plan. A card earns its place here when the book (or the
   records) already says everything a spec needs; a writeback that
   would only restate a settled decision so a planner can card it later
   is the indirection this cuts.
4. **What is deliberately left queued** — items proposed for no round
   yet, so silence about them is never read as approval.

### Approval is one gesture, and the session applies it

The operator approves the plan in the round (annotating exceptions —
see partial approval). On approval the session, holding the operator's
word, applies it directly — the existing rule "the operator's word is
applied directly, by whoever holds it," exercised three ways in one
close:

- writes `stage:done` on its own items (`flywheel-stage`) — already
  the contract today;
- flips the next elaboration (and any approved bolt cards) to board
  **Ready** (`flywheel-board`) — the word making ready is explicit in
  the approved plan, so the invariant "only the operator's word makes
  ready" holds; what changes is only *who carries the word to the
  board*;
- settles. The loop then does exactly what it does today with
  `stage:done` items and a Ready batch: collect, merge, close the
  pane, charge the next session. **The loop changes not at all in this
  path** — no inference, no new labels, no new states.

### Partial approval and rejection

An annotation striking an item from the plan is folded: the struck item
stays queued at Backlog (or is re-batched per the annotation), the
approved remainder proceeds. Rejecting the plan outright is an ordinary
round iteration — redraft, re-run. The gesture is only ever additive on
explicit approval; nothing becomes Ready by silence.

### The fallback path stays

The chain is an option a session takes when it has a next round to
propose, not an obligation. A session with nothing to propose settles
as today; the loop's compose guard still batches orphans at Backlog and
the board flip still releases them. Sessions without operator rounds
(research, prototype today) use the fallback unless their close has a
plan worth a round — any type MAY run a closing round; none must.
Amend-not-rebirth is untouched: the session-composed batch is the open
elaboration newcomers join.

### Contract edits this implies (construction, via a bolt)

1. Session profiles and the planning/interactive skills gain the
   round-close plan and the approval-application recipe; the "you never
   move an item to `state:ready`" prose gains its one exception: *when
   applying the operator's explicit approval given in a round you ran*.
2. `skills/inception/SKILL.md` and `_reference/tracker.md`: the compose
   guard's description notes the session-composed batch; the state
   ladder's "only the operator's word makes ready" text names the round
   approval as one form of that word.
3. `flywheel-board` grows (or already has) the flip-to-Ready invocation
   a session can run; `_reference/herdr.md` documents it.

## The writeback type's fate — the fold this design was gating

**Recommendation: keep `type:writeback`, narrowed to repair and
catch-up** (option (a) from the #312 draft). The chain removes the
failure mode that made the type suspect: "settle now, write later"
drift is gone because the write is the close (decision
`the-close-writes-the-destination`), and a repair item — a
contradiction found in the books, a restructuring, a backlog write like
#320 — now rides a chained round like any other item instead of
waiting for a stranger's future batch. The type keeps its skill (the
chapter discipline), loses its role as every settlement's tail.

## What approval of this draft closes

- Decision: the chaining DX as designed above (round-close plan; one
  approval gesture; session applies the word; loop unchanged).
- Decision: `type:writeback` narrowed to repair/catch-up — the open
  half of #312's decision 2.
- Consequences to queue: assertions for the contract edits (1)–(3)
  above.
