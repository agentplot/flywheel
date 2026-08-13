## Purpose

The fourth bolt type: a named loop config faster than `bolt-quick`, running
spec, build, merge and land with no verify stage. It exists for work whose
correctness the merge gate and the spec together already settle, and it
carries the same unweakened repo gate as every other type.

## ADDED Requirements

### Requirement: `bolt-direct` exists as a fourth named loop config

A bolt type named `bolt-direct` SHALL ship alongside `bolt-quick`,
`bolt-default` and `bolt-adversarial`, as a schema whose `loop:` block is
read by the same reader that reads theirs.

Its `loop:` block SHALL declare strategy `ff` — one spec command generating
every artifact, the same strategy `bolt-quick` uses — and SHALL declare the
stage set `spec`, `build`, `merge`, `land`, with no verify stage.

Its declared hooks SHALL name only boundaries its stages actually create, so
`post-verify` — which every existing type declares — SHALL NOT appear among
them. A hook naming a boundary that never occurs is a review point nothing
can ever attach to.

The type SHALL be published the way its three siblings are, so a consuming
repo acquires it by the same installation and shadows it by the same
per-repo copy.

#### Scenario: A bolt binds the type

- **WHEN** a change's binding names `bolt-direct`
- **THEN** the loop resolves the schema, reads its `loop:` block, and runs
  the strategy and stage set it declares

#### Scenario: The type is listed among the bolt types

- **WHEN** a reader looks up which bolt types exist
- **THEN** `bolt-direct` is among them, described as the no-verify type

#### Scenario: A consuming repo installs the schemas

- **WHEN** the flywheel's schemas are published into a consuming repo
- **THEN** `bolt-direct` arrives with the other three

### Requirement: A `bolt-direct` item goes built → merged with no verify

On a bolt bound to `bolt-direct` the loop SHALL run spec, build, merge and
land, and SHALL NOT run a verify stage or launch a verify session.

An item on such a bolt SHALL go from `stage:built` to `stage:merged`
directly, and `stage:verified` SHALL never appear on it.

Skipping verify SHALL be a property of the bound type alone. It SHALL NOT be
reachable by a per-bolt declaration on another type, for the reason the
plan-mode path is refused outside `bolt-quick`: the bolt type is the
scrutiny the release approved, and no program downgrades it.

#### Scenario: A batch completes on a bolt-direct bolt

- **WHEN** a batch is specced and built on a `bolt-direct` bolt
- **THEN** the next stage the loop runs is merge, with no verify session
  launched
- **AND** the batch's items carry `stage:merged` without ever having
  carried `stage:verified`

#### Scenario: A declaration cannot skip verify on another type

- **WHEN** a bolt bound to `bolt-default` or `bolt-adversarial` declares
  that verify be skipped
- **THEN** the declaration is refused rather than honoured quietly

### Requirement: The repo's merge gate runs at merge and at landing, whatever the type

On a `bolt-direct` bolt the repo's own merge gate SHALL run at the merge
back to the bolt branch and again at the landing, exactly as on every other
type, and SHALL never be suppressed, weakened or hand-substituted.

The gate belongs to the repo, not to the type. What a bolt type varies is
how much *review* the flywheel schedules; what the repo's hooks assert about
the tree that lands is not the flywheel's to trade away, and a type that
could waive it would make "the gate is always implied and never weakened"
false for one type and true for three.

#### Scenario: A merge-back on a bolt-direct bolt

- **WHEN** a build branch is merged back to a `bolt-direct` bolt's branch
- **THEN** the repo's pre-merge hooks run on the exact rebased tree, and a
  failing hook aborts with nothing landed

#### Scenario: The landing of a bolt-direct bolt

- **WHEN** a `bolt-direct` bolt's branch lands on main
- **THEN** the full gate runs, unweakened, with one writer to main at a
  time

#### Scenario: The type is read as a licence to skip the gate

- **WHEN** any tool or prose describing `bolt-direct` is read
- **THEN** it states that the merge gate is unaffected by the type, so that
  "no verify stage" is never read as "no gate"
