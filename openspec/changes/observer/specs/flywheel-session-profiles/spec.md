# flywheel-session-profiles Delta

## ADDED Requirements

### Requirement: Every profile body carries the finding-routing rule

Every session profile body SHALL state the finding-routing rule: findings
about the machinery itself — loop bugs, prompt problems, dispatch mistakes —
go in the session's report and nowhere else; the session never files a
tracker item about the machinery. Tracker writes remain what they were:
state moves on the work items of the system under construction.

#### Scenario: A session notices the machinery misbehaving

- **WHEN** a session under any flywheel profile observes a defect in the
  loops, prompts, or dispatch
- **THEN** it records the observation in its report and stops, and no tracker
  item about the machinery is created

#### Scenario: A session finds a defect in the system under construction

- **WHEN** a session finds a defect in the code or books its work order
  targets
- **THEN** the ordinary discovery path still applies — the finding-routing
  rule restricts only findings about the machinery
