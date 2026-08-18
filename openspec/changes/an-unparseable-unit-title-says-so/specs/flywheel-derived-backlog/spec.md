## MODIFIED Requirements

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

**A unit whose title parses no slug SHALL stop the cycle with a reason
naming it.** The file is named by the slug the card's title carries, so a
title that carries none names no file; the loop SHALL NOT pass over such a
unit as though there were nothing to write. It SHALL halt the cycle with a
reason, and the reason SHALL reach the run record and the run report the
same way every other pause reason does. Passing over it is a guess — that
an approval the operator made does not matter — and the loop pauses rather
than guessing.

The reason SHALL name every unit on the milestone whose title parses no
slug, in item order, each by its number and by its title exactly as the
tracker carries it, and SHALL state what a unit title must carry for a
file to be named from it. One pause SHALL report them all, so a milestone
carrying several is fixed in one pass rather than one pause per card.

**The units of that pass whose titles do parse are still written.** A
nameable unit missing its file SHALL be written and committed exactly as
it would be on a pass with no unnameable unit on the milestone, and the
pause SHALL follow those writes: one misnamed card does not hold another
approval's durable prose. Where that pass also failed to commit, the
commit failure SHALL be the reason returned and the unnameable unit SHALL
be reported on a later pass — both conditions persist until a hand clears
them, so neither is lost.

**The reason SHALL be given wherever the guard reports at all**, including
a pass that makes no write of its own: a dry run over a milestone carrying
an unnameable unit SHALL state that the bolt would pause and why rather
than reporting that there was nothing to write, and a run whose tracker is
a fixture — which writes no tree — SHALL still give the reason, because
naming the unit is a read of the tracker and not a write to anyone's
checkout.

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

#### Scenario: a unit title that parses no slug

- **WHEN** a pass finds a unit on the milestone whose title parses no
  slug
- **THEN** the cycle halts with a reason naming that unit by number and by
  its title, and stating what a unit title must carry — and the run record
  carries that reason

#### Scenario: a nameable unit beside an unnameable one

- **WHEN** a pass finds one unit whose title parses a slug and is missing
  its file, and another whose title parses none
- **THEN** the nameable unit's file is written and committed, and the
  cycle then halts with the reason naming the unnameable one

#### Scenario: several unnameable units

- **WHEN** a pass finds more than one unit on the milestone whose title
  parses no slug
- **THEN** one reason names all of them, in item order

#### Scenario: a dry run over an unnameable unit

- **WHEN** a dry run passes over a milestone carrying a unit whose title
  parses no slug
- **THEN** it reports the pause and its reason, writes nothing, and does
  not report the pass as having nothing to write
