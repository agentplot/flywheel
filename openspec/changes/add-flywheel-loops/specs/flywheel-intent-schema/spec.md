# flywheel-intent schema

## ADDED Requirements

### Requirement: One OpenSpec change per intent

The blueprints repo SHALL track each design intent as one OpenSpec change on
the main branch, bound to the `flywheel-intent` schema by a `.openspec.yaml`
in the change directory (`schema: flywheel-intent`, `skip_specs: true`), so
intents and spec-driven changes coexist in one `openspec/changes/` tree.

#### Scenario: Intent coexists with spec-driven changes

- **WHEN** `openspec status --change <intent>` runs with no `--schema` flag
- **THEN** the schema resolves to `flywheel-intent` from the change metadata
- **AND** `openspec validate <intent>` passes without delta specs

### Requirement: The intent artifact model

The `flywheel-intent` schema SHALL define six artifacts: `intent`
(`intent.md`: Destination, Map, Scope, Fog), `decisions`
(`decisions/**/*.md`, one record per closed decision), `sessions`
(`sessions/**/*`, one directory per design session, uniquely named
`sessions/<date>-<slug>/`), `design` (`design.md`, the catalog of design
output — one row per session report and per prototype finding), `prototypes`
(`prototypes/**/*.md`, findings only — code stays in the spike repo), and
`tasks` (`tasks.md`, the living checklist).

#### Scenario: Artifact completion is machine-readable

- **WHEN** `openspec status --change <intent> --json` runs
- **THEN** each of the six artifacts reports its status and the resolved
  files that satisfy its glob

### Requirement: Typed tasks are the frontier

`tasks.md` SHALL organize tasks under typed section headings — Design,
Writeback, ADR, Handoff — where a handoff task names the built repo whose
OpenSpec proposal it generates, blocked tasks carry `(blocked by: …)`
in-line, and new fog appends new tasks rather than reopening checked ones.

#### Scenario: Task progress is parsed by OpenSpec itself

- **WHEN** `openspec list --json` runs
- **THEN** the intent reports `completedTasks`, `totalTasks`, and a derived
  status without any flywheel-specific tooling

#### Scenario: A closed decision leaves a record

- **WHEN** a design-session task that closed a decision is checked off
- **THEN** a `decisions/<slug>.md` record exists stating the decision, its
  context (map nodes, chapters, producing report), and the tasks it appends
