# flywheel-construction-skill Specification

## Purpose
The construction loop's practice — what `flywheel-construction` tells a
bolt conductor and the agents it dispatches: the review bar that lets
construction deliver without a standing human stage, the bound on spec
review and the instruments a conductor chooses instead of a prescribed
sequence, the state-claim rule the spec agents write under, the
one-proposal bolt as the small end of the single path out of the gate, and
the three rules a conductor must not be able to reason its way past.
## Requirements
### Requirement: The review bar that earns automated delivery

The skill SHALL state the construction review bar outright: **adversarial
agent review plus automated testing** are how construction earns automated
delivery. The inner loop minimizes human review deliberately, and the bar
is what makes that safe.

The skill SHALL describe the `agent` review mode as adversarial rather than
confirmatory: an independent reviewer reads the full artifact set *and the
cited sources* and hunts for plumbing-only specs, cross-proposal drift,
unaccounted source material, and ungrounded assumptions, verifying
unfamiliar APIs against current documentation rather than training memory.
The reviewer never edits artifacts; a bounce re-dispatches a spec agent and
returns the row to `to-spec` with the gaps noted in tasks.

The skill SHALL state that automated delivery rests on that bar holding, so
any proposal to weaken it — dropping the independent reviewer, letting the
reviewer edit what it reviews, landing without the repo's named suites — is
a design finding routed to dispatch, not a local call the bolt conductor
makes.

#### Scenario: A reviewer approves a spec it also fixed

- **WHEN** an independent reviewer would correct a gap it found rather than
  bounce the row
- **THEN** the skill forbids it: the reviewer's output is a verdict, the
  bounce re-dispatches a spec agent, and the row returns to `to-spec`

#### Scenario: A bolt wants to land without acceptance because the change is small

- **WHEN** a conductor would skip batched acceptance on the bolt branch
  because a proposal looks trivial
- **THEN** the skill names that as weakening the bar that earns automated
  delivery, and routes the question to dispatch as a design finding rather
  than deciding it in the bolt

### Requirement: Spec review is bounded to one round

The skill SHALL state that a proposal gets **one review round**. A bounce
is followed by a fix or by a **re-spec from the proposal's decision
record**, and the result of either is built rather than read again. The
re-spec SHALL start from the decision, never from the bounced spec plus its
fixes, and SHALL NOT itself be reviewed. Past that point each row takes one
binary call on the evidence already in hand — approved, or re-spec from its
decision record — and then builds.

The skill SHALL name the **churn signal** as the trigger for calling the
bound early: re-reviews bouncing on defects the fixes introduced rather
than on anything the first round missed. At that point every further round
buys wording rather than correctness.

The skill SHALL state that verification does not relax. What is bounded is
*spec review* — an agent reading a proposal against its sources — not the
checks that run against the tree that lands: the merge gate, the bolt's
merge criteria, and the acceptance evidence all still bind.

The skill SHALL state that findings which would have opened another review
round go to the end-to-end run's report while a run is pending, as a
redirection rather than a suppression, and that a declared review which is
not run is recorded as **not run** rather than left standing on the row as
if it had been.

The skill SHALL NOT describe a review loop that continues until a reviewer
is satisfied, and SHALL NOT leave the bounce path open-ended.

#### Scenario: A re-review bounces on a defect the previous fix introduced

- **WHEN** a row's second reading fails on something the first round's
  fixes created rather than on anything the first round missed
- **THEN** the skill has the conductor stop reviewing that row and take the
  binary call — approve on the evidence in hand, or re-spec from the
  decision record — and build the result

#### Scenario: A conductor wants a third reading before building

- **WHEN** a conductor would dispatch another reviewer over a bounced and
  re-specced row
- **THEN** the skill forbids the round: the re-spec is built, and any
  finding that would have justified the round goes to the end-to-end run's
  report

#### Scenario: A bounded review is mistaken for a bounded gate

- **WHEN** a conductor reads the bound as licence to land without the
  repo's named suites or the bolt's merge criteria
- **THEN** the skill contradicts it outright: only spec review is bounded,
  and the automated half of the review bar is untouched

### Requirement: The reads are instruments the conductor chooses, not steps it runs

The skill SHALL state the bolt conductor's accountability in one line: that
the batch it is about to build is **buildable and internally coherent**,
with how it satisfies that left to its judgment.

The skill SHALL state that reads are **across the batch, not per
proposal**, because the defects that occur are relational — a rule
compressed in one record and carried into several proposals, a naming
collision spanning two, a proposal requiring a form of a rule its sibling
correctly does not state, a positive specification living in a shared
source that several proposals cite and none restates. A reader holding one
proposal cannot see any of those.

The skill SHALL name three kinds as **instruments**, each for what it
catches: **fidelity** (does this match the sources it cites),
**buildability** (could an agent holding only this and the repo produce the
right file — where would it stall, guess, go hunting, or do the wrong thing
confidently), and **coherence** (do these proposals agree with each other
and with the decisions they cite).

The skill SHALL NOT prescribe a sequence, SHALL NOT make any read
mandatory, and SHALL NOT present the three as stages of the proposal flow.
It SHALL state why: naming three kinds and requiring all three produces a
liturgy, and a liturgy is performed rather than judged.

The skill SHALL state the boundary with the review bound: a read is one
pass with no verdict and no bounce — it patches a spec or it finds nothing
— so reaching for an instrument is not a review round. It SHALL also state
that a row whose tasks cannot produce the right file is not approved
whatever a reader concluded about its claims, and that re-speccing such a
row is the bound's re-spec branch rather than a reopening.

The skill SHALL carry the heuristic, as a heuristic and not a rule about
when a read must run: proposals that write **new files from scratch** carry
buildability risk disproportionately, having no existing text to anchor
against, because review pressure hardens the negative checks while the
positive specification stays wherever it was first written — and the more
rounds a proposal survives, the worse that skews.

The skill SHALL state that the `review` column on a `proposals.md` row
keeps its narrow meaning — a declaration that a row wants the operator's
eyes — and is never a statement that a mandatory read type has been
performed.

#### Scenario: A conductor plans its reading for a batch of five proposals

- **WHEN** a bolt conductor has a batch specced and is deciding what to
  read before building
- **THEN** the skill gives it three instruments and its accountability, and
  the choice of which to run — it does not hand it a sequence of three
  reads to execute per proposal

#### Scenario: A conductor asks which read is required

- **WHEN** a conductor looks for the mandatory read type before approving a
  row
- **THEN** the skill states that there is none, and that the `review`
  column declares the operator's eyes are wanted rather than that a read
  was performed

#### Scenario: A defect spans two proposals

- **WHEN** two proposals in one batch collide on a name, or one requires a
  form of a rule its sibling correctly does not state
- **THEN** the skill's unit of reading is the batch, so a coherence read
  over the set is what is reached for — a per-proposal reading cannot see
  it

#### Scenario: A read is mistaken for a review round

- **WHEN** a conductor believes running a buildability read over the batch
  would reopen the bounded review loop
- **THEN** the skill distinguishes them: a read is one pass with no verdict
  and no bounce, and the bound is on rounds

### Requirement: The state-claim rule, carried verbatim

The skill SHALL carry the state-claim rule **word for word** as the intent
records it: the defect (a claim about a neighbouring artifact's state that
the neighbour no longer bears out), the rule in three parts, its closing
warrant, and both corollaries. It SHALL NOT be paraphrased, summarized, or
adapted for this reader.

The three parts SHALL read: prefer a CONTENT claim to a STATE claim;
where a state claim is unavoidable, name the MECHANISM rather than its
current output; and carry a **build-time** task enumerating every neighbour
the artifact asserts something about, instructing the builder to re-read
each from disk.

Both corollaries SHALL be present: that a decision record is authoritative
on its decision and provisional on its measurements, and that **a
line-number citation is itself a state claim**, to be replaced by an
anchor, a heading, or a quoted phrase.

The seam paragraph SHALL travel with the rule, because it is what explains
the rule's two homes: the loops run at different clock rates and the fast
loop writes the claims the slow loop has to keep true. The wording SHALL be
identical to the copy in `flywheel-inception`; only the framing sentence
naming which actor writes these claims may differ.

The skill SHALL apply the rule in its own spec step: every spec carries the
build-time re-read task, and cites by anchor or quoted phrase rather than
by line number.

#### Scenario: A spec agent needs to describe a sibling proposal

- **WHEN** a spec asserts something about a sibling proposal, a decision
  record, the registry, or the archive
- **THEN** the skill has it prefer a content claim, name the mechanism
  where a state claim is unavoidable, and enumerate that neighbour in a
  build-time re-read task

#### Scenario: A spec cites a file by line number

- **WHEN** a spec locates a passage in a file a sibling is about to edit
- **THEN** the skill treats the line number as a state claim and requires
  an anchor, heading, or quoted phrase instead

#### Scenario: The two copies of the rule are compared

- **WHEN** the passage in `flywheel-construction` is read beside the one in
  `flywheel-inception`
- **THEN** the rule's body is identical in both, because a rule about the
  precision of claims is not reworded per reader

### Requirement: Human code review is a request, not a stage

The skill SHALL state that human code review is a **request an agent may
make**, not a stage the pipeline runs. The `human` review mode on a
`proposals.md` row exists because an agent asked for it with a reason —
recorded on the row or its task line — and the default review mode is
`agent`.

The skill SHALL NOT present `agent` and `human` as two equal modes a
conductor picks between by taste, and SHALL NOT describe any point in the
flow at which the pipeline waits for a human to read code.

#### Scenario: A conductor sets review mode on a new row

- **WHEN** a proposal joins the registry as a new `to-spec` row
- **THEN** the skill has the conductor set `agent`, because that is the
  default and `human` requires a request with a reason

#### Scenario: A build agent is unsure its approach is what the design meant

- **WHEN** an agent building a proposal cannot resolve whether its approach
  matches the cited design source
- **THEN** the skill lets it request a human round — `plannotator annotate`
  on the proposal, the operator's approve/deny as the verdict — and the
  request and its reason are recorded on the row

#### Scenario: An agent is confident and the change is ordinary

- **WHEN** no agent has asked for a human round
- **THEN** the pipeline runs adversarial agent review and the repo's
  automated suites and delivers, without stopping for a human to read the
  code

### Requirement: The one-proposal bolt

The skill SHALL describe the one-proposal bolt as a named special case of
the single path out of the phase gate, not as a different path: the same
artifacts (`bolt.md`, a `proposals.md` registry of exactly one row, tasks)
and the same actors (a bolt conductor, a spec agent, an apply agent, a
reviewer, a testing agent) at the smallest size.

The skill SHALL state why the bolt earns its keep below the size at which
its tracking would: writing the proposal and building the code stay two
agents, an independent review and the archive stay available, and feedback
that has to travel back to dispatch has an owner to catch it and a place to
land.

The skill SHALL state that nothing releases into a bare work branch off
main, and that building directly on the bolt branch — legal only for a bolt
with a single small proposal — is a branch-shape choice inside the bolt, not
a way to skip having one.

#### Scenario: A released unit carries a single small change

- **WHEN** the operator approves a unit whose whole content is
  one rename in one repo
- **THEN** the skill has a bolt created with a bolt conductor and a one-row
  registry, with spec and build still two agents — not a branch cut off
  main and worked inline

#### Scenario: A conductor proposes skipping the spec agent for a trivial row

- **WHEN** the apply agent could plausibly write both the proposal and the
  code for a one-row bolt
- **THEN** the skill keeps them two agents, because that separation is the
  stated reason the one-proposal bolt exists

### Requirement: Every edit a bolt lands is carried by a proposal row

The skill SHALL state the write scope per actor: the bolt conductor writes
the bolt change's own artifacts, and the spec, apply and testing agents it
dispatches write the spec-driven change and branch that their registry row
names, in the built repo. Every file edit the bolt lands is carried by such
a row; there is no untracked edit inside a bolt.

The attribution SHALL NOT be compressed into one clause covering the
conductor and its agents together — the conductor is the sole writer of the
bolt change, and an agent reports its outcome rather than editing the
registry or the tasks itself.

The skill SHALL state that this holds when the built repo is blueprints
itself. A bolt whose subject is the machinery blueprints carries — skills,
agent profiles, schema instructions, `CLAUDE.md` conventions, plugins —
runs exactly as any other bolt: a bolt branch and worktree per repo, a
registry row per proposal, the same states, the same gates. Blueprints
being the repo the conductor runs in changes nothing.

#### Scenario: A conductor is asked to fix a typo it noticed in a skill

- **WHEN** a bolt conductor sees a small correctable problem in a file no
  registry row covers
- **THEN** the skill has it either grow the registry with a row that covers
  the work, or route the idea to dispatch — never edit the file directly

#### Scenario: The bolt's built repo is blueprints

- **WHEN** a bolt's proposals all edit `.claude/` and `openspec/schemas/`
  in blueprints
- **THEN** the skill has the conductor cut a `bolt/<slug>` branch and
  worktree in blueprints and run the ordinary flow on it, rather than
  editing the main checkout because the bolt change happens to live there

### Requirement: The chore route is closed inside a bolt

The skill SHALL state that the chore route — running `opsx` directly with
no tracking — belongs to dispatch at the moment of triage and is closed
once a bolt owns the work. A bolt conductor SHALL NOT drain scope that
belongs to its bolt as an untracked edit, however small.

The skill SHALL keep the existing rule that new work pushed into a live
bolt joins the registry as new `to-spec` rows and new tasks — the bolt
grows, and never spawns a sibling for scope that belongs to it — and SHALL
state the third option explicitly: scope that does not belong to the bolt
goes back to dispatch, not into the bolt as an unrowed edit.

#### Scenario: A one-line fix arrives mid-bolt

- **WHEN** an amendment request drops a one-line fix into a running bolt's
  `inbox/`
- **THEN** the skill has the conductor drain it into the registry as a row
  and into tasks — not apply it directly because it is one line

#### Scenario: An idea arrives that the bolt does not cover

- **WHEN** an inbox request names work outside the bolt's scope
- **THEN** the conductor routes it to dispatch rather than growing the
  registry past what `bolt.md` says the bolt is

### Requirement: The skill names dispatch, not intake

No occurrence of `intake` as the name of the standing singleton SHALL
remain in the file; the singleton is `dispatch` everywhere, including the
opening paragraph's list of pushed work ("design releases, intake requests,
testing findings") and step 4's routing rule ("**design-level findings
route to intake**"). This change owns the file; no other proposal edits it,
and the "route to dispatch" sentence this change adds elsewhere in the same
file SHALL NOT be left sitting beside the old name.

#### Scenario: The construction skill is searched for the old name

- **WHEN** `.claude/skills/flywheel-construction/SKILL.md` is searched for
  `intake`
- **THEN** there are no hits: the singleton is dispatch everywhere,
  including the design-findings routing rule

### Requirement: The phase gate covers the bolt's waves

The skill SHALL state that the operator's phase gate — the approval that
released the bolt — is the brief approval for the bolt's waves, so a bolt
conductor does **not** re-gate each spec agent. Launching the next wave
inside a released bolt needs no new operator approval.

The skill SHALL state why a per-wave gate can read as required: the
practice predates the flywheel, when the operator reviewed each wave brief
before launch. Inside a released bolt that is exactly the ceremony
`the-gate-is-inline.md` exists to stop, so the flywheel's gate supersedes
it there.

#### Scenario: A conductor is about to launch its second wave

- **WHEN** a bolt conductor has three specced rows ready to build and
  recalls the older per-wave-brief practice
- **THEN** it launches without presenting a brief and waiting: the phase
  gate that created the bolt already covered its waves

#### Scenario: The bolt's scope would grow

- **WHEN** work arrives that `bolt.md` does not cover
- **THEN** the wave rule does not apply — that is out-of-scope work routed
  to dispatch, and the gate that covered the bolt's waves did not cover it

### Requirement: Spec agents sharing a bolt worktree do not commit

The skill SHALL state that spec agents sharing a bolt worktree do not
commit: the conductor lands each finished spec itself, staging by explicit
pathspec. Agents in one worktree share one git index, so a pathspec-less
commit takes whatever a sibling has staged.

The skill SHALL state the standing form of the rule for every actor that
does commit — stage and commit only the paths you wrote, never `-a`, never
`add -A`, never a pathspec-less `git commit` — and SHALL NOT leave the
unqualified instruction to commit after any artifact change standing beside
it.

#### Scenario: Five spec agents work one bolt worktree

- **WHEN** several spec agents produce finished changes in the same bolt
  worktree
- **THEN** none of them commits; the conductor commits each by pathspec, so
  no agent's commit can carry another's staged work

#### Scenario: The conductor commits a finished spec

- **WHEN** the conductor lands one agent's artifacts while another is still
  writing
- **THEN** it stages the paths that agent wrote and nothing else

### Requirement: The bolt conductor drives its registry and parks only when empty

The skill SHALL state that the bolt conductor drives continuously: every
registry row whose state has an unblocked next action is dispatched without
waiting for the operator to raise the subject. A conductor that has
unblocked work and is waiting is malfunctioning.

The skill SHALL scope the long-lived parked posture to the case that
earns it: the conductor parks on running agents (bare `herdr agent wait`),
drains the inbox, and waits only when **no row has an unblocked next
action**. The operator's two moments in a bolt's life are the phase gate
that created it and the closure it agrees to; nothing between them is a
standing human stage.

Both unqualified statements of the posture SHALL be repaired, not only the
one in the long-lived section. The opening paragraph's "stay alive between
batches — waiting on the operator, accepting pushed work" carries the same
reading as the sentence that produced the intent conductor's stall, and it
is the first thing a bolt conductor reads.

#### Scenario: Three rows sit at to-spec and one at built

- **WHEN** the registry has rows with unblocked next actions and the
  operator has said nothing since the bolt started
- **THEN** the skill has the conductor dispatch the spec agents and the
  acceptance run immediately, rather than reporting the registry and
  waiting

#### Scenario: Everything is in flight

- **WHEN** every row is waiting on an agent that is running
- **THEN** the parked posture applies: park on the agents, drain the inbox,
  keep the change committed

