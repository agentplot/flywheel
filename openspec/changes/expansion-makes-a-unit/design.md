## Context

See `proposal.md` — Why. The surfaces this change touches, as they stand
at writing (`bin/_flywheel_bolt_loop.py`, read from disk on this branch):

- `guards()` runs, in order, `guard_expand` (−1), `guard_scaffold` (0),
  `guard_topology` (0.5), `guard_flip_consume` (1), `guard_route` (2),
  `guard_stages` (3). Each is idempotent and records only the writes it
  made; an empty `actions` list is the loop's STOP condition.
- `guard_expand` selects cards with `c.at_ready and c.bolt ==
  self.params.milestone`. `PlanCard.bolt` (in `bin/_flywheel_inbox.py`)
  returns the card's milestone when it is a `bolt/*` one and otherwise
  falls back to the title slug — a fallback its own docstring scopes to
  "a card filed before milestones were the planner's".
- `_expand_card` calls `create_milestone` unconditionally and
  `set_milestone` when `card.milestone` differs, then swaps the label,
  files the items, attaches them, and clears the board status.
- `guard_topology` is what sets `self.params.bolt_worktree` to the bolt
  branch's worktree; before it runs on a fresh process the value is
  `repo_dir` (`BoltParams.__post_init__`), so `change_dir` points at the
  main worktree until then.
- `guard_scaffold` returns early when `self.params.change_dir.exists()`,
  which is why the charter is written exactly once per bolt today.

## Goals / Non-Goals

**Goals:**

- The expansion guard reads the card's milestone and writes no
  milestone.
- Every expanded unit's plan document reaches `bolt.md`, whichever pass
  expanded it, with a content test that makes a second pass silent.
- A defer predicate that is satisfiable inside one bolt.

**Non-Goals:**

- The server's bolt-job filter and `PlanCard.bolt`'s title fallback —
  `the-bolt-job-filter`.
- The landing's precondition over open unit cards —
  `the-landing-waits-for-the-cards`.
- The bolt-level sections of `bolt.md` (`## Scope`, `## Merge
  criteria`). A planner-born charter carries none today, so
  `merge_criteria()` reads an empty string for such a bolt; that gap
  predates this change and is queued rather than fixed here.

## Decisions

**The charter write is its own guard, ordered after topology, not part
of `_expand_card`.** Expansion is a tracker write and runs at −1, before
the bolt branch or its worktree exist on a fresh process; a git write
from there would land on whatever branch `repo_dir` has checked out.
A `guard_charter` placed after `guard_topology` (0.5) runs with
`params.bolt_worktree` pointing at the bolt branch's worktree, so the
append lands where the bolt's record lives. The alternative — writing
the charter inside `_expand_card` — was rejected for exactly that
ordering, and because expansion would then have two failure modes
(tracker and git) in one guard.

**The guard's test is the charter's COMMITTED content, not a stored
"expanded" flag and not the working tree.** The loop is stateless by
construction and re-derives what it can from the tracker and the tree
(`guard_stages` does the same for `stage:*`). So the guard compares the
`# Unit: <slug>` headings `bolt.md` carries at HEAD — read with
`git show HEAD:<path>`, falling back to the working tree only when HEAD
does not carry the path at all — against the `unit`-labeled issues on the
milestone, and writes only the missing ones. A second pass writes
nothing: the dry-cycle property every other guard has.

The requirement's clause is "SHALL be committed", and the working tree
cannot answer it. The section is on disk the moment the write returns, so
a guard testing the working tree would read a failed or interrupted
commit back as done, report a clean dry cycle forever, and never retry —
the one failure mode this content test was chosen to avoid. Against HEAD
a killed process genuinely leaves nothing to repair: the next pass finds
the section still uncommitted, skips the append because the working tree
already holds it, and re-runs the half that did not happen.

**Unit sections are appended after whatever the charter already holds.**
`merge_criteria()` takes the *first* `^## Merge criteria` in the file, so
appending unit documents (whose own subsections are `##`) after the
bolt-level sections keeps the bolt's criteria the ones the test reads.
Prepending would shadow them.

**The scaffold keeps its copy of the first unit's document.** Its work
order says "If the milestone's unit parent carries a plan document as
its body, copy it into `bolt.md` verbatim", which is ambiguous once a
milestone carries several; it is narrowed to name the unit it is copying
and the charter guard supplies the rest. Since the guard's test is the
heading, a document the scaffold already copied is not written twice.
Stripping the copy from the scaffold entirely was rejected: a bolt with
no unit cards at all (a quick bolt born at triage) still needs that
session to write a charter, and the fallback branch of the same order is
what does it.

**The defer predicate reads the blocker's work, not its close.** Under
bolt-of-units a blocking card is a sibling unit on the same milestone,
and its `closed:done` comes only after the landing — which waits on the
cards. So the predicate becomes: the blocker is closed, or it is a
`unit` whose every sub-issue is closed. An unexpanded blocker has no
sub-issues and is therefore not satisfied — the right answer, since its
work has not been born yet. Keeping `closed:done` was rejected as
provably deadlocking (proposal.md — Why); waiting on `stage:merged`
labels instead of closure was rejected because the merge closes the item
`closed:merged` in the same step, and closure is the fact both the
tracker and `guard_stages` already repair.

## Risks / Trade-offs

- **A blocker that is neither a unit nor a work item** (an ordinary
  issue someone linked as blocked-by) → it satisfies the predicate only
  by being closed, which is the conservative direction and matches
  today's behavior for everything except sibling units.
- **An unexpanded blocker that the operator never approves holds its
  dependent forever** → visible: the defer is recorded in the run record
  every pass, and the operator's approval or close releases it. This is
  the book's "deferral, never a refusal".
- **A hand-edited charter section** (someone rewrites a unit's section
  in git) → the guard sees the heading and leaves it alone; the card's
  body is not re-copied over an edited section. Durable prose in git
  wins over mutable tracker state, which is the direction the book
  states.
- **Two cards approved before the loop's first pass** → both expand in
  one pass and the scaffold session copies the lowest-numbered one's
  document; the other's section lands on the NEXT pass. `guards()` hands
  the same snapshot to `guard_expand` and `guard_charter`, so a card
  expanded at −1 is still `plan`-labeled in the snapshot the charter
  guard reads at 0.6 and is not yet a unit to it. That is a convergence,
  not a gap: expansion records an action, an action means the cycle is
  not the STOP condition, and the next cycle re-snapshots and appends.
  Order of sections follows expansion order, which is card number order.

## Migration Plan

No data migration. A bolt already mid-flight keeps its charter as it
stands: the guard adds only missing sections, and an existing
single-unit charter whose heading matches its unit is already complete.
A plan card filed before the planner owned the milestone carries no
`bolt/*` milestone and is no longer expandable by this guard. There is
none open at writing: the four open `plan` cards (#221–#224) all sit on
`bolt/matches-the-book` with `Unit: <slug>` titles, and the one expanded
unit card is #220.

The first bolt to exercise the new charter guard is this one: its
charter, `openspec/changes/matches-the-book/bolt.md`, opens
`# Unit: bolt-of-units`, so #220's section is already present and the
guard appends only what later approvals bring.
