# flywheel plugin

## ADDED Requirements

### Requirement: Two skills, two phases

The flywheel plugin SHALL ship two skills keeping the marketplace's
word+phase convention: `flywheel-inception` (the design loop) and
`flywheel-construction` (the build loop, with the repo-readiness audit
folded in). Both prototype as blueprints project skills before any
marketplace move.

#### Scenario: Design loop runs an intent session

- **WHEN** the design conductor starts a session for an intent picked from
  the frontier
- **THEN** the session works a batch of tasks through a lavish artifact in
  its own `sessions/<date>-<slug>/` directory, and the conductor records
  closed decisions under `decisions/`, catalogs the report in `design.md`,
  performs writeback tasks (book chapters in destination voice,
  `map-check --write` green), and checks off tasks as outcomes land

#### Scenario: Construction runs from released handoffs

- **WHEN** the operator releases staged handoff tasks (the phase gate)
- **THEN** the intent conductor requests the bolt — creating the
  flywheel-bolt change and auto-starting its conductor when none exists,
  or prompting the running one — and the bolt conductor drives the
  proposals through its registry: spec agents per proposal, the declared
  review (agent or human via plannotator), apply agents on nested
  construction worktrees, batched testing

### Requirement: Skills state criteria, not steps

Both skills SHALL present decision points with criteria — branch shape,
working arrangement (solo / reviewed / paired), acceptance batch size, test
staging — and require the choosing agent to record its choice and reason in
the artifact it produces, rather than prescribing fixed steps. The fixed
invariants are only: every pipeline stage runs somewhere; acceptance suites
are batched on the integration branch, never run per work branch; the
release gate on main is never weakened.

#### Scenario: Working arrangement is a recorded choice

- **WHEN** a generated proposal is dispatched to a work branch
- **THEN** the proposal records the chosen working arrangement with its
  reason, not a copy of a prescribed default

### Requirement: Completion flows back to the intent

Landing a proposal SHALL cause the bolt conductor to report to the
originating intent's conductor (prompt or inbox), which checks off the
handoff task; construction findings that alter the design SHALL route
through intake and append new tasks to the intent — an intent archives
only when its tasks are complete and its writebacks are green.

#### Scenario: Finding reopens the outer loop

- **WHEN** a bolt's testing batch surfaces a finding that changes the design
- **THEN** the finding routes through intake, a new task (and, when
  warranted, a Fog question) appears in the intent, and the intent is not
  archivable until it resolves
