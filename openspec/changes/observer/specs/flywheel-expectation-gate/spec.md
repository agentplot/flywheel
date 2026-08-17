# flywheel-expectation-gate Delta

## Purpose

The operator can veto a loop run by reading what it intends before it acts:
a pass that would act pauses behind an expectation report until the operator
approves that exact set of intentions.

## ADDED Requirements

### Requirement: An acting pass is gated on operator approval

A loop pass that intends to drive work — launch a session, merge a branch,
land a bolt — SHALL, before the first such action, render an expectation
report (preconditions and expected outcomes, no actuals) and stop without
driving unless the operator has approved that expectation set. The approval
SHALL be keyed to the content of the expectation set: an approved set does
not re-gate on later passes, and a pass whose intentions differ from any
approved set gates again. Idempotent bookkeeping writes (container and label
repair by the guards) are recorded in the ledger but do not gate.

#### Scenario: A pass intends unapproved drives

- **WHEN** a loop pass computes work it would drive and no approval covers
  that expectation set
- **THEN** the pass writes the expectation report and exits without driving

#### Scenario: The same intentions return after approval

- **WHEN** a later pass computes an expectation set the operator has already
  approved
- **THEN** the pass proceeds without pausing

#### Scenario: The plan changes after approval

- **WHEN** a pass computes intentions that differ from every approved set
- **THEN** the pass gates again with a fresh expectation report

### Requirement: The operator grants approval with flywheel approve

`flywheel approve <milestone-slug>` SHALL approve the pending expectation set
for that milestone's loop, and SHALL print what it is approving. Approving
when nothing is pending SHALL say so and change nothing.

#### Scenario: The operator approves a pending set

- **WHEN** the operator runs `flywheel approve` for a milestone whose loop is
  gated
- **THEN** the pending expectation set is approved and the next pass acts

#### Scenario: Nothing is pending

- **WHEN** the operator runs `flywheel approve` for a milestone with no gated
  pass
- **THEN** the command reports there is nothing to approve and grants nothing

### Requirement: The gate can be relaxed once trusted

The gate SHALL be on by default. An explicit org- or invocation-level setting
SHALL turn it into a courtesy: the expectation report is still written, but
the pass proceeds without waiting.

#### Scenario: The operator relaxes the gate

- **WHEN** the gate is explicitly set to courtesy mode and a pass intends
  actions
- **THEN** the expectation report is written and the pass acts without
  approval
