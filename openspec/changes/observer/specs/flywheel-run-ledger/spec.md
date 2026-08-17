# flywheel-run-ledger Delta

## Purpose

Every loop run leaves a machine-readable record of what it read, what it
intended, and what happened — the factual substrate every observation report
and expectation gate is rendered from.

## ADDED Requirements

### Requirement: A loop run writes a ledger

Each loop process run SHALL append a run ledger — one JSON object per line —
under the org state directory at
`observations/<milestone-slug>/<run-id>.jsonl`, where `<run-id>` is unique per
loop process. Entries SHALL speak the loop's own vocabulary (milestone slugs,
stage names, batch and item numbers) and SHALL NOT embed issue bodies or
comment threads. The ledger sits beside the server and loop logs and replaces
neither.

#### Scenario: A bolt loop pass runs a stage

- **WHEN** a bolt loop process executes a stage for its milestone
- **THEN** the run's ledger file under `observations/bolt-<slug>/` contains an
  entry for that stage naming the trigger that fired it

#### Scenario: An intent loop pass dispatches a session

- **WHEN** an intent loop process charges a design session for a batch
- **THEN** the run's ledger records the dispatch with the batch number and
  session type, and no issue body text appears in the entry

### Requirement: Preconditions and expectations are recorded before acting

Before taking any action, a loop run SHALL record the preconditions it read
(the tracker state and repo state its decisions derive from) and, for each
action it intends, an expectation entry naming the step, its trigger, and the
outcome the loop expects. Expectation entries SHALL be written before the
action they describe is taken.

#### Scenario: A pass computes its intended actions

- **WHEN** a loop pass determines it will act
- **THEN** the ledger already holds the preconditions and one expectation
  entry per intended action before the first action executes

#### Scenario: A pass finds nothing to do

- **WHEN** a loop pass finds no ready work and takes no action
- **THEN** the run records its preconditions and an explicit no-action outcome

### Requirement: Actual outcomes are recorded as they land

For each action taken, the loop SHALL append an actual-outcome entry naming
the step and what actually happened, in the same vocabulary as the
expectation entry it answers, so expected and actual are joinable by step.

#### Scenario: An action completes

- **WHEN** a ledgered action finishes, successfully or not
- **THEN** the ledger holds an actual entry for that step stating the outcome,
  joinable to its expectation entry

### Requirement: The server ledgers dispatch nudges

When the server sends dispatch a nudge or relay, it SHALL append an entry to
`observations/dispatch/<run-id>.jsonl` recording what it asked of dispatch and
the delivery outcome, so dispatch activity is observable through the same
surface as loop runs.

#### Scenario: The server nudges dispatch

- **WHEN** the server prompts the dispatch pane
- **THEN** the dispatch ledger records the nudge and whether delivery
  succeeded
