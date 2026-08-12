# Decision: The work-object names

## Decision

The plugin's work objects carry these names — this list is the
enumeration to copy, stated here and nowhere else:

- the durable claim of what must be built, which a bolt's spec agents
  work from, is an **assertion**;
- the batch kind that releases construction work is a **unit**;
- the batch kind that authorizes design sessions on an intent is an
  **elaboration**.

No name carries two of these meanings. **Proposal** names exactly one
thing anywhere the flywheel reads or writes: OpenSpec's own `proposal.md`
artifact inside a change directory, which flywheel does not define and
does not touch. The word *unit* outside the batch kind is ordinary
English, never the claim.

## Context

- Map: none — this repo ships no context map; the surfaces standing in
  are listed in `../intent.md`.
- Produced by: `../sessions/2026-08-12-naming-call/work-object-naming.html`,
  the option page the operator worked; the operator's word landed in the
  page's annotation round and is recorded on item #13
  (<https://github.com/agentplot/flywheel/issues/13#issuecomment-5271266083>).
- Cost evidence: #18's blast-radius inventory, measured at tree
  `2e707e9`
  (<https://github.com/agentplot/flywheel/issues/18#issuecomment-5270769621>).
  Under these names every breaking identifier keeps its value — the
  `assertions` schema artifact id and its `assertions/**/*.md` record
  directory in consuming repos, the `type:assertion` label, the
  `flywheel-batch --kind unit|elaboration` values, the compose predicate
  in `bin/flywheel` — and the cost is prose: 253 `proposal` occurrences
  at `2e707e9`, 119 of them in `openspec/specs/**` including 13
  requirement/scenario heading keys. Re-measure before landing if the
  tree has moved.

## Consequences

- The landing pass: every surface in `../intent.md`'s Map moves to
  these names in one pass, driven from #18's identifier migration list,
  ordered code → labels → prose (`bin/flywheel-setup`'s `ensure_labels`
  is create-if-missing, so a tracker migrated ahead of the code regrows
  the old labels). The tracker half is two renames of never-applied
  `type:proposal-*` labels.
- What the pass may touch beyond plain prose is licensed separately in
  `landing-pass-licence.md`.
- The specs pass lands while zero `## MODIFIED Requirements` deltas
  exist in-tree (true at `2e707e9`), keeping the 13 heading-key edits
  text edits rather than migrations.
- Item #20 (whether the pass includes `add-flywheel-loops`' active
  deltas or sequences after its archive) now has its input: the claim
  word those deltas must end on is *assertion*.
- Adjacent defects this decision exposes but does not close stay on
  their own items: #23, #24, #26, #27.
