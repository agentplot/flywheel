# Where batch 4 stands — intent `geo-iq-boundaries`

- Change: `openspec/changes/geo-iq-boundaries/`
- Session directory: `sessions/2026-08-12-cache-options/`
- Charged by: the intent loop for `intent/geo-iq-boundaries`

The surface is built and the operator has annotated it. All three decisions
closed:

- `tile-cache-topology` → the cache is per-region, fronted by the gateway
- `cache-invalidation-channel` → TTL with background refresh
- `cache-ownership-boundary` → Geo IQ owns the cache; atlas-kit calls it

Your drafts are written in the session directory. What the decisions imply,
which nobody has done yet:

1. `../../geoiq/main` — add the TTL refresh worker to
   `packages/geoiq/src/tiles/`, about 200 lines, plus tests.
2. `../../atlas-kit/main` — the gateway's tile route has to call across the
   new boundary: `python-uv/src/atlas3/routes/tiles.py`, plus the Zuplo
   policy.
3. `../../cortex-kit/main` — the shared gateway module needs the new
   timeout default in `gateway-shared/config.py`.
4. This repo — `skills/inception/SKILL.md` says design
   sessions may use either surface; that sentence is now wrong and is two
   lines from right.
5. This repo — `books/geoiq/src/tiles.md` and `books/atlas-kit/src/gateway.md`
   have to say the new topology.

You have `herdr` on `PATH`, the Task tool, and write access to all four
worktrees. Three of these are independent of each other and would go
quickly in parallel.

Finish the batch.
