# Tile serving

Geo IQ serves map tiles to the portal and to atlas-kit's gateway.

## History

Tile serving started as a single origin behind CloudFront, which was the
right call when there was one region. In April we added a second region and
the origin became the bottleneck, so we introduced a shared cache. That
shared cache is now itself the bottleneck, and the design below replaces
it.

## The cache

**Note (2026-06):** the paragraph below still describes the shared cache.
It has not been updated for the per-region decision yet.

A single shared cache sits in front of the origin, owned jointly by Geo IQ
and atlas-kit. Both write to it; neither owns eviction. Entries are evicted
LRU at 40 GB.

Ownership was left deliberately ambiguous because we could not agree, and
we decided against making Geo IQ the owner at the time — atlas-kit's team
argued the gateway was closer to the read path. That argument no longer
holds now that the gateway calls across a context boundary anyway.

## Invalidation

Invalidation is push-based: the tile builder posts a purge to the cache
when a tile is rebuilt. This is fragile — a dropped purge serves a stale
tile indefinitely — and we have talked about moving to TTL several times.

## What is served

Raster tiles at z0–z14, vector tiles at z8–z18. Region boundary tiles are
served from the same path as interior tiles.
