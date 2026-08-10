---
name: construction
description: Run the flywheel construction loop — a bolt conductor drives proposals through spec, review, build, test, and merge across built-repo bolt branches, tracked in a bolt OpenSpec change whose schema member is its review depth. Use when a bolt is created or amended, when the operator asks to check on or land construction work, or when construction findings need routing.
---

# Flywheel construction — the bolt loop

One bolt = one construction iteration = one OpenSpec change on blueprints
**main**, bound to the bolt schema member matching its work —
`bolt-default`, `bolt-quick`, `bolt-deep` (shipped in this plugin's `schemas/`) —
where **the member picked at creation IS the review depth**, chosen once
and never argued per proposal. `bolt-no-spec` binds no schema: plan mode
replaces the spec step, and the plan, the commits and the report are the
whole record. `flywheel-bolt` is the pre-family schema live bolts still
bind; it carries the default depth and retires when they archive. The **bolt conductor** (herdr agent
`bolt-<slug>`, session on blueprints main, long-lived, launched under the
`flywheel-bolt-conductor` agent profile with the first prompt naming the
bolt) owns that change and drives everything it tracks. A bolt exists only
past the operator's approval, so bolt conductors auto-start on request
and stay alive across batches — dispatching every row that has an unblocked
next action, accepting pushed work (design handoffs, dispatch requests,
testing findings) at any time, and waiting only when no row has one.

The repo-readiness audit is part of this skill: before first construction in
a repo, confirm its `.config/wt.toml` gates, named verification commands,
reset path, and OpenSpec root — record gaps in the bolt's tasks rather than
improvising around them.

## Running agents

Construction runs on herdr. A **workspace** groups one worktree's tabs and
panes, a **pane** is one terminal, and an **agent** is a named interactive
session attached to a pane. Names are the addressing scheme: the conductor
prompts an agent by name, waits on it by name, and tears it down by name.

**Every standing delegated agent runs as a herdr agent in its own
worktree.** An `Agent`-tool subagent is invisible to the operator: it
reads as a stalled pane, it cannot be prompted mid-run, and nothing it
does appears in `herdr agent list`. This bolt loop's first run dispatched
98 of them and the operator could not see any of it.

The one amendment
(`flywheel/decisions/rule-1-amended-for-workflow-sessions.md`): inside the
conductor's own loop run, sessions the loop launches are permitted — and
they are the only mutating calls it makes, each isolated in its own
worktree, with the run ID reported and every session branch merged by the
conductor so nothing is stranded. Read-only calls inside the run (the
query, the analysis) get no worktree. Visibility inside a run is
`/workflows` and the reported run ID; everywhere else, herdr, as ever.

Check `test "${HERDR_ENV:-}" = 1` before starting anything. If it fails
you cannot address standing agents; say so and stop rather than reaching
for the `Agent` tool.

An agent reports by prompting the conductor by name — `bolt-<slug>` — or by
dropping a file in the bolt change's `inbox/` when it is not running. The
conductor reads a settled agent with `herdr agent read` before deciding what
to send next.

**The invocations are in the flywheel plugin's `skills/_reference/herdr.md`, the one
shared copy.** Read it
before starting an agent, cutting a worktree, or merging. It carries the
rename-then-confirm protocol, the wait rule, the prompt-submission check, the
pathspec commit form, `wt step rebase`, the gate, kill-by-PID, and teardown —
each one written out because it was rediscovered by trial and error at least
once.

## What a bolt is allowed to write

Two write scopes, and they belong to different actors:

- **The bolt conductor** writes the bolt change's own artifacts — `bolt.md`,
  the `proposals.md` registry, its tasks — and nothing else.
- **The spec, apply and testing agents it dispatches** write the
  spec-driven change and the branch that their registry row names, in the
  built repo — and nothing else. An agent reports its outcome; it does not
  edit the registry or the bolt's tasks itself.

**Every file edit a bolt lands is carried by a `proposals.md` row, except
the three named below.** A conductor that notices a small correctable
problem in a file no row covers grows the registry with a row that covers
the work, or routes the idea to dispatch. Not editing the file because the
fix is small.

**Three edits the bolt conductor makes directly** — no nested construction
worktree, no tracked proposal:

- **`CLAUDE.md`** in a repo the bolt is already building.
- **An architecture decision record.** The bolt is where the material for
  one exists, so the bolt conductor writes it: into the built repo's
  log4brains layout, in the ordinary destination voice, naming the decision
  and what follows from it. This is why the intent side routes ADRs nowhere
  — an intent has the decision but not the construction detail the record
  is about.
- **The loop's own machinery**, where the change is small and self-evident:
  a stale name, a broken pointer, a rule that contradicts a settled record.

Everything else stays inside the tracked path. The test is whether a
reviewer would have anything to review: if the right content is a judgement
call, it is a proposal.

**The tracked path holds when the built repo is blueprints itself.** A bolt
whose subject is the machinery blueprints carries — skills, agent profiles,
schema instructions, plugins — runs exactly as any other bolt: a
`bolt/<slug>` branch and worktree in blueprints, a registry row per
proposal, the same states, the same gates. Blueprints being the repo the
conductor happens to run in changes nothing.

**The chore route is closed inside a bolt.** Running `opsx` directly with
no tracking belongs to dispatch at the moment of triage; once a bolt owns
the work the route is shut. Work in scope grows the registry with a row and
tasks; work out of scope goes back to dispatch. Neither is applied directly
because it is small — the three direct edits above are the whole exception,
and they are named rather than sized.

## Shared rules

- **Edit only what you own.** The bolt conductor edits its bolt change and
  nothing else; spec/apply agents edit their own spec-driven change and
  branch and nothing else. To affect another change, prompt its conductor
  or write to its `inbox/`.
- **Draining re-enters the artifact sequence.** Drain the inbox at every
  turn start — and a request is not an append: revise the *earliest*
  artifact it touches (new scope → `bolt.md`, then the `proposals.md`
  registry, then tasks), re-walking forward (`/opsx:continue`) so the
  sequence stays coherent. Delete the drained file in the same commit as
  the revision.
- The schema's artifact instructions are the authoring contract
  (`openspec instructions <artifact> --change <id>`); the opsx skills
  pick up the right artifacts automatically from the change's
  `.openspec.yaml` schema binding.
- **Commit by pathspec, after any artifact change.** Stage and commit only
  the paths you wrote — never `-a`, never `add -A`, never a pathspec-less
  `git commit`. Never hand-maintain a status page.
- **Spec agents sharing a bolt worktree do not commit.** Several spec
  agents work one bolt worktree, and agents in one worktree share one git
  index, so a pathspec-less commit takes whatever a sibling has staged. The
  conductor lands each finished spec itself, staging by explicit pathspec,
  while the other agents are still writing.
- **Read files with `Read`, search with `Grep`.** Bash is for commands
  that change state — git, openspec, herdr, wt, the gates — and for reading
  the gates' own output. `Read` truncates, paginates and gives line numbers;
  `cat` and `sed` do none of it. This loop's first bolt made 412
  `cat`/`sed`/`for … cat` calls for ~276k tokens against 73 `Read` calls and
  no `Grep` at all.
- **Catch up on your base branch rather than drifting from it.**
  `wt step rebase` is the primitive — a construction worktree onto its bolt
  branch, a bolt branch onto main. `wt merge` runs it anyway, so a branch
  that rebases as it goes meets no surprises at merge time.
- Plain language. The closed vocabulary is in `openspec/config.yaml`,
  which every `openspec instructions` call carries.

## What a task line is, and how long a report is

**`tasks.md` holds orchestration steps and nothing else.** Every line is a
step in dispatching, tracking or landing a subagent's work: what gets
spawned, what it is charged with, what state it moved to, what blocks it. It
is not a scratchpad, and you do not need one — your reasoning belongs in the
report you send and in the decision records the intent holds. Where a ruling
has to survive, it goes to the intent as a finding, not into the task file as
a paragraph.

Both skills mandate re-reading the change at every turn start, so every
paragraph written into `tasks.md` is re-read for the rest of the run. One
bolt's reached 1,464 lines for 149 tasks — ten lines per task.

**A report states three things and stops:** what was found, the evidence for
it, and what it asks the reader to decide or do. Length is the problem, not
content. Inbound reports here ran to 36,839 characters, and every one stays
in the receiving conductor's context for the rest of its run. Where the
reasoning behind a finding matters, it belongs in the decision record the
finding produces, which is where a later reader will look for it.

## The review threshold that earns automated delivery

**Depth is the schema member's, chosen once at the bolt's creation and
never argued per proposal** (`the-bolt-schema-family.md`): what reviews
the loop schedules is stated in the member's `apply.instruction`, and
nothing in this skill re-decides it. What this section holds is the
threshold those scheduled reads defend, and the latitude a conductor has
beyond them.

**Adversarial agent review plus automated testing are how construction
earns automated delivery.** The inner loop minimizes human review
deliberately, and that threshold is what makes it safe.

**Human code review is a request an agent may make, not a stage the
pipeline runs.** The default review mode on a row is `agent`. The `human`
mode exists because an agent asked for it, with its reason recorded on the
row or its task line — it is not a mode the conductor picks between by
taste, and there is no point in the flow at which the pipeline waits for a
human to read code.

Automated delivery rests on that threshold holding. Anything that would
weaken it
— dropping the independent reviewer, letting the reviewer edit what it
reviews, landing without the repo's named suites, skipping batched
acceptance because a proposal looks trivial — re-opens a settled decision.
Route it to dispatch as a design finding; it is not a local call the bolt
conductor makes.

### Extra reads are a judgement, not a rule

The member's loop schedules the reviews the bolt runs. **Beyond that
schedule, a conductor MAY add a read where a plausible-but-wrong success
claim would be expensive and no mechanical check would catch it**, and
MAY run more than one round where the risk warrants. Reads may span
proposals rather than being one per row.

Neither "always" nor "once" is that judgement. What decides is the cost
of being confidently wrong, weighed against what a mechanical check and
the member's scheduled reads already cover.

**The churn signal ends a run of rounds.** When re-reviews begin bouncing
on defects the fixes introduced rather than on anything the first round
missed, the review loop is churning and every further round buys wording
rather than correctness. Take the binary call there — **approved**, or
**re-spec from its decision record** — rather than after another bounce. A
re-spec starts from the decision, never from the bounced spec plus its
fixes, and is not itself reviewed.

**Verification does not relax.** What is judged is *spec review* — an agent
reading a proposal against its sources — not the checks that run against
the tree that lands. The merge gate, the bolt's merge criteria and the
acceptance evidence all still bind, and the automated half of the threshold
above is untouched.

**Findings that would have opened another round go to the end-to-end run's
report instead** while a run is pending. That is a redirection, not a
suppression: the finding still lands somewhere it will be read, and it
lands where evidence about it will exist. The run is the arbiter — an
artifact that is imperfect but runnable teaches more in one pass than a
further round of reading teaches in three.

A declared review that is not run is recorded on the row as **not run**,
never left standing as if it had been.

(`flywheel/decisions/the-run-replaces-the-review.md`,
`flywheel/decisions/bolt-conductor-latitude.md`)

### The reads are instruments, not steps

A bolt conductor is accountable for one thing: that the batch it is about
to build is **buildable and internally coherent**. How it satisfies that is
its judgment. **Nothing here prescribes a sequence, and no read must always
run.**

**Reads are across the batch, not per proposal.** The unit of reading is
the set of proposals a bolt is carrying, because the defects that actually
occur are relational — a rule compressed in one record and carried into
several proposals, a naming collision spanning two, a proposal requiring a
form of a rule its sibling correctly does not state, a positive
specification living in a shared source that four proposals cite and none
restates. A reader holding one proposal cannot see any of those.

Three kinds are worth naming, each for what it catches:

| instrument | the question it asks | what it is good at |
|---|---|---|
| **fidelity** | does this match the sources it cites? | what review mode `agent` already declares |
| **buildability** | could an agent holding only this and the repo produce the right file? | where a builder would stall, guess, go hunting, or do the wrong thing confidently |
| **coherence** | do these proposals agree with each other and with the decisions they cite? | the relational defects, visible only across the batch |

Naming three kinds and requiring all three produces a liturgy, and a
liturgy is performed rather than judged. Choosing among them is the
conductor's call against its accountability for the batch.

Where to spend a read, as a heuristic and never as a rule about when one
must run: proposals that write **new files from scratch** carry
buildability risk disproportionately, having no existing text to anchor
against. Review pressure hardens the *negative* checks — what must not
appear — because negatives are what a reviewer is good at. The *positive*
specification is the part nobody is adversarial about, so it stays wherever
it was first written and never migrates into the file a builder holds.
**The more rounds a proposal survives, the worse this skews:** rounds do
not converge on buildability, they converge away from it.

A read is not a review round. One pass, no verdict, no bounce — it patches
a spec or it finds nothing. The bound above is on rounds, and a conductor
reaching for an instrument once is not a round. A row whose tasks cannot
produce the right file is not approved, whatever a reader concluded about
its claims; unapproving and re-speccing such a row is the re-spec branch of
the bound, not a reopening of it.

The `review` column on a `proposals.md` row keeps its narrow meaning: a
declaration that a particular row wants the operator's eyes. It is never a
statement that a mandatory read type has been performed.

(`flywheel/decisions/the-conductor-chooses-the-read.md`)

## State claims — what a spec may assert about its neighbours

Spec agents write these claims, so this rule is theirs first; the conductor
enforces it when it lands a spec. It is copied verbatim from the record of
the bolt that found it (`bolt-flywheel-machinery`, formulated by one of its
spec agents), and it reads the same in `flywheel:inception`.

**The defect:** a claim about a neighbouring artifact's STATE that the
neighbour no longer bears out. Roughly eight instances across this bolt's
seven proposals — a sibling said to carry a sentence it does not carry, a
decision said to leave open a question it had closed, an archived bolt said
to still own a file, chapters called mid-rewrite that had landed, a profile
count of four from a record that now says five, a landing SHA read off the
top of `git log`, a merge criterion inherited from a handoff phrasing that
was false on disk. None was careless; every one was true when written. A
bolt has several proposals, two repos, and a live intent all moving at
once, so any statement about something you do not own has a shelf life
measured in rounds.

**The rule, in three parts:**
1. Prefer a CONTENT claim to a STATE claim. Content is checkable
   against the thing itself and fails loudly; state decays silently.
2. Where a state claim is unavoidable, name the MECHANISM rather than
   its current output. "The split bolt derives its re-edit list by
   query" survives; "this section is on that list" did not.
3. Carry a build-time task enumerating every neighbour the artifact
   asserts something about — decision records, sibling proposals, the
   registry, the archive — instructing the builder to re-read each
   from disk. Build time because that is when the neighbours have had
   longest to move.

Ending the task with its own warrant is what makes it work: *do not
trust this file; every round of review here has found at least one
such claim gone stale between writing and reading, so assume this one
has too.*

**Corollary: a decision record is authoritative on its decision and
provisional on its measurements.** A record saying "the split lands
after the runs" is settled and must not be re-derived. A record
saying "two of three gates fail" is a measurement that may have been
inherited rather than taken, and a reader should re-run it. Where
both kinds of statement sit in one record, the measurement is the one
to distrust. Written after the intent conductor raised the severity
of its own record on a bolt's report without running the three
commands — the state-claim rule's first test after it was written,
failed by the actor who wrote it down.

**Corollary: a measurement is a claim about a TREE, and naming the
tree is part of naming the measurement.** Two conductors reported the
same five files as mandating a deleted chapter and as clean, and both
were right — one had measured `main`, the other a bolt branch where the
row had already fixed them. Neither was stale. Both quoted a count as
though there were only one tree to count on. A bolt branch, its build
branches, and main diverge for the whole life of a bolt, so an unlocated
count is not a weak claim, it is an ambiguous one: it cannot be checked,
because the checker does not know where to stand. Give every count its
ref.

**Corollary: a line-number citation is a state claim.** One spec
agent applied the rule unprompted to work nobody had asked it to
re-examine and stripped every line number from its change, on the
grounds that a line number asserts the current state of a file a
sibling is about to edit. Cite by anchor, heading, or quoted phrase.

**Why the rule matters most where the two loops meet:** they
run at different speeds. A decision settles in one conductor turn; a
proposal citing it takes a review round to catch up, and in that
window the proposal asserts something false about a record that has
just been made true. The intent loop's amendments are therefore a
steady source of staleness in the bolt loop — not a fault in either,
a consequence of their clock rates — and content-and-mechanism claims
are what survive the crossing. This is the whole reason the rule
belongs in `flywheel:inception` as well as `flywheel:construction`:
the fast loop writes the claims the slow loop has to keep true.

## Routing does not transfer the obligation

Stated in full in `flywheel:inception`, under this heading. It is one rule
with two halves and it reads the same from both loops, so it is written once
rather than twice slightly differently — read it there.

The half that bites here: a design-level finding routed to dispatch stays on
this bolt's registry until you observe dispatch carrying it. A row reading
"routed, not allocated" is a live obligation, not a disposal. Three findings
sat in no proposal at all because a bolt and an intent each believed the other
held them.

## State a constraint at its measured strength

Never at its remembered or feared strength — this binds every charge you write
to a build agent. If the strength is unknown, say that instead of rounding up.

**The defect:** this loop's first bolt told every apply agent "two of the three
gates cannot run" when one cannot; `map-check.mjs` imports only node builtins
and was never affected.

**Why it is not a rounding error:** an agent told to expect a failure that
cannot happen meets a passing gate and learns *the gate is broken, my edit is
fine*. Overstating a constraint teaches agents to discount constraints. A
charge that overstates is a work order the next agent is right to discount.

## A mechanism is not a justification

Where a proposal names a mechanism that constrains order, coupling or
membership, it states the fact that makes the constraint **correct** — not the
mechanism that makes it **stick**. This binds proposals and their verification.

**The defect:** a retirement pair had to run in a set order, and what was
written down was "the sibling's task 1.1 halts if `skills/book-decompose/` is
still present, so the sequence is enforced rather than merely intended". The
actual reason — every `book-decompose` reference sits inside the machinery the
sibling deletes wholesale — was verified by a reviewer and appears nowhere.

**Why it matters:** an enforced order whose reason is unrecorded is one
refactor from being reversed by someone who sees only the halt and reads it as
ceremony. The guard outlives the argument, and then the guard looks arbitrary.
Sibling of the state-claim rule: content survives, enforcement decays.

## Topology

The conductor cuts **one bolt branch + worktree per involved built repo**
(`bolt/<slug>`, via `herdr worktree create --cwd <repo-root>`), alive for
the bolt's lifetime. Construction runs on **nested worktrees off the bolt
branch** — one per proposal being built — concurrent when proposals are
independent, serial when they share contracts. Choose and record:

- **Branch topology** — nested construction worktrees per proposal by
  default; building directly on the bolt branch is legal only for a bolt
  with a single small proposal. That is a branch-topology choice *inside* a
  bolt, never a way to skip having one: nothing releases into a bare work
  branch off main.
- **Working arrangement** per proposal — solo / reviewed / paired.
  Criterion: the cost of a plausible-but-wrong success claim vs review
  round-trip latency. Record the choice and reason on the Build task.
- **Batch size** — acceptance after 2–3 merge-backs by default; a batch of
  one for high-risk changes. Criterion: blast radius of a red run across
  unmerged siblings.

### The one-proposal bolt

A handoff carrying a single proposal is a **named special case of the one
path out of the gate, not a different path**: the same artifacts
(`bolt.md`, a `proposals.md` registry of exactly one row, tasks) and the
same actors (a bolt conductor, a spec agent, an apply agent, a reviewer, a
testing agent) at the smallest size.

It earns its keep below the size at which its tracking would, for three
reasons worth naming because they are what the shortcut would cost:
writing the proposal and building the code stay two agents; an independent
review and the archive stay available; and feedback that has to travel back
to dispatch has an owner to catch it and a place to land. So a one-row bolt
keeps spec and build as two agents even when one agent could plausibly do
both.

## The proposal flow — `proposals.md` states drive everything

`to-spec → specced → in-review → approved → building → built → verified →
merged`; a bounced review returns to `to-spec` with gaps noted in tasks.

1. **Spec.** Delegate an agent per proposal (`opsx ff` in the built repo,
   on the bolt-branch worktree) citing the design sources the handoff
   named — chapters, decision records. `openspec validate` green →
   `specced`. The agent reports; the conductor commits its artifacts by
   pathspec. Every spec carries the build-time re-read task the state-claim
   rule requires, and cites by anchor or quoted phrase rather than by line
   number.
2. **Review**, `agent` by default:
   - `agent` — an independent reviewer reads the full artifact set *and
     the cited sources*; hunts plumbing-only specs, cross-proposal drift,
     unaccounted source material, ungrounded assumptions (verify unfamiliar
     APIs against current docs, never training memory). Verdict on the
     task line.
   - `human` — only from an agent's request with its reason recorded:
     `plannotator annotate` the proposal for the operator, whose
     approve/deny feedback is the verdict. An agent asks for one when it
     cannot resolve whether its approach matches the cited design source.
   The reviewer never edits artifacts; a bounce re-dispatches a spec agent
   and returns the row to `to-spec`. How many rounds a row gets is the
   judgement above, not a number. Whether a fidelity, buildability or
   coherence read runs over the batch alongside this step is the
   conductor's call, and none of the three is a stage.
3. **Build.** Apply agents on nested worktrees work the proposal's own
   tasks. Pipeline stages are invariant: **commit stage** on every push
   (the repo's named checks via its wt pre-commit hook; `moon ci` where
   adopted); **merge gate** on the rebased tree at merge-back into the
   bolt branch (`wt merge <bolt-branch> --no-remove -C <worktree>`).
   Acceptance suites never run inside a construction worktree — an agent
   that wants broader proof escalates to the conductor.
4. **Test.** Batched acceptance on the bolt branch by a one-shot testing
   agent: full reset, the affected scenarios reseeded, the repo's named
   suites. Findings are reports, never fixes: construction-level findings
   append bolt tasks; **design-level findings route to dispatch** (the
   design is wrong, not the build) and are noted in the bolt.
5. **Merge.** When the bolt's merge criteria hold (its own bolt.md is the
   authority), land each repo's bolt branch on that repo's main through
   the **full release gate** (`wt merge`, full hooks, never weakened, one
   writer to main at a time). Record SHAs; archive the built repos'
   spec-driven changes; report each landed handoff back to its intent
   conductor (prompt or inbox) so the intent's task is checked off.

**The operator's release covers everything the bolt builds.** The approval
that released the bolt is the approval for every batch of agents inside it,
so launching the next batch of spec or apply agents needs no new approval and
the conductor asks for none. Work that `bolt.md` does not cover is not part
of the bolt at all — it is out-of-scope work routed to dispatch, and the
approval that released the bolt did not cover it.

## The long-lived posture

**Drive the registry.** Every row whose state has an unblocked next action
is dispatched without waiting for the operator to raise the subject: rows
at `to-spec` get spec agents, rows at `approved` get apply agents, a batch
at `built` gets the acceptance run. A conductor that has unblocked work and
is waiting is malfunctioning.

**Park only when nothing is unblocked.** When every row is waiting on an
agent that is running: park on them (bare `herdr agent wait`), drain the
inbox, keep the change committed. The operator's two moments in a bolt's
life are the approval that created it and the closure it agrees to;
nothing between them is a standing human stage.

New work pushed into a live bolt joins the registry as new `to-spec` rows
and new tasks — the bolt grows; it never spawns a sibling for scope that
belongs to it, and never absorbs scope that does not. When the registry is
fully `merged`, propose closure to the operator: tear down every
construction worktree, the bolt branches, and allocated resources; `openspec archive <bolt-id>` moves the whole record — registry,
tasks, drained decisions — to the archive as one unit.
