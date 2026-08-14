# Bolt plan — loops-run-unattended handoff, 2026-08-14

**No bolt is cut by this handoff.** The set item #141 names is `#140`,
and #140 is closed `closed:done` with its fix on `main`. A handoff
whose whole set has landed has no assertion to move and no bolt to
plan, so this plan carries no bolt section — only the held-back entry
that says why, and the wave that comes next.

Custody moved: **nothing**. No milestone was created, no item was
relabelled, no sequencing was wired.

## Held back

- **#140** — *A build session that commented before the re-prompt is
  judged silent, and re-prompted forever* — not held back for a reason
  that can be resolved: it is **already done**. Closed `closed:done` at
  2026-08-13T19:42:44Z, four seconds after #141 was born naming it. It
  was fixed inline by the build session that found it, on
  `bolt/stage-labels`, at `489ec46` (*"fix(loop): the deliverable window
  and the one-re-prompt rule survive restarts"*), shipped in 0.10.10.

  Verified in the tree rather than taken from the comment: the failure
  mode cannot recur, because the deliverable contract no longer asks
  about comments at all. `BoltLoop.deliverables`
  (`bin/_flywheel_bolt_loop.py:1057`) now checks two objective facts —
  the change validates, and `build/<slug>` carries a commit — and its
  docstring says the tracker comment "is the LOOP's to write now". The
  re-prompt window that started at the re-prompt is gone with it:
  `launch_origin` (`:1090`) reads the durable `flywheel:session` marker
  off the item, and `reprompt_deliverables` (`:1672`) writes a marker
  comment so a restarted process sees its predecessor's re-prompt and
  pauses instead of re-prompting again.

  Nothing to move, nothing to queue back.

## The next wave, not this one

`#202` — *type:build on an intent milestone is a dead end: no loop
dispatches it, no guard bolts it* — is open on
`intent/loops-run-unattended`, `type:assertion`, no parent batch, no
open blockers. It is a settled unbolted assertion **right now**, and it
is not in this handoff's set: it was created at 2026-08-14T21:41:50Z,
two minutes after this session was dispatched, and this handoff is
sealed — invariant 6 amends a handoff only while its batch sits at
Backlog, and #141's parent #109 is at board Status **Ready**.

So #202 belongs to the next handoff, which the intent loop's birth
branch will produce on its next cycle. Releasing it here would be this
session taking the operator's word for itself; it is named here so the
next wave is expected rather than surprising.
