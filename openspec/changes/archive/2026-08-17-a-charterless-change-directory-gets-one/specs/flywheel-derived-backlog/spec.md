## MODIFIED Requirements

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

**A charter that is absent is written, never assumed present.** The test
that decides whether a charter is owed SHALL be `bolt.md` itself, not the
change directory that holds it: a change directory that exists carrying
no `bolt.md` SHALL be driven to a charter on the same pass that finds it,
and SHALL NOT be read as a bolt whose charter is already written. This
covers the record whose directory was created and whose charter was not —
a scaffold that settled without writing one, or a change made by any
other hand — and it holds on every pass after the first, so a record that
was charterless when the stages began does not stay charterless because a
directory was there.

**A charter owed to an existing change is asked for as an addition to
it.** Where the change directory is already present, the session SHALL be
ordered through the invocation that adds a missing artifact to an
existing change, not the one that creates a change: an order to create a
change that exists cannot be obeyed, and a session that cannot obey its
order writes nothing while reading as settled. What the order asks for
SHALL be the same on both paths — the four sections, the `Landing:` line
stated, the milestone's description as the charter's stated source, and
no unit's plan document — so the charter a record gets does not depend on
which path wrote it.

**A charter that is present is left exactly as it stands.** Where
`bolt.md` exists, this guard SHALL drive no session and write nothing,
whether or not the charter reads back merge criteria. A charter that has
lost its sections, or never carried them, is named by the landing's
refusal; rewriting it here would put a guard over committed prose, which
outranks the state it came from. A pass over a record whose charter is
present SHALL record no action, which is the loop's dry-cycle property.

**The charter is checked, not assumed.** After the session that writes
the charter settles, the loop SHALL read `bolt.md` and confirm it carries
a merge-criteria section with a body. A charter that does not SHALL stop
the cycle with a reason naming the change directory and what is missing:
a settle is not the whole post-condition. The check SHALL use the same
reader the landing reads the criteria through, so "the guard passed" and
"the landing can read it" cannot disagree, and it SHALL read the file, so
a later pass over a charter that has since gained its sections passes
without re-driving anything. The check SHALL apply to every path that
drives a charter session, so a charter written into an existing change is
held to what a charter written with its directory is held to.

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

#### Scenario: a change directory that exists without a charter

- **WHEN** a pass finds `openspec/changes/<slug>/` present and
  `openspec/changes/<slug>/bolt.md` absent
- **THEN** a session is driven to write the charter into that change,
  ordered through the invocation that adds an artifact to an existing
  change and asked for the same four sections, `Landing:` line and
  description-borne content as a charter written with its directory

#### Scenario: the scaffold that settled without writing one

- **WHEN** a scaffold session created the change directory and settled
  without a `bolt.md`, stopping that cycle, and a later pass runs over
  the record it left
- **THEN** the later pass drives the charter again rather than reading
  the directory as evidence that the charter was written, and the record
  does not reach the stages carrying no charter

#### Scenario: the charter comes back without its sections

- **WHEN** the session that was driven to write the charter settles and
  `bolt.md` carries no merge-criteria section, or carries an empty one
- **THEN** the cycle stops with a reason naming the change directory and
  the missing sections, and the run does not proceed to the stages —
  whichever path drove that session

#### Scenario: a charter already present is not this guard's business

- **WHEN** a pass finds `bolt.md` present, whether it reads back merge
  criteria or not
- **THEN** no session is driven, nothing is written, no action is
  recorded, and a charter that reads back nothing is left for the
  landing's refusal to name

#### Scenario: a dry run over a charterless record

- **WHEN** the loop runs without writing and finds a change directory
  carrying no `bolt.md`
- **THEN** it reports the charter it would write into that change,
  launches no session and leaves the tree untouched

#### Scenario: a leftover unit section cannot supply the criteria

- **WHEN** a `bolt.md` written under the older shape carries a
  `# Unit: <slug>` section whose plan document contains its own
  `## Merge criteria` subsection, and no merge criteria above it
- **THEN** this bolt's merge criteria read as absent, and the unit's
  prose is never read as the bolt's criteria
