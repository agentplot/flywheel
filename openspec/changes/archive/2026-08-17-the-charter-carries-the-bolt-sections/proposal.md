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

The tree splits the difference, and lands on neither. A build session has
already made the charter half of this true: `BoltParams` now carries the
milestone description, `guard_scaffold`'s work order names
`CHARTER_SECTIONS` — `## Scope`, `## Sources`, `## Repos`,
`## Merge criteria` — and asks for the `Landing:` line stated under every
schema, the guard checks the settled charter through `merge_criteria()`
rather than trusting the settle, and `land_stage` carries a third refusal
for a charter that states no criteria.

What none of that touched is the record's shape.
`schemas/bolt-default/schema.yaml` — and its three siblings — still
declare one artifact, `bolt`, and no `unit`. Each still says "EXACTLY
these four sections, and nothing else" and then contradicts itself in the
next paragraph: "What follows those four sections is not narrative and is
not yours to compose: one `# Unit: <slug>` section per unit expanded on
this bolt's milestone … You copy the lowest-numbered unit's document when
you scaffold; the loop appends every later one as each approval expands."
`guard_scaffold`'s order still says "BELOW them: … copy the
LOWEST-NUMBERED one's body into bolt.md verbatim, under a
`# Unit: <slug>` heading"; `guard_charter` still appends the rest into
that same file; and `merge_criteria()`'s `^#{1,2}\s` lookahead exists —
by its own docstring — to survive those headings.

So a charter that now opens correctly still ends as a container for prose
the book says belongs in its own file, and one failure survives the fix
outright. The two records already in the older shape —
`openspec/changes/loop-boundaries/bolt.md` and
`openspec/changes/archive/2026-08-17-matches-the-book/bolt.md` — open at
`# Unit: <slug>` with no charter above, and the reader returns `""` for
both. Because it takes the first `## Merge criteria` anywhere in the
file, a unit document carrying one of its own would be handed to the
landing as this bolt's criteria. Neither record has a unit artifact,
because the shape that would write one does not exist yet.

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
- **The merge criteria are read from the charter's own region.** A
  `# Unit:` section left in an existing `bolt.md` by the older shape can
  never supply this bolt's criteria: the reader stops at the first such
  heading, so an absent charter reads as absent rather than as whatever
  the unit prose below happened to say.
- **Three behaviours the tree already has become requirements of record**,
  since this change is what carries them into `openspec/specs/`: the
  milestone description reaching the scaffold session as the charter's
  stated source; the guard checking the settled charter through the same
  reader the landing uses; and the landing refusing a charter that states
  no criteria, ahead of any landing session and under a force as much as
  automatically.

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
- `bin/_flywheel_bolt_loop.py` — `guard_scaffold`'s work order, whose
  charter paragraph stands and whose "BELOW them: … copy the
  LOWEST-NUMBERED one's body" paragraph goes; `guard_charter`, which
  appends `# Unit:` sections into `bolt.md` and must instead write one
  file per unit; `UNIT_HEADING`, whose only job is that append;
  `merge_criteria()`, which must bound itself to the charter's region.
  `BoltParams.description`, the post-settle check, and `land_stage`'s
  charter refusal are already as the specs state and are verified, not
  rewritten.
- `tests/test_bolt_loop.py` — the charter tests assert the
  append-into-`bolt.md` shape; `LandingTest.program` stubs
  `merge_criteria` on every landing test; and `ReadingTest`'s one
  real-reader test reads a path that has since been archived, so it takes
  its `skipTest` branch on any current worktree.
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
