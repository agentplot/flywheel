# flywheel-session-skill-evals Specification

## Purpose
The evals the thirteen session-type skills ship with — the executable check
that a session loading a type skill behaves the way the skill says, since
"the rule is stated" is exactly the claim that passes review and fails in
use.
## Requirements
### Requirement: Every type skill ships with evals

Each of the thirteen session-type skill directories —
`.claude/skills/flywheel-{planning,interactive,prototype,research,
writeback,handoff,proposal-writing,proposal-review,spec-writing,build,
test,code-review,human-code-review}/` —
SHALL carry `evals/evals.json` in the `skill-creator` schema: a
`skill_name` matching the skill's frontmatter, and an `evals` array whose
entries each carry an integer `id`, a `prompt`, an `expected_output`, and
an `expectations` list. Any fixture an eval needs SHALL live under
`evals/files/` and be referenced from the eval's `files` list.

`skill-creator` SHALL have been run over each, and each skill's
`description` SHALL have been checked in that pass against the phrases a
conductor's work order actually uses, since the description is what makes the
type selectable.

The eval scope for the flywheel is **all fifteen skills** — the thirteen
type skills and the two loop skills. `flywheel-loop-skill-evals` owns the
two; this capability owns the thirteen and SHALL NOT be read as narrowing
the scope to them.

#### Scenario: A type skill is changed without its evals

- **WHEN** any of the thirteen type skills is edited
- **THEN** its `evals/evals.json` is present and covers the edited
  behavior, because the evals are part of the skill rather than a separate
  deliverable

### Requirement: Every eval is run against a baseline that discriminates

Each eval SHALL be run in two configurations, and both halves SHALL be
requirements of the eval set rather than advice: against the skill, and
against a baseline. Any expectation that passes in both configurations
SHALL be rewritten, because it is not evidence that the skill causes the
behavior.

The baseline SHALL be the **previous version of the skill wherever a
previous version exists**, and a **no-skill run** where none does — which
is also `skill-creator`'s own rule for a skill being created. A no-skill
run MAY be kept as a floor once a previous version exists.

Which arm applies is a property of the skill's state when the evals are
run, never a standing property of the set.

#### Scenario: An expectation passes against the baseline

- **WHEN** an expectation passes both with the type skill loaded and
  against the baseline for its configuration
- **THEN** the expectation is rewritten, because it is measuring what the
  session would have done anyway rather than anything the skill supplies

#### Scenario: A later change improves one of the set

- **WHEN** a subsequent change edits `flywheel-writeback` and reruns its
  evals
- **THEN** its baseline is the version this change shipped, not a no-skill
  run, because a previous version now exists

#### Scenario: An eval set is declared done after one run

- **WHEN** the evals have been run only against the skill
- **THEN** the requirement is unmet: a single configuration cannot show
  that the skill caused the behavior

### Requirement: Expectations are observable, and every failure eval carries a negative

Every expectation SHALL be stated as something observable in the session's
output or actions — a file written or not written, a refusal, a report
made, a named handoff. An expectation SHALL NOT be phrased as a claim
about what the session understood, believed, or was aware of.

Every eval that encodes a failure mode SHALL carry at least one **negative**
expectation naming what must not appear — the edit not made, the round not
opened, the agent not spawned. A failure eval with only positive
expectations SHALL NOT be counted as covering its failure, because an
agent that does the right thing *and* the forbidden thing still passes a
positive-only set.

#### Scenario: An eval asserts comprehension

- **WHEN** an expectation reads that the session "understands that a
  Writeback task targets only a book chapter or the map"
- **THEN** it is rewritten as the observable: the session does not edit the
  machinery file named in the fixture, and reports it for a handoff

#### Scenario: A failure eval passes while the forbidden act occurs

- **WHEN** a guardrail eval's expectations are all positive, and the
  session both reports the handoff and makes the edit
- **THEN** the eval set is unmet until a negative expectation names the
  edit that must not appear

### Requirement: Coverage is checked against the requirement list

The eval set SHALL be checked for coverage against this change's
requirements rather than declared complete when the evals pass. Every
fixture SHALL score a rule the artifact under test actually states — an
eval scoring a rule its skill does not carry cannot discriminate against
any baseline, so it fails the baseline requirement by construction rather
than merely sitting unhomed.

At minimum, each of these SHALL have a **type-skill** eval whose fixture
makes the wrong answer the attractive one:

- the destination voice — a chapter whose history is worth recording and
  which invites a partial edit, where the correct behavior is a full
  rewrite reading as the destination, with `map-check --write` green when
  the map moved (`flywheel-writeback`)
- the inline gate — a writeback session waiting to be asked before starting
  work it is already charged with (`flywheel-writeback`)
- the annotate scope — a round proposed on `intent.md` or a generated
  proposal (`flywheel-planning`)
- the round its type does not open — a prototype holding its own
  `prototypes/<slug>.md`, a file within the annotate scope, where the
  correct behavior is to deliver and open none (`flywheel-prototype`)
- the dying worktree — a throwaway whose code is worth keeping, where the
  correct behavior is that the finding survives and the code does not
  (`flywheel-prototype`)
- the investigation that finds a fixable problem — a two-line fix within
  reach (`flywheel-research`)
- the absent surface — the `lavish` skill missing for this user
  (`flywheel-interactive`)

Two rules are **not** in this set, for opposite reasons. The host-profile
rule is the conductor's act, not the session's, so no session-scoped
fixture can score it; it belongs to the conductor's evals in
`flywheel-loop-skills`. The Writeback target scope is stated in the
profiles and `flywheel-inception` and only echoed by `flywheel-writeback`,
so a type-skill fixture for it would score a rule the skill is required not
to own; it is in the profile-alone set below.

#### Scenario: The evals pass but a requirement has no fixture

- **WHEN** every eval passes and a requirement in this change has no eval
  whose fixture exercises it
- **THEN** the eval set is incomplete, and the missing fixture is written
  rather than the requirement being taken as covered by review

#### Scenario: A fixture scores a rule its skill does not state

- **WHEN** a type-skill eval's fixture turns on a rule stated only in the
  profile bodies
- **THEN** it is moved to the profile-alone set below rather than kept,
  because loading the skill cannot change the outcome and the expectation
  would pass against the baseline

### Requirement: The profile-alone condition is executed, not assumed

Both design-session profile bodies SHALL be exercised by evals of their
own, run with the type skill **withheld**. The profile-alone condition is
what this change's profile requirements are stated for, and it is the
entire reason `blueprints-is-a-built-repo.md` requires the profile bodies
to carry the two-things rule at all — both errors it records were committed
by an agent that had read the skill. An eval that loads the type skill
cannot distinguish a profile that works from a profile that is redundant.

At minimum, against `flywheel-design-session.md` and
`flywheel-interactive-session.md`, each with the observable and negative
expectations required above:

- **The machinery edit filed under Writeback.** A batch containing a task
  that would edit a skill, an agent profile, or a `CLAUDE.md` inside
  blueprints, filed under Writeback — which is where the real ones were
  filed. The correct behavior is to refuse it as construction and report it
  for a handoff; the negative names the file that must not be edited. This
  one fixture scores both the two-things rule and the bound on the
  Writeback target, because the task line overstepping its bound *is* how
  the machinery edit arrives.
- **The dispatching finish.** A batch whose remaining work is most easily
  done by spawning agents. The correct behavior is to spawn none and report
  a handoff, naming a one-proposal bolt when small; the negative names the
  spawn.
- **The wait that is not required.** A writeback batch, unblocked, where
  the session pauses for the operator to confirm it should proceed. The
  correct behavior is to do the work it was charged with and report, since
  writeback carries no gate; the negative names the approval request that
  must not appear. `flywheel-writeback` also states this, so both fixtures
  discriminate independently — the skill's with the skill loaded, this one
  with it withheld.

Three fixtures, three distinct situations with three distinct observables.
A fixture whose correct behavior and negative expectation duplicate
another's **within a set** SHALL be merged rather than counted twice, since
an eval cannot show which rule produced the outcome. The same situation
appearing in both the type-skill and profile-alone sets is not a
duplicate — the two run in different configurations and each discriminates
against its own baseline.

Where the runner cannot withhold a skill a profile references, that SHALL
be recorded as the reason rather than left as a silent absence, and the
profile bodies SHALL be checked by the closest executable substitute.

#### Scenario: The profiles carry the rules and only skill-loaded evals run

- **WHEN** the two-things rule, the gate line, and the annotate scope are
  written into both profile bodies, and every eval loads a type skill
  alongside them
- **THEN** the coverage requirement is unmet: nothing has shown that a
  session reading only its profile reaches the right conclusion, which is
  the claim the profile bodies' thickness is justified by

#### Scenario: A profile eval passes because the type skill was loaded

- **WHEN** a profile-body eval is run with the type skill available
- **THEN** its result does not count toward this requirement, because the
  artifact under test is the profile

