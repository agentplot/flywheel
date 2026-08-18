# Decision draft: the close writes the destination

Three coupled decisions, drafted together because the operator asked for
them together (item #312, milestone `intent/writeback-in-session`). The
dictation: writeback should be a natural part of every design session,
not a separate typed item queued for a later round.

---

## Decision 1 — every design session writes back what it settles, as part of its own close

**Proposed.** A design session that settles something writes the
settlement into its destination before it settles. The destination is:

- **a book chapter**, when a chapter owns the subject — rewritten in
  full, in destination voice, per `books/CLAUDE.md`, with the map moved
  and the three gates green (`preview.py --check`, `check-mermaid`,
  `map-check`). Exactly the discipline the writeback skill teaches
  today, executed by the session that made the chapter stale instead of
  a stranger a round later.
- **the intent's records**, when no chapter fits — the
  `decisions/<slug>.md` record, the pointer on the question record, the
  closing comment on the item. This is already the planning type's
  obligation; it becomes every type's.

**No session queues a writeback item for what it itself settled.** The
queued-writeback pattern — settle now, write later, hope the round
happens — is the thing the operator dictated away. A consequence item is
still queued when the settlement obligates work *beyond* the writer's
own close: a chapter in a repo the session has no worktree for, or a
contradiction the write reveals.

**Why the machinery already admits this.** The intent loop merges every
session branch through the same gate (`wt merge --no-remove`), and the
repo's `[pre-merge]` hooks are the books/mermaid/map gates — the merge
gate does not care which session type wrote the chapter. The only
machinery that assumes writeback is a separate type is prose (skills,
profiles) and one launch bit (research runs without a worktree).

**Mechanical consequence — worktrees for every type.** Research is the
one type launched with `worktree=False` (`bin/_flywheel_intent.py`,
`TYPES`). A research answer that closes a decision now needs somewhere
to write it. Proposal: flip research to `worktree=True`. Worktrunk
removes an unchanged worktree at teardown, so a session that only reads
and comments pays nothing; the alternative — the loop guessing in
advance which research answers will move a chapter — is a guess the
loop is forbidden to make.

## Decision 2 — the standalone writeback type narrows to repair

Two options; the draft recommends (a).

**(a) Keep `type:writeback`, narrowed — recommended.** The type stops
being the tail of every settlement and becomes book work that IS the
work: catch-up on a backlog of settled-but-unwritten decisions,
repairing a contradiction the books already hold, restructuring
chapters. Its skill reframes from "decisions have closed and the books
do not say so yet" (now the exceptional case) to book maintenance. The
full-rewrite / destination-voice / gates-green discipline moves to a
shared reference both the writeback skill and every session's close can
cite.

**(b) Delete the type.** Cleaner story, but the repair work in (a)
still exists and would have to masquerade as research or planning,
which teaches neither the book conventions nor the gates. Rejected
unless the operator prefers it.

Either way, the decision template's default consequence line
(`schemas/flywheel-intent/templates/decisions/decision.md`: "Appended
task: writeback / new question") loses `writeback` — the write is the
close, not a task.

## Decision 3 — rounds get numbers

**Proposed.** The compose guard titles every elaboration
`Elaboration: <slug> — round N`, where N = 1 + the count of
elaborations already on that milestone in the snapshot (open or
closed). One line in `apply_compose` (`bin/_flywheel_intent.py`); the
amend-not-rebirth rule is untouched — newcomers still join the open
Backlog elaboration, which keeps its number.

**Why it belongs with decisions 1–2.** With the write folded into the
close, a round becomes a complete unit — elaborate, settle, write —
instead of a settle-round trailed by a writeback-round. Numbering rounds
is meaningful exactly when a round is whole; numbering the current
half-rounds would stamp near-duplicates with serials and call it fixed.

The board gets distinct rows for free; nothing else consumes the title,
so no other machinery moves.

---

## Consequences (queued as items once this round closes)

All machinery edits — they reach the repo through a bolt, not through
this session:

1. Flip research to `worktree=True` in `bin/_flywheel_intent.py` TYPES.
2. Round number in `apply_compose`'s elaboration title.
3. Reframe `skills/writeback/SKILL.md` to repair/catch-up; extract the
   chapter-writing discipline to a shared `_reference` both it and the
   session profiles cite.
4. Add the close-writes-destination obligation to the four other type
   skills and both session profiles
   (`agents/flywheel-design-session.md`,
   `agents/flywheel-interactive-session.md`).
5. Amend `skills/inception/SKILL.md`: "the books and map for writeback
   batches" widens to any session whose close moves them; the
   compose/round prose picks up the round number.
6. Drop `writeback` from the decision template's consequence line.

## What this session will itself do (the meta-case)

The flywheel repo has no `books/` — for this org the destination is the
intent's records, the fallback path of decision 1. When the operator's
annotations close these decisions, this session writes
`decisions/` records under `openspec/changes/writeback-in-session/`,
points them at this draft, and comments #312 — its own close
demonstrating the decision it closes.
