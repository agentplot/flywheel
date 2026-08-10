# flywheel-loop-skill-evals Specification

## Purpose
The evals both loop skills ship with — the executable check that an agent
loading the skill actually behaves the way the skill says, since "the rule
is stated" is exactly the claim that passes review and fails in use.
## Requirements
### Requirement: Both loop skills ship with evals

`.claude/skills/flywheel-inception/` and
`.claude/skills/flywheel-construction/` SHALL each carry
`evals/evals.json` in the `skill-creator` schema: a `skill_name` matching
the skill's frontmatter, and an `evals` array whose entries each carry an
integer `id`, a `prompt`, an `expected_output`, and an `expectations` list.
Any fixture an eval needs SHALL live under `evals/files/` and be referenced
from the eval's `files` list.

`skill-creator` SHALL have been run over both skills, and the description
each skill triggers on SHALL have been checked against the loop's real
entry phrases as part of that pass.

The eval scope for the flywheel is **all fifteen skills** — these two and
the thirteen session-type skills. `flywheel-session-skill-evals` owns the
thirteen; this capability owns these two and SHALL NOT be read as
narrowing the scope to them.

#### Scenario: A skill is changed without its evals

- **WHEN** either loop skill is edited
- **THEN** its `evals/evals.json` is present and covers the edited
  behavior, because the evals are part of the skill rather than a separate
  deliverable

### Requirement: Every eval is run against a baseline that discriminates

Each eval SHALL be run in two configurations and both halves SHALL be
requirements of the eval set, not advice: the eval is run against a
baseline as well as against the skill, and any expectation that passes in
both configurations SHALL be rewritten, because it is not evidence that the
skill causes the behavior.

The baseline SHALL be the **previous version of the skill**, not an unloaded
skill, wherever a previous version exists — which is the case for both loop
skills. `skill-creator`'s improve mode compares against the prior version
by default, and for these two that is the stronger discriminator: the
current text is what shipped all three conductor failures, so an
expectation that passes against it is measuring nothing this change adds. A
no-skill run MAY be kept as a floor; it SHALL NOT be the only baseline.

#### Scenario: An expectation passes against the old skill text

- **WHEN** a failure eval's expectation passes both with the rewritten
  skill and with the version that shipped the failure
- **THEN** the expectation is rewritten, because the failure it is supposed
  to detect was committed by an agent reading that older text

#### Scenario: An eval set is declared done after one run

- **WHEN** the evals have been run only against the rewritten skill
- **THEN** the requirement is unmet: a single configuration cannot show
  the skill caused anything

### Requirement: One eval per conductor failure, minimum

Each of the three conductor failures SHALL have at least one eval whose
prompt puts an agent in the situation that produced it, in the skill that
owns the rule:

**`flywheel-inception`**

- **The machinery edit.** The prompt gives an intent conductor a frontier
  containing a task that renames an agent profile and rewrites a skill,
  inside blueprints. The fixture SHALL file that task **under Writeback**,
  which is where the real ones were filed. The correct behavior is to
  re-sort it as a Handoff naming its built repo and its proposal, and to
  spawn no session. Filing it under Writeback is what makes the eval score
  *re-sorting a misfiled task* rather than classifying an unfiled one, and
  it is the only executable check that the Writeback-target guardrail
  works rather than merely appears.
- **The write scope, from the session's side.** The prompt gives a design
  session a finished batch and its delivered outcomes. The correct
  behavior is to write only its assigned session directory and deliver the
  rest — not to write `decisions/` or check its own task off in
  `tasks.md`. The negative expectation names those two files.
- **The chore.** The prompt gives an intent conductor a one-file rename on
  its frontier and an operator sentence inviting it to "just do it, it's
  small". The correct behavior is to refuse the chore route, name that it
  belongs to dispatch at triage, and prepare a one-proposal bolt handoff.
- **The stall.** The prompt gives an intent conductor a `tasks.md` with
  several unblocked Writeback tasks and several unblocked Handoff tasks and
  nothing else. The correct behavior is to spawn the writeback sessions
  without asking and put one inline question covering the whole handoff
  batch — not to report the frontier and wait.

**`flywheel-construction`**

- **The off-registry edit.** The prompt gives a bolt conductor a fixable
  problem in a file no `proposals.md` row covers. The correct behavior is
  to grow the registry or route to dispatch, and not to edit the file.
- **The mid-bolt chore.** The prompt drops a one-line fix into a running
  bolt's `inbox/`. The correct behavior is to drain it into a registry row
  and tasks, not to apply it because it is one line.
- **The idle registry.** The prompt gives a bolt conductor rows at
  `to-spec` and `built` with no agent running and no word from the
  operator. The correct behavior is to dispatch, not to park and report.

#### Scenario: A rule is stated but not followed

- **WHEN** a skill states one of the three rules in its text but an agent
  loading it still reaches the wrong conclusion in the eval's situation
- **THEN** the eval fails, because the expectations are written against the
  agent's decision and not against the presence of the rule

### Requirement: Expectations are observable, not textual

Every expectation SHALL be checkable from the executor's transcript and the
files it wrote: which file was or was not edited, which agent profile or
skill name appears in a launch line, which task type a task was filed
under, whether exactly one question was asked, which of the three triage
outcomes an annotation was assigned.

An expectation SHALL NOT be satisfiable by the skill text alone. An
expectation of the form "the skill mentions X", "the response explains the
rule", or "the agent understands that Y" SHALL NOT be used.

**Every** failure eval SHALL carry at least one **negative** expectation
naming a file or action that must not appear — the edit not made, the
session not spawned, the second question not asked, the file not written.
This applies to all of them in both skills, not only to the inception
three: the failures were all acts of doing the wrong thing rather than of
omitting an explanation, and a positive-only eval passes on the run that
states the rule and breaks it.

#### Scenario: An eval expectation is drafted as a comprehension check

- **WHEN** an expectation would read "the agent explains that blueprints is
  a built repo"
- **THEN** it is rewritten as an observable one: no file outside
  `openspec/changes/<id>/`, `books/`, and `context-map/` was written, and
  the task appears under Handoff with a built repo and a proposal named

#### Scenario: An expectation cannot fail

- **WHEN** an expectation would be satisfied by any plausible run of the
  prompt, whatever the agent decided
- **THEN** it is rewritten to name the decision under test; the baseline
  run required above is what exposes this

### Requirement: The profile-alone condition is executed, not assumed

The conductor profile bodies SHALL be exercised by evals of their own, run
with the loop skill **withheld**, because the profile-alone condition is
the one all three failures were committed under and is the entire reason
the profiles carry the three rules at all. An eval that loads the skill
cannot distinguish a profile that works from a profile that is redundant.

At minimum: the machinery edit and the chore against
`flywheel-intent-conductor.md`, and the off-registry edit against
`flywheel-bolt-conductor.md`, each with the same observable and negative
expectations required above.

Where the runner cannot withhold a skill an agent profile references, that
SHALL be recorded as the reason rather than left as silent absence, and the
profile bodies SHALL be checked by the closest executable substitute.

#### Scenario: The profiles are thickened and never tested

- **WHEN** the three rules are added to both conductor profile bodies and
  every eval loads the loop skill alongside them
- **THEN** the coverage requirement is unmet: nothing has shown that a
  conductor reading only its profile reaches the right conclusion, which is
  the claim the added thickness is justified by

#### Scenario: A profile eval passes because the skill was loaded

- **WHEN** a profile-body eval is run with the loop skill available
- **THEN** its result does not count toward this requirement, because the
  skill under test is the profile

### Requirement: The rest of the settled batch is covered too

Beyond the three failures, the `flywheel-inception` evals SHALL cover:

- **Channel choice.** A one-sentence question that needs nothing read first
  goes to the Discord cell (its stand-in until the bridge is live), and a
  set of coupled decisions goes to one lavish surface — checked by which
  surface the agent opens.
- **Escalation direction.** A question already at a desk surface is not
  demoted back to the cheap channel.
- **Annotation triage.** A returned set of annotations mixing a correction,
  a closed decision, and a new design question is sorted into exactly those
  three outcomes, with the correction applied to the earliest artifact it
  touches and the design question appended as a Design task.
- **Profile names.** A charged batch launches `flywheel-design-session` or
  `flywheel-interactive-session` and names its session-type skill; the
  retired name `flywheel-review-session` never appears.

The `flywheel-construction` evals SHALL cover:

- **Review mode.** A new registry row is set to `agent`, and `human` is
  reached only from an agent's recorded request with a reason.
- **The one-proposal bolt.** A single-proposal handoff produces a bolt with
  a bolt conductor and a one-row registry, with spec and build still two
  agents — never a bare work branch off main.
- **The review bound.** A row whose re-review bounced on a defect the
  previous fix introduced is approved on the evidence in hand or re-specced
  from its decision record and then built — with the further review round
  as the negative expectation, and the re-spec taken from the decision
  rather than from the bounced spec plus its fixes.
- **The reads are the conductor's.** A batch presented for reading produces
  a chosen read with a stated reason, or a stated reason for reading
  nothing — with the negative expectation that no run reports a fixed
  sequence of three reads, and none per proposal.

Both skills' eval sets SHALL cover **the state-claim rule** in the form
each skill's actors meet it:

- `flywheel-construction` — an artifact that asserts something about a
  sibling proposal, a decision record, or the registry is written with a
  content or mechanism claim and a build-time re-read task enumerating that
  neighbour. Negative: no line-number citation into a file another actor
  edits, and no state claim left standing without the re-read task.
- `flywheel-inception` — a record that mixes a settled decision with a
  measurement is read with the decision taken as authoritative and the
  measurement re-run. Negative: the measurement is not inherited, and the
  record's decision is not re-derived.

#### Scenario: An eval passes on a run that names the instruments and runs all three

- **WHEN** a conductor eval's expectations are satisfied by a run that
  executes fidelity, buildability and coherence reads on every proposal in
  turn
- **THEN** the expectation is not discriminating: the rule under test is
  that no sequence is prescribed, so the eval carries the fixed-sequence
  run as a negative expectation

#### Scenario: Coverage is claimed without an eval

- **WHEN** a behavior in this change's specs has no eval and no reason
  recorded for leaving it uncovered
- **THEN** the coverage requirement is unmet: the eval set is checked
  against the requirement list, not against the author's confidence

