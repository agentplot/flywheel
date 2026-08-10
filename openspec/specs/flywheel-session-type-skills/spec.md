# flywheel-session-type-skills Specification

## Purpose
The skills that steer a flywheel session by the kind of work it is doing —
one per session type across both loops, each wrapping the tool or the
convention that type runs on — so that launching a nested session under a
conductor means loading the skill for its type.
## Requirements
### Requirement: Thirteen session-type skills

The repo SHALL carry one skill per session type under `.claude/skills/`:

| skill | type | default model | what it wraps |
|---|---|---|---|
| `flywheel-planning` | planning | fable | plannotator, over drafts the session wrote |
| `flywheel-interactive` | interactive design | fable | lavish, over a built surface |
| `flywheel-prototype` | prototype | fable | a throwaway built in a spike-repo worktree |
| `flywheel-research` | research | fable | an investigation that reads rather than builds |
| `flywheel-writeback` | writeback | fable | `books/CLAUDE.md` and the destination voice |
| `flywheel-handoff` | handoff | fable | the release request to a bolt conductor, and its receipt |
| `flywheel-proposal-writing` | proposal-writing | fable | a bolt proposal drafted from released assertions |
| `flywheel-proposal-review` | proposal-review | fable | a read across the batch, against the cited decisions |
| `flywheel-spec-writing` | spec-writing | fable | `/opsx:ff` in the built repo, from the cited sources |
| `flywheel-build` | build | `opus[1m]` | `/opsx:apply` on a nested construction worktree |
| `flywheel-test` | test | `opus[1m]` | the batched acceptance run on the bolt branch |
| `flywheel-code-review` | code-review | `opus[1m]` | an adversarial or persona read of built work |
| `flywheel-human-code-review` | human-code-review | `opus[1m]` | plannotator, over built diffs for the operator |

The default-model column is the one enumeration of session-model
defaults (`session-model-defaults.md`); every launch path accepts a
runtime override via the invocation's args or the work order, and the
override wins.

Each skill SHALL state what its type is for, what its output is, and where
that output lands. Each SHALL point at `flywheel-inception` for the loop
practice rather than restating it.

#### Scenario: A conductor charges a batch that needs a throwaway

- **WHEN** a task batch turns on a fact a throwaway can prove faster than
  an argument can settle
- **THEN** the work order names the prototype type, and the session loads
  `flywheel-prototype`

#### Scenario: Writeback is a type without a surface tool

- **WHEN** a batch of chapter rewrites detaches from the session that
  closed the decisions behind them — because one surface closed more
  decisions than a single session can write back
- **THEN** it is charged as its own writeback session, steered by
  `flywheel-writeback`, which is a type in the same sense as
  prototype and research even though it wraps a convention rather than a
  tool

### Requirement: The planning skill applies the shared invoker rule to its own type

The invoker rule and the conductor's triage of returned annotations from
`decisions/review-launch-points.md` are obeyed by dispatch and both
conductors as well as by sessions, so they SHALL live as shared rules in
`flywheel-inception`. `flywheel-planning` SHALL point at them and
SHALL NOT restate them as its own.

What the skill SHALL state is what follows for a planning session: because a
round is opened by the sole writer of the file under review, this session's
rounds are on the drafts and plans in its own directory and nowhere else;
`plannotator annotate` returns its result to the session that ran it, which
folds corrections into its own drafts; raw annotations are never relayed to
another actor and never written into another actor's directory. The
three-way triage is the conductor's — a session SHALL report an outcome and
SHALL NOT append a task itself.

#### Scenario: An annotation asks for work beyond the batch

- **WHEN** an operator's annotation on a session's decision draft calls for
  design work the batch does not cover
- **THEN** the session reports it to its conductor as proposed new work,
  and the conductor decides whether it is a correction, a closed decision,
  or an appended Design task — the session appends nothing to `tasks.md`

#### Scenario: A session finishes a round on its own draft

- **WHEN** a round on a decision draft in the session's directory returns
- **THEN** the session applies the corrections to that draft, which it is
  the sole writer of, and reports which decisions closed

### Requirement: The type is chosen at work-order time and named in the work order

The intent conductor SHALL choose the session type when it charges a
session, and the work order SHALL name it alongside the change id, the task
batch, and the session directory. The session SHALL load that type's skill
before working the batch. A session SHALL NOT pick its own type.

#### Scenario: A session starts without a named type

- **WHEN** a session's work order does not name a type
- **THEN** the session asks its conductor rather than choosing, because the
  type determines which skill it loads, and — through the one rule in
  `flywheel-session-profiles` — which profile it should have been launched
  under

#### Scenario: The batch turns out to need a different type

- **WHEN** a planning session finds mid-batch that the decisions cannot be
  closed from a document and need a built surface
- **THEN** it reports that to its conductor as the next batch's type rather
  than switching surfaces inside its own run

### Requirement: Session types are skills, not OpenSpec schema types

Session types SHALL NOT become OpenSpec schema types with their own
artifact instructions. `flywheel-intent` and `flywheel-bolt` remain the two
schemas, and no session SHALL open an OpenSpec change of its own. What a
session did and what it produced are already carried by the intent's
`tasks.md`, `design.md`, and its own session directory.

#### Scenario: A session considers tracking itself

- **WHEN** a session looks for where to record that it ran and what it
  produced
- **THEN** it finds its `sessions/<date>-<slug>/README.md` and its report,
  which the conductor catalogs in `design.md` — and creates no change

### Requirement: Each type's output has one home

The type skills SHALL agree with the `flywheel-intent` schema on where
output lands, and SHALL NOT introduce a second home for anything:

- planning and interactive design — the surface and the decision drafts live
  in the session's own directory. What the conductor then does with them —
  promoting closed decisions into `decisions/`, giving the report a row in
  `design.md`, turning consequences into appended tasks — is named as the
  conductor's and pointed at, not described: a session reports an outcome
  and appends no task itself
- prototype — the finding is `prototypes/<slug>.md` (negative results are
  findings) and the throwaway code dies with its worktree
- research — the finding is delivered in the session's report; nothing is
  built, so no code outlives the session and no `prototypes/` note is
  written
- writeback — book chapters in destination voice and the context map, with
  `node context-map/bin/map-check.mjs --write` green when the map moved

#### Scenario: A prototype proves the negative

- **WHEN** a prototype shows the approach it was testing does not work
- **THEN** that is the finding: it is written to `prototypes/<slug>.md`
  with the question, the spike-repo location, and the decision it feeds,
  and the worktree is discarded

#### Scenario: A writeback session finishes a chapter

- **WHEN** a writeback session has rewritten the chapters its tasks name
- **THEN** the chapter reads as the destination with no record that the
  work happened, the book gates pass, and the map check is green if the map
  moved

### Requirement: Type skills do not widen a session's write scope

No session-type skill SHALL authorize a write outside its loop's write
matrix — for a design session: its own session directory, its own task
lines, its charged closures, and the books and context map its tasks
name; for a construction session: the built repo inside its worktree and
its own task lines. In particular, the prototype skill SHALL send code to a
spike-repo worktree that dies, the research skill SHALL build nothing at
all, and the writeback skill SHALL confine its mechanics to book chapters
and the map. Machinery edits in any repo, blueprints included, are
construction and leave through the phase gate as a handoff.

No type skill SHALL be the only home of a guardrail. Where a rule binds
more than one role — the target scope of a Writeback task, the invoker
rule, the annotation triage — the skill SHALL point at where it is stated
and SHALL NOT restate it as its own.

#### Scenario: A research session wants to fix what it found

- **WHEN** a research session investigating a tool finds the bug it was
  looking for and could fix it in a few lines
- **THEN** the skill routes it to a finding and a handoff — a one-proposal
  bolt if small — rather than to the edit

#### Scenario: A writeback task names a non-book target

- **WHEN** a task's writeback target is a skill file, an agent profile, a
  schema instruction, or a `CLAUDE.md`
- **THEN** the session refuses it as construction and reports it for a
  handoff task, on the two-things rule it carries from its profile — the
  writeback skill does not restate that scope rule as its own, because it
  is stated independently in `flywheel-inception` and the conductor
  profiles, where a task gets filed

### Requirement: Each type skill states whether its own type opens a round

In the design loop only the planning type opens a plannotator round; in the
construction loop only human-code-review does. That rule spans the types,
so it is stated in the profiles rather than owned by any one skill — but
**each type skill SHALL state the application to its own type**:
`flywheel-planning` that its rounds are on the drafts and plans in its own
directory, `flywheel-human-code-review` that its rounds are on built diffs,
and every other type that it opens none and delivers instead.

This is per-type application, not a shared guardrail with one home. A
prototype session's own finding note is a file it wrote, and so falls
inside the annotate scope a planning session is bounded by; without its own
skill saying so, nothing **in its own skill** tells it its type opens
none.

#### Scenario: A prototype session holds an annotatable file

- **WHEN** a prototype session has written `prototypes/<slug>.md` — a file
  it wrote, and therefore within the annotate scope as bounded — and
  considers opening a round on it
- **THEN** `flywheel-prototype` tells it its type opens none — from the
  skill itself, with the profile withheld — and it delivers the finding to
  its conductor, which charges a review-type session if the operator should
  annotate what the prototype proved

#### Scenario: A research session finishes its investigation

- **WHEN** a research session has written its report and considers putting
  it in front of the operator
- **THEN** `flywheel-research` tells it its type opens no round; the report is
  delivered and the conductor decides what follows

### Requirement: The writeback skill carries the inline-gate line

`flywheel-writeback` SHALL state that a Writeback task carries no phase
gate: writeback is the conductor's own scope, so a writeback session is
spawned and works its work order without waiting on an approval that does not
exist for it. `decisions/the-gate-is-inline.md` names this skill alongside
the two profiles because the failure it records was committed by an agent
reasoning from the skill it had read.

#### Scenario: A writeback session looks for its approval step

- **WHEN** a writeback session loads `flywheel-writeback` and looks for the
  point at which it should seek release before rewriting chapters
- **THEN** the skill tells it there is none — only Handoff tasks are gated
  — and it proceeds with the batch it was charged with

### Requirement: The profiles and their type skills ship together

The three host profiles and the thirteen session-type skills SHALL be
treated as one shipping unit — a profile without its skill leaves a session
unsteered, and a skill without its profile leaves the role unassigned. Any
later move of the flywheel machinery into a plugin SHALL carry them
together.

Shipping together is necessary and not sufficient: the surface tools the
type skills wrap are not carried by this repo. `plannotator` resolves on
`PATH` from the user's environment, and `lavish` is a **user-level skill**
living outside this repo, so it may be absent for the user a session runs
for. Its CLI needs no global install — `flywheel-interactive` SHALL
record `npx -y lavish-axi <html-file>` as the documented invocation, and
SHALL NOT treat `lavish-axi` missing from `PATH` as a fault, since that is
the normal healthy state.

A type skill whose steering source is genuinely absent SHALL report the
shortfall and stop, naming what is missing, rather than failing at the
moment it tries to open a surface.

#### Scenario: The machinery moves to a plugin

- **WHEN** the flywheel skills and profiles are packaged for a marketplace
  plugin
- **THEN** the package carries all three profiles and all thirteen type
  skills, not a subset

#### Scenario: The lavish skill is absent for this user

- **WHEN** an interactive session starts and the user-level `lavish` skill
  is not installed for the user it runs for
- **THEN** it reports the shortfall to its conductor and stops rather than
  half-building a surface — and the conductor decides whether to re-charge
  the batch as a review-type session, which is a new charge under the other
  profile, not this session switching surfaces mid-run

#### Scenario: lavish-axi is not on PATH

- **WHEN** an interactive session finds no `lavish-axi` on `PATH`
- **THEN** it proceeds normally via `npx -y lavish-axi <html-file>`, because
  a global install is not required and its absence is not a fault

