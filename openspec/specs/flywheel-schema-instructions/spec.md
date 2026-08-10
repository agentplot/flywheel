# flywheel-schema-instructions Specification

## Purpose
The two flywheel OpenSpec schemas' artifact instructions are the one steering
surface every flywheel agent renders, whatever skill or profile it loaded. This
capability states what that surface must say, so an agent reading only
`openspec instructions` reaches the actor model, files each task under the
right type, and takes the single path out of the phase gate.
## Requirements
### Requirement: The sessions instruction enumerates the launch identities

The `flywheel-intent` schema's `sessions` artifact instruction SHALL state that
the intent conductor launches a design session, and SHALL enumerate every
identity a session may be launched under. An artifact instruction is static
text rendered identically for every session, so it SHALL NOT be written as if
it addressed one particular session's profile or type.

The enumeration SHALL name both design-session profiles and all five
session-type skills, and SHALL state the sentence that connects them: the
conductor launches the session under one of the two profiles and names the type
in the work order, and the session loads that type's skill before working its
batch. Because the counts do not pair — five types, two profiles — the
instruction SHALL NOT imply a one-to-one profile-to-type correspondence. Which
profile hosts which type is mechanics assigned by `flywheel-session-profiles`,
and the instruction SHALL stop before it rather than restating or contradicting
that assignment.

`decisions/session-types-are-skills.md` is the naming authority for all seven
identifiers — an actor says "session", a way of working never does — and
`flywheel-session-profiles` creates the files. This capability SHALL cite them,
not own them; the identifiers written into the instruction SHALL be the settled
names.

One name is constrained by this surface itself. The reads-only investigation
type SHALL be named `flywheel-research`, the same word the schema's own `tasks`
instruction uses for the task type that session works, so a `research:` task and
the session working it share a name. The instruction SHALL NOT name any session
type "spike" in any spelling — neither a `flywheel-spike` identifier nor the
bare word in surrounding prose: the `prototypes` instruction two artifacts away
in the same file
already spends that word on the repo where throwaway code is built, and a
session type carrying it would cross the two meanings inside one rendered
schema.

#### Scenario: A session agent reaches its identity from the schema alone

- **WHEN** an agent renders `openspec instructions sessions` for a
  `flywheel-intent` change, having loaded no flywheel skill and no agent profile
- **THEN** the rendered instruction names the intent conductor as the actor that
  launches the session
- **AND** it names both profiles — `flywheel-design-session` and
  `flywheel-interactive-session` — and the six design session-type skills
- **AND** it states that the work order names the type and the session loads that
  type's skill before working its batch

#### Scenario: The enumeration covers a type that wraps no surface tool

- **WHEN** a conductor charges a batch of chapter rewrites as a writeback
  session, whose type wraps `books/CLAUDE.md` and the destination voice rather
  than either surface tool
- **THEN** the rendered instruction names `flywheel-writeback` among the five, so
  the session loads a skill the schema named rather than inferring one from a
  profile's surface
- **AND** the instruction does not imply a one-to-one profile-to-type
  correspondence that the two-against-five counts would make unsatisfiable

#### Scenario: The named identifiers resolve

- **WHEN** the seven identifiers named in the `sessions` instruction are looked
  up on disk
- **THEN** each names a file or directory that exists — two
  `.claude/agents/<name>.md` profiles and five `.claude/skills/<name>/` skills
- **AND** each matches the names settled in
  `decisions/session-types-are-skills.md` and created by
  `flywheel-session-profiles`, read from those rather than from any literal
  copied into this change
- **AND** no skill name carries a `session-` infix, since a way of working never
  says "session"
- **AND** the reads-only type is `flywheel-research`, matching the `research`
  task type the same schema's `tasks` instruction names, and no session type is
  named "spike", which that file spends on the throwaway-code repo

### Requirement: The sessions instruction stops at the pointer

The `sessions` instruction SHALL carry the pointer and no session mechanics. It
SHALL state that the conductor chooses the type at work-order time, because a
session that reads only the schema must not conclude it may choose its own. It
SHALL NOT state which surface tool a type runs on, what a design surface should
contain, or how a conductor weighs one type against another; that content
belongs to the session-type skills and the `flywheel-inception` skill.

#### Scenario: Mechanics stay out of the schema

- **WHEN** the rendered `sessions` instruction is read end to end
- **THEN** it contains no instruction on what a surface should contain — no
  guidance on code samples, configuration examples, diagrams, or conceptual SVGs
- **AND** it contains no rule for weighing one session type against another

#### Scenario: A session does not choose its own type

- **WHEN** a session renders the `sessions` instruction and finds no type named
  in its work order
- **THEN** the instruction has already told it the conductor chooses the type at
  work-order time, so the session asks its conductor rather than choosing

#### Scenario: The existing session-directory contract is untouched

- **WHEN** the rendered `sessions` instruction is compared against the text it
  replaced
- **THEN** the directory-naming rule, the collision rule, the `README.md`
  contract, the sole-writer split between session and conductor, and the
  never-rewritten closed directory all still read as they did

### Requirement: A review round is a launch point for design tasks

The `flywheel-intent` schema's `tasks` artifact instruction SHALL state, under
the **Design** type, that a review round may append a Design task: when a
conductor triages returned annotations and finds work that needs design, that
work becomes an appended Design task, by the same route a task from the board
takes.

#### Scenario: A conductor triaging annotations finds the route

- **WHEN** an intent conductor holding returned annotations renders
  `openspec instructions tasks`
- **THEN** the **Design** type states that a review round may append a Design
  task
- **AND** the existing Design contract still holds: a design session task names
  the decisions it aims to close, and links the decision record and the design
  report on the task line when it closes one

### Requirement: Handoff is the single motion out of the phase gate

The `tasks` artifact instruction SHALL keep exactly one Handoff motion. It
SHALL name the one-proposal handoff as a special case of that motion — still
requested as a bolt with a bolt conductor — and SHALL NOT offer any second path
out of the gate.

#### Scenario: A single-proposal handoff still requests a bolt

- **WHEN** an intent conductor with a settled slice carrying one proposal renders
  `openspec instructions tasks`
- **THEN** the **Handoff** type names the one-proposal bolt as a special case of
  the same motion
- **AND** the staged-then-released contract still holds: the task is staged,
  passes through the operator's phase gate, and on release the conductor
  requests the bolt rather than writing a bolt change itself

#### Scenario: No bare work branch is offered

- **WHEN** the rendered `tasks` instruction is searched for an alternative exit
- **THEN** it describes no route from a Handoff task to a work branch off main
  that skips a bolt, and no size threshold below which the bolt is skipped

### Requirement: The intent's typed sections are Design, Writeback, and Handoff

The `flywheel-intent` schema SHALL define three task types, not four. The ADR
type is retired: an architecture decision record destined for a built repo is a
Handoff task like any other built-repo edit, and `decisions/adr-is-a-handoff.md`
is the authority. The `tasks` artifact instruction SHALL NOT define an ADR type
and SHALL NOT name the retired type in any residual form — no parenthetical, no
aside directing a reader from ADR to Handoff — since the instruction is static
text rendered identically for every reader and a type named in passing is a type
a reader will file under.

Every surface that enumerates the intent's task types SHALL enumerate the same
three. In the schema: the `tasks` artifact instruction, the `decisions` artifact
instruction's **Consequences** description, `templates/tasks.md`'s headings, and
`templates/decisions/decision.md`'s appended-task placeholder. Outside it: the
project-level `rules.tasks` line in `openspec/config.yaml`, which names both
schemas' typed sections and is the one statement of them an opsx session reads
without loading a skill.

#### Scenario: A conductor filing a decision's consequences finds three types

- **WHEN** an intent conductor renders `openspec instructions tasks` and
  `openspec instructions decisions` for a `flywheel-intent` change
- **THEN** the typed sections are Design, Writeback, and Handoff
- **AND** the `decisions` instruction describes the tasks a decision appends as
  writebacks, handoffs, or new questions, with no ADR term between them

#### Scenario: No enumeration of the types is left at four

- **WHEN** the `flywheel-intent` schema directory and `openspec/config.yaml` are
  searched for the retired type name, case-insensitively and on a word boundary
- **THEN** there are no occurrences
- **AND** `templates/tasks.md` carries the same three headings, in the same
  order, as the `tasks` instruction's types

### Requirement: The Handoff type names the ADR case and its ordering

The `tasks` artifact instruction's **Handoff** type SHALL name the ADR as a case
of the one Handoff motion. It SHALL state that an ADR destined for a built repo
names the repo and the record to generate, that it leaves through the operator's
phase gate like every other Handoff, and that it is ordered first in the bolt
carrying the work it explains — normally row one, merged ahead of the code rows,
so the repo carries the reasoning before it carries the change.

"Ahead of construction" SHALL be preserved by that ordering inside the bolt and
by nothing else. The instruction SHALL NOT offer any route that reaches a built
repo without passing the gate.

#### Scenario: A conductor with an ADR to write finds the route

- **WHEN** an intent conductor holding a decision whose consequence is an
  architecture decision record in a built repo renders
  `openspec instructions tasks`
- **THEN** the **Handoff** type names the case, and the task it files names the
  built repo and the record to generate
- **AND** the task is staged and passes the operator's phase gate like any other
  Handoff, rather than being written into the built repo on the intent's own
  authority

#### Scenario: The ordering, not an exemption, carries "ahead of construction"

- **WHEN** the released ADR handoff reaches a bolt
- **THEN** the instruction places its proposal first in that bolt, ahead of the
  rows carrying the code it explains
- **AND** nothing in the instruction lets an ADR bypass the gate on the grounds
  that it precedes construction

### Requirement: Retiring the type does not strand a live intent

A change that removes a task type from a live schema SHALL NOT land while a
change governed by that schema still files tasks under the removed type without
its conductor having been told. This capability's landing SHALL therefore be
gated on the affected intents having been notified through their own inbox,
written by the actor that owns that timing rather than by the build.

#### Scenario: A live intent files tasks under the retired type

- **WHEN** this change is ready to merge and an intent governed by
  `flywheel-intent` carries tasks under an `## ADR` heading
- **THEN** the merge waits on a note in that change's `inbox/` telling its
  conductor the type has retired and that such tasks are Handoffs ordered first
  in their bolt
- **AND** the note is not written by this change's build, which edits only the
  schemas, the templates, and the project config

### Requirement: Writeback is closed, and both conductor carve-outs are stated

The `tasks` artifact instruction SHALL state both of the things the outer loop
writes, not one, and SHALL attribute each to the actor that writes it: an intent
conductor writes the change's own artifacts under `openspec/changes/<id>/`, its
design sessions write their session directories under it, and both write the
books and the context map. It SHALL NOT lump conductor and sessions together as
writers of the change's own artifacts, since a session reading the sentence
literally would take that as a grant of `design.md`, `decisions/` and
`tasks.md`, which `decisions/sole-writer-conductors.md` and this schema's own
`sessions` instruction both deny.

It SHALL define **Writeback** as a closed type — a book chapter rewrite or a
context map update and nothing else — and it SHALL state that the change's own
artifacts are what the conducting produces, so that writing `decisions/`,
`design.md` and `tasks.md` is never pushed onto the Handoff side. It SHALL state
that every *other* file edit, in any repo — including blueprints itself, where
the flywheel machinery lives — is a Handoff task naming its built repo and its
proposal.

The carve-out SHALL bear only on the Handoff boundary: no task is filed to
perform the writing itself. It SHALL NOT be stated in terms that exclude the
change's own artifacts from being a task's *product*, since the same
instruction's **Design** type has a design session task naming the decisions it
aims to close and linking the decision record on the task line, and its Rules
block requires that record to exist before the task is checked off.

The instruction SHALL carry the misfile test as a test: a task filed as
Writeback whose target is neither a book chapter nor the context map is a
misfiled Handoff.

The three surfaces that state this guardrail — this instruction,
`flywheel-inception`, and `.claude/agents/flywheel-intent-conductor.md` — SHALL
state the same rule: the two write scopes, everything else is a handoff whatever
repo it lives in, and the misfile test. This instruction SHALL NOT carry a
clause the other two lack.

`.claude/agents/flywheel-bolt-conductor.md` is NOT one of the three surfaces. A
bolt conductor has no Writeback tasks, so `flywheel-loop-skills` states that it
carries no version of this rule; a cross-surface check SHALL NOT report its
absence there as a gap, and SHALL NOT add the rule to it.

#### Scenario: A machinery task cannot be filed as Writeback

- **WHEN** an intent conductor is filing a task that edits an agent profile, a
  skill, a schema file, or a conventions document in the blueprints repo
- **THEN** the rendered **Writeback** type excludes it by saying so, not only by
  omitting it
- **AND** the misfile test names it: its target is neither a book chapter nor
  the context map, so it is a misfiled Handoff
- **AND** the instruction states that such a task is a Handoff naming its built
  repo and its proposal, with blueprints named as a built repo like any other

#### Scenario: The conductor's own artifacts are not handoffs

- **WHEN** an intent conductor writes a decision record, updates `design.md`, or
  appends to `tasks.md` in its own change directory
- **THEN** the instruction places that inside what the conductor writes, so the
  "everything else is a Handoff" clause excludes it rather than capturing it
- **AND** no task is filed to perform that writing itself

#### Scenario: A design session does not read the carve-out as a grant

- **WHEN** a design session renders `openspec instructions tasks` and reads the
  two things the outer loop writes
- **THEN** the sentence attributes the change's own artifacts to the intent
  conductor and gives the session its own `sessions/<date>-<slug>/` directory
- **AND** the session cannot read it as licence to write `design.md`,
  `decisions/` or `tasks.md` directly, which would contradict this schema's
  `sessions` instruction — "the conductor is the sole writer everywhere else"

#### Scenario: A Design task still produces a decision record

- **WHEN** a conductor files a Design task naming the decisions a session aims to
  close, and checks it off once the session closes one
- **THEN** the Writeback carve-out does not forbid it: the conductor writes the
  decision record under `openspec/changes/<id>/`, promoting what the session
  produced, and the **Design** type and the Rules block both still require the
  task line to link that record
- **AND** the carve-out reads as bearing on the Handoff boundary only, and its
  narrowed attribution does not disturb it — the writer is the conductor either
  way

#### Scenario: The done condition survives

- **WHEN** a Writeback task covering the context map is filed
- **THEN** the instruction still gives `map-check --write` green as the done
  condition, and still requires destination voice for book chapter rewrites

### Requirement: The bolt schema describes the one-proposal bolt

The `flywheel-bolt` schema SHALL describe the one-proposal bolt. Its `bolt`
artifact instruction SHALL state that a bolt carrying a single proposal is an
ordinary bolt — every `bolt.md` section written, the same bolt conductor as sole
writer — and its `proposals` artifact instruction SHALL describe the one-row
registry: the single row carries the same columns and moves along the same
forward-only status ladder as any other row.

#### Scenario: A conductor opening a one-proposal bolt finds it named

- **WHEN** a bolt conductor charged with a single-proposal handoff renders
  `openspec instructions bolt`
- **THEN** the instruction names the one-proposal bolt and states that nothing
  about the record's sections or its sole writer changes

#### Scenario: The one-row registry keeps the full contract

- **WHEN** the same conductor renders `openspec instructions proposals`
- **THEN** the instruction states that a one-row registry is the ordinary
  registry with one row
- **AND** the row's columns and the forward-only status ladder
  (`to-spec` → `specced` → `in-review` → `approved` → `building` → `built` →
  `verified` → `merged`, with a bounced review the only return to `to-spec`)
  apply to it unchanged

### Requirement: The one-proposal bolt keeps the same actors

The `flywheel-bolt` schema SHALL state that a one-proposal bolt keeps the same
actors as any other bolt, not only the same sole writer. Sole writership is the
bolt conductor's write monopoly over the change's artifacts; the actor
separation is a different claim, and it is the one a single row is tempted to
collapse. The instruction SHALL state that for one row as for any other, the
agent that specs the proposal is not the agent that builds it, the row's
declared review still runs, and the archive still happens.

#### Scenario: One row does not collapse spec and build into one agent

- **WHEN** a bolt conductor drives a one-proposal bolt from `to-spec` to `built`
- **THEN** the instruction states that the spec agent and the build agent are
  separate agents, so the conductor cannot read the single row as licence to do
  both in one run

#### Scenario: A single row does not make the review or the archive optional

- **WHEN** a bolt conductor holding a one-proposal bolt at `specced` renders
  `openspec instructions proposals` while deciding whether the single row's
  declared review and the bolt's archive are worth the ceremony
- **THEN** the instruction states that both still happen for a one-proposal bolt
- **AND** neither is described as optional or skippable on grounds of the bolt's
  size

### Requirement: The bolt schema prescribes no read

The `flywheel-bolt` schema SHALL NOT imply that a read of any particular kind is
required. Its `proposals` instruction SHALL state that the `review` column
declares that a row wants a particular kind of eyes on it, and is not a
statement that a mandatory read type has been performed; and it SHALL state the
accountability that replaces the implication — a bolt conductor is accountable
for one thing, that the batch it is about to build is buildable and internally
coherent, and how it satisfies that is its judgment.

The instruction SHALL state that reads are taken across the batch rather than
one proposal at a time, and that nothing in the schema prescribes a read that
must always run. It SHALL NOT enumerate the kinds of read or state what each
catches; that content belongs to the construction skill, and the schema states
only that the choice among them is the conductor's. The `tasks` instruction's
**Review** type SHALL say the same, and SHALL admit a read the conductor chose
over the batch as a Review task in its own right.

None of this weakens the declared review. A review a row declares still runs,
whatever the bolt's size; what is not fixed is which kind of read the conductor
takes over the batch.

#### Scenario: A conductor reads the registry and finds no liturgy

- **WHEN** a bolt conductor renders `openspec instructions proposals` while
  deciding how to satisfy itself that a batch is buildable
- **THEN** the instruction states that the `review` column is a declaration of
  the eyes a row wants, not evidence that a required read type has run
- **AND** it states that the conductor chooses the reads, and prescribes no
  sequence and no read that must always run

#### Scenario: A read over the batch has somewhere to be recorded

- **WHEN** a conductor takes a read over the whole batch rather than over one
  proposal, and renders `openspec instructions tasks` to record it
- **THEN** the **Review** type admits it as a Review task recording what it
  found
- **AND** the row-level declared review is unaffected: it still runs, and a
  one-proposal bolt does not make it optional

### Requirement: A build task re-reads the neighbours its proposal asserts about

The `flywheel-bolt` schema's `tasks` artifact instruction SHALL carry the
state-claim rule's build-time task under its **Build** type. It SHALL state the
defect the task guards — a claim about a neighbouring artifact's STATE that the
neighbour no longer bears out — and SHALL require a build-time task enumerating
every neighbour the artifact asserts something about (decision records, sibling
proposals, the registry, the archive), instructing the builder to re-read each
from disk, at build time because that is when the neighbours have had longest to
move. It SHALL give the warrant that task ends with, in the rule's own words.

The wording SHALL be the rule's verbatim, not a paraphrase, so this instruction
and the skills carrying the rule's other parts read as one rule. The rule's
remaining parts — prefer a content claim to a state claim, and name the
mechanism rather than its current output — and its corollaries belong to the
construction and inception skills, and SHALL NOT be restated here.

#### Scenario: A builder is sent back to the sources

- **WHEN** a bolt conductor files a Build task for a proposal that cites decision
  records, sibling proposals, or the registry
- **THEN** the rendered **Build** type requires the task to enumerate those
  neighbours and instruct the builder to re-read each from disk
- **AND** the task ends with the warrant, telling the builder not to trust the
  file it is holding

#### Scenario: The rule is not duplicated across altitudes

- **WHEN** the rendered `tasks` instruction is read against the state-claim rule
  as the intent states it
- **THEN** the build-time task and its warrant appear here word for word
- **AND** the writer-facing parts of the rule do not, being the skills' to state

### Requirement: The bolt schema declares nothing about verification docking

Verification docking stays on the individual proposal. The `flywheel-bolt`
schema SHALL NOT gain a verification artifact, SHALL NOT gain a docking section
in the `bolt` instruction or the `bolt.md` template, and SHALL NOT gain a
docking column in the `proposals` instruction or the `proposals.md` template.

#### Scenario: The schema's artifact set is unchanged

- **WHEN** the `flywheel-bolt` schema's artifact ids are listed after this change
- **THEN** they are exactly `bolt`, `proposals`, and `tasks`, with their
  `requires` edges and the `apply` block unchanged

#### Scenario: The registry keeps seven columns

- **WHEN** the `proposals` instruction and the `proposals.md` template are read
- **THEN** the registry is
  `| proposal | repo | change id | review | status | branch | owner |` and no
  fixture, harness, or docking column has been added

#### Scenario: bolt.md gains no docking section

- **WHEN** the `bolt` instruction's enumerated output sections are read
- **THEN** they are exactly Scope, Sources, Repos, and Merge criteria, and the
  `bolt.md` template carries the same four

