# Assertion: The settled specs speak the settled vocabulary

- **Repo:** agentplot/flywheel
- **Item:** #32
- **Raised by:** `sessions/2026-08-12-naming-call/` — the operator's call
  on #13, carved into the landing pass by the conductor's fold.

## The claim

`openspec/specs/**` carries the settled names. When this is built, the
119 claim-sense `proposal` occurrences across eight spec files at
`2e707e9` — re-measure before landing — read **assertion**, including
the 13 requirement/scenario heading keys (5 of them `### Requirement:`
headings, OpenSpec's identity key) renamed consistently in the heading
and in every cross-reference to it, and the ~30 fused compounds
(`one-proposal bolt`, `single-proposal handoff`) recast as their
assertion forms rather than word-swapped. The 4 `assertion` uses and
the incidental-English hits #18 classifies INC are untouched. After the
pass, a claim-sense grep for `proposal` over `openspec/specs/**` at the
landed tree returns nothing.

## Why

`decisions/work-object-names.md` settles the names and records why this
lands now: zero `## MODIFIED Requirements` deltas exist in-tree at
`2e707e9`, so the heading-key renames are text edits while that window
is open. The file-by-file counts, heading list and fused-compound sites
are #18's inventory at `2e707e9`
(<https://github.com/agentplot/flywheel/issues/18#issuecomment-5270769621>).

## Boundaries

Identifiers — labels, directories, `bin/` strings — are #30; prose
outside `openspec/specs/**` is #31. Whether this claim also covers the
four active `## ADDED Requirements` deltas in
`openspec/changes/add-flywheel-loops/` (16 `proposal` occurrences at
`2e707e9`, of which six describe retiring a book's `src/proposals.md`
chapter — a file, not the work object — and must not be word-swapped)
is #20's decision: until #20 settles, this claim's coverage is
`openspec/specs/**` alone, and the deltas that would become settled
specs on archive sit outside it. The `proposals.md` registry the specs
still describe names an artifact no shipped schema declares; retiring
that object is #26, not this pass — here its sentences change words
only where the claim word appears.
