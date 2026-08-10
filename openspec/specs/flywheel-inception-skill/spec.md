# flywheel-inception-skill Specification

## Purpose
The design loop's practice — what `flywheel-inception` tells dispatch, an
intent conductor, and a design session to do: where a raw idea goes, which
human channel carries which question, who opens a review surface and what
happens to what comes back, what a design surface should contain, what a
record or a task line may assert about its neighbours, and the two things a
conductor and its sessions are allowed to write.
## Requirements
### Requirement: The state-claim rule, carried verbatim

The skill SHALL carry the state-claim rule **word for word** as the intent
records it — the defect, the rule in three parts, its closing warrant, and
both corollaries — as a shared rule binding every role the skill steers.
It SHALL NOT be paraphrased, summarized, or adapted for this reader.

The three parts SHALL read: prefer a CONTENT claim to a STATE claim; where
a state claim is unavoidable, name the MECHANISM rather than its current
output; and carry a **build-time** task enumerating every neighbour the
artifact asserts something about, instructing the builder to re-read each
from disk.

Both corollaries SHALL be present: that a decision record is authoritative
on its decision and provisional on its measurements — where both kinds of
statement sit in one record, the measurement is the one to distrust — and
that **a line-number citation is itself a state claim**, to be replaced by
an anchor, a heading, or a quoted phrase.

The seam paragraph SHALL travel with the rule, because it is what explains
why the rule belongs here as well as in `flywheel-construction`: the loops
run at different clock rates, and the fast loop writes the claims the slow
loop has to keep true. The wording SHALL be identical to the copy in
`flywheel-construction`; only the framing sentence naming which actor
writes these claims may differ.

The skill SHALL apply the rule where the design loop's claims cross into
the bolt loop: a handoff's merge criteria and repo list are drafted against
disk rather than against an earlier handoff's phrasing.

#### Scenario: A conductor writes a decision record that describes a sibling change

- **WHEN** a `decisions/<slug>.md` record asserts something about another
  change's artifacts, a book chapter, or a running bolt
- **THEN** the skill has it prefer a content claim, name the mechanism
  where a state claim is unavoidable, and enumerate that neighbour for a
  build-time re-read

#### Scenario: A reader meets a measurement inside a settled record

- **WHEN** a record states both a settled decision and a measurement, such
  as which gates were green when it was written
- **THEN** the skill has the reader treat the decision as authoritative and
  re-run the measurement rather than inherit it

#### Scenario: A task line locates a passage by line number

- **WHEN** a task line cites `SKILL.md:91` to point at the passage it
  changes
- **THEN** the skill treats that as a state claim about a file another
  actor may be editing, and requires an anchor, heading, or quoted phrase

#### Scenario: A handoff inherits its merge criteria from an earlier one

- **WHEN** a conductor drafts a handoff's merge criteria by reusing the
  phrasing of a previous handoff
- **THEN** the skill has it check the criteria against disk first, naming
  that as where a stale claim crosses into the bolt loop

### Requirement: The outer-loop channel default and the escalation rule

The skill SHALL state that the shape of the answer decides the channel and
the loop decides the default. Shape: a question whose answer is a sentence
and needs nothing read first goes to Discord and is non-blocking, so the
agent keeps working on whatever the answer does not gate; margin notes on a
document that already exists go to plannotator; choices across coupled
decisions, and anything that needs options side by side, go to lavish. Both
desk channels are blocking rounds — the session stands at its surface until
the operator has been through it.

The skill SHALL state the outer loop's default: the desk channels, with
dispatch triage the exception that is Discord-first. It SHALL state the
escalation rule and its direction: take the cheapest channel that can carry
the answer, and when that channel cannot carry it, say so and open the
surface, leaving a pointer behind on the channel that could not. Escalation
runs one way only — a question that has reached a desk channel is not
demoted back to Discord.

The skill SHALL state that a question an agent would have to stop and wait
on was never a Discord question.

#### Scenario: A one-sentence question during an intent

- **WHEN** a conductor needs the operator to pick between two names, or to
  confirm a release, and nothing has to be read first
- **THEN** the skill sends it to Discord (with `AskUserQuestion` standing in
  until that bridge is live), explicitly not to a plannotator or lavish
  round, and the conductor keeps working on everything the answer does not
  gate

#### Scenario: A Discord question turns out to need a surface

- **WHEN** an answer that was asked for in one sentence comes back needing
  trade-offs the operator cannot weigh without seeing them
- **THEN** the skill has the agent say so on the channel, open the desk
  surface, and leave the pointer to it behind — and not re-ask the same
  question in the cheaper channel

#### Scenario: Coupled decisions arrive together

- **WHEN** a batch aims to close several decisions whose answers constrain
  each other
- **THEN** the skill puts them on one lavish surface with the options side
  by side, rather than as a sequence of separate questions

### Requirement: The sole writer opens the review, and feedback returns to the invoker

The skill SHALL state that a review surface is opened by whoever is the
sole writer of the file under review — dispatch annotates the intent it
just wrote, a conductor annotates its canonical artifacts, a design session
annotates the decision drafts in its own directory, and a bolt conductor
annotates a generated proposal.

The skill SHALL state that feedback returns to the invoker and nowhere
else: `plannotator annotate` hands its result to the session that ran it.
Annotations SHALL NOT be relayed raw to another actor and SHALL NOT be
written into another actor's directory.

#### Scenario: A conductor wants a session's drafts reviewed

- **WHEN** an intent conductor would open a plannotator round on decision
  drafts that live in a session's own directory
- **THEN** the skill routes it the other way: the session that wrote the
  drafts is their sole writer and runs the round, and the conductor
  receives the outcome as a session report

#### Scenario: A session receives annotations meant for another actor

- **WHEN** annotations come back that concern a different change or a
  different actor's artifacts
- **THEN** the session delivers them through its report and the messaging
  protocol (prompt the conductor, or the change's `inbox/`), and writes
  nothing into that actor's directory

### Requirement: Returned annotations are triaged into exactly one of three

The skill SHALL state that the conductor triages each returned annotation
into exactly one of three outcomes, and that there is no fourth:

1. a **correction** it applies to the earliest artifact the annotation
   touches, before re-walking the artifact sequence forward
   (`/opsx:continue`) so the downstream artifacts stay coherent;
2. a **decision the annotation closed on its own**, which becomes a
   `decisions/<slug>.md` record before the task that closed it is checked;
3. **work that needs design**, which becomes an appended Design task and
   then a session with its own directory and batch.

The skill SHALL state that a review round is therefore a launch point for
design sessions by the same route the board is: the round produces the
task, and the conductor spawns the session.

#### Scenario: An annotation opens new scope

- **WHEN** an annotation on `intent.md` widens what the intent covers
- **THEN** the conductor revises `intent.md` first and re-walks forward,
  rather than appending the new scope to `tasks.md` and leaving the earlier
  artifacts stale

#### Scenario: An annotation raises a question nobody has answered

- **WHEN** an annotation names a design question the round did not settle
- **THEN** the conductor appends a Design task for it and spawns a session
  with its own directory and batch — it does not answer the question itself
  and does not leave the annotation parked in the surface

#### Scenario: An annotation settles a decision outright

- **WHEN** the operator's margin note answers the decision the draft put to
  them
- **THEN** the conductor writes the `decisions/<slug>.md` record and only
  then checks the task, because a checked decision task without its record
  is not a closed decision

### Requirement: The session section coaches what a surface contains

The skill's design-session section SHALL state what a surface should
actually contain rather than only that one should be built: code samples,
configuration examples, diagrams, and conceptual SVGs that carry the shape
of the thing being decided. It SHALL name `branch-topology-diagram` as a
ready tool for branch and worktree topology, so a session reaches for it
rather than describing a topology in prose.

The skill SHALL state the criterion for the other answer: when the material
is a document the operator reads rather than a set of choices they work, a
plan reviewed in plannotator is the better surface and no interactive one
is built.

#### Scenario: A session builds a surface of prose

- **WHEN** a session would present coupled options as paragraphs of
  description
- **THEN** the skill directs it to show the thing — the config that would
  change, the sample the choice produces, the diagram of the shape — beside
  each option

#### Scenario: A decision turns on branch topology

- **WHEN** a batch has to settle how branches and worktrees are laid out
- **THEN** the session uses `branch-topology-diagram` rather than writing
  the topology out in prose

#### Scenario: The material is a document, not a set of choices

- **WHEN** the batch's output is a plan or a chapter the operator reads
  through
- **THEN** the skill has the session run a plannotator round on it instead
  of building an interactive surface

### Requirement: The dispatch section, retitled and carrying both directions

The section titled "Intake agent — raw idea → the right place"
SHALL be retitled **"Dispatch — raw idea → the right place, and the relay
in both directions"** and SHALL carry both halves of the actor's job:

- **Routing** a raw idea to one of three places: a new intent change, an
  amendment requested of a running bolt, or the chore route.
- **Relaying** in both directions — inner-loop escalations from bolt
  conductors out to the operator, and the operator's answers back to the
  bolt conductor that raised them.

The skill's frontmatter `description` and its list of the roles that load
it SHALL name dispatch rather than intake. The word `intake` SHALL NOT
appear in the skill as the name of the actor.

The skill SHALL refer to *dispatch* the actor and SHALL NOT use
*dispatching* as a verb where the sentence could be read as job-queue
vocabulary.

#### Scenario: An agent looks for the intake section

- **WHEN** an agent reads the skill for what to do with a raw idea
- **THEN** it finds the dispatch section, and finds nothing in the skill
  that names an intake actor

#### Scenario: A bolt conductor escalates a question it cannot answer

- **WHEN** a bolt conductor has a question for the operator
- **THEN** the skill's dispatch section is where the relay is described:
  dispatch carries it out to the operator and carries the answer back to
  the bolt conductor that raised it, rather than the bolt conductor
  addressing the operator through a channel of its own

### Requirement: A conductor and its sessions each have an exact write scope

The skill SHALL state as a rule — not as an implication of the task types —
that an intent conductor writes the change's own artifacts under
`openspec/changes/<id>/`, that its design sessions write their session
directories under it, their own task lines, and the decision records for
questions their work orders charged them to close — all inside their own
worktrees, admitted by the conductor's merge — and that both write the
books and the context map. Every
other file edit in any repo is construction and leaves through the phase
gate as a handoff, **including edits to blueprints itself**.

The rule SHALL be stated in that three-part form and SHALL NOT be
compressed into a single clause attributing the change's artifacts to the
conductor and its sessions together. Compressed, it reads on a steering
surface as a grant of the canonical artifacts to a session, which
contradicts `sole-writer-conductors.md` and `session-directories.md` — the
conductor is the only writer of the canonical artifacts, a session writes
only its assigned directory, and the conductor promotes outward. It
remains the *two-things* rule because each actor writes two things: the
conductor its artifacts and the books-and-map, the session its directory
and the books-and-map. The skill SHALL NOT add a fourth part.

The skill SHALL state that when an intent's subject is the machinery
blueprints carries — its skills, agent profiles, schema instructions,
`CLAUDE.md` conventions, plugins — blueprints is that intent's built repo
in the ordinary sense, and being the repo the conductor happens to run in
changes nothing.

The skill SHALL state that a design session is single-purpose within the
intent: it burns fog into decisions, writes the destination into the books
and map, and checks tasks off. It does not dispatch agent work. Work that
dispatches agents is a proposal in a bolt, and a small one is a
one-proposal bolt, never an untracked edit.

The skill SHALL state that a Writeback task is a book chapter or the
context map and nothing else, and that a task filed as Writeback whose
target is neither is a misfiled Handoff.

The skill SHALL NOT simultaneously authorize what that rule forbids. The
existing writebacks rule ends *"Non-book writeback targets (research docs,
the roadmap) are named on the task line"*, which grants exactly the targets
the guardrail excludes, in the same file. That sentence SHALL be removed,
and research documents and the roadmap SHALL be named as Handoff targets:
they are files in a built repo like any other, and a task that edits one
leaves through the phase gate.

#### Scenario: A task names the roadmap as its writeback target

- **WHEN** a conductor reaches a task whose target is `research/` or the
  kit-reorg roadmap, filed as Writeback
- **THEN** the skill routes it to Handoff, and carries no sentence that
  could be read as permitting the edit under a writeback task line

#### Scenario: A task on the frontier would rewrite an agent profile

- **WHEN** an intent conductor reaches an unchecked task that renames an
  agent profile, rewrites a skill, or edits a schema instruction — all
  inside blueprints, the repo it is running in
- **THEN** the skill stops it: the task is construction against blueprints
  as a built repo, so the conductor re-sorts it as a Handoff naming its
  built repo and its proposal, and spawns no session for it

#### Scenario: A Writeback task points at a conventions doc

- **WHEN** a task filed under Writeback names `books/CLAUDE.md`, a plugin
  skill, or a `.claude/` file as its target
- **THEN** the skill identifies it as a misfiled Handoff and has the
  conductor move it, rather than treating the Writeback label as
  authorization

#### Scenario: A session is asked to make an agent build something

- **WHEN** a design session's batch would be worked by dispatching agents
  to write code
- **THEN** the skill tells it that is a proposal in a bolt, and the session
  reports the work for handoff rather than dispatching

#### Scenario: A session reads the rule to learn what it may write

- **WHEN** a design session finishes a batch and reads this rule to decide
  whether it may write the decision record it drafted into `decisions/`, or
  check its own task off in `tasks.md`
- **THEN** the rule tells it no: those are the change's canonical artifacts
  and the conductor is their only writer. The session writes its assigned
  directory and delivers outcomes, and the conductor promotes and checks
  off

#### Scenario: A conductor writes into a session's directory

- **WHEN** an intent conductor would edit a decision draft inside
  `sessions/<date>-<slug>/`
- **THEN** the rule's second part is the session's, not the conductor's:
  the conductor promotes what the session delivers rather than editing in
  place

### Requirement: The chore route belongs to dispatch at triage and closes after

The skill SHALL scope the chore route — running `opsx` directly in a built
repo with no tracking at all — to dispatch, at the moment of triage, before
any intent exists. It SHALL state that the route closes once an intent owns
the work: an intent conductor and its sessions SHALL NOT reach for it, and
a task already sitting on an intent's `tasks.md` SHALL NOT be drained as a
chore however small it is.

The skill SHALL state the one path out of the phase gate for such work: a
released handoff becomes a bolt with a bolt conductor whatever its size,
and a handoff carrying a single proposal is a one-proposal bolt — a named
special case of that path, not a different one. Nothing releases into a
bare work branch off main.

#### Scenario: A conductor judges a task too small to be worth a bolt

- **WHEN** an intent conductor reaches a one-file rename on its frontier
  and would do it inline as a pure chore
- **THEN** the skill refuses the route: the chore route is dispatch's
  alone and closed once the intent owns the work, so the conductor prepares
  it as a one-proposal bolt handoff instead

#### Scenario: Dispatch triages an idea with no design content

- **WHEN** a raw idea arriving at dispatch is small, fully defined, and
  carries no design content
- **THEN** the chore route is open, dispatch takes it, and no tracking is
  created — and the skill notes that if even that feels heavy, some ideas
  are just a shell command

### Requirement: The conductor drives continuously and the gate authorizes

The skill's conductor section SHALL be written around driving rather than
around permission. It SHALL state, per task type:

- An unblocked **Design** task spawns a design session.
- An unblocked **Writeback** task spawns a writeback session **without
  asking anyone** — writeback is the books and the map, which is the
  conductor's own scope.
- An unblocked **Handoff** task is prepared to the point of one decision —
  the proposals batched, the bolt named, the repos and merge criteria
  drafted — and then gated by **one inline approval covering the whole
  batch at once**, on the cheapest channel that carries it, explicitly not
  a plannotator or lavish round.

The skill SHALL state that the gate authorizes release and is not a
meeting, a status report, or a reason to stop, and that a conductor with
unblocked work that is waiting for the operator to raise the subject is
malfunctioning.

The skill SHALL keep the rule that handoff is a request and never a write —
the conductor never authors a bolt change's decision to exist — while
stating that the conductor does the naming and drafting before asking, so
the operator answers rather than designs.

#### Scenario: The frontier has several unblocked tasks of both kinds

- **WHEN** a conductor's `tasks.md` shows three unblocked Writeback tasks
  and seven unblocked Handoff tasks
- **THEN** the skill has it spawn the three writeback sessions immediately
  without asking, batch the seven handoffs into named bolts with drafted
  merge criteria, and put **one** inline question to the operator covering
  the batch — rather than reporting the frontier and waiting

#### Scenario: A conductor has reported and heard nothing back

- **WHEN** a conductor has told the operator what is unblocked and the
  operator has not raised the subject again
- **THEN** the skill names that state as a malfunction rather than as
  patience, and the conductor drives the work its own scope covers and
  gates the rest in one question

#### Scenario: A conductor would gate its own writeback

- **WHEN** a conductor would ask permission before rewriting a book chapter
  or moving a map status
- **THEN** the skill tells it not to: writeback is its own scope and needs
  no gate

### Requirement: Launch lines name the profiles that exist

The skill SHALL launch design sessions under
`.claude/agents/flywheel-design-session.md` or
`.claude/agents/flywheel-interactive-session.md`, chosen by the
host-profile rule below and by no other basis, and the spawn line SHALL
name which one it is starting. The work order SHALL name the session-type
skill for the batch's type.

The six design-type skills are `flywheel-planning`, `flywheel-interactive`,
`flywheel-prototype`, `flywheel-research`, `flywheel-writeback` and
`flywheel-handoff` (`session-types-are-skills.md`); the seven
construction-type skills are the bolt loop's and named in
`flywheel-construction`.

The naming rule the skill SHALL follow wherever it distinguishes the two:
**an actor says "session", a way of working never does.** A profile is
`flywheel-<type>-session`; a skill is `flywheel-<type>`. The distinction is
the presence or absence of the word, not the order of the words — an
earlier draft used `flywheel-session-<type>`, the same words as the profile
in the other order, and two independent reviewers confused the pair, the
second reporting a correct proposal as internally inconsistent. The skill
SHALL NOT state the rule as a word-order rule.

These names are the public invocation surface once the machinery splits out
(`flywheel:planning`, `flywheel:writeback`), which is why they are fixed
before they harden across skills, profiles, schema instructions and launch
lines.

The retired name `flywheel-review-session` SHALL NOT appear anywhere in
the skill, and the same holds for
`.claude/agents/flywheel-intent-conductor.md` under the conductor-profiles
capability: the rename applies forward everywhere, and a surviving
reference is the one-answer defect.

#### Scenario: A batch of decision drafts is charged

- **WHEN** the conductor charges a batch that works written artifacts
  through plannotator and builds no lavish surface
- **THEN** the skill's launch line starts `flywheel-design-session` — the
  host-profile rule answers no — and the work order names `flywheel-planning`

#### Scenario: A batch needing options side by side is charged

- **WHEN** the conductor charges a batch that will build a lavish surface
- **THEN** the skill's launch line starts `flywheel-interactive-session` —
  the one case the rule answers yes — and the work order names
  `flywheel-interactive`

#### Scenario: A prototype batch is charged

- **WHEN** the conductor charges a batch that will build a throwaway to
  settle a fact
- **THEN** the skill charges it under `flywheel-design-session` — the
  session builds no lavish surface — with `flywheel-prototype` as
  the type skill; it does not look for a prototype profile, because there
  is none

### Requirement: The boundary with the session-type skills

The **criterion for choosing** a session type SHALL stay in this skill,
where the conductor reads it when charging. The **practice for running** a
type SHALL move to that type's skill, where the session reads it after
being charged. Applied to the passages the type skills draw from:

| passage | disposition |
|---|---|
| "Review surfaces" bullet | stays, trimmed to the choosing criterion and pointed at the five type skills; the per-surface mechanics move out |
| "Prototype when talk stalls" | splits — the criterion clause stays; the mechanics move to `flywheel-prototype` |
| "Write the destination" | moves whole to `flywheel-writeback` |
| "Batch decisions into one artifact" | moves to `flywheel-interactive` |

Nothing else in the shared-rules block SHALL move.

The rule that a Writeback task may target only a book chapter or the
context map SHALL be stated in this skill **independently of the moved
passage**, as part of the two-things rule. A guardrail SHALL NOT depend on
a passage that moves.

The cross-role content this change adds — the channel matrix, the
outer-loop default, the escalation rule, the invoker rule, the annotation
triage — SHALL be stated as shared rules of its own rather than folded into
the trimmed "Review surfaces" bullet, whose job is to help a conductor pick
a type.

#### Scenario: The prototype passage is looked for after the split

- **WHEN** an agent reads `flywheel-inception` for how to run a prototype
- **THEN** it finds the criterion — the decision turns on a fact a
  throwaway can prove faster than an argument can settle — and is pointed
  at `flywheel-prototype` for the practice; the worktree and the
  finding's shape are stated there and not here

#### Scenario: The writeback passage moves whole and the guardrail survives

- **WHEN** an agent reads `flywheel-inception` for what a Writeback task
  may target, after "Write the destination" has moved out
- **THEN** it finds the rule stated in the two-things rule — a book chapter
  or the context map and nothing else, anything else a misfiled Handoff —
  and is pointed at `flywheel-writeback` for how the rewrite is
  done

#### Scenario: A shared rule is restated in a type skill

- **WHEN** any session-type skill would restate the channel matrix, the
  invoker rule, the two-things rule, or the sole-writer and inbox protocols
- **THEN** the content belongs to `flywheel-inception` and the type skill
  points at it, with the two-things rule the one deliberate duplication and
  its reason on the record

### Requirement: A session owns a worktree and a branch, not only a directory

The skill's conductor section SHALL carry the spawn recipe: a design
session runs in its own worktree on its own branch, cut by worktrunk —
`wt switch --create sess/<slug> --base main --no-cd`, then
`herdr tab create --cwd <worktree>` and `herdr agent start` in that pane.
`--no-hooks` SHALL NOT appear: this repo configures no `wt` lifecycle
hooks, so the flag suppresses nothing today and would silently skip the
cold-start hook the moment one exists.

The skill's session section SHALL state that a session owns a worktree and
a branch, not only a `sessions/<date>-<slug>/` directory, and that the
session commits to `sess/<slug>`.

The fold SHALL gain one step ahead of promotion: the conductor merges the
session branch through the gate — `wt merge --no-remove -C <worktree>` —
and then the worktree and its branch are removed. The full gate is the
right gate for a documentation session, since books, mermaid and map are
what it should have to pass.

Teardown SHALL be named as the conductor's duty: a session is not done
until its worktree and branch are gone.

The skill SHALL keep commit-by-pathspec as a standing rule regardless,
because the conductor still commits on main where a session's fold may be
in flight: an actor stages and commits the paths it wrote — never `-a`,
never `add -A`, never a pathspec-less `git commit`.

#### Scenario: A conductor spawns a session

- **WHEN** an intent conductor charges a batch
- **THEN** it cuts `sess/<slug>` with worktrunk and starts the session in a
  pane on that worktree, rather than starting a session in the main
  checkout

#### Scenario: Two sessions run in parallel

- **WHEN** two sessions work disjoint batches at the same time
- **THEN** they share neither a working tree nor a git index, which is what
  the rule protects: a pathspec-less commit in one can no longer sweep what
  the other staged

#### Scenario: A session reports and the conductor promotes

- **WHEN** a session delivers its outcomes
- **THEN** the conductor merges `sess/<slug>` through the full gate before
  promoting, and removes the worktree and branch — the session is not done
  while either survives

### Requirement: One rule assigns every type to a host profile

Wherever the skill states which profile a session runs under, it SHALL
state exactly this rule and nothing more: does this session build a lavish
surface? Yes → `flywheel-interactive-session`. No — planning, research,
prototype, writeback, handoff → `flywheel-design-session`.

The skill SHALL NOT offer a second or competing basis for the assignment,
such as which surface the session reports through, which surface the batch
works, or which tool it happens to use. **Neither profile SHALL be
described by the surface its session works**:
`flywheel-design-session` hosts prototype, research, writeback and handoff
as well as planning, and none of those four works a written-artifact surface, so a
description by surface leaves a conductor charging a writeback batch with a
rule that has no answer.

#### Scenario: A research batch is charged

- **WHEN** the conductor charges a batch that will read rather than build
  and answer a factual question
- **THEN** the host profile is `flywheel-design-session`, because the
  session builds no lavish surface, and the work order names
  `flywheel-research`

#### Scenario: A writeback batch is charged

- **WHEN** the conductor charges a batch of book chapters and a map update
- **THEN** the host profile is `flywheel-design-session` and the work order
  names `flywheel-writeback`

#### Scenario: An option comparison is charged

- **WHEN** the batch will put coupled options side by side on a built
  surface
- **THEN** the host profile is `flywheel-interactive-session` — the one
  case the rule answers yes

