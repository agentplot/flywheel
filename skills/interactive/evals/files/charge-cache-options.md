# Charge — intent `geo-iq-boundaries`, batch 4

- Change: `openspec/changes/geo-iq-boundaries/`
- Session type: **interactive design**
- Session directory: `sessions/2026-08-12-cache-options/`
- Your conductor: herdr agent `intent-geo-iq-boundaries`, running in pane 2

## Task lines this batch works

- [ ] 3.1 Design: close `decisions/tile-cache-topology` — three candidate
      topologies, and the operator has to see the latency and cost
      trade-offs side by side.
- [ ] 3.2 Design: close `decisions/cache-invalidation-channel` — push vs
      poll vs TTL.
- [ ] 3.3 Design: close `decisions/cache-ownership-boundary` — which
      context owns the cache, with the map nodes it moves.

Map nodes in play: `geo-iq-tile-cache`, `atlas-kit-gateway`.
Chapters in play: `books/geoiq/src/tiles.md`, `books/atlas-kit/src/gateway.md`.
