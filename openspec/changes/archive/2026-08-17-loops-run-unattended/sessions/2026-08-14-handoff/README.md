# Session — handoff, loops-run-unattended, 2026-08-14

**Type**: handoff · **Item**: #141 · **Branch**:
`sess/handoff-loops-run-unattended`

## What was charged and what happened

Item #141 named one assertion — `#140` — in its `flywheel:handoff-set`
block. #140 is closed `closed:done`, fixed and shipped before this
session was dispatched. The batch therefore has **nothing to hand off**:
no bolt cut, no milestone created, no item relabelled, no sequencing
wired. `bolt-plan.md` beside this file is the plan in that state, with
the held-back entry and its evidence.

## What was verified, and how

- **#140 is done, in the tree — not on its comment's word.** The
  failure mode it reports cannot recur, because the deliverable
  contract no longer asks about comments at all:
  `BoltLoop.deliverables` (`bin/_flywheel_bolt_loop.py:1057`) checks
  that the change validates and that `build/<slug>` carries a commit,
  and its docstring moves the tracker comment to the loop. The window
  defect itself is fixed either way: `launch_origin` (`:1090`) reads
  the durable `flywheel:session` marker off the item, and
  `reprompt_deliverables` (`:1672`) writes a marker comment so a
  restarted process pauses rather than re-prompting a second time.
  Commit `489ec46`, shipped 0.10.10.
- **The set is empty, not merely stale.** No other open item on
  `intent/loops-run-unattended` was in it: the milestone's open
  `type:assertion` items are #202 and #203, both created after this
  handoff was born and both outside its sealed set.
- **The handoff is sealed.** #141's parent batch #109 is at board
  Status **Ready**, so invariant 6's amend branch cannot extend it.

## What was queued

- **#203** — *A handoff item outlives its set: an emptied handoff still
  charges a design session.* The defect this session is itself the
  trace of: `handoff_plan` freezes the settled set into the item body
  at birth, nothing re-derives it at dispatch, and the amend branch
  that would shrink a stale set is disabled by `if not settled: return
  None` — the exact case that needs it. Two candidate fixes stated,
  neither chosen. `type:assertion`, `state:queued`, no parent batch —
  so the next handoff wave names it.

## Held for the operator

- **#202** — *type:build on an intent milestone is a dead end* — is a
  settled unbolted assertion on this milestone right now, and is **not**
  this handoff's to release: it arrived two minutes after this session
  was dispatched, into a sealed batch. The intent loop's birth branch
  will produce the next handoff naming it (and now #203).
- **This session's directory created a change shell.**
  `openspec/changes/loops-run-unattended/` did not exist — this intent
  has a milestone and no openspec change — so writing the session
  directory the work order names created a change with no `proposal.md`.
  It now appears in `openspec list` as `loops-run-unattended  No tasks`,
  and `openspec validate loops-run-unattended --strict` fails for having
  no deltas. The merge gate does not run `openspec validate` (its three
  `[pre-merge]` hooks are `manifests`, `paths`, `site`), so nothing is
  blocked by it. Who scaffolds a missing change is the open question on
  **#87** — *Does the intent loop need guard 0, the scaffold-if-missing?*
  — and this session did not answer it by writing a proposal it was not
  charged to write.

## Why no plannotator round

The round in the handoff skill exists to approve a custody move. There
are zero bolts to approve here, and one blocking round asking the
operator to approve "no bolts" spends the attention the round is for.
The findings above are in the report instead. If the operator wants the
round anyway, the plan is on disk and unchanged.
