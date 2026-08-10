# flywheel-conductor-profiles Specification

## Purpose
The two conductor agent profiles — the identity that is in place before a
conductor's first prompt and survives compaction — carrying edit scope and
the three rules a conductor must reach correctly from its profile alone,
because each of those three was broken by an agent that had read the skill.
## Requirements
### Requirement: Profiles stay thin, and the three rules are the exception

Both `.claude/agents/flywheel-intent-conductor.md` and
`.claude/agents/flywheel-bolt-conductor.md` SHALL keep their existing shape:
identity, the change the first prompt binds them to, edit scope, and
pointers at their loop skill and the schema's artifact instructions as the
single statement of the practice.

The three rules below are the deliberate exception to that thinness, and
the reason SHALL be legible: each names a conclusion a conductor must not
be able to reach, and each was reached by an agent that had already loaded
the skill. A rule stated only in the skill is not enough.

Neither profile SHALL restate the practice its skill carries beyond those
three rules, and neither SHALL bind the conductor to a particular change —
that comes from the first prompt.

#### Scenario: A conductor needs to know how to run a review round

- **WHEN** a conductor needs the mechanics of a plannotator round, the
  channel matrix, or what a decision record contains
- **THEN** the profile points it at its loop skill and the schema
  instructions rather than answering

#### Scenario: A conductor reads only its profile before acting

- **WHEN** a conductor's first action after launch would break one of the
  three rules, and it has not yet loaded its skill
- **THEN** the profile alone stops it

### Requirement: The intent conductor profile carries the two-things rule

`.claude/agents/flywheel-intent-conductor.md` SHALL state, as a rule rather
than an implication, that the conductor writes the change's own artifacts
under `openspec/changes/<id>/`, its design sessions write their session
directories under it, and both write the books and the context map — and
that every other file edit in any repo is construction leaving through the
phase gate as a handoff, **including edits to blueprints itself**.

The attribution SHALL NOT be compressed into one clause covering the
conductor and its sessions together: on a steering surface that reads as a
grant of the canonical artifacts to a session, against
`sole-writer-conductors.md` and `session-directories.md`. The profile SHALL
state that the conductor is the only writer of the canonical artifacts and
that it promotes what a session delivers rather than editing the session's
directory in place. The three-part shape SHALL NOT gain a fourth part.

It SHALL state that when the intent's subject is the machinery blueprints
carries — skills, agent profiles, schema instructions, `CLAUDE.md`
conventions, plugins — blueprints is that intent's built repo in the
ordinary sense, and being the repo the conductor runs in changes nothing.

It SHALL state that a Writeback task is a book chapter or the context map
and nothing else, and that a task filed as Writeback with any other target
is a misfiled Handoff. This rule belongs to **this profile only**: a bolt
conductor has no Writeback tasks, so `flywheel-bolt-conductor.md` carries
no version of it and gains nothing from one.

It SHALL state the conductor's session duties per
`decisions/session-worktrees.md`: sessions are spawned into their own
worktree and branch (`sess/<slug>`), the fold merges that branch through
the full gate before promoting, and teardown — worktree and branch gone —
is the conductor's, since a session is not done until they are.

#### Scenario: A frontier task would rewrite a skill in blueprints

- **WHEN** an intent conductor reaches an unchecked task that renames an
  agent profile or rewrites a skill, in the blueprints checkout it is
  running in
- **THEN** the profile it read tells it this is construction against
  blueprints as a built repo, so it re-sorts the task as a Handoff and
  spawns no session for it — reaching that conclusion from the profile
  alone

#### Scenario: The conductor would write a session's decision draft

- **WHEN** an intent conductor would edit a decision draft inside a
  session's `sessions/<date>-<slug>/` directory, or a session would write
  the change's `decisions/` or `tasks.md` directly
- **THEN** the profile's three parts assign each write to one actor: the
  canonical artifacts are the conductor's alone, the session directory is
  the session's alone, and outcomes cross between them by promotion

#### Scenario: Six machinery tasks sit under Writeback

- **WHEN** tasks that edit profiles, skills, schema files, and conventions
  docs have been filed under Writeback
- **THEN** the profile has the conductor move them to Handoff, because the
  Writeback label is a description and not an authorization

### Requirement: The intent conductor profile closes the chore route

`.claude/agents/flywheel-intent-conductor.md` SHALL state that the chore
route — running `opsx` directly in a built repo with no tracking — belongs
to dispatch at the moment of triage, before an intent exists, and that it
is closed to the conductor. A task already sitting on the intent's
`tasks.md` SHALL NOT be drained as a chore however small it is.

It SHALL state the one path out: a released handoff becomes a bolt with a
bolt conductor whatever its size, and a single-proposal handoff is a
one-proposal bolt — a named special case, not an exit.

#### Scenario: The conductor judges a task too small for a bolt

- **WHEN** an intent conductor would do a one-file rename inline as a "pure
  chore" because opening a bolt for it feels heavy
- **THEN** the profile refuses the route and names where it lives —
  dispatch, at triage — so the conductor prepares a one-proposal bolt
  handoff instead

### Requirement: The intent conductor profile makes driving the default

`.claude/agents/flywheel-intent-conductor.md` SHALL state that the
conductor drives continuously:

- an unblocked Design task spawns a design session;
- an unblocked Writeback task spawns a writeback session **without asking
  anyone**, because writeback is the conductor's own scope;
- an unblocked Handoff task is prepared to one decision — proposals
  batched, bolt named, repos and merge criteria drafted — and then gated by
  **one inline approval covering the whole batch**.

It SHALL state that the gate authorizes release and is not a meeting, a
status report, or a reason to stop, and that a conductor with unblocked
work waiting for the operator to raise the subject is malfunctioning.

The existing line "Handoff is a request, behind the operator's phase gate —
you never write a bolt change" SHALL keep its rule and lose any reading
that the conductor waits to be asked.

#### Scenario: The conductor reports a frontier and stops

- **WHEN** a conductor has counted its unblocked Writeback and Handoff
  tasks and would tell the operator about them and wait
- **THEN** the profile names that as a malfunction: it spawns the writeback
  sessions immediately and puts one inline question covering the whole
  handoff batch

#### Scenario: The operator is asked proposal by proposal

- **WHEN** a conductor has seven releasable proposals and would ask about
  each in turn
- **THEN** the profile has it batch them into one question, with the naming
  and drafting done first so the operator answers rather than designs

### Requirement: The bolt conductor profile carries the same three rules, from its side

`.claude/agents/flywheel-bolt-conductor.md` SHALL state:

1. The conductor writes the bolt change's own artifacts, its spec, apply
   and testing agents write the spec-driven changes and branches their
   registry rows name, and every file edit the bolt lands is carried by
   such a row — there is no untracked edit inside a bolt. This holds when
   the built repo is blueprints itself, which runs as an ordinary built
   repo with its own `bolt/<slug>` branch and worktree. As on the intent
   side, the attribution is per actor and SHALL NOT be compressed into one
   clause covering the conductor and its agents together: the conductor is
   the only writer of the bolt change, and an agent that edits it directly
   instead of reporting is the failure the split prevents.
2. The chore route is closed inside a bolt: work in scope grows the
   registry with a row, and work out of scope goes back to dispatch. It is
   never applied directly because it is small.
3. The conductor drives its registry — every row with an unblocked next
   action is dispatched without waiting to be asked — and the parked
   posture applies only when no row has one. The operator's moments are the
   phase gate that created the bolt and the closure it agrees to; the gate
   that released the bolt is also the approval for its waves, so the
   conductor does not re-gate each spec agent.

The profile's existing line "Between batches you wait on the operator,
drain requests, and accept pushed work" SHALL be repaired rather than left
standing: unqualified, it is the same sentence shape that produced the
intent conductor's stall, and the intent conductor's profile is repaired
for exactly that reason. Waiting is conditional on no row having an
unblocked next action.

#### Scenario: The bolt conductor notices a fixable problem off-registry

- **WHEN** a bolt conductor sees a small problem in a file no row covers
- **THEN** the profile has it grow the registry or route to dispatch, and
  never edit the file directly

#### Scenario: The registry has unblocked rows and the operator is quiet

- **WHEN** rows sit at `to-spec` and `built` with nothing running
- **THEN** the profile has the conductor dispatch, not park — parking is
  for a registry with nothing unblocked

#### Scenario: A blueprints-machinery bolt

- **WHEN** the bolt's proposals all edit `.claude/` and `openspec/schemas/`
  in blueprints
- **THEN** the profile has the conductor treat blueprints as an ordinary
  built repo: a bolt branch and worktree, a row per proposal, the same
  gates

### Requirement: The intent conductor's spawn line names the profiles that exist

`.claude/agents/flywheel-intent-conductor.md`'s spawn line SHALL name
`flywheel-design-session` or `flywheel-interactive-session`, chosen by the
host-profile rule — does this session build a lavish surface? yes →
interactive, no → the default host — and by no other basis, and SHALL
state that the work order names the session-type skill. The retired name
`flywheel-review-session` SHALL NOT appear in either conductor profile.

#### Scenario: The profile is searched for the deleted name

- **WHEN** either conductor profile is searched for `flywheel-review-session`
  after the rename has landed
- **THEN** there are no hits

