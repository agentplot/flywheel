# `plannotator annotate` result

Round on: `sessions/2026-08-11-boundary-drafts/tile-cache-owner.md`
Returned to: this session
Status: complete, 3 annotations

---

**Annotation 1** — on "the tile cache is owned by Geo IQ"

> Yes. Geo IQ owns it. Say so plainly and drop the hedge in the next
> sentence.

**Annotation 2** — on "eviction policy: LRU"

> LRU is wrong for this — the access pattern is seasonal, not recent.
> Make it TTL-with-refresh and say why.

**Annotation 3** — on the Consequences list

> This raises something the batch doesn't cover: if Geo IQ owns the cache
> then the atlas-kit gateway is calling across a boundary it doesn't
> declare today. Somebody needs to design that seam — what the contract is,
> who publishes it, whether it's synchronous. That's a whole piece of work,
> not a line in this draft.

---

Batch 3's task lines are 2.4 (close `decisions/tile-cache-owner`) and 2.5.
Nothing in the batch covers the atlas-kit / Geo IQ seam.
