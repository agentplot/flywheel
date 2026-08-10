# Decision: the widget split lands after the two runs

## Decision
The widget kit does not split out of the monorepo until both end-to-end
runs have finished. The runs are what tell us which seams are real, and a
split taken before them would harden the wrong ones.

## Context
- Map: `widget-kit`
- Chapter: `books/widget-design/src/kit-boundaries.md`
- Produced by: the operator's word, given directly.
- Measured at the time of writing: two of the three repo gates fail on the
  split branch — `books/preview.py --check` exits 2 on a missing sidecar,
  and `context-map/bin/map-check.mjs` exits 1 on an unresolved `ref`. The
  mermaid check passes.

## Consequences
- The split is not proposed as a handoff until the runs report.
- The two failing gates are the split's entry criteria: they go green
  before the handoff is drafted, not after.
