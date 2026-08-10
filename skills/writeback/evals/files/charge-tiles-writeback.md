# Charge — intent `geo-iq-boundaries`, batch 6

- Change: `openspec/changes/geo-iq-boundaries/`
- Session type: **writeback**
- Session directory: `sessions/2026-08-15-tiles-writeback/`
- Your conductor: herdr agent `intent-geo-iq-boundaries`, running in pane 2

## Task lines this batch works

- [ ] 5.1 Writeback: `books/geoiq/src/tiles.md` for the three cache
      decisions. The current chapter is attached.
- [ ] 5.2 Writeback: the map — node `geo-iq-tile-cache` moves from
      `candidate` to `settled`, and its `ref` moves to
      `books/geoiq/src/tiles.md`.

## The closed decisions this writes back

- `decisions/tile-cache-topology` — the cache is **per-region**, one per
  serving region, fronted by the gateway. There is no shared cache.
- `decisions/cache-invalidation-channel` — **TTL with background refresh**,
  600 s for raster and 3600 s for vector. No purge channel.
- `decisions/cache-ownership-boundary` — **Geo IQ owns the cache**, all of
  it: writes, eviction, and the TTL policy. atlas-kit's gateway is a caller
  across a declared boundary.

The record of how these were argued is in `decisions/` and in
`sessions/2026-08-12-cache-options/`. The operator has already read it.
