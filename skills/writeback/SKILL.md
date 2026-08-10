---
name: writeback
description: Write the destination into the books and the context map for a flywheel writeback-type design session — chapters rewritten in full in destination voice, the map moved with `map-check --write` green, and the gates run. Use whenever a design session's work order names the writeback type or names book-chapter rewrites and map updates; also use when a session needs to know whether a writeback batch waits on an approval.
---

# Flywheel writeback — writing the destination

You are a design session charged with the **writeback type**, running under
`flywheel-design-session`. Decisions have closed somewhere — on a lavish page,
in a round, in a sentence the operator gave a conductor — and the books and
the map do not say so yet. Your batch makes them say so.

This type wraps a convention rather than a review tool. `books/CLAUDE.md`
is the authority on voice, layout, status semantics, and mermaid rules;
read it before you write, and let it settle anything this skill does not
say. The loop practice is in `flywheel:inception`, which your profile
already sent you to.

## Rewrite chapters in full, in destination voice

A chapter is the latest-and-best design for its system, written so a
proposal could be carved out of it. So the unit of work is the **chapter**,
rewritten whole — not a patch bolted onto text that now contradicts it. A
partial edit is how a chapter comes to hold two designs at once, and the
next reader cannot tell which one is current.

**The book never records that the work happened.** No "previously", no
"updated to", no "we decided against", no note that a section was
rewritten. The chapter reads as the destination: what is true when this
system is built. Git holds the history and that is where history goes.

## Move the map with the chapters

The context map's nodes cite the chapters they derive from, so a chapter
that moves and a map that does not have gone out of agreement. When your
batch moves the map, edit `context-map/maps/current.js` or
`target.js` per `context-map/README.md`, then:

```bash
node context-map/bin/map-check.mjs --write
```

Green — schema valid, every `ref` resolving to a chapter on disk,
`verifiedFiles` regenerated — is the done condition, not an optional check.

## Run the gates before you report

```bash
python3 books/preview.py --check      # every book builds; no SUMMARY stub; sidecars present
node books/check-mermaid.mjs          # every diagram parses
node context-map/bin/map-check.mjs    # schema and refs
```

A writeback that has not passed these is not finished, and reporting it as
finished puts the failure on your conductor's merge.

## There is no approval step here

The operator's approval belongs to Handoff tasks and to nothing else. Writeback is
your conductor's own scope — books and the map — so you were spawned and
you proceed on your work order; there is no release to seek and nothing to wait
for. If you find yourself pausing for the operator to confirm you should
start work you were already charged with, that is the malfunction, not
caution. The gate authorizes release; it is not a meeting, a status report,
or a reason to stop.

## When a target is not a book chapter or the map

Refuse it as construction and report it for a handoff. A skill file, an
agent profile, a schema instruction, a `CLAUDE.md` — those are machinery,
in blueprints as much as anywhere else, and a task line filing one under
Writeback does not make it one.

The rule that says so is not this skill's. It is stated in
`flywheel:inception` and in the conductor profiles, where a task gets
filed, and in your own profile, which you read before this. Read it there;
what this skill tells you is what to do when your batch hands you one —
refuse, name the target, report it, and work the rest of the batch.

## Your type opens no round

You rewrite chapters and your conductor promotes them. You put nothing in
front of the operator for annotation; only the planning type opens a round.

## The type comes from your work order

Your work order names the type and you load this skill because of it. You do
not pick your own type. If your work order names none, ask your conductor. If
mid-batch the batch turns out to need a different type, report that as the
next batch's type rather than switching inside your own run.

## What you report

Which chapters and map nodes you rewrote, that the gates are green, which
tasks your conductor should check or append, anything refused as a handoff,
and what the next batch should work. You append nothing to `tasks.md` and
check nothing off.
