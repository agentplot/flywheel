## ADDED Requirements

### Requirement: Each bolt schema declares the charter and the unit artifact

Every `bolt-*` schema SHALL declare two artifact types: `bolt`,
generating `bolt.md`, the bolt's charter; and `unit`, generating
`units/<slug>.md`, one approved unit's document. The declaration is what
makes the unit record an artifact of the change rather than prose
somebody appended, and it SHALL be present in all four members —
`bolt-default`, `bolt-quick`, `bolt-adversarial`, `bolt-direct` — since
the record's shape is not a function of the type.

The `unit` artifact's instruction SHALL state that the loop writes it at
expansion, verbatim from the body of the card the operator approved, and
that no session composes or edits it. It is the one artifact of the bolt
that is copied rather than authored.

#### Scenario: the artifact list names both

- **WHEN** any of the four `bolt-*` schemas is read for its artifacts
- **THEN** both `bolt` → `bolt.md` and `unit` → `units/<slug>.md` are
  declared

#### Scenario: a session asks what a unit artifact is

- **WHEN** a session renders the `unit` artifact's instruction
- **THEN** it is told the file is copied verbatim from the approved
  card's body by the loop at expansion, and is not a session's to compose
  or edit

### Requirement: The bolt instruction stops at the charter's four sections

The `bolt` artifact instruction SHALL describe `bolt.md` as the four
sections and nothing else — scope, sources, repos, and merge criteria
with its `Landing:` line — and SHALL NOT direct any session to write a
unit's plan document into that file, at scaffold or afterwards. An
instruction that says "exactly these four sections, and nothing else" and
then names a fifth thing to append teaches the opposite of what it
states, and the session obeys the more specific paragraph.

The instruction SHALL name the bolt milestone's description as the
charter's source, so the session writing it knows where the delivery, the
unit sequence and the price come from.

#### Scenario: a scaffold session renders the bolt instruction

- **WHEN** a session about to write `bolt.md` renders
  `openspec instructions bolt --change <slug>`
- **THEN** it is told to write the four sections from the milestone's
  description, and is told nothing about copying a unit's document into
  that file

#### Scenario: no member contradicts itself

- **WHEN** any of the four `bolt-*` schemas' `bolt` instruction is read
  end to end
- **THEN** no paragraph in it directs content beyond the four sections
  into `bolt.md`
