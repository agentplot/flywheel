## Why

The book makes `bolt.md` the bolt's charter and nothing else. Each
`bolt-*` schema carries **two** artifact types: `bolt`, generating
`bolt.md` — "the charter: the delivery statement, the unit sequence and
price, the merge criteria the landing verifies — born at scaffold from
the milestone's description, the planner's summary or the operator's
dictated words" — and `unit`, generating `units/<slug>.md` — "one
approved unit's document, verbatim — written by the loop at expansion,
the moment board approval freezes the card body"
(`books/flywheel/src/schemas.md`, "The bolt schemas and the loop block").
"The record mirrors the board one-to-one: one charter per bolt, one unit
file per approved card."

`books/flywheel/src/bolt-planning.md` says the same from the planner's
side: approval "freezes it, and expansion copies it verbatim into the
record as the unit's own artifact, `units/<slug>.md` on the bolt branch —
durable prose in git, one file per approved unit. The charter, `bolt.md`,
carries the bolt-level statement instead: the delivery, the unit sequence
and price, the merge criteria — born at scaffold from the milestone's
description." `books/flywheel/src/lifecycles.md` names the change as "the
charter `bolt.md` plus one `units/<slug>.md` per approved unit", born
"the charter at scaffold, from the milestone's description; each unit
artifact at its expansion, frozen by the approval".

The tree does neither. `schemas/bolt-default/schema.yaml` — and its three
siblings — declare one artifact, `bolt`, and no `unit`. Its `bolt`
instruction demands "EXACTLY these four sections, and nothing else" and
then contradicts itself in the next paragraph: "What follows those four
sections … one `# Unit: <slug>` section per unit expanded on this bolt's
milestone … You copy the lowest-numbered unit's document when you
scaffold; the loop appends every later one as each approval expands."
`guard_scaffold` in `bin/_flywheel_bolt_loop.py` orders exactly that, and
`guard_charter` appends the rest into the same file.

The result is that no planner-born bolt has a charter at all. Both such
charters in this tree — `openspec/changes/loop-boundaries/bolt.md` and
`openspec/changes/archive/2026-08-17-matches-the-book/bolt.md` — open at
`# Unit: <slug>` and carry no `## Scope`, `## Sources`, `## Repos` or
`## Merge criteria`. Run the loop's own two readers over them and both
come back empty-handed: `merge_criteria()` returns `""`, and
`landing_mode()` searches that empty string and falls through to its
`merge` default — so a bolt that meant to land by pull request lands
straight onto main, and a defaulted mode is indistinguishable from a
declared one. The landing session is told to "VERIFY every one of its
Merge criteria … by running them" and is handed nothing to run.

The description the planner authored — the delivery, the unit sequence,
the price, which the book names three times as the charter's source — is
read once by `bin/flywheel-bolt-loop` for the plan-mode flag and never
reaches the session that writes the charter.

`bolt/matches-the-book` is merged and waiting to land through this path.

## What Changes

- **`bolt.md` is the charter and only the charter.** Its four sections —
  scope, sources, repos, merge criteria with the `Landing:` line — are
  written at scaffold from the bolt milestone's description. No unit's
  plan document is written into it, ever.
- **Each approved unit's document becomes `units/<slug>.md`**, written
  verbatim by the loop at that unit's expansion, one file per approved
  card, committed on the branch that carries the bolt's record. This is
  where the durable prose that used to be appended into `bolt.md` now
  lives.
- **The `bolt-*` schemas declare both artifacts.** `bolt` keeps
  `bolt.md`; a new `unit` artifact generates `units/<slug>.md`. The
  `bolt` artifact instruction stops at "exactly these four sections, and
  nothing else" and drops the paragraph that told the scaffold session to
  append a unit's document beneath them.
- **The milestone description reaches the scaffold session.** It is
  already read by `bin/flywheel-bolt-loop`; it is carried to the work
  order as the charter's stated source rather than dropped after the
  plan-mode flag.
- **The scaffold guard checks the charter it got back.** Settling is no
  longer the whole test: the guard reads `bolt.md` through the same
  reader the landing uses and fails with a reason naming what is missing.
- **The merge criteria are read from the charter's own region.** A
  `# Unit:` section left in an existing `bolt.md` by the old shape can
  never supply this bolt's criteria: the reader stops at the first such
  heading.
- **A landing refuses an unreadable charter.** No bolt-level merge
  criteria, or an empty section, and the landing fails ahead of any
  landing session — nothing verified, nothing on main, nothing closed or
  upgraded. Verifying an empty criteria list is not a green landing.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `flywheel-derived-backlog`: the requirement that the charter carries
  every expanded unit's plan is removed and replaced by the two the book
  now states — the charter is the bolt's own statement, and each approved
  unit's document is its own artifact.
- `flywheel-schema-instructions`: the `bolt-*` schemas gain a stated
  contract — two declared artifacts, and a `bolt` instruction that stops
  at the four sections.
- `flywheel-construction-stages`: the landing's preconditions gain one —
  a charter whose merge criteria cannot be read is not landable.

## Impact

- `schemas/bolt-default/schema.yaml`, `schemas/bolt-quick/schema.yaml`,
  `schemas/bolt-adversarial/schema.yaml`, `schemas/bolt-direct/schema.yaml`
  — the artifact list and the `bolt` instruction's self-contradicting
  paragraph.
- `schemas/*/templates/bolt.md` — read as the authority for the four
  section headings, and **not edited**: the template already names them
  and nothing else, which is exactly the shape the book asks for.
- `bin/_flywheel_bolt_loop.py` — `guard_scaffold`'s work order and its
  post-settle check; `guard_charter`, which appends `# Unit:` sections
  into `bolt.md` and must instead write one file per unit;
  `UNIT_HEADING`, whose only job is that append; `merge_criteria()`,
  whose `^#{1,2}\s` lookahead exists to survive those headings;
  `BoltParams`, which carries no milestone description; `land_stage`,
  which reads the criteria only through `landing_mode()` and never asks
  whether there were any.
- `bin/flywheel-bolt-loop` — `build_loop` already reads the milestone's
  `description`; it passes it on.
- `tests/test_bolt_loop.py` — the charter tests assert the append-into-
  `bolt.md` shape, and `LandingTest.program` stubs `merge_criteria` on
  every landing test, so no test reaches the real reader from
  `land_stage`.
- **Existing records are not rewritten in place.** The two `bolt.md`
  files already carrying a `# Unit:` section keep it: a guard that
  rewrote committed prose would contradict the rule that durable prose in
  git outranks the tracker state it came from. They are made harmless
  instead — the stale section cannot supply merge criteria, and the unit
  artifact each is missing is written by the same guard that writes every
  other one, because its test is whether `units/<slug>.md` exists. The
  charter half is the operator's one-file edit, and until it is made the
  landing refuses with the reason.
- **Out of scope**: a change directory that exists without a `bolt.md`,
  and a unit title that parses no slug. Both are siblings in this unit
  (`a-charterless-change-directory-gets-one`,
  `an-unparseable-unit-title-says-so`) and both build on the record shape
  this change defines.
