# flywheel-session-profiles Specification

## Purpose
The agent profiles a flywheel design session runs under — the identity that
is in place before the first prompt and survives compaction, split by
whether the session's batch work builds a lavish surface, carrying edit
scope and nothing more.
## Requirements
### Requirement: Two design-session profiles

The repo SHALL carry exactly two design-session agent profiles:
`.claude/agents/flywheel-interactive-session.md`, which hosts the one type
that builds an interactive surface in lavish, and
`.claude/agents/flywheel-design-session.md`, the default host for every
other type — whose *planning type* works written artifacts through
plannotator. `flywheel-design-session` SHALL NOT be described by the
surface its session works, since four of the five types it hosts do not
work plannotator at all, and describing it that way would supply a second
basis for the assignment the next requirement forbids.
`flywheel-interactive-session` may be described by its surface, because
the lavish surface is exactly what its one hosted type is defined by and
is the assignment's only basis.

The intent conductor SHALL choose between them at work-order time, and its
spawn line SHALL name which one it is starting.

Both profiles SHALL be usable as a main session's identity
(`claude --agent <profile>` in a herdr pane) and SHALL declare that they
are not intended as Task-tool subagents.

#### Scenario: A batch is charged as a planning-type session

- **WHEN** an intent conductor charges a batch as the planning type, whose
  work is annotating the decision drafts and plans the session itself
  writes
- **THEN** it launches `flywheel-design-session`, and the spawn line names
  that profile

#### Scenario: A batch needing an option comparison is charged

- **WHEN** an intent conductor charges a batch as the interactive design
  type — options with trade-offs, a report with controls, diagrams
- **THEN** it launches `flywheel-interactive-session`, and the spawn line
  names that profile

### Requirement: One rule assigns every type to a host profile

Every session type SHALL run under one of the three host profiles, and
the assignment SHALL follow one two-part question: which loop is this,
and does the session's BATCH WORK build a lavish surface? Construction —
all seven
types — SHALL run under `flywheel-construction-session`. Design whose
batch work builds a lavish surface is interactive design and SHALL run
under `flywheel-interactive-session`; design whose batch work does not —
planning, research, prototype, writeback — SHALL run under
`flywheel-design-session`.

The round-close plan any design session may end with
(`skills/_reference/round-close.md`) is NOT part of the basis: its lavish
page belongs to the close, not to the batch work, and counting it would
collapse every type into the interactive profile. Of the four types the
default profile hosts, **only the planning type opens a plannotator round
over its batch work**. Prototype, research, and writeback batch work
opens none: a prototype delivers a finding note, a research session
delivers its report, and a writeback session rewrites chapters — none of
which the session puts in front of the operator for annotation. No
further design profile SHALL be created for them.

This question is the assignment's only basis. No profile, skill, or schema
instruction SHALL offer a second one — not the task type, not the surface
the session reports through, not which tool it happens to open — because a
second basis is what lets two readers reach different profiles for the same
type.

#### Scenario: A prototype session is charged

- **WHEN** an intent conductor charges a prototype session
- **THEN** it launches `flywheel-design-session` with the prototype type
  named in the work order, because the session builds no lavish surface

#### Scenario: A writeback session is charged

- **WHEN** an intent conductor charges a batch of book-chapter rewrites,
  whose batch work uses neither plannotator nor lavish
- **THEN** it launches `flywheel-design-session` with the writeback type
  named in the work order, and the session rewrites chapters and runs the
  gates without opening a review round on them — a round-close plan at its
  end, if it has one to propose, does not change which profile hosted it

#### Scenario: A prototype session considers annotating its finding

- **WHEN** a prototype session has written `prototypes/<slug>.md` and could
  open a round on it, since it is a file the session itself wrote
- **THEN** it opens none and delivers the finding to its conductor, because
  only the planning type opens batch-work rounds — a round-close plan
  routes outcomes and is not an annotation surface; if the operator should
  annotate what the prototype proved, the conductor charges a
  planning-type session for it

#### Scenario: An agent looks for a third profile

- **WHEN** an agent looks for a profile of its own for prototype, research,
  or writeback work
- **THEN** it finds none: those are session *types* steered by skills, and
  the one rule above assigns each to a host profile — and it finds no
  second rule anywhere that could assign them differently

### Requirement: A planning session annotates only what it wrote

`flywheel-design-session`'s body SHALL bound its plannotator scope to files
the session itself wrote — the decision drafts and plans in its own
`sessions/<date>-<slug>/` directory. It SHALL NOT open a round on
`intent.md`, whose sole writer is the conductor or dispatch, nor on a
generated proposal, whose sole writer is the bolt conductor.

The profile SHALL state this as its own scope and SHALL point at the
invoker rule in `flywheel-inception` rather than restating it: that rule
binds dispatch and both conductors as well as sessions, so the profile is
not its home. This is the same treatment the two-things rule gets in
reverse — that rule is restated here because
`blueprints-is-a-built-repo.md` requires the profile to carry it; the
invoker rule carries no such requirement, so pointing is correct.

#### Scenario: A session is asked to run a round on the intent

- **WHEN** a planning session is charged with, or reaches, a task that would
  annotate `intent.md` or a generated proposal
- **THEN** it declines the round and reports it to its conductor, because
  running it would route the operator's feedback to an actor that is not
  the file's sole writer

#### Scenario: Annotations come back to the session that ran the round

- **WHEN** the operator finishes annotating a decision draft in the
  session's own directory
- **THEN** the result returns to that session, which folds it into its own
  draft — the raw annotations are not relayed to another actor and not
  written into another actor's directory

### Requirement: Profiles are thin — identity and edit scope only

Each design-session profile SHALL carry only its identity, its edit scope,
and pointers to the practice: the `flywheel-inception` skill's design
session section, its own session-type skill, and the `flywheel-intent`
schema's artifact instructions. A profile SHALL NOT restate the practice
those sources carry, and SHALL NOT bind the session to a particular change
— which change and which task batch come from the work order, not the profile.

#### Scenario: Practice is read from the skill, not the profile

- **WHEN** a session needs to know how to run its surface, what a decision
  draft contains, or how a report is delivered
- **THEN** the profile points it at `flywheel-inception` and its
  session-type skill rather than answering, and those remain the single
  statement of the practice

#### Scenario: The work order, not the profile, names the work

- **WHEN** a session starts under either profile
- **THEN** its work order names the intent change, the task batch, and its
  `sessions/<date>-<slug>/` directory, and the profile names none of them

### Requirement: Every profile body carries the write-scope rule

Each session profile body SHALL state, as a rule rather than an
implication, exactly what its sessions write inside their worktrees — the
assigned session directory, the session's own task lines, the decision
records for questions the work order charged it to close, and the books
and the context map that its tasks name (for a construction session: the
built repo and its own task lines) — and that every other file edit in
any repo is construction, **including edits to the machinery's own
repos**: construction work is born by the planner's cards and the
operator's approval, and a session that finds such work queues the
finding and makes no edit. Each body SHALL also state that a session is
never the way to make an agent build something: it launches no other
session and spawns no agents onto its work.

#### Scenario: A task proposes editing machinery in blueprints

- **WHEN** a session working in blueprints reaches a task that would edit a
  skill, an agent profile, a schema instruction, or a `CLAUDE.md`
- **THEN** the profile it read tells it this is construction against
  a built repo, so it queues the finding instead of making the edit —
  reaching that conclusion from the profile alone, without having loaded
  any skill

#### Scenario: A session's batch would be finished by dispatching agents

- **WHEN** a session working its batch concludes the remaining work is best
  done by spawning agents to do it
- **THEN** it spawns none, and queues the work as a finding for the
  loop that charged it — reaching that from the profile alone, without
  having loaded any skill

### Requirement: A session owns a worktree and a branch, not only a directory

Both profile bodies SHALL state that a design session runs in its own
worktree on its own branch — `sess/<slug>`, cut by worktrunk — and not
merely in a directory inside the conductor's checkout. The session commits
to that branch; the conductor stays on main, merges the session branch
through the full gate before promoting, and removes the worktree and branch
afterwards, so a session is not done until they are gone.

Both bodies SHALL also carry the standing staging rule: an actor stages and
commits the paths it wrote — never `-a`, never `add -A`, never a
pathspec-less `git commit`.

#### Scenario: Two sessions run at once

- **WHEN** an intent conductor runs two sessions on disjoint batches at the
  same time
- **THEN** each is in its own worktree on its own branch, so neither can
  stage into the other's index — the failure that put one session's five
  chapter deletions into another session's commit

#### Scenario: A session commits its work

- **WHEN** a session commits what it produced
- **THEN** it names the paths it wrote, using no `-a`, no `add -A`, and no
  pathspec-less `git commit`

#### Scenario: A session's outcomes are promoted

- **WHEN** a session reports and its conductor promotes the outcomes
- **THEN** the conductor merges `sess/<slug>` through the full gate first,
  then removes the worktree and the branch — the session is not done until
  both are gone

### Requirement: A session never idles waiting to be asked

A session with unblocked work in its charge SHALL proceed on it without
seeking an approval that does not exist for it: the operator's approval
was spent releasing the batch. A session that has unblocked work and is
waiting for the operator to raise the subject SHALL be treated as
malfunctioning, not as being careful.

#### Scenario: A writeback session waits to be told to start

- **WHEN** a session charged with book-chapter rewrites finishes reading
  its batch and pauses for the operator to confirm it should proceed
- **THEN** that is the malfunction the profile names: writeback carries no
  gate, and the session does the work it was charged with and reports

#### Scenario: A session reaches settled work that would build something

- **WHEN** a session's batch turns up a settled slice ready for
  construction
- **THEN** it queues the finding rather than seeking a release itself —
  released construction arrives through the planner's cards, and the
  session neither asks for that release nor waits on it

### Requirement: Session edit scope is stated per profile

Each profile SHALL state its writes precisely: the assigned session
directory is the session's alone (surfaces, decision drafts, prototype
notes — real committed files, committed on the session's own branch in its
own worktree), the intent change's canonical artifacts beyond the session's own task
lines and charged closures are never written by a session but delivered
to the conductor, whose merge admits and who opens what the session
discovered, and writeback targets are only those the session's tasks name — stated
with its bound attached, **book chapters per `books/CLAUDE.md` and the
context map with `map-check --write` green**, never as a bare "the targets
your tasks name", which delegates the decision to whatever the task line
happens to say.

#### Scenario: A task line names a target outside the bound

- **WHEN** a session's task line is filed as Writeback but names a skill
  file, an agent profile, or a `CLAUDE.md`
- **THEN** the profile's own sentence settles it against the task line: the
  target is not a book chapter or the map, so the session refuses it as
  construction and queues the finding

#### Scenario: A session checks off its own task lines and no others

- **WHEN** a session finishes a batch and would mark task lines done in
  `tasks.md`
- **THEN** the profile permits exactly the lines its work order assigned,
  checked off inside the session's own worktree, and forbids every other
  line; the conductor's merge is what admits them, and the conductor
  opens what the session discovered

#### Scenario: Two sessions write disjoint batches

- **WHEN** an intent conductor runs two sessions on disjoint batches
- **THEN** each writes only its own session directory, its own task
  lines, and its own charged closures, in its own worktree — disjoint
  batches, disjoint writes

### Requirement: The retired profile name is removed

`.claude/agents/flywheel-review-session.md` SHALL be removed, and no
launch line, skill, schema instruction, or end-to-end script left in the
repo SHALL name it — the rename to `flywheel-design-session` applies
forward everywhere.

#### Scenario: A stale launch line survives the rename

- **WHEN** the repo is searched for `flywheel-review-session` after the
  rename has landed
- **THEN** there are no hits outside change artifacts and requirements
  that guard the retired name

