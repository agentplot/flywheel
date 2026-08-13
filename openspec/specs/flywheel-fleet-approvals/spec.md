# flywheel-fleet-approvals Specification

## Purpose
The fleet places agents into repos whose merge gate is `wt`'s hook machinery,
and `wt` runs a project hook only against an operator's standing grant. This
capability makes that grant a checked start precondition: the fleet refuses to
start actors into a repo whose gate they cannot run, and says so loudly at
fleet start with the exact remedy, rather than letting the stoppage land
mid-merge on an agent that cannot fix it.
## Requirements
### Requirement: A repo's hook approvals are a fleet start precondition

The fleet command SHALL define a repo as **gate-ready** when every hook
template defined in that repo's worktrunk project config has a matching grant
in the operator's worktrunk approvals store, under the project identifier
worktrunk itself resolves for that repo.

A **hook template** is any command string worktrunk resolves from a **project**
hook in that repo's config, under any of worktrunk's ten hook events —
`pre-switch`, `post-switch`, `pre-start`, `post-start`, `pre-commit`,
`post-commit`, `pre-merge`, `post-merge`, `pre-remove`, `post-remove`.

An event's value is not a table alone. Worktrunk's project-hook grammar is
`String | Table<name → String> | Array<String | Table<name → String>>`, and
every branch of it produces commands worktrunk runs and
`wt config approvals add` enumerates. The definition SHALL cover all of them:
a bare string, a named table, an inline table, an array of strings, an array
mixing strings and tables, and the `[[event]]` pipeline blocks that are TOML's
array-of-tables spelling of the last branch. A definition covering only the
named-table form would report a repo gate-ready whose hooks are entirely
ungranted — a false green, and the precise failure this capability exists to
prevent. See `design.md`, *The hook-template grammar*, for the measurement and
its provenance.

Only **project** hooks require approval; user-level hooks in the operator's own
worktrunk config do not, and SHALL NOT be counted as gaps. Anything in the
project config that worktrunk does not resolve as a hook — a project alias, any
non-hook table — SHALL NOT be checked.

Because that grammar has five accepted shapes and is worktrunk's own, the check
SHALL obtain the templates by asking worktrunk to enumerate its configured
hooks, taking each record's template text where the record's source is the
project, rather than by re-parsing the config against a hand-written grammar.
Worktrunk is authoritative about its own configuration; the approvals store is
authoritative about grants. The check SHALL NOT take any approval-state field
returned alongside those templates — whether a template is approved is
determined only by comparison against the store
(`openspec/changes/merge-gate-remedy/bolt.md`, *Where `wt` is the authority, and
where it is not*, read from disk at this revision).

If that enumeration fails — worktrunk reporting the project config unloadable
or unparseable, or exiting non-zero for any reason — the result SHALL be
indeterminate, never an empty template set. An unparseable project config
otherwise reads as "no hooks configured" and resolves gate-ready, which is a
false green on a repo whose gate is definitionally unrunnable.

Matching SHALL be exact string equality against the template text as
configured, unexpanded — the same text worktrunk keys its grants on, so one
grant covers every branch's expansion of a template. Matching SHALL NOT
normalize whitespace, expand template placeholders, or compare loosely.

A repo SHALL be reported gate-ready when it defines no hook templates at all,
including when it carries no worktrunk project config: there is no gate to be
unable to run.

#### Scenario: The repo's templates are all granted

- **WHEN** the fleet evaluates a repo whose project config defines four hook
  templates, and the approvals store's table for that repo's identifier holds
  all four strings
- **THEN** the repo is gate-ready

#### Scenario: One template is ungranted

- **WHEN** the fleet evaluates a repo whose project config defines four hook
  templates and whose approvals table holds three of them
- **THEN** the repo is not gate-ready
- **AND** the one unmatched template is the reported gap

#### Scenario: The repo has no entry in the approvals store

- **WHEN** the fleet evaluates a repo that defines hook templates and whose
  identifier has no table in the approvals store — the state of
  `github.com/agentplot/flywheel` on this machine at authoring time, alongside
  six unrelated project tables
- **THEN** the repo is not gate-ready
- **AND** every one of its hook templates is reported as a gap

#### Scenario: The approvals store does not exist

- **WHEN** the fleet evaluates a repo that defines hook templates on a machine
  with no approvals store file
- **THEN** the repo is not gate-ready, exactly as if the file existed and held
  no table for it

#### Scenario: An event configured as a bare string

- **WHEN** the fleet evaluates a repo whose project config sets a hook event to
  a bare command string, and that string has no grant
- **THEN** the repo is not gate-ready and that string is reported as a gap

#### Scenario: An event configured as a named table

- **WHEN** the fleet evaluates a repo whose project config sets a hook event to
  a table of two named commands, neither granted
- **THEN** both commands are reported as gaps

#### Scenario: An event configured as an inline table

- **WHEN** the fleet evaluates a repo whose project config sets a hook event to
  an inline table of one named command, ungranted
- **THEN** that command is reported as a gap

#### Scenario: An event configured as an array

- **WHEN** the fleet evaluates a repo whose project config sets a hook event to
  an array holding both bare strings and named tables, none granted
- **THEN** every command in the array is reported as a gap, whichever form it
  took

#### Scenario: An event configured as `[[event]]` pipeline blocks

- **WHEN** the fleet evaluates a repo whose project config sets a hook event as
  a sequence of `[[event]]` pipeline blocks, whose steps are ungranted
- **THEN** every command across every block is reported as a gap
- **AND** no block's key name is mistaken for a command

#### Scenario: A repo configures no project hooks

- **WHEN** the fleet evaluates a repo with no worktrunk project config, or one
  whose project config resolves no project hook
- **THEN** the repo is gate-ready, and no remedy is printed for it

#### Scenario: Only user-level hooks are configured

- **WHEN** the fleet evaluates a repo that resolves no project hook, on a
  machine whose own worktrunk config defines hooks of its own
- **THEN** the repo is gate-ready
- **AND** no user-level hook is reported as a gap, because user hooks require
  no approval

#### Scenario: The project config cannot be parsed

- **WHEN** the fleet evaluates a repo whose worktrunk project config is
  malformed, so worktrunk fails to load it and enumerates no hooks
- **THEN** the result is indeterminate and no actor is started into that repo
- **AND** the repo is NOT reported gate-ready on the strength of an empty
  template set

#### Scenario: A template moves between hook events without changing text

- **WHEN** a granted template is moved from one hook event table to another
  with its command text unchanged
- **THEN** the repo remains gate-ready, because matching is on template text
  and not on the event it is registered under

### Requirement: The check reads; it never writes and never grants

The check SHALL determine approval state by reading the operator's approvals
store and comparing it against the repo's hook templates. It SHALL NOT write to
the approvals store, create it, or modify the repo's project config. It SHALL
NOT invoke worktrunk with any flag that bypasses approval prompting, and SHALL
NOT run any hook.

Worktrunk MAY be invoked read-only for facts about **its own configuration** —
the project identifier, the project config's location, and the enumeration of
configured hooks and their template text. Worktrunk SHALL NOT be asked whether
a template is approved: any approval-state field returned alongside those facts
SHALL be ignored, and no worktrunk command SHALL be invoked for the purpose of
learning approval state. This is the line the bolt record draws — worktrunk is
the authority on its own configuration, the approvals store is the authority on
grants (`openspec/changes/merge-gate-remedy/bolt.md`, *Where `wt` is the
authority, and where it is not*).

The write boundary is the decision's, not an implementation preference: a
converger that wrote the grants was considered and declined because it would
have the machinery approve the machinery's own hooks
(`openspec/changes/gated-merge-guarantee/decisions/approvals-are-an-onboarding-grant.md`,
section *What was declined, and why*, read from disk at this change's
authoring).

#### Scenario: A failing check leaves the store untouched

- **WHEN** the fleet evaluates a repo that is not gate-ready
- **THEN** the approvals store's contents are byte-identical before and after
- **AND** no hook has been executed

#### Scenario: Worktrunk's own approval verdict is not consulted

- **WHEN** worktrunk's hook enumeration reports a template as needing approval
  while the approvals store holds that exact template text
- **THEN** the template is treated as granted, because the store is the
  authority on grants
- **AND** the enumeration's approval-state field played no part in the verdict

### Requirement: `flywheel up` starts no actor into a repo that is not gate-ready

`flywheel up` SHALL determine, for each actor it would otherwise start on this
host, the repo that actor's working directory belongs to, and SHALL start no
actor into a repo that is not gate-ready.

For each such repo it SHALL print the repo, its resolved project identifier,
and every ungranted hook template verbatim, together with the exact remedy —
`wt config approvals add`, run interactively with the working directory inside
that repo. It SHALL NOT print a generic failure, and SHALL NOT suggest any
approval-skipping flag.

A repo failing the check SHALL NOT prevent actors in other, gate-ready repos
from starting in the same pass. `flywheel up` SHALL exit non-zero when it
refused to start any actor for this reason.

Each repo SHALL be evaluated once per pass however many actors resolve to it,
and reported once.

#### Scenario: Every actor's repo is ungranted

- **WHEN** `flywheel up` runs against a manifest whose running-state actors on
  this host all resolve to one repo that is not gate-ready
- **THEN** no actor is started
- **AND** the output names the repo, its identifier, and each ungranted
  template verbatim
- **AND** the output contains the literal command `wt config approvals add`
- **AND** the command exits non-zero

#### Scenario: One repo fails while another passes

- **WHEN** `flywheel up` runs against a manifest whose actors span two repos,
  one gate-ready and one not
- **THEN** the actors in the gate-ready repo are started as they are today
- **AND** the actors in the other repo are not started
- **AND** the command exits non-zero

#### Scenario: Two actors share one repo

- **WHEN** `flywheel up` would start two actors whose working directories
  resolve to the same repo, and that repo is not gate-ready
- **THEN** the repo and its ungranted templates are reported once, not once
  per actor

#### Scenario: The repo becomes granted

- **WHEN** `flywheel up` runs after the operator has granted every hook
  template of the repo its actors resolve to
- **THEN** the command starts actors exactly as it did before this capability
  existed, and prints no approval output

### Requirement: `flywheel status` reports the check as a row and starts nothing

`flywheel status` SHALL report the gate-readiness of every repo it can inspect
from here — the repos of the manifest's actors placed on this host whose
working directories are present on this machine — one row per repo, naming the
repo and whether it is gate-ready. For a repo that is not gate-ready the row
SHALL be accompanied by the ungranted templates and the same remedy
`flywheel up` prints.

`flywheel status` SHALL NOT report gate-readiness for a repo it cannot inspect:
another host's repo is not inspectable from here, and a working directory that
does not resolve on this machine has no config to read. Reporting either would
be a claim about a gate the command never looked at.

**What it skips, it SHALL name.** For every actor whose repo is excluded from
the gate rows, `flywheel status` SHALL say that it was skipped and why —
placed on another host, or its working directory absent here. It SHALL NOT
silently omit them. A gate report that covers fewer repos than the actor rows
imply, with nothing saying why, reads as a clean bill of health for repos
nobody checked; that silence is the disease this capability exists to cure, and
it is not permitted to reappear in the report itself.

`flywheel status` SHALL start no actor and SHALL leave the existing per-actor
rows and their drift reporting intact.

#### Scenario: Status reports an ungranted repo

- **WHEN** `flywheel status` runs against a manifest whose actors resolve to a
  repo that is not gate-ready
- **THEN** the output carries a row for that repo showing it is not gate-ready
- **AND** the existing actor rows are still printed
- **AND** no agent has been started

#### Scenario: An actor is placed on another host

- **WHEN** `flywheel status` runs against a manifest holding actors on a
  different host
- **THEN** no gate row claims those repos are gate-ready
- **AND** the output names them as skipped because they are on another host

#### Scenario: An actor's working directory is absent from this machine

- **WHEN** `flywheel status` runs against a manifest whose actor names a
  working directory that does not resolve here
- **THEN** no gate row claims that repo is gate-ready
- **AND** the output names it as skipped because its directory is not present
  on this machine

#### Scenario: The gate rows cover fewer repos than the actor rows

- **WHEN** `flywheel status` prints gate rows for fewer repos than its actor
  rows imply
- **THEN** every actor whose repo has no gate row is accounted for by a stated
  reason
- **AND** a reader can tell from the output alone which repos were checked and
  which were not

### Requirement: `flywheel reconcile` is bound by the same precondition

`flywheel reconcile` SHALL apply the same precondition to every actor it
starts — the manifest's standing rows and the tracker-driven conductors alike.
It SHALL start no actor into a repo that is not gate-ready, and SHALL report
the refusal with the same remedy.

`flywheel reconcile --dry-run` SHALL report which starts the precondition
would refuse, and SHALL start nothing.

A repo that is not gate-ready SHALL NOT stop the rest of a reconcile pass:
nudges, stops, and starts into gate-ready repos SHALL proceed.

#### Scenario: Reconcile wants a conductor in an ungranted repo

- **WHEN** `flywheel reconcile` finds a milestone with a job whose conductor
  would start in a repo that is not gate-ready
- **THEN** no conductor is started for it
- **AND** the output names the repo, the ungranted templates, and the remedy

#### Scenario: Reconcile still nudges and stops

- **WHEN** a reconcile pass refuses a start for an ungranted repo
- **THEN** the pass still nudges settled conductors with a job and still stops
  settled conductors whose milestone has no job

#### Scenario: A dry run reports the refusal without acting

- **WHEN** `flywheel reconcile --dry-run` runs against a manifest whose actors
  resolve to a repo that is not gate-ready
- **THEN** the output states that the starts would be refused for that repo
- **AND** no agent is started and the approvals store is untouched

### Requirement: An indeterminate check fails closed and says which way it failed

When the fleet cannot determine a repo's project identifier, cannot enumerate
its project hooks, or cannot read the approvals store — worktrunk unavailable,
a worktrunk query exiting non-zero, a project config worktrunk cannot load, or
an approvals store that is unreadable or not shaped as expected — the repo
SHALL be treated as not gate-ready for every command that starts actors.

The output SHALL distinguish this state from an ungranted repo: it SHALL say
that the check could not be made and why, rather than naming templates as
ungranted. It SHALL NOT report a repo gate-ready on the strength of a check
that did not run.

An indeterminate result SHALL NOT abort the command. It concerns one repo, and
the other repos in the same pass SHALL still be evaluated and reported.

The stated reason SHALL be a description the fleet composes. Where it draws on
a worktrunk failure, it SHALL summarise it rather than relaying the tool's raw
error stream verbatim.

#### Scenario: worktrunk is not available

- **WHEN** `flywheel up` evaluates a repo on a host where the worktrunk command
  cannot be run
- **THEN** no actor is started into that repo
- **AND** the output says the approval check could not be made, and why
- **AND** the output does not claim any template is ungranted

#### Scenario: The actor's working directory is in no repo

- **WHEN** an actor's working directory resolves to no worktrunk project
- **THEN** the repo is reported gate-ready under the no-hooks rule, not as an
  indeterminate check

#### Scenario: The approvals store is not shaped as expected

- **WHEN** the approvals store parses but its project table or grant list is
  not the shape the check expects
- **THEN** the repo is reported as an indeterminate check
- **AND** the command completes and reports its other repos, rather than
  failing outright

#### Scenario: One repo is indeterminate and another is fine

- **WHEN** a pass evaluates two repos and only the first is indeterminate
- **THEN** the second is still evaluated and reported on its own merits

### Requirement: The fleet skill documents the grant as an onboarding step

`skills/fleet/SKILL.md` SHALL document, in the section an operator reads when
bringing a repo into a fleet, that each built repo needs its worktrunk hook
approvals granted once — interactively, by the operator, with the working
directory inside that repo — before the fleet will start actors into it.

The documentation SHALL name the command to run and SHALL state that the fleet
commands check this and refuse to start actors otherwise. It SHALL NOT
instruct an operator or an agent to bypass approval with a skip-prompts flag,
and SHALL NOT describe any way for the machinery to grant approvals on the
operator's behalf.

#### Scenario: An operator sets up a new org's fleet

- **WHEN** an operator follows the fleet skill's setup section for a new org
- **THEN** they are told to grant each built repo's hook approvals
  interactively before bringing the fleet up
- **AND** they are told that `flywheel up` refuses to start actors into a repo
  whose approvals are missing

#### Scenario: The documentation never offers a bypass

- **WHEN** the fleet skill's text on approvals is read end to end
- **THEN** it contains no instruction to skip approval prompts and no
  suggestion that the fleet can write the approvals store

