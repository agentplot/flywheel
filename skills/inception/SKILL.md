---
name: inception
description: Run the flywheel design loop — dispatch raw ideas into OpenSpec intent changes, run design sessions that close decisions and write the books and the context map, request bolts at handoff. Use when the operator files or discusses a new idea or intent, asks where an idea should go, asks to work an intent's design tasks, or asks "what's in design".
---

# Flywheel inception — the design loop

One intent = one OpenSpec change on blueprints **main**, bound to the
`flywheel-intent` schema (shipped in this plugin's `schemas/`). Its
`tasks.md` is the list of open items; the design loop's whole job is
closing open questions into decisions, writing the destination into the
books and map, and handing settled slices to construction. **Inception
requests; construction is a bolt** (`flywheel:construction`, the
`bolt-{default,quick,deep}` schema family — the member is the review
depth) — releasing work into a bolt is the operator's
approval to give.

Three roles load this skill: **dispatch**, the **intent conductor**, and
**design sessions** under either session profile
(`flywheel-design-session`, `flywheel-interactive-session`).

## Running agents

The loop runs on herdr. A **workspace** groups one worktree's tabs and panes,
a **pane** is one terminal, and an **agent** is a named interactive session
attached to a pane. Names are the addressing scheme: a conductor prompts an
agent by name, waits on it by name, and tears it down by name.

**Standing delegated work runs as a herdr agent in its own worktree.** An
`Agent`-tool subagent is invisible to the operator: it reads as a stalled
pane, it cannot be prompted mid-run, and nothing it does appears in
`herdr agent list`. One bolt ran 98 of them and the operator could not see
any of it.

The one amendment
(`flywheel/decisions/rule-1-amended-for-workflow-sessions.md`): inside the
conductor's own loop run, sessions the loop launches are permitted — and
they are the only mutating calls it makes, each isolated in its own
worktree, with the run ID reported and every session branch merged by the
conductor so nothing is stranded. Read-only calls inside the run get no
worktree. Visibility inside a run is `/workflows` and the reported run ID;
everywhere else, herdr, as ever.

Check `test "${HERDR_ENV:-}" = 1` before starting anything. If it fails you
cannot address standing agents; say so and stop rather than reaching for
the `Agent` tool.

A conductor addresses a running agent with `herdr agent prompt <name>`, parks
on one with a bare `herdr agent wait <name>`, and reads a settled one with
`herdr agent read`. A session reports back by prompting its conductor by name
— `intent-<slug>` — or by dropping a file in the change's `inbox/` when the
conductor is not running.

**The invocations are in the flywheel plugin's `skills/_reference/herdr.md`, the one
shared copy.** Read it
before starting an agent, cutting a worktree, or merging. It carries the
rename-then-confirm protocol, the wait rule, the prompt-submission check, the
pathspec commit form, `wt step rebase`, the gate, and teardown — each one
written out because it was rediscovered by trial and error at least once.

## What each actor writes, and what everything else is

Two write scopes, not one, and they are different:

- **The intent conductor** writes its change's own canonical artifacts
  under `openspec/changes/<id>/` — `intent.md`, `decisions/`, `tasks.md`,
  `design.md` — and the books and the context map.
- **A design session** writes, inside its own worktree: its assigned
  session directory under that change — `sessions/<date>-<slug>/` — its
  own task lines, the decision records for questions its work order
  charged it to close (with the `State:` flips on those question
  records), and the books and the context map.
- **Both** write the books and the context map, and nothing else is shared
  between them.

The conductor is the sole writer **on main**: its merge is what admits a
session's writes. The session closes what it was charged with — its task
lines, its charged closures — because it knows them firsthand; the
conductor opens what the session discovered — new tasks, new questions,
re-sequencing — because a session sees its batch and never the frontier.
The conductor does not write inside a session's directory either; it
promotes what the session delivers rather than editing in place.

**Every other file edit in any repo is construction, and leaves on the
operator's approval as a handoff — including edits to blueprints itself.** When an
intent's subject is the machinery blueprints carries — its skills, agent
profiles, schema instructions, `CLAUDE.md` conventions, plugins —
blueprints is that intent's built repo in the ordinary sense, and being the
repo the conductor happens to run in changes nothing.

**A Writeback task is a book chapter or the context map and nothing else.**
A task filed as Writeback whose target is neither — a research document,
the kit-reorg roadmap, a `.claude/` file, `books/CLAUDE.md`, a schema
instruction — is a **misfiled Handoff**. The Writeback label is a
description, not an authorization: re-sort the task to Handoff naming its
built repo and its proposal, and spawn no session for it. Research
documents and the roadmap are files in a built repo like any other.

**A design session is single-purpose within the intent**: it closes open
questions into decisions, writes the destination into the books and map, and reports what
to check off. It never sends agents off to build. Work that needs agents
building is a proposal in a bolt, and a small one is a one-proposal bolt,
never an untracked edit.

**The chore route is closed to a conductor and its sessions.** Running
`opsx` directly in a built repo with no tracking at all belongs to
**dispatch, at the moment of triage, before any intent exists** (below).
The route closes once an intent owns the work: a task already sitting on an
intent's `tasks.md` is never drained as a chore, however small it is.

**A release has one path out of it.** A released handoff becomes a
bolt with a bolt conductor whatever its size, and a handoff carrying a
single proposal is a **one-proposal bolt** — a named special case of that
path, not a different one. Nothing releases into a bare work branch off
main.

Why these are stated as rules rather than left to the task types: the
schema already defined Writeback correctly and six machinery tasks were
filed under it anyway, by a conductor that had read this skill and then
proposed a design session to rewrite two skills and a "pure chore" to
rename an agent profile. A definition that is only correct is not a
guardrail.

## Shared rules (every role)

- **Edit only what you own.** Beyond the write scopes above: you may edit
  the change you were charged with — nothing else. A design session owns
  only its session directory. To affect any other change, prompt its
  conductor or write to its `inbox/`.
- **Messaging.** To reach a change's conductor: `herdr agent list` for the
  conventional name (`intent-<slug>` / `bolt-<slug>`); running →
  `herdr agent prompt` it; absent → drop a request file in the change's
  `inbox/` (`inbox/<date>-<from>-<slug>.md`).
- **Draining re-enters the artifact sequence.** At every turn start the
  conductor re-reads its change and drains its inbox — and a request is
  not an append: revise the *earliest* artifact it touches (new scope →
  `intent.md` first), then re-walk forward (`/opsx:continue`) so the
  downstream artifacts stay coherent. Delete the drained file in the same
  commit as the revision.
- The schema's artifact instructions are the authoring contract
  (`openspec instructions <artifact> --change <id>`); the opsx skills
  pick up the right artifacts automatically from the change's
  `.openspec.yaml` schema binding.
- **Commit by pathspec.** Commit via the `git-commit` skill after any
  artifact change, and stage and commit only the paths you wrote — never
  `-a`, never `add -A`, never a pathspec-less `git commit`. Never
  hand-maintain a status page.
- **A conductor on main works in a worktree of its own.** An intent or bolt
  conductor editing directly in the blueprints main checkout shares one git
  index with every sibling running there, and that collision is not
  theoretical — one session's chapter deletions landed inside another's
  commit. Cut your own worktree for your edits and merge it back when you
  dispatch a session. Keep it cheap: no test run, no server, no acceptance
  suite. It exists to own an index, nothing more.
- **Review channels — choose the type, then read its skill.** The criterion
  is what the operator does with the material: reads a document that
  already exists → a plannotator round (`flywheel:planning`); works a set of
  coupled choices → a lavish page (`flywheel:interactive`);
  settles a fact a throwaway can prove faster than an argument can settle →
  `flywheel:prototype`; answers a factual question by reading rather than
  building → `flywheel:research`; carries a settled destination into the books
  and the map → `flywheel:writeback`. The conductor picks the type at
  work-order time and names its skill in the work order; the practice for running
  each type lives in that skill.
- Checking off a task that closed a decision requires the
  `decisions/<slug>.md` record to exist. A new open question appends a task;
  unchecked tasks may be reworded, checked ones never reopen.
- Writebacks obey `books/CLAUDE.md` (destination voice, mermaid rules) and
  end with `node context-map/bin/map-check.mjs --write` green when the map
  moved.
- **Read files with `Read`, search with `Grep`.** Bash is for commands
  that change state — git, openspec, herdr, wt, the gates — and for reading
  the gates' own output. `Read` truncates, paginates and gives line numbers;
  `cat` and `sed` do none of it. One bolt made 412 `cat`/`sed`/`for … cat`
  calls for ~276k tokens against 73 `Read` calls and no `Grep` at all.
- **Catch up on your base branch rather than drifting from it.**
  `wt step rebase` is the primitive, and it is what `wt merge` runs anyway,
  so a session branch that rebases as it goes meets no surprises when its
  conductor folds it.
- Plain language everywhere. The closed vocabulary is in
  `openspec/config.yaml`, which every `openspec instructions` call carries.

## What a task line is, and how long a report is

**A task line is a checkbox, a blocker and a pointer.** It records what has
to happen, what stops it, and where the output went — not the reasoning that
produced it. Reasoning belongs in the decision record, which is where a later
reader will look for it, and in the session report that produced it.

The rule exists because nothing said what a task line was for, so conductors
used `tasks.md` to record their own thinking about orchestration. This
intent's own file grew from 302 to 643 lines while its checked count moved by
one. Every actor here re-reads the change at every turn start, so a paragraph
written into `tasks.md` is re-read for the rest of the run.

**A report states three things and stops:** what was found, the evidence for
it, and what it asks the reader to decide or do. Length is the problem, not
content — reports here ran to 36,839 characters, and every inbound one stays
in the receiving conductor's context for the rest of its run.

## State claims — what a record or a task line may assert

Decision records and task lines are full of these claims, so this rule
binds every actor here. It is copied verbatim from the record of the bolt
that found it (`bolt-flywheel-machinery`, formulated by one of its spec
agents), and it reads the same in `flywheel:construction`.

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

## One answer per record

Sibling of the state-claim rule above, and a different defect. That one is a
claim about a neighbour that went stale. This one is a contradiction *inside
one file*, where a correct addition never reached backwards into text already
written, so the record states two answers and gives a reader no way to tell
which is meant.

Four instances, found by audit rather than by reading: a record opened with a
list of four agent profiles, two of them names retired since, while its own
Consequences said five; another said all three gates run green two bullets
above the measurement showing one exits 2; a third named the same skill twice,
differently; a fourth still counted four task types after one retired.

**Why it is worse than it looks:** an enumeration is the thing a spec agent
copies. One stale profile list was live in a bolt, and a skill directory that
should never have existed was created on a build branch before anyone noticed.
A record is authoritative on its decision **only if it says one thing**.

**The rule:** when a decision moves, rewrite every statement of it in that
record, not only the section being amended — and state each enumeration ONCE,
in one place, marked as the one to copy. Where a record must keep a superseded
reading, it says so in the sentence that holds it, the way this intent's
records already do with measurements ("this record first said two, on a report
it did not measure").

## Routing does not transfer the obligation

The whole rule, stated here once. `flywheel:construction` points at this
statement rather than restating it.

**The defect:** a finding routed between the loops lands in neither. Three
instances, all live at the time: the ADR retirement, the state-claim rule, and
the `books/CLAUDE.md` link rule each sat in no proposal, because a bolt's
registry read "routed to intent, not allocated" while the intent had already
allocated it back. Both sides were honest and both were stale, so the item was
invisible from either end — and the link rule silently blocked a built
proposal from reaching verified.

- **Sending.** The router keeps the item on its own list until it observes the
  receiver carrying it. Sending closes nothing.
- **Receiving.** A routed finding is not closed when it is routed. The
  receiver's registry names the item and what it waits on, and a row reading
  "routed, not allocated" is a live obligation, not a disposal.

Same discipline as never queueing a second prompt before the first one's
effect is observed, applied to work rather than to turns.

## State a constraint at its measured strength

Never at its remembered or feared strength. If the strength is unknown, say
that instead of rounding up.

**The defect:** a bolt told every apply agent "two of the three gates cannot
run" when one cannot — `map-check.mjs` imports only node builtins and was
never affected.

**Why it is not a rounding error:** an agent told to expect a failure that
cannot happen meets a passing gate and learns *the gate is broken, my edit is
fine*. Overstating a constraint teaches agents to discount constraints — the
same mechanism by which a superseded list in settled voice teaches them to
trust the list. Both train a reader to weigh the artifact against what they
observe, and the artifact loses. A work order that overstates is a work order the next
agent is right to discount.

## Which channel carries which question

What the answer looks like decides the channel; the loop decides the default.

| the answer is | channel | blocking? |
|---|---|---|
| a sentence, needing nothing read first | Discord — `AskUserQuestion` stands in until that bridge is live | **no** — keep working on whatever the answer does not gate |
| margin notes on a document that already exists | `plannotator annotate <file>` | **yes** — you stand at the round until the operator has been through it |
| a choice across coupled decisions, or anything that needs options side by side | a lavish page | **yes** |

**The outer loop defaults to the desk channels** — plannotator and lavish.
Dispatch triage is the exception that is Discord-first, and becomes more so
as new channel sources arrive.

**Escalation runs one way.** Take the cheapest channel that can carry the
answer; when it cannot carry it, say so on that channel, open the desk
channel, and leave the pointer to it behind. A question that has reached a
desk channel is never demoted back to Discord, and the same question is
never re-asked on the cheaper channel. A question you would have to stop
and wait on was never a Discord question in the first place.

## Review rounds — who opens one, and where the answers go

**The sole writer of the file under review opens the round.** Dispatch
annotates the intent it just wrote; a conductor annotates its canonical
artifacts; a design session annotates the decision drafts in its own
directory; a bolt conductor annotates a generated proposal. A conductor
that wants a session's drafts reviewed does not open the round itself —
the session wrote them and is their sole writer, so the session runs it and
the conductor receives the outcome as a session report.

**Feedback returns to the invoker and nowhere else.** `plannotator
annotate` hands its result to the session that ran it. Annotations are
never relayed raw to another actor and never written into another actor's
directory. Annotations that concern a different change or another actor's
artifacts travel through your report and the messaging protocol above — the
conductor's prompt, or the change's `inbox/`.

**The conductor triages what comes back into exactly one of three, and
there is no fourth:**

1. **A correction** — applied to the *earliest* artifact the annotation
   touches, before re-walking the artifact sequence forward
   (`/opsx:continue`) so the downstream artifacts stay coherent. An
   annotation that widens what the intent covers revises `intent.md`
   first; it is not appended to `tasks.md` with the earlier artifacts left
   stale.
2. **A decision the annotation closed on its own** — written as
   `decisions/<slug>.md` *before* the task that closed it is checked,
   because a checked decision task without its record is not a closed
   decision.
3. **Work that needs design** — appended as a Design task, and then a
   session with its own directory and batch. The conductor neither answers
   the question itself nor leaves the annotation parked in the round.

A review round is therefore a launch point for design sessions by the same
route the board is: the round produces the task, and the conductor spawns
the session.

## Dispatch — raw idea → the right place, and the relay in both directions

The standing singleton on blueprints main, under
`agents/flywheel-dispatch.md`. Its job has two halves.

### Routing a raw idea

Input: a sentence, bullets, or a document from the operator (or a
design-level finding routed back from a bolt). Three routes — suggest one,
and say which you chose and why:

1. **New intent.** Dedupe first (`openspec list` for open intents; grep
   `context-map/maps/target.js` for the concepts). Creating the change is
   dispatch's one write — it exists before any conductor does:
   `.openspec.yaml` (`schema: flywheel-intent`, `skip_specs: true`),
   `intent.md` per the schema instruction, seeded `tasks.md`. Supporting
   repos off the map cite their governing doc in the Map section. The
   intent then waits until the operator says to work it — and starting the
   conductor on that word is dispatch's job (below).
2. **Amendment to a running bolt.** The idea is construction-scoped work
   already covered by an active bolt: request it (herdr prompt or the
   bolt's `inbox/`). Never edit the bolt change.
3. **Chore.** Small, fully defined, no design content: run `opsx` directly
   in the built repo and create no tracking at all. **This route is open
   here and only here — at triage, before an intent exists.** It closes the
   moment an intent owns the work, so it is never how a task on an intent's
   `tasks.md` gets drained. If even this feels heavy, say so — some ideas
   are just a shell command.

Starting an intent conductor is dispatch's, on the operator's word:
`herdr agent start intent-<slug> --kind claude --pane <pane> -- --agent flywheel-intent-conductor`,
then (after the rename-then-confirm protocol) `/opsx:continue <slug>`.

### The relay, in both directions

Dispatch is the one bridged actor, so inner-loop escalations travel through
it: a question a bolt conductor cannot answer comes **out** to the operator
through dispatch, and the operator's answer goes **back** to the bolt
conductor that raised it — never to a different actor, and never as an edit
to that conductor's change. A bolt conductor does not open a channel of its
own to the operator. Triage is the sorting half and the cheap half; the
routing in both directions is the work, which is what the actor is named
for.

## Intent conductor — one per intent, blueprints main

How one comes to exist: on the operator's word, dispatch starts it under
its agent profile —
`herdr agent start intent-<slug> --kind claude --pane <pane> -- --agent flywheel-intent-conductor`
— and (after the rename-then-confirm protocol) prompts `/opsx:continue <slug>`
(or `/opsx:ff <slug>` for a change with artifacts still to create). The
profile carries the role identity; the change's schema binding gives opsx
the flywheel-intent artifacts automatically; this skill is the practice.
The conductor is the sole writer of the change's canonical artifacts from
then on.

**Drive the open items.** An approval authorizes a release; it does not
schedule your work. Per task type:

- **Design** — an unblocked Design task spawns a design session.
- **Writeback** — an unblocked Writeback task spawns a writeback session
  **without asking anyone**. Writeback is the books and the map, which is
  your own scope; asking permission to rewrite a chapter or move a map
  status is asking permission to do your own job.
- **Handoff** — an unblocked Handoff task is prepared to the point of one
  decision: the proposals batched, the bolt named, the repos and merge
  criteria drafted. Then **one approval covering the whole batch at once**,
  asked for with `AskUserQuestion` — explicitly not a plannotator or lavish
  round, and never one question per proposal.

**Asking for an approval is not waiting for one.** Ask, then keep working
on everything the answer does not block. Do not hold a blocking question
form open in your own pane: an operator whose composer is occupied by your
question cannot type anything else into that pane, and one release had to be
relayed through a second session for exactly that reason.

An approval authorizes a release. It is not a meeting, a status report, or a
reason to stop. **A conductor that has unblocked work and is waiting for
the operator to raise the subject is malfunctioning** — reporting a list of
unblocked tasks and then waiting is the exact failure this rule exists to
stop, and it was committed by a conductor that had read this skill.

- **Spawn sessions into their own worktree.** A session runs in its own
  worktree on its own branch, cut by worktrunk:

  ```bash
  wt switch --create sess/<slug> --base main --no-cd
  herdr tab create --cwd <worktree>     # then herdr agent start in that pane
  ```

  No `--no-hooks`: this repo configures no `wt` lifecycle hooks, so the
  flag suppresses nothing today and would silently skip the cold-start hook
  the moment one exists. Start the session in that pane under its host
  profile, and name in the spawn line which profile you are starting:

  ```bash
  herdr agent start <slug>-session-<n> --kind claude --pane <pane> \
    -- --agent flywheel-design-session
  ```

  Issue each session a work order naming the change id, its task batch,
  its `sessions/<date>-<slug>/` directory, its worktree, and the
  session-type skill for the batch. Sessions may run in parallel on
  disjoint batches — beyond their own task lines they never write the
  canonical artifacts, and they no longer share a working tree or a git
  index; the conductor serializes the folding.

  **The host profile follows one two-part question and no other:** which
  loop is this, and does the session build a lavish page? Construction —
  all seven types — → `flywheel-construction-session`. Design that builds
  a lavish page → `flywheel-interactive-session`; design that builds
  none — planning, research, prototype, writeback, handoff →
  `flywheel-design-session`. Do not choose by the channel the session
  reports through, the channel its batch works, or the tool it happens to
  use; those are second bases for one decision and there is only one. The
  other five design types have no profile of their own. The six
  design-type skills a work order names from are `flywheel:planning`,
  `flywheel:interactive`, `flywheel:prototype`, `flywheel:research`,
  `flywheel:writeback` and `flywheel:handoff`.

  **The naming is a rule about a word's presence, never about word order:**
  an actor says "session", a way of working never does. A profile is
  `flywheel-<type>-session`; a skill is `flywheel-<type>`. An earlier draft
  used `flywheel-session-<type>` — the same words as the profile in the
  other order — and two independent reviewers confused the pair, the second
  reporting a correct proposal as internally inconsistent. Word order is
  not a distinction a reader can hold; the presence or absence of a word
  is.

- **Fold, then tear down.** A session delivers by reporting. Merge its
  branch through the full gate before promoting —
  `wt merge --no-remove -C <worktree>` — because books, mermaid and map are
  exactly what a documentation session should have to pass. Then promote:
  the report given a row in `design.md` (the catalog of design output,
  where it stays put), finalized decisions into `decisions/`, findings into
  `prototypes/` and a row of their own, task check-offs and appends into
  `tasks.md`. Teardown is yours: a session is not done until
  its worktree and its branch are gone.
- **Handoff is a request, never a write.** You never author a bolt change's
  decision to exist — but you do the naming and the drafting before asking,
  so the operator answers rather than designs. On the operator's release
  (their word, given directly or via a session): an
  existing bolt in scope → prompt/inbox its conductor; no bolt → create the
  bolt change (binding the `bolt-*` member the work warrants — the member
  IS the review depth — artifacts per its instructions) and
  start `bolt-<slug>` under its profile (`-- --agent
  flywheel-bolt-conductor`) — bolts auto-start because they exist only past
  that approval. Record the bolt/change id on the intent's handoff task
  line. Draft the merge criteria and the repo list against disk rather than
  against an earlier handoff's phrasing — a criterion inherited from a
  phrasing that was false on disk is the state-claim defect above, and the
  handoff is where it crosses into the bolt loop.
- **Route findings**: bolt-reported design findings append tasks (and open
  questions when warranted); never fix construction problems from here.
- **Close honestly**: all tasks checked + writebacks green → propose
  `openspec archive <id>` to the operator. Parked intents with unchecked
  tasks are raised, not silently closed.

## Design session — per batch, charged by the intent conductor

A session owns a worktree and a branch, not only a directory. It commits to
`sess/<slug>` in the worktree its conductor cut, and it is the sole writer
of the `sessions/<date>-<slug>/` directory it was assigned under the change
— lavish artifacts, decision drafts, prototype notes, all real committed
files. Every report belongs to a session; a one-shot report gets its own
small session directory rather than living loose. The session delivers by
reporting to the conductor, which merges the branch through the gate and
promotes. In its worktree it checks off its own task lines and writes the
decision records for questions its work order charged it to close; every
other canonical artifact is the conductor's alone, and the conductor's
merge is what admits the session's writes to main.

Read the session-type skill your work order names for how your type is
run.
What follows is what every session owes the operator when it puts material
in front of them.

- **Show the thing, not a description of it.** What you put in front of
  the operator carries code samples, configuration examples, diagrams, and
  conceptual SVGs that hold what is being decided — the configuration that
  would change, the sample each option produces, the diagram of it —
  beside each option, rather than paragraphs describing them. For branch and worktree
  topology reach for `branch-topology-diagram`: it is a ready tool, and
  prose is not a topology.
- **When a plan is the better channel.** If the material is a document the
  operator reads through rather than a set of choices they work, run a
  plannotator round on the plan and build no lavish page.
- **Prototype when talk stalls.** Criterion: the decision turns on a fact
  a throwaway can prove faster than an argument can settle. The practice —
  where the throwaway gets built, what the finding looks like, what dies
  afterwards — is `flywheel:prototype`.
- End of session: the session directory committed on `sess/<slug>`, the
  report delivered to the intent conductor — which outcomes landed, which
  tasks to check or append, what the next batch should work. The conductor
  merges, folds, and commits the canonical artifacts.
