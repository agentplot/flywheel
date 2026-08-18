# Decision: records follow the book, and every design write rides the gate

## Decision

An intent's records live beside its book:
`openspec/changes/intent-<slug>/` in the repo that holds the book —
for the flywheel's own intents, `agentplot/blueprints`. The intent
loop cuts each design session's worktree from the **book repo** named
in `fleet.yaml`, not from the fleet's built repo, so the session's
records and its chapter rewrites ride one `sess/*` branch through one
merge gate. There is one write path: nothing a design session
produces reaches any main directly. The `lifecycles.md` claim that the
record "is written onto the book repo's main as the sessions work"
falls; the record waits on the branch exactly as long as the session
runs, and the merge at settle is what makes it live. The
`design-loop.md` escape — queue an item for a chapter in a repo the
session holds no worktree for — survives only as the different-book
remainder (another intent's book, another fleet's), never as the
normal path for the intent's own book. The directory name is
`intent-<slug>`, mirroring the milestone; the machinery's bare-slug
scaffold is the defect. Existing flywheel intents filed in
`agentplot/flywheel` are a known anomaly, migrated per-intent as each
is next touched or at milestone close, never by a big-bang move.

## Context

- Raised by #322, from the writeback of #320, which had to push
  chapters straight to `agentplot/blueprints@main` under ordinary git
  credentials because no `sess/*` branch of the flywheel repo could
  carry them.
- Chapter: the flywheel book at `agentplot/blueprints` —
  `lifecycles.md` *The intent's change directory* and `design-loop.md`
  *The close writes the destination* (write queued — see Consequences;
  this session's worktree is of the flywheel repo, the exact shape the
  decision retires).
- Produced by:
  sessions/2026-08-18-records-home/records-home-draft.md, annotated by
  the operator 2026-08-18 (one annotation: "Looks good" on Option A —
  records follow the book; no objection to the coupled write-path and
  naming calls).

## Consequences

- Assertion: the intent loop worktrees the book repo named in
  `fleet.yaml` for design sessions — `repo_dir` splits into the
  fleet repo (tracker-side operations) and the book repo (worktrees,
  records, merges).
- Assertion: the loop's scaffold and work-order prompt say
  `openspec/changes/intent-<slug>/`.
- Writeback item: rewrite `lifecycles.md` *The intent's change
  directory* (drop the straight-to-main sentence, state the branch-and-
  gate path) and reword `design-loop.md`'s escape clause to the
  different-book remainder — beyond this session's worktree.
- Migration item: move the flywheel intents' records from
  `agentplot/flywheel` to `agentplot/blueprints` under `intent-<slug>`
  names, per-intent as touched.
