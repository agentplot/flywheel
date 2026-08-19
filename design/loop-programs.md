# Decision draft: the loops are programs; a server runs them; the tracker is the only bus

Status: RELEASED to construction by the operator, 2026-08-13, as bolt/loop-server. R1-R3 are settled by the bolt plans or by the operator in-session.

## Decision (proposed)

Two loops, two programs — they are different workflows and stay that
way: `bin/flywheel-bolt-loop` (construction) and
`bin/flywheel-intent-loop` (design). Ordinary Python beside the other
bin tools, calling herdr, wt, gh, and openspec directly: token-free
orchestration, unit-testable, no agent asked to behave like code. A
model runs only where judgment lives — inside sessions.

There are no conductor agents. `flywheel server` is a daemon the
operator starts on any host they want in the fleet; it runs the
reconcile pass every 60s and starts or stops one loop process per
milestone with a job. Multi-host is just a server per host sharing the
tracker; a server takes only the loops whose Team maps to it. The old
conductor lifecycle becomes process semantics: no job -> the loop
process stops; a job -> a stateless process starts and re-reads
tracker + records (the idempotent guards make that safe); a closed
milestone -> a one-shot archive run. Operator visibility is server
logs for now. Dispatch survives as the one standing agent (triage and
relay need a mind and a Discord channel).

What an end user changes is what plugs into the loops, on a
three-rung ladder: DECLARE (a `loop:` block in schema.yaml), SCRIPT (a
hook names a user workflow script), FORK (machinery construction
through the flywheel's own bolts). The declaration surface is STUBBED
now and built later — the programs ship with fixed behavior first.

## Inboxes — the tracker is the only bus

No session, loop, or server ever messages another. Everything moves
through GitHub issues, and each consumer has an exact filter:

- **server**: milestones with a job — any open `intent/*` or `bolt/*`
  milestone holding an open item labelled `state:ready` or
  `state:in-progress`, or a bolt milestone holding a `closed:merged`
  item still awaiting its landing, or a batch at board Status Ready,
  or an open `intent/*` milestone holding guard-only work: settled
  unbatched assertions (handoff birth) or orphan `state:queued` items
  (compose); plus closed
  milestones whose change still sits in openspec/changes/ (archive).
  The guard-only test is a sweep, and the asymmetry licensing it is a
  rule: **a server filter may over-approximate; a loop filter must be
  exact** — a false positive costs one process start and a clean exit
  (the loop STOPs when nothing is ready and the guards wrote nothing),
  while a false negative costs work that never happens.
- **bolt loop for bolt/<slug>**: open items on that milestone
  labelled `state:ready`, plus that bolt's units at board Status
  Ready (their `state:queued` sub-issues are relabelled first).
- **intent loop for intent/<slug>**: same filter on its milestone,
  plus the guard sweeps: settled unbatched assertions (handoff
  birth) and orphan `state:queued` items (compose).
- **dispatch**: open issues with no milestone (triage), and open
  issues labelled `needs-operator` (relay).

These filters are the whole coordination model. A discovery is an
issue; an escalation is a label; a completion is item state. Anything
not expressible in the filters is a design smell. (The conductor's
old direct-edit privileges go the same way: a CLAUDE.md fix, an ADR,
a machinery tweak are GitHub issues like all work — nothing edits
without one.)

## The bolt loop

    query+guards -> spec (per strategy) -> apply -> verify -> merge
    -> land -> bookkeeping -> re-query ... STOP

- GUARDS every cycle, idempotent, writes-only actions; a failing
  cycle halts the run. (Flip-consume relabel; discovery routing by
  the merge-criteria test; scaffold-if-missing.)
- SPEC, by the type's strategy (below): the session runs /opsx:ff, or
  /opsx:new then /opsx:ff, or /opsx:new then /opsx:continue per
  artifact. `openspec validate --strict` green before it counts.
- APPLY: /opsx:apply on the item's worktree.
- VERIFY: /opsx:verify — checks what was built against the change's
  artifacts and writes the findings to a file the loop owns
  (`.flywheel/verify.md`), never a verdict. Judging the findings is
  the REVIEW's: a proxy-for-the-operator session reads them and rules
  through `.flywheel/review.json` — proceed, refix with the exact
  prompt for the build session (relayed to the SAME session, warm),
  or escalate to needs-operator. An unreadable ruling escalates,
  never guesses. After the fix-round budget the loop pauses the item.
  Work sessions do work, the review judges, the loop does
  bookkeeping.
- MERGE, a static loop step — no session: `wt merge` through the
  gate, serialized per target branch, success answered by ancestry;
  the loop archives the change on green. A red gate goes back to the
  build session with the gate's own output, on the fix-round budget;
  a conflict pauses for the operator (an agent seat is reserved
  there, stubbed today).
- LAND per bolt.md: merge criteria verified by the landing session,
  which refuses otherwise; `Landing: merge` (default) or
  `Landing: pr`. A failing criterion births one born-ready fix item,
  idempotently; the same criterion failing after its fix landed
  pauses the bolt and sets needs-operator.
- Each assertion closes `closed:merged` with the merge SHA at the
  merge-back — which is what checks it off on its unit parent's native
  bar — and the landing upgrades that reason to `closed:done` with the
  landing SHA; STOP when nothing is ready and the guards wrote nothing;
  all items closed AND none left at `closed:merged` -> propose closure;
  the operator's milestone close is the archive signal.

## The bolt types — named configs of the same program

- **bolt-quick** — strategy `ff`, no extensions. For work too small
  for even that, a per-bolt declaration in the handoff plan selects
  the plan-mode path instead: no spec-driven change; the build
  session starts in `--permission-mode plan` and the plan, checked
  against the item's claim, is the spec surrogate. Plan-mode is
  bolt-quick-only — settled, no more back-and-forth.
- **bolt-default** — strategy `new+ff`: the proposal exists before
  the rest of the spec is generated, which is where a proposal
  review attaches when extensions arrive.
- **bolt-adversarial** (renames bolt-deep) — strategy
  `new+continue`: stepwise artifact generation, a review point after
  each artifact when extensions arrive, and the persona battery.
- **bolt-direct** — strategy `ff`, and the stage set `spec, build,
  merge, land`: no verify stage, no verify session, and
  `stage:verified` never on one of its items. For work whose
  correctness the spec and the repo's merge gate settle between them.
  Skipping verify is a property of this type alone and is not
  reachable by a per-bolt declaration on another, exactly as plan mode
  is bolt-quick's alone. The repo's merge gate is not a function of
  the type and runs unweakened here as everywhere: what a type varies
  is how much review the flywheel schedules, never what the repo's
  hooks assert about the tree that lands.

Types live in schema.yaml (`loop:` block per schema); a repo
customizes by shadowing the schema; the handoff plan overrides per
bolt (it already carries type and landing). A type declares the
stages its cycle runs, which is what makes a type that varies the
sequence a named config rather than a branch in the loop's code.
Hook names follow the
real command boundaries — post-new, post-artifact, post-spec,
post-apply, post-verify, pre-merge, pre-land — so each strategy
exposes exactly the review points its commands create, and a type
declares only the boundaries its own stages create.

## The intent loop — its own program

    query+guards (scaffold-if-missing, flip-consume, handoff birth,
    compose) -> typed design sessions -> collect deliverables ->
    merge sess/* branches -> re-query ... STOP

Guard 0 is scaffold-if-missing, exactly as on the bolt loop and as a
program step — `openspec new change <slug> --schema flywheel-intent`
is non-interactive, so no model is involved. Triage creates intent
milestones without inception; the loop is the only actor guaranteed
to be there when the change dir is missing
(decision: openspec/changes/loops-run-unattended/decisions/intent-scaffold-guard.md).

Design-session completion is OPERATOR-DRIVEN, one path, and the signal
is the `stage:done` label: the operator marks an item done — by saying
so in the session (the session then writes `stage:done` to that item
and settles) or by adding the label on GitHub directly — and the loop
reacts to the tracker change: collects that item's deliverables
(session directory, drafts, item comments), marks it
`stage:collected`, and closes it. There is one flip and one filter,
and no parameter names which signal is in use. The loop never infers
completion from a round artifact, because the operator may iterate a
plannotator or lavish round, or a round-close plan, as many times as
they want.

Each item's stages advance independently — an operator who marks two
of a session's three items done gets those two collected and closed.
The session-scoped acts wait for the whole session: the `sess/*`
branch is merged and the pane is closed once every item the session
carries has reached `stage:collected`, because a branch merged
mid-session merges a half-finished tree and a pane closed under a
running session destroys the work in it.

Construction sessions are
the opposite: completion is objective — settle plus the deliverable
contract (change validates, commit on branch, comment on item);
settle without deliverables is one re-prompt, then needs-operator.

## Sessions and runners

One abstraction in the programs — launch(spec), wait(handle),
collect(handle), close(handle) — with three runners:

- **herdr** — a pane; supervised; anything the operator might watch
  or answer. Plannotator and lavish run here for now.
- **headless** — `claude -p` (later the Agent SDK) from the program;
  reuses the CLI login; unsupervised work only.
- **cloud** — future managed agents; same interface.

Runner choice is per stage, by supervision need, and is config.
Launches are idempotent (an agent already running under the name is
reused); work orders are one prompt with the invocation first line;
the PROGRAM owns all waiting with real clocks — notify at 90 min via
needs-operator, stall at 4 h except operator-round sessions, which
never auto-stall. Every design session is one, since any may end with
a round-close plan.

## The andon cord — no judgment in the loop

A SESSION raises the andon: when it finds the work wrong in a way no
fixing will help, it writes the stop as a structured marker in its
item comment and settles. The loop recognizes the marker — code, not
judgment — pauses the batch, and sets needs-operator. All judgment
lives in sessions and with the operator; the loops only read state
and enforce contracts.

## What the schemas remain for

Three roles kept: the record contracts (bolt.md and the intent's
decisions/questions/assertions/sessions artifacts, templates,
`openspec validate --strict`); the type identity (binding a schema IS
choosing the type; the type is a named `loop:` config); the user-edit
channel (a repo's openspec/schemas/ copy shadows the installed one).
Lost: the procedural apply prose.

## Agent SDK — skeleton first

The programs ship first. The SDK arrives at three triggers: policy as
code (permission callbacks replacing the skip flag - #63; a tool hook
enforcing fail-closed credentials - #61); unsupervised stages moving
from panes to SDK calls with structured outputs; and replacing the
programs' launch/wait/collect code with SDK primitives. Sessions the
operator supervises stay herdr panes permanently.

## Supersedes

The compile-then-run design (0.9.x) — its bench findings carry into
the programs' unit tests. The conductor agent profiles and their
fleet rows — `flywheel up` starts the server; fleet.yaml becomes
server config plus dispatch. The trigger phrase and launch-prompt
machinery. The churn-call machinery (verify's go-fix conversation and
the two-round pause replace it). The bolt-deep name.

## Resolved

- R1 The GitHub signal for "operator marks a design session done" is
  **the `stage:done` label, set by the operator** — in the pane (the
  session writes it to its own item and settles) or on GitHub
  directly, one flip either way. The intent loop consumes that label
  and has no other completion signal and no parameter naming one.
  Taken over a board Status, because per-item session state lives in
  labels with every other signal the loops read and a Status would be
  a second store; and over closing the items, because closing is the
  loop's own act on collection. Board Status keeps its one meaning:
  the operator's batch-approval surface.

## Open questions (two)

- R2 Verify's go-fix rounds: is two-then-pause right, and does the
  operator want the session's questions relayed live (dispatch DM) or
  batched on the item?
- R3 The bolt-adversarial rename and the two-programs split are
  mechanical but touch schemas, skills, profiles, and the fleet
  driver — one machinery bolt for the whole cutover, or staged?
