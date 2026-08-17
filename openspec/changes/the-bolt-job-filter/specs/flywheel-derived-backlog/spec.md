# flywheel-derived-backlog Delta

## MODIFIED Requirements

### Requirement: A Ready plan card is a bolt job

The server inbox SHALL yield a `run` job for the `bolt/*` milestone an
open `plan` card at board Status Ready sits on, so the bolt loop starts
and expands the card. The milestone the card names is the milestone the
job carries: the server SHALL NOT derive a bolt name from a card's
title, and a card that names no `bolt/*` milestone SHALL yield no job.

The job's reason SHALL name the card and that it awaits expansion, and
SHALL be the reason reported for that milestone even when the same pass
finds another reason for it — the reason is what the run record prints
and what the restart backoff fingerprints, so the card must be legible
as the thing the loop was started for.

The milestone SHALL be open. A Ready card sitting on a closed milestone
SHALL yield no `run` job, leaving that milestone's archive job as its
only job.

A card at board Status Backlog SHALL yield no job: approval is the
operator's flip to Ready, and nothing starts before it.

#### Scenario: card approved

- **WHEN** an open `plan` card at Status Ready sits on the open
  milestone `bolt/<slug>`
- **THEN** the server starts a bolt loop for `bolt/<slug>`, and the
  job's reason names that card as awaiting expansion

#### Scenario: the milestone has another reason too

- **WHEN** a Ready card's milestone also holds a batch at Status Ready
  or an item at `state:ready` on the same pass
- **THEN** one `run` job is reported for that milestone and its reason
  names the card awaiting expansion

#### Scenario: a card naming no bolt milestone

- **WHEN** an open `plan` card sits at Status Ready with no `bolt/*`
  milestone, whatever its title says
- **THEN** the server starts nothing for it and no job names a
  milestone the tracker does not hold

#### Scenario: a card on a closed milestone

- **WHEN** a Ready card sits on a `bolt/*` milestone the operator has
  closed
- **THEN** no `run` job is yielded for that milestone, and its archive
  job — if its change still sits in `openspec/changes/` — is unchanged

#### Scenario: card awaiting approval

- **WHEN** an open `plan` card sits at Status Backlog on its milestone
- **THEN** the server starts nothing for it

## ADDED Requirements

### Requirement: Unexpanded cards count as outstanding work

`flywheel status` SHALL report every open, unexpanded `plan` card as
outstanding work on its bolt, so a planned bolt is never invisible
between the planning run and expansion.

A card at Status Ready SHALL appear through its milestone's job row. A
card at Status Backlog SHALL appear under what waits on the operator,
naming the card, the `bolt/*` milestone it sits on, and that the flip
to Ready releases it — the report SHALL NOT treat a milestone holding
only unapproved cards as quiet.

A card at Status Ready that names no `bolt/*` milestone SHALL appear
under what waits on the operator with that defect named, since the
server yields no job for it: a card the filter declines to read is
reported, never silently dropped.

`status` SHALL start nothing on account of any card, and a tracker it
cannot read SHALL remain a reported line rather than a failure.

#### Scenario: a bolt awaiting its first approval

- **WHEN** a planning run has filed cards on `bolt/<slug>` and none has
  been moved to Ready
- **THEN** `flywheel status` lists each card under what waits on the
  operator, naming its number, `bolt/<slug>`, and the flip to Ready

#### Scenario: an approved card is already counted

- **WHEN** a card on `bolt/<slug>` sits at Ready
- **THEN** the milestone appears in the job rows with the card as its
  reason, and the card is not also listed as waiting on the operator

#### Scenario: an unroutable card is visible

- **WHEN** a card at Ready carries no `bolt/*` milestone
- **THEN** `flywheel status` lists it under what waits on the operator
  and says it names no bolt milestone

#### Scenario: status starts nothing

- **WHEN** `flywheel status` runs against a tracker holding cards in
  any state
- **THEN** no loop process is started and no tracker write is made
