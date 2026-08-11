# flywheel-session-type-skills Specification

## Purpose
The skills that steer a flywheel session by the kind of work it is doing —
one per session type across both loops, each stating what the type is,
what its output is, and where that output lands — so that launching a
session under a conductor means loading the skill for its type.
## Requirements
### Requirement: Thirteen session-type skills

The plugin SHALL carry one skill per session type under `skills/`:

| skill | type | default model | what it wraps |
|---|---|---|---|
| `flywheel:planning` | planning | fable | plannotator, over drafts the session wrote |
| `flywheel:interactive` | interactive design | fable | lavish, over a built surface |
| `flywheel:proposal-review` | proposal-review | fable | a read across the batch, against the cited decisions |
| `flywheel:prototype` | prototype | opus | a throwaway built in a spike-repo worktree |
| `flywheel:writeback` | writeback | opus | `books/CLAUDE.md` and the destination voice |
| `flywheel:handoff` | handoff | opus | the release request to a bolt conductor, and its receipt |
| `flywheel:proposal-writing` | proposal-writing | opus | the exception path for unmineable assertions |
| `flywheel:research` | research | `opus[1m]` | an investigation that reads rather than builds |
| `flywheel:spec-writing` | spec-writing | `opus[1m]` | `/opsx:ff` in the built repo, from the assertion and its cited sources |
| `flywheel:build` | build | `opus[1m]` | `/opsx:apply` on a nested construction worktree |
| `flywheel:test` | test | `opus[1m]` | the batched acceptance run on the bolt branch |
| `flywheel:code-review` | code-review | `opus[1m]` | an adversarial or persona read of built work |
| `flywheel:human-code-review` | human-code-review | `opus[1m]` | plannotator, over built diffs for the operator |

The default-model column is the one enumeration of session-model
defaults; every launch path accepts a runtime override via the
invocation's args or the work order, and the override wins. Fable sits
where reasoning is the work — adversarial reads and operator-facing
decision surfaces; `opus[1m]` where the work is context-bound — large
trees and long reads; opus where it is rule-following composition.

#### Scenario: A conductor charges a batch that needs a throwaway

- **WHEN** an item batch turns on a fact a throwaway can prove faster than
  an argument can settle
- **THEN** the work order names the prototype type, and the session loads
  `flywheel:prototype`

#### Scenario: A design-heavy assertion needs more than the default

- **WHEN** a spec-writing batch covers an assertion whose derivation is
  genuinely design-heavy
- **THEN** the conductor overrides the model in the work order, and the
  override wins over the table's default

### Requirement: The type is chosen at work-order time and named in the work order

The conductor SHALL choose the session type when it charges a session,
and the work order SHALL name it alongside the change id, the item
numbers, and the goal. The session SHALL load that type's skill before
working the batch. A session whose work order names no type SHALL ask
its conductor.

#### Scenario: The batch turns out to need a different type

- **WHEN** a planning session finds mid-batch that the decisions cannot be
  closed from a document and need a built surface
- **THEN** it reports that as the next batch's type rather than switching
  surfaces inside its own run

### Requirement: A session without file edits runs without a worktree

A session whose batch edits no files — most research, any read-and-
verdict batch that reports rather than commits — SHALL be launched
without a worktree and SHALL deliver through comments and its report
alone. A worktree exists to isolate file edits, and a session that makes
none has nothing to isolate.

#### Scenario: A research batch only reads

- **WHEN** a research session's batch answers questions from code and
  docs without editing a file
- **THEN** it runs in the conductor's launch directory with no worktree,
  no branch, and no merge, and delivers its findings as comments and a
  report

### Requirement: Each type's output has one home

The type skills SHALL agree with the schemas on where output lands, and
SHALL NOT introduce a second home for anything:

- planning and interactive design — the surface and the decision drafts
  live in the session's own directory; closures the work order charged
  are written by the session; everything else is reported
- prototype — the finding is `prototypes/<slug>.md` (negative results are
  findings) and the throwaway code dies with its worktree
- research — the finding is the item comment and the report; nothing is
  built
- writeback — book chapters in destination voice and the context map,
  with `node context-map/bin/map-check.mjs --write` green when the map
  moved
- the construction types — the built repo inside the session's worktree,
  comments on the items, and the report

#### Scenario: A prototype proves the negative

- **WHEN** a prototype shows the approach it was testing does not work
- **THEN** that is the finding: it is written to `prototypes/<slug>.md`
  with the question, the spike-repo location, and the decision it feeds,
  and the worktree is discarded

### Requirement: Discovery is queued, in-scope fixes are made

Every type skill SHALL treat new work the session notices as a queued
item — one `gh issue create`, never a reason to stop or escalate — and a
small fix inside the batch's released scope as work the session does and
notes in its report. The escalation path is for being blocked, and the
andon cord for a defect no further work inside the batch can fix.

#### Scenario: A research session finds the bug it was looking for

- **WHEN** a research session investigating a released batch finds a bug
  it can fix inside that batch's scope
- **THEN** it makes the fix, commits it in its worktree, and notes it in
  its report — and queues an item instead only when the fix falls
  outside its batch's released scope

### Requirement: The profiles and their type skills ship together

The three host profiles and the thirteen session-type skills SHALL be
treated as one shipping unit — a profile without its skill leaves a
session unsteered, and a skill without its profile leaves the role
unassigned.

The surface tools the type skills wrap are not carried by the plugin.
`plannotator` resolves on `PATH` from the user's environment, and
`lavish` is a user-level skill that may be absent. `flywheel:interactive`
SHALL record `npx -y lavish-axi <html-file>` as the documented
invocation and SHALL NOT treat `lavish-axi` missing from `PATH` as a
fault. A type skill whose steering source is genuinely absent SHALL
report the shortfall and stop, naming what is missing.

#### Scenario: The lavish skill is absent for this user

- **WHEN** an interactive session starts and the user-level `lavish` skill
  is not installed for the user it runs for
- **THEN** it reports the shortfall to its conductor and stops rather than
  half-building a surface

#### Scenario: lavish-axi is not on PATH

- **WHEN** an interactive session finds no `lavish-axi` on `PATH`
- **THEN** it proceeds normally via `npx -y lavish-axi <html-file>`, because
  a global install is not required and its absence is not a fault
