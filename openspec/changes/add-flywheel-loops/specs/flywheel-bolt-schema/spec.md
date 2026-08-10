# flywheel-bolt schema

## ADDED Requirements

### Requirement: One OpenSpec change per bolt, on blueprints main

Each construction iteration SHALL be tracked as one OpenSpec change on
blueprints main bound to the `flywheel-bolt` schema by `.openspec.yaml`
(`schema: flywheel-bolt`, `skip_specs: true`), so `openspec list` and the
OpenSpec UI board cover intents and bolts together.

#### Scenario: Bolts appear beside intents

- **WHEN** `openspec list --json` runs on blueprints main
- **THEN** bolt changes report task counts and status alongside intent
  changes, with no flywheel-specific tooling

### Requirement: The bolt artifact model

The `flywheel-bolt` schema SHALL define three artifacts: `bolt`
(`bolt.md`: Scope, Sources, Repos with per-repo bolt-branch names, Merge
criteria), `proposals` (`proposals.md`: one registry row per proposal —
repo, change id, review mode `agent`|`human`, forward-only status
`to-spec → specced → in-review → approved → building → built → verified →
merged`, branch, owner), and `tasks` (`tasks.md`: typed sections Spec /
Review / Build / Test / Merge, tracked by `apply.tracks`).

#### Scenario: A bounced review is the only backward move

- **WHEN** a proposal's declared review rejects its spec
- **THEN** its registry status returns to `to-spec` with the gaps recorded
  as tasks, and no other status transition moves backward

### Requirement: Single writer with inbox messaging

A bolt change SHALL be edited only by its bolt conductor (herdr agent
`bolt-<slug>`, session in the blueprints repo). Requests from other actors
arrive via `herdr agent prompt` when the conductor runs, or as files in
the change's `inbox/` (`inbox/<date>-<from>-<slug>.md`) when it does not;
the conductor drains the inbox at the start of every turn — folding each
request into its artifacts and deleting the file in the same commit.

#### Scenario: Inbox request round-trips

- **WHEN** a testing agent drops a finding file into a bolt's `inbox/`
  while the conductor is not running
- **THEN** on its next turn the conductor's commit shows the finding as an
  appended task and the inbox file removed, together

### Requirement: Bolt branches in built repos, conductor in blueprints

A bolt conductor SHALL run in the blueprints repo and cut one bolt branch
plus worktree per involved built repo, alive for the bolt's lifetime, with
construction running on nested worktrees off those bolt branches.
Acceptance suites run batched on bolt branches — never inside construction
worktrees — and each repo's bolt branch lands on its main only through the
full release gate.

#### Scenario: A bolt spans repos without moving its record

- **WHEN** a bolt's scope grows to include a second built repo
- **THEN** the conductor adds the repo and its bolt branch to `bolt.md`,
  cuts the branch and worktree there, and the tracking record stays the
  one change on blueprints main
