# flywheel-observation-report Delta

## Purpose

The operator evaluates a loop run by reading one report — expected and actual
side by side, mismatches first — instead of spelunking issues, panes, and
logs.

## ADDED Requirements

### Requirement: A run ends with an expected-vs-actual report

At the end of an acting pass the loop SHALL render an observation report
beside the run's ledger: the run's preconditions, then a table joining each
step's trigger, expected outcome, and actual outcome. Rows where actual
diverges from expected SHALL be surfaced before matching rows. Every fact in
the report SHALL derive from the ledger and the run's logs; the report speaks
in slugs and quick summaries, never issue bodies.

#### Scenario: A run completes with a divergence

- **WHEN** an acting pass ends and one step's actual outcome diverges from
  its expectation
- **THEN** the report exists beside the ledger with the diverging row surfaced
  ahead of the matching rows

#### Scenario: A run completes clean

- **WHEN** an acting pass ends with every actual matching its expectation
- **THEN** the report states the run matched expectations and shows the table

### Requirement: A mismatch is reported, not judged

A divergence between expected and actual SHALL be stated as a divergence; the
report SHALL NOT mark the run failed, file any tracker item, or take remedial
action. Judgment belongs to the operator reading the report.

#### Scenario: A divergent run ends

- **WHEN** the report records a divergence
- **THEN** no tracker write and no remedial action results from the report
  itself

### Requirement: Observer narrative is additive and originates no facts

An observer agent MAY append narrative to a report — comparison across runs,
plain-language summary of a divergence. Narrative SHALL be marked as the
observer's and SHALL introduce no factual claim about the run that the ledger
or logs do not carry.

#### Scenario: The observer annotates a report

- **WHEN** an observer agent runs over a completed report
- **THEN** the factual table is unchanged and the narrative section is
  attributed to the observer
