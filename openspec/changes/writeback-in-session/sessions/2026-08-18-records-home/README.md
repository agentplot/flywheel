# Session: records-home (planning, 2026-08-18)

Worked item #322 on `intent/writeback-in-session`: settle where an
intent's records live and how the write lands when the book is in
another repo, plus the `intent-<slug>` naming discrepancy.

## Deliverables

- `records-home-draft.md` — the decision draft the plannotator round
  ran on: records follow the book (loop worktrees the book repo), one
  write path (`sess/*` through the gate, the straight-to-main sentence
  in `lifecycles.md` falls), `intent-<slug>` stands and the machinery
  is fixed.

## Round outcome

One annotation, 2026-08-18: "Looks good" on Option A — records follow
the book, the loop worktrees the book repo. No corrections to fold; no
objection to the coupled write-path and naming calls. Closed as
`decisions/records-follow-the-book.md`.

## Queued from the close

- Assertion: loop worktrees the book repo (`fleet.yaml`'s book entry).
- Assertion: scaffold and work-order prompt say `intent-<slug>`.
- Writeback: `lifecycles.md` and `design-loop.md` rewrites (beyond
  this session's worktree — it is of the flywheel repo, the shape the
  decision retires).
- Migration: flywheel intents' records move to `agentplot/blueprints`
  per-intent as touched.
