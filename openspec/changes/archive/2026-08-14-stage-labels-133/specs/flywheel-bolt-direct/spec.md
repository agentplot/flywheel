## MODIFIED Requirements

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

**What the shipped schema declares SHALL be held on disk, for every shipped
type without exception.** The declaration that matters here is not read from
a config a test constructs — a stage set or strategy built by hand in a test
asserts what the author believed, not what the plugin ships, and a schema
edited to disagree with it leaves every check green. Whatever pins the
shipped types' declared strategy, invocations and stage set SHALL load them
from the schemas as published, and SHALL cover `bolt-direct` alongside the
other three; a type absent from that enumeration is a type whose published
behaviour nothing holds.

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

#### Scenario: A shipped type's declaration is changed

- **WHEN** any shipped bolt type's published schema is edited so that its
  declared strategy, invocations or stage set no longer match what this
  capability states
- **THEN** that disagreement is caught against the schema as published, for
  `bolt-direct` as for its three siblings

### Requirement: A `bolt-direct` item goes built → merged with no verify

On a bolt bound to `bolt-direct` the loop SHALL run spec, build, merge and
land, and SHALL NOT run a verify stage or launch a verify session.

An item on such a bolt SHALL go from `stage:built` to `stage:merged`
directly, and `stage:verified` SHALL never appear on it.

Skipping verify SHALL be a property of the bound type alone. It SHALL NOT be
reachable by a per-bolt declaration on another type, for the reason the
plan-mode path is refused outside `bolt-quick`: the bolt type is the
scrutiny the release approved, and no program downgrades it.

**"No program downgrades it" SHALL cover every route to a type, not only the
change's binding.** The binding on disk is what the loop believes, ahead of
anything it was told on the command line, so a type named on the command line
that disagrees with the binding SHALL be refused rather than silently
preferred. The refusal SHALL name the disagreement — the type the binding
records and the type it was asked for — the way the refusal of a stage
declaration already names the rule it broke.

An operator does have a legitimate need to run a loop against a bolt whose
binding is wrong; that need is met by correcting the binding, which is a
recorded act on disk, and not by a flag whose effect leaves no trace on the
tracker. A type resolved from a flag alone SHALL NOT be able to run a bolt
with fewer stages than its binding approved.

Where no binding exists on disk, a type named on the command line SHALL
still be honoured: there is nothing for it to disagree with, and refusing it
would leave an unbound bolt unable to run at all.

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

#### Scenario: A command-line type disagreeing with the binding

- **WHEN** a loop is started against a bolt whose binding records
  `bolt-default`, naming `bolt-direct` on the command line
- **THEN** it is refused, naming both types, and no cycle runs — rather than
  the bolt merging and landing with no verify session and no
  `stage:verified` while its binding still says the release approved
  `bolt-default`

#### Scenario: A command-line type agreeing with the binding

- **WHEN** a loop is started naming the same type the binding records
- **THEN** it runs, because there is no disagreement to refuse

#### Scenario: A bolt with no binding on disk

- **WHEN** a loop is started against a bolt whose change carries no binding
  and a type is named on the command line
- **THEN** that type is used, because there is no recorded approval for it
  to contradict
