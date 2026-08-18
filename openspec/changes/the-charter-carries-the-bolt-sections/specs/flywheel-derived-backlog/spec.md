## ADDED Requirements

### Requirement: The bolt's charter opens with the bolt's own sections

`openspec/changes/<slug>/bolt.md` is the bolt's charter, and it SHALL
carry the bolt-level sections the bound `bolt-*` schema's `bolt.md`
template names — the scope, the sources, the repos, and the merge
criteria with the landing mode stated on its `Landing:` line — before any
unit's plan document. A charter is born at scaffold whatever the bolt's
origin, and this SHALL hold for a planner-born bolt exactly as for one
the operator dictated: a milestone carrying unit cards is not a reason to
write the units and skip the bolt.

**The milestone's description is the charter's stated source.** The
description the planner authored — the delivery, the unit sequence, the
price — SHALL be carried to the session that writes the charter, so the
sections are written from it rather than re-derived or guessed. A bolt
whose milestone carries no description SHALL still get its sections,
written from what the milestone and its items say; an absent description
is a thinner charter, never a missing one.

**The charter is checked, not assumed.** After the session that writes
the charter settles, the loop SHALL read `bolt.md` and confirm it carries
a bolt-level merge-criteria section with a body. A charter that does not
SHALL stop the cycle with a reason naming the change directory and what
is missing, in place of the "the session settled" pass it gets today. The
check reads the file, so a later pass over a charter that has since
gained its sections passes without re-driving anything.

**A landing mode that was defaulted is not a mode that was declared.**
Because the charter states its `Landing:` line, the reader that picks
merge or pull request finds a declaration rather than falling through to
its default on a charter that said nothing.

#### Scenario: a planner-born charter

- **WHEN** a bolt's change directory is scaffolded on a milestone that
  carries unit cards and a description the planner authored
- **THEN** `bolt.md` opens with the bolt-level scope, sources, repos and
  merge criteria written from that description, with the `Landing:` line
  stated, and the lowest-numbered unit's plan document follows below them
  under its `# Unit: <slug>` heading

#### Scenario: a bolt whose milestone carries no description

- **WHEN** the milestone has no description — a bolt born at triage, or
  one whose description was never written
- **THEN** the charter still carries all four bolt-level sections,
  written from what the milestone and its items say, and the scaffold
  does not pass on a charter that carries none of them

#### Scenario: the charter comes back without its sections

- **WHEN** the scaffold session settles and `bolt.md` carries no
  bolt-level merge-criteria section, or carries an empty one
- **THEN** the cycle stops with a reason naming the change directory and
  the missing sections, and the run does not proceed to the stages

#### Scenario: a unit's own subsections never shadow the bolt's criteria

- **WHEN** the charter carries the bolt's merge criteria and one or more
  `# Unit: <slug>` sections whose plan documents contain their own `##`
  subsections
- **THEN** the merge criteria read for this bolt are the bolt's own — the
  first such section in the file — and a unit's prose is never read as
  the bolt's criteria

## MODIFIED Requirements

### Requirement: The bolt's charter carries every expanded unit's plan

The plan document behind an approved card is mutable state on the
tracker until expansion; expansion is what makes it durable prose in
git. The loop SHALL ensure that `openspec/changes/<slug>/bolt.md` holds
the plan document of every unit expanded on the bolt's milestone, each
as its own `# Unit: <slug>` section, in expansion order, verbatim from
the card's body. The write SHALL be committed to the bolt's change
directory on the branch that carries the bolt's record — main only
before the bolt branch is cut, the bolt branch after.

Every unit's section SHALL sit **below** the bolt-level sections the
charter opens with, appended after whatever the charter already holds.
The bolt's own merge-criteria section stays the first one in the file,
so the reader that takes the first such section takes the bolt's.

The charter is not written from the milestone's "unit parent": a bolt
carries as many units as the operator approves, and each one's document
belongs in the charter. A unit whose section is already present SHALL
NOT be written again, so a pass with nothing newly expanded makes no
commit.

#### Scenario: the first unit

- **WHEN** the first card on a bolt's milestone is expanded and the
  bolt's change directory does not yet exist
- **THEN** the directory is scaffolded and `bolt.md` carries that unit's
  plan document under its `# Unit: <slug>` heading, below the bolt-level
  sections the charter opens with

#### Scenario: a second unit expands into an existing charter

- **WHEN** a second card on the same milestone is expanded and the
  bolt's change directory already exists
- **THEN** `bolt.md` gains that unit's document as a second
  `# Unit: <slug>` section, committed on the bolt branch, and the first
  unit's section and the bolt-level sections above them are unchanged

#### Scenario: nothing newly expanded

- **WHEN** a pass expands no card and every unit on the milestone
  already has its section
- **THEN** no charter write and no commit happen
