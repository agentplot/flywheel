# Intent: work-object-vocabulary

## Destination

The plugin names each of its work objects exactly once, and every surface
uses that name. A reader who moves from the landing page to the README to
a skill to a schema instruction to a tracker label meets the same word for
the same thing, and never meets one word carrying two meanings.

Two distinct objects are separately named and never conflated: the durable
claim of what must be built — the thing a bolt's spec agents work from —
and the batch kind that releases such claims for construction. Today both
can be read as "unit": `site/index.html` says *"Units become bolts"*
(the hero's walkthrough), while 8b8a1a3 made `unit` the name of a batch
kind. Whichever names win, the destination is that those two sentences
cannot both be true of one word.

The settled names live in `decisions/` under this change, and every
consumer cites that record rather than restating the call. The surfaces
carry the names: the site, the README, the skills — including the skill
directory names, which are the slash commands (`/flywheel:proposal-writing`,
`/flywheel:proposal-review`) — the agent profiles, the schemas'
`instruction` text, this repo's own `openspec/specs/`, and the tracker's
label objects. Nothing in the repo reads as a survivor of an earlier
vocabulary.

This repo ships no book and no context map today, so there is no chapter
to cite and none to write against; `openspec/specs/` is the settled prose
this intent must leave coherent, and the landing page is the public face
of it.

## Map

No `system-context-map.html` exists in this repo — the map is a thing the
flywheel schemas ask consuming repos for, and agentplot/flywheel has not
built its own. The surfaces this intent moves, standing in for map nodes:

- `site/index.html` — public landing page — **settled design, unsettled words**: the hero study is ruled settled (#12); its copy says *units* and *bolts*, its body prose says *proposals*
- `README.md` — **candidate** — says *proposals*
- `skills/*/SKILL.md` + skill directory names — **candidate** — say *assertions*; two directory names say *proposal*
- `schemas/*/schema.yaml` instruction text — **candidate** — `flywheel-intent` says *assertions*, *units*, *elaborations*; the three bolt schemas say *assertions* and *proposals*
- `agents/*.md` — **candidate** — mixed
- `openspec/specs/**` — **open** — this repo's own settled specs still say *proposals* throughout (119 uses across eight spec files at 2e707e9, per #18's inventory), including the specs of the very skills that were renamed to *assertion*
- the tracker's labels — `type:assertion`, and `flywheel-batch --kind unit|elaboration` — **open** — live label objects with issues attached, including closed #12

## Scope

**In scope.** Settling the names of the loops' work objects and batch
kinds, and landing the settled names across every surface listed in Map in
one pass — text edits in the repo, and label operations on the tracker with
live issues re-tagged. The `openspec/specs/` drift is in scope: leaving the
specs on an older vocabulary than the skills they spec is the same defect
one layer down.

**Out of scope.**

- The hero study's *design* — settled per #12, and this intent does not reopen it. If the settled names require touching hero copy, that is a decision to put to the operator, not a licence this intent already holds.
- The behaviour of either loop. This intent renames; it changes no mechanic, no state machine, no session type's job.
- The AI-DLC source vocabulary itself, which is input to the decision rather than subject of it.
- Other repos' bound changes and their own records. Consuming repos follow the schemas they install; migrating anyone else's tracker is not this intent's work.
- `intent/gated-merge-guarantee` (#14). Filed the same day, also machinery, unrelated subject; neither gates the other.
