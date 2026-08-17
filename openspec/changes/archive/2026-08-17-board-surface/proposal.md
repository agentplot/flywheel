# Board surface

## Why

Bolt 1 of the approved 2026-08-17 plan
(`design/plans/2026-08-17/01-board-surface.md`). The next bolt's two
behaviors — the planner setting a plan card's Team, and expansion
refusing a card without one — need the board surface the book's
tracker protocol describes
(`books/flywheel/src/tracker-protocol.md` in willdan-blueprints).
Fields and the view-template copy already exist in `flywheel-setup`;
the gaps are the `plan` batch label and a stale clause in
`stage:planned`'s description.

## What Changes

- `plan` joins the label table `flywheel-setup` converges, beside
  `unit` and `elaboration`: one proposed bolt awaiting approval, the
  plan document as the card body.
- `stage:planned`'s description drops "or its plan is approved" — the
  book defines the stage as "the item's spec validates", and the
  plan-approval clause described machinery that no longer exists.
- The existing convergence — Status/Team/Quarter/Start/Target fields,
  the template-copied views — is pinned as the
  `flywheel-board-surface` capability so later bolts change it by
  spec, not by drift.

## Impact

- Affected specs: `flywheel-board-surface` (new)
- Affected code: `bin/flywheel-setup` (label table), tests
