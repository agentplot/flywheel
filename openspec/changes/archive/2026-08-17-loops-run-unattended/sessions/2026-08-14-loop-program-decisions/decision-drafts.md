# Decision drafts — the loop programs' six open calls

Planning round for `intent/loops-run-unattended`, items #81, #85, #87,
#88, #89, #161. Each section is one decision draft: the proposed
decision first, the alternatives after, evidence as pointers. Annotate
inline; a section left unannotated is taken as assent to its proposal.

One observation grounds several of these drafts and is worth stating
once: **`openspec/changes/loops-run-unattended/` did not exist on any
branch of this repo when this session started.** The milestone was
born at triage, no inception scaffolded a change dir, and the intent
loop has no guard that would have. This session created the directory
itself to have somewhere to write. That is live evidence in #87's
question, and a small demonstration of what "the loops run unattended"
still lacks.

---

## Draft 1 (#81) — The server filter names its sweep in the record

**Proposed decision.** Amend `design/loop-programs.md`'s Inboxes
section so the server filter reads as built: milestones with a job
include, besides the ready/in-progress/Ready-batch/awaiting-landing
tests, any open `intent/*` milestone holding **settled unbatched
assertions or orphan `state:queued` items** — the guard-only work that
today only the intent loop's own filter names. State the licensing
rule beside it: *a server filter may over-approximate; a loop filter
must be exact* — a false positive costs one process start and a clean
exit; a false negative costs work that never happens.

This blesses what is already built and tested:
`_flywheel_inbox.server_inbox(sweep=True)` (bin/_flywheel_inbox.py:339,
with the hole documented in its docstring and a containment property
test), and the shared reference `skills/_reference/tracker.md` already
carries the rule verbatim ("A server filter may over-approximate; a
loop filter must be exact"). Only `design/loop-programs.md` — the
record the code cites — still states the literal filter that loses
handoff births.

**Alternatives.**
- *Make the record literal and drop the sweep.* An intent whose last
  question just closed is a milestone with no job; its handoff is
  never born until some other write happens to wake it. This is the
  hole, not a fix.
- *Give the server the exact guard filters.* The server would
  duplicate the intent loop's guard queries (settled-unbatched,
  orphan-queued) instead of a cheap superset. More reads per pass, two
  places to keep the same logic true, for no behavioural difference —
  the loop STOPs cleanly on a false positive either way.

**Consequences.** One small amendment to `design/loop-programs.md`
(this session can write it on the operator's word here — the record's
Status line already marks it released, so the amendment is a
correction, not a re-litigation). No code change. #81 closes on the
record matching the build.

---

## Draft 2 (#85) — Shared modules stay in `bin/`, and the README stops calling it open

**Proposed decision.** The `_`-prefixed shared modules
(`_flywheel_gh.py`, `_flywheel_sessions.py`, `_flywheel_inbox.py`,
`_flywheel_bolt_loop.py`, `_flywheel_intent.py`, `_flywheel_server.py`)
stay in `bin/`, beside the commands that import them. Amend
`bin/README.md` to settle its own open question (the paragraph at
bin/README.md:32 "Whether shared modules like these belong here at all
… is an open question") into the rule: *a command must be reachable by
name; its logic lives in an importable sibling module when tests need
it or commands share it; `tools/` is for a large command's whole
implementation behind a thin entry point, not for shared libraries.*

Why here and not `tools/`: the import mechanism the commands use
(`sys.path.insert` of their own directory) only works for siblings —
moving the modules to `tools/` means every command grows a second path
computation, five commands and the test suite churn, and the user-facing
surface doesn't change by one character. The README's stated bar
("self-contained is the bar for skipping the tools/ split") was written
for *commands*; the underscore files are not commands and already read
as not-a-command by name and extension. `tools/` keeps its stated
purpose: `context-map`'s implementation lands there behind a thin
`bin/` entry.

Note: the item's second defect ("Two commands live here now" vs seven)
is already fixed — the current README enumerates the commands with no
count claim.

**Alternative.** *Move all `_*.py` to `tools/`.* Honors a strict
reading of "public commands only", at the cost of touching five
commands, the test imports, and inventing a cross-directory import
convention — for a directory whose contents already self-describe as
non-commands.

**Consequences.** One `bin/README.md` amendment (queued as an item —
nothing edits without one — or folded into an existing docs item).
#85 closes on the ruling.

---

## Draft 3 (#87) — Yes: the intent loop gets guard 0, as a program step

**Proposed decision.** The intent loop gets scaffold-if-missing, and it
needs no model: `openspec new change <slug> --schema flywheel-intent
--description …` is fully non-interactive (verified against openspec
1.8.0), so guard 0 is a plain subprocess call plus a commit — exactly
the shape the programs want. The guard is idempotent (dir exists →
no write) and runs first, like the bolt loop's.

The asymmetry the schema/record disagreement encodes ("an intent
change is scaffolded at inception") is empirically false: this
milestone — `intent/loops-run-unattended` — was born at triage as a
container for another bolt's aftermath, and no change dir existed
until this session created one. Triage creates intent milestones
without inception; the loop is the only actor guaranteed to be there.
The schema's apply instruction (schemas/flywheel-intent/schema.yaml:233)
already lists guard 0; it is `design/loop-programs.md`'s three-guard
list and `bin/flywheel-intent-loop`'s implementation that lack it.

**Alternatives.**
- *Keep the three-guard loop; make inception/triage scaffold.* Puts a
  repo write into dispatch — an actor that is deliberately "a pure
  GitHub-and-relay actor — no repo checkout, no file writes." Breaking
  that seal for a scaffold is a worse asymmetry than the one repaired.
- *Charge a one-shot session to scaffold.* A model asked to behave
  like code — the record's own words for what the programs exist to
  end. The CLI makes it unnecessary.

**Consequences.** The record's intent-loop guard list gains guard 0
(same amendment pass as Draft 1); an item queues the build (add the
guard to `_flywheel_intent.run_guards`, a subprocess seam so the test
suite fakes it, fixture coverage). #87 closes as "yes — omission, not
design."

---

## Draft 4 (#88) — `flywheel-intent` gets its stubbed `loop:` block

**Proposed decision.** Add a `loop:` block to
`schemas/flywheel-intent/schema.yaml`, parsed-but-unbuilt, exactly the
DECLARE-rung stub the bolt types carry (schemas/bolt-quick/schema.yaml:33).
Its content is the design loop's configurable surface — the
`_flywheel_intent.TYPES` table externalized:

    loop:
      types:
        planning:    {profile: design, model: fable, operator_round: true,  worktree: true}
        interactive: {profile: interactive, model: fable, operator_round: true, worktree: true}
        handoff:     {profile: design, model: opus, operator_round: true,  worktree: true}
        research:    {profile: design, model: "opus[1m]", operator_round: false, worktree: false}
        prototype:   {profile: design, model: opus, operator_round: false, worktree: true, alone: true}
        writeback:   {profile: design, model: opus, operator_round: false, worktree: true}
      hooks: []

Rationale: the record's ladder (DECLARE / SCRIPT / FORK) says the
end-user channel is a `loop:` block in schema.yaml, and "the
declaration surface is STUBBED now and built later." The bolt types
honor that; the intent schema silently doesn't, so a repo can shadow a
bolt type's config but not the design loop's — an asymmetry with no
stated reason. A stub costs one schema block and keeps the record's
promise honest; wiring `TYPES` to read it is a later build, like the
bolt stubs.

**Alternatives.**
- *Leave `TYPES` in Python until someone needs to shadow it.* Cheapest
  today, but the schema-shadow channel is the *only* user-edit channel
  the record kept for schemas; an intent schema with no `loop:` block
  means the design loop has no declared surface at all, and the first
  user need arrives as a fork instead of a declaration.
- *A separate config file (fleet.yaml / config.yaml).* Puts per-type
  session config in fleet plumbing rather than beside the type
  identity; the record already ruled schemas are where types live.

**Consequences.** One schema edit (item queued for the build);
`schemas/README.md` mention if it documents the blocks. #88 closes on
the ruling; the wiring stays unbuilt until the DECLARE rung is built
for the bolt types too.

---

## Draft 5 (#89) — The restart sweep: re-attach where alive, escalate where dead

**Proposed decision.** The intent loop gains a resume sweep, run each
cycle before dispatch (beside today's `resume_collect`), over items
`state:in-progress` **without** `stage:done`/`stage:collected` on its
milestone:

1. Group them by the session name in their dispatch marker
   (`<!-- flywheel:dispatch name=… origin=… notified=… -->` — already
   written on every item precisely for this).
2. For each group, ask the runner whether an agent is **alive under
   that name** (`herdr agent list`; the same roster
   `HerdrRunner.launch` consults for idempotent reuse).
3. **Alive** → rehydrate supervision only: `supervise(…,
   origin=<from marker>, notified=<from marker>)`, then the normal
   land/collect path. Never `launch` — launch on a live name would
   re-send the work order into a running session.
4. **Dead** (no agent under the name, item not `stage:done`) → never
   auto-relaunch. Comment what was found (session gone, work state
   unknown — deliverables may sit half-written on the `sess/*`
   branch), set `needs-operator`. The operator either flips
   `stage:done` (collect path takes it) or flips the item back
   `state:ready` (a fresh dispatch, on their word).

The dangerous half is (4), and the proposal keeps the machinery out of
it: a plain launch on a dead name starts a fresh session, re-sends the
work order, and restarts finished or half-finished work; only a
judgment can say whether the dead session's tree is resumable, and
judgment belongs to sessions and the operator, not the loop.

Coupling to R1 is already discharged: `stage:done` is the completion
signal, `resume_collect` consumes it; this sweep covers exactly the
complement (in-progress, not done).

**Alternatives.**
- *Do nothing; rely on `resume_collect`.* Works only when the operator
  eventually flips `stage:done`. A research session that hangs after a
  loop restart is supervised by nobody, notifies nobody at 90 minutes,
  and stalls silently forever.
- *Dead → flip back to `state:ready` automatically.* Self-healing, but
  re-runs work whose deliverables may be half-committed, and violates
  "the loops only read state and enforce contracts" the moment the
  relaunch overwrites a session directory.

**Consequences.** One build item (the sweep in `_flywheel_intent`,
roster fake in the suite, fixture: restart-with-live-pane,
restart-with-dead-pane). #89 closes on the design.

---

## Draft 6 (#161) — Compose writes the operator's brief into the unit parent

**Proposed decision.** Every compose that births or amends a unit
parent marks the parent's body **stale**; once per loop cycle that
ended with a stale parent, the loop charges one small headless session
(sonnet, effort low — pricing per #69's currency: one short
model call per compose-touched cycle, not per sub-issue) to rewrite
the parent body as a brief: discoveries grouped by theme, mechanical
vs. risk-carrying, what needs an operator ruling before work starts,
issue numbers as footnotes. The body is the surface because the board
card and the approval click show it; comments scroll away under
bookkeeping. The brief freezes when the operator moves the unit to
Ready — the flip that seals the batch already; the loop simply never
charges a refresh for a unit at Ready.

Cadence guard: "once per cycle that composed" is the cost ceiling — a
cycle that births a unit and amends it twice pays one refresh, and a
tracker at rest pays zero.

**Stated assumptions where this touches open neighbours** (the
dispatch comment names #98/#142 and #125 — none decided here):
- Wherever the parent lives (#98/#142), the brief is written into
  *that* issue's body; this decision is location-independent.
- Whatever closes a sub-issue (#125), the brief describes the set at
  refresh time; it does not track checkoff.

**Alternatives.**
- *Program-generated digest, no model.* Titles grouped by `type:` with
  counts — free, but it is a formatted list, and the defect is that
  the operator has nothing between "the title" and "all 19 bodies"; a
  grouped list of 19 titles is still 19 titles.
- *Brief only when the batch is proposed for approval.* There is no
  such single moment — compose is incremental and the operator may
  flip at any time; a brief written "at the end" is a brief the flip
  usually beats.

**Consequences.** One build item (stale-mark in `compose_batch`, the
refresh charge in the loop, freeze-at-Ready test). #161 closes on the
design; the per-compose cost is stated above as #69 asked.
