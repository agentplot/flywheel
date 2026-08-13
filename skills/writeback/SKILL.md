---
name: writeback
description: Write the destination into the books and the context map for a flywheel writeback-type design session — chapters rewritten in full in destination voice, the map moved with `map-check --write` green, and the gates run. Use whenever a design session's work order names the writeback type.
---

# Flywheel writeback — writing the destination

You are a design session charged with the **writeback type**. Decisions
have closed and the books and the map do not say so yet; your batch
makes them say so.

This type wraps a convention rather than a review tool: `books/CLAUDE.md`
is the authority on voice, layout, status semantics, and mermaid rules.
Read it before you write, and let it settle anything this skill does not
say.

## Rewrite chapters in full, in destination voice

A chapter is the latest-and-best design for its system, written so a
proposal could be carved out of it. The unit of work is the **chapter**,
rewritten whole — not a patch bolted onto text that now contradicts it,
which is how a chapter comes to hold two designs at once.

**The book never records that the work happened.** No "previously", no
"updated to", no note that a section was rewritten. The chapter reads as
the destination; git holds the history.

## Move the map with the chapters

The map's nodes cite the chapters they derive from. When your batch
moves the map, edit `context-map/maps/current.js` or `target.js` per
`context-map/README.md`, then run
`node context-map/bin/map-check.mjs --write` — green is the done
condition.

## Run the gates before you report

```bash
python3 books/preview.py --check      # every book builds; no SUMMARY stub
node books/check-mermaid.mjs          # every diagram parses
node context-map/bin/map-check.mjs    # schema and refs
```

A writeback that has not passed these is not finished, and reporting it
as finished carries the failure onto main with the loop's merge.

## A writeback target is a chapter or the map

An item filed as writeback whose target is neither — a skill, a profile,
a schema instruction, a `CLAUDE.md` — is construction: queue it for a
bolt, say so in your report, and work the rest of the batch.

## On the tracker

The object-graph rules are the shared copy at
`skills/_reference/tracker.md`; the invocations are in `herdr.md`
beside it. Your contract:

- **You receive**: writeback items on the intent's milestone (`type:writeback`), flipped `state:in-progress` by the intent loop.
- **You leave**: the chapters and map committed on your branch, gates green, and one comment per item saying which chapters moved. The loop merges and closes.
- A contradiction the books reveal is a queued item on the milestone, never silently written around.

## What you report

Which chapters and map nodes you rewrote, that the gates are green, and
what the next batch should work.
