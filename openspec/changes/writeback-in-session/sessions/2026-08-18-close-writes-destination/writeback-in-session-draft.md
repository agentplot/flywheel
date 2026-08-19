# Decision draft: the close writes the destination

Three coupled decisions for item #312, milestone
`intent/writeback-in-session`. The dictation: writeback should be a
natural part of every design session, not a separate typed item queued
for a later round. Annotated by the operator 2026-08-18; the round's
outcomes are folded in below and recorded in
`../../decisions/`.

---

## Decision 1 — every design session writes back what it settles, as part of its own close  **[CLOSED, as amended]**

A design session that settles something writes the settlement into its
destination before it settles. **The destination is an open-ended list,
and the plumbing is what the flywheel specifies, not the list.** Today
the list holds: plans, book chapters, context maps, HTML design docs,
research result reports — and it will extend. Two instances carry the
mechanics:

- **a book chapter**, when a chapter owns the subject — rewritten in
  full, in destination voice, per `books/CLAUDE.md`, with the map moved
  and the three gates green (`preview.py --check`, `check-mermaid`,
  `map-check`). Exactly the discipline the writeback skill teaches
  today, executed by the session that made the chapter stale instead of
  a stranger a round later.
- **the intent's records**, when the settlement is about the intent
  itself — the `decisions/<slug>.md` record, the pointer on the
  question record, the closing comment on the item.

**The context map is a first-class destination.** The system context
map being built in willdan-blueprints joins the list; the operator
proposes moving that code into flywheel or a new agentplot project,
with the map JSON living in the blueprint repo it describes. Where that
code lands is an open question, queued on this milestone.

**No session queues a writeback item for what it itself settled.** A
consequence item is still queued when the settlement obligates work
*beyond* the writer's own close: a chapter in a repo the session has no
worktree for, or a contradiction the write reveals.

**Why the machinery already admits this.** The intent loop merges every
session branch through the same gate (`wt merge --no-remove`), and the
repo's `[pre-merge]` hooks are the books/mermaid/map gates — the merge
gate does not care which session type wrote the chapter. The only
machinery that assumes writeback is a separate type is prose (skills,
profiles) and one launch bit (research runs without a worktree).

**Mechanical consequence — worktrees for every type.** Research is the
one type launched with `worktree=False` (`bin/_flywheel_intent.py`,
`TYPES`). A research answer that closes a decision needs somewhere to
write it: flip research to `worktree=True`. Worktrunk removes an
unchanged worktree at teardown, so a session that only reads and
comments pays nothing.

## Decision 2 — the fate of the standalone writeback type  **[OPEN — coupled to the session-chaining DX]**

The draft proposed narrowing `type:writeback` to repair and catch-up
work. The operator's response: it could make sense, **but the real
design is the chain** — a sequence of design sessions that close one
and move to the next in a single DX action:

- (a) present the next elaboration plan to the operator to approve, and
  upon approval
- (b) close the current session and charge the next —

one gesture, not two. The plan presented for approval may also carry
**direct bolt plans** where construction is the right next step,
alongside (or instead of) book writebacks that then generate bolt
plans.

The writeback type's fate folds into that design: whether a narrowed
repair type survives depends on what the chain makes of session
boundaries. Queued as a planning question on this milestone; this
decision waits on it.

## Decision 3 — rounds get numbers  **[CLOSED — approved as drafted]**

The compose guard titles every elaboration
`Elaboration: <slug> — round N`, where N = 1 + the count of
elaborations already on that milestone in the snapshot (open or
closed). One line in `apply_compose` (`bin/_flywheel_intent.py`); the
amend-not-rebirth rule is untouched — newcomers still join the open
Backlog elaboration, which keeps its number. The board gets distinct
rows for free; nothing else consumes the title.

---

## Consequences

Machinery edits reach the repo through a bolt; design questions are
queued on this milestone.

From the closed decisions (assertions, waiting for the bolt planner):

1. Round number in `apply_compose`'s elaboration title (decision 3).
2. Flip research to `worktree=True` in `bin/_flywheel_intent.py` TYPES
   (decision 1).

Waiting on the session-chaining design before their final shape:

3. The close-writes-destination obligation in the four other type
   skills and both session profiles.
4. The reframing (or retirement) of `skills/writeback/SKILL.md`, and
   extraction of the chapter-writing discipline to a shared reference.
5. `skills/inception/SKILL.md`: "the books and map for writeback
   batches" widens to any session whose close moves them; compose prose
   picks up the round number.
6. The decision template's consequence line
   (`schemas/flywheel-intent/templates/decisions/decision.md`) drops
   `writeback` as a default appended task.

Queued questions:

7. Design the session-chaining DX (decision 2's gate).
8. Settle where the context-map system code lives (out of
   willdan-blueprints; into flywheel or a new agentplot project; map
   JSON stays with the repo it describes).

## The meta-case

The flywheel's book is **`agentplot/blueprints`** — a repo this session
holds no worktree for. Per decision 1's own exception path, the write
of these closed decisions into that book is a queued `type:writeback`
item on this milestone; this session's close writes the intent's
records here and queues that item.
