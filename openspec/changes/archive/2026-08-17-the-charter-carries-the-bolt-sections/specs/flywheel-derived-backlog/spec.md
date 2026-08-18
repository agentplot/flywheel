## ADDED Requirements

### Requirement: The bolt's charter is the bolt's own statement

`openspec/changes/<slug>/bolt.md` is the bolt's charter and carries the
bolt-level statement alone: the delivery, the unit sequence and price,
and the merge criteria the landing verifies. It SHALL carry the sections
the bound `bolt-*` schema's `bolt.md` template names — scope, sources,
repos, and merge criteria with the landing mode stated on its `Landing:`
line — and SHALL carry no unit's plan document. The record mirrors the
board one-to-one: one charter per bolt.

**The charter is born at scaffold, from the milestone's description.**
The description the planner authored — the delivery in three sentences,
the unit sequence, the total price — SHALL be carried to the session that
writes the charter, so the sections are written from it rather than
re-derived or guessed. This SHALL hold for a planner-born bolt exactly as
for one the operator dictated: a milestone carrying unit cards is not a
reason to write a unit and skip the bolt. A bolt whose milestone carries
no description SHALL still get its sections, written from what the
milestone and its items say; an absent description is a thinner charter,
never a missing one.

**The charter is checked, not assumed.** After the session that writes
the charter settles, the loop SHALL read `bolt.md` and confirm it carries
a merge-criteria section with a body. A charter that does not SHALL stop
the cycle with a reason naming the change directory and what is missing:
a settle is not the whole post-condition. The check SHALL use the same
reader the landing reads the criteria through, so "the guard passed" and
"the landing can read it" cannot disagree, and it SHALL read the file, so
a later pass over a charter that has since gained its sections passes
without re-driving anything.

**The bolt's merge criteria are read from the charter's own region.**
The region ends at the first `# `-level heading that opens a unit
section, so prose left in an older `bolt.md` under a `# Unit: <slug>`
heading SHALL NOT be read as this bolt's merge criteria however it is
subdivided. A charter with no such heading is its own region entire.

**A landing mode that was defaulted is not a mode that was declared.**
Because the charter states its `Landing:` line, the reader that picks
merge or pull request finds a declaration rather than falling through to
its default on a charter that said nothing.

#### Scenario: a planner-born charter

- **WHEN** a bolt's change directory is scaffolded on a milestone that
  carries unit cards and a description the planner authored
- **THEN** `bolt.md` carries the scope, sources, repos and merge criteria
  written from that description, with the `Landing:` line stated, and no
  unit's plan document anywhere in the file

#### Scenario: a bolt whose milestone carries no description

- **WHEN** the milestone has no description — a bolt born at triage, or
  one whose description was never written
- **THEN** the charter still carries all four sections, written from what
  the milestone and its items say, and the scaffold does not pass on a
  charter that carries none of them

#### Scenario: the charter comes back without its sections

- **WHEN** the scaffold session settles and `bolt.md` carries no
  merge-criteria section, or carries an empty one
- **THEN** the cycle stops with a reason naming the change directory and
  the missing sections, and the run does not proceed to the stages

#### Scenario: a leftover unit section cannot supply the criteria

- **WHEN** a `bolt.md` written under the older shape carries a
  `# Unit: <slug>` section whose plan document contains its own
  `## Merge criteria` subsection, and no merge criteria above it
- **THEN** this bolt's merge criteria read as absent, and the unit's
  prose is never read as the bolt's criteria

### Requirement: Each approved unit's document is its own artifact

A plan document is mutable state on the tracker while its card is
unapproved. The operator's approval freezes it, and expansion is what
makes it durable prose in git. The loop SHALL write each expanded unit's
plan document to `openspec/changes/<slug>/units/<unit-slug>.md` —
verbatim from the body of the card the operator approved, one file per
approved unit, named by the slug the card's title carries. The write
SHALL be committed to the bolt's change directory on the branch that
carries the bolt's record — main only before the bolt branch is cut, the
bolt branch after.

The unit artifacts are not written into the charter. `bolt.md` is the
bolt's statement and a unit file is the approval's, and neither is
appended to the other.

**A unit whose file is already present SHALL NOT be written again**, so a
pass with nothing newly expanded makes no commit and the loop keeps its
dry-cycle property. The test SHALL be the committed state of the record,
not a stored flag and not the working tree alone: a pass following an
interrupted commit SHALL re-run the commit rather than read the file it
already wrote as evidence that the write is done.

A unit file already on disk SHALL NOT be overwritten, whether the loop
wrote it or a hand did: durable prose in git outranks the mutable tracker
state it came from.

#### Scenario: the first unit

- **WHEN** the first card on a bolt's milestone is expanded
- **THEN** `units/<unit-slug>.md` is written with that card's body
  verbatim and committed, and `bolt.md` is unchanged by it

#### Scenario: a second unit expands

- **WHEN** a second card on the same milestone is expanded
- **THEN** a second file appears under `units/`, committed on the bolt
  branch, and the first unit's file and the charter are both unchanged

#### Scenario: nothing newly expanded

- **WHEN** a pass expands no card and every unit on the milestone already
  has its file at HEAD
- **THEN** no unit write and no commit happen

#### Scenario: a torn write is repaired, not read as done

- **WHEN** a previous pass wrote a unit's file but its commit did not
  land
- **THEN** the next pass leaves the file's content alone and re-runs the
  commit, so the record ends carrying it

## REMOVED Requirements

### Requirement: The bolt's charter carries every expanded unit's plan

**Reason**: The book now splits the bolt's record in two — `bolt.md` is
the charter, carrying the bolt-level statement alone, and each approved
unit's document is its own artifact at `units/<slug>.md`
(`books/flywheel/src/schemas.md`, "The bolt schemas and the loop block";
`books/flywheel/src/bolt-planning.md`;
`books/flywheel/src/lifecycles.md`, "The bolt's changes"). A charter that
carries unit documents is the shape this change ends.

**Migration**: The durable-prose guarantee is unchanged and moves whole
to "Each approved unit's document is its own artifact" — same verbatim
copy, same commit on the branch carrying the record, same
never-written-twice and never-overwritten rules, at a per-unit path
instead of an appended section. Records already carrying `# Unit:`
sections in `bolt.md` are not rewritten: the section is inert under
"The bolt's charter is the bolt's own statement", which will not read
criteria out of it, and the unit file each record is missing is written
by the same guard, whose test is whether the file exists.
