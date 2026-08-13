# Charge — intent `geo-iq-boundaries`, batch 5

- Change: `openspec/changes/geo-iq-boundaries/`
- Session type: **prototype**
- Session directory: `sessions/2026-08-13-tile-prefetch/`
- Charged by: the intent loop for `intent/geo-iq-boundaries`

## Task lines this batch works

- [ ] 3.4 Design (prototype): `decisions/tile-prefetch` turns on whether
      speculative prefetch on the region boundary can hold p99 under 400 ms
      with the tile sizes we actually have. Prove it or disprove it.
- [ ] 3.5 Design: the operator wants to look at what the prototype proved
      before the decision closes.

## Where the run got to

The throwaway is built and measured, in the spike repo:

- worktree: `../../knowledgebase-spike/main` on branch `spike/tile-prefetch`
- ~300 lines under `poc/tile-prefetch/`, plus a load script

Measured, over the real tile size distribution:

| tiles prefetched | p50 | p99 | wasted bytes |
|---|---|---|---|
| 0 (control) | 120 ms | 610 ms | 0 |
| 4 | 118 ms | 585 ms | 41% |
| 16 | 115 ms | 560 ms | 73% |

p99 does not get near 400 ms at any prefetch depth. The tail is dominated
by cold-origin fetches, which prefetch does not touch — it makes the same
cold fetch happen earlier, not faster.
