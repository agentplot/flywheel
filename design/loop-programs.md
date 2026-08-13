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
  `state:in-progress`, or a batch at board Status Ready; plus closed
  milestones whose change still sits in openspec/changes/ (archive).
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
  artifacts. Findings are handled the way the operator does it by
  hand: the loop re-prompts the SAME build session — "go fix these" —
  relays its questions if it asks any, and re-runs verify. After two
  fix rounds on the same finding the loop pauses the item and sets
  needs-operator. No other machinery.
- MERGE, serialized per target branch, through the gate, never
  --yes; archive the change on green; the session's pane closes.
- LAND per bolt.md: merge criteria verified by the landing session,
  which refuses otherwise; `Landing: merge` (default) or
  `Landing: pr`. A failing criterion births one born-ready fix item,
  idempotently; the same criterion failing after its fix landed
  pauses the bolt and sets needs-operator.
- Items close at landing with the SHA; STOP when nothing is ready and
  the guards wrote nothing; all items closed -> propose closure; the
  operator's milestone close is the archive signal.

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

Types live in schema.yaml (`loop:` block per schema); a repo
customizes by shadowing the schema; the handoff plan overrides per
bolt (it already carries type and landing). Hook names follow the
real command boundaries — post-new, post-artifact, post-spec,
post-apply, post-verify, pre-merge, pre-land — so each strategy
exposes exactly the review points its commands create.

## The intent loop — its own program

    query+guards (flip-consume, handoff birth, compose) ->
    typed design sessions -> collect deliverables ->
    merge sess/* branches -> re-query ... STOP

Design-session completion is OPERATOR-DRIVEN, one path: the operator
marks done — by saying so in the session (the session then records it
on the tracker and settles) or by changing the item state on GitHub
directly — and the loop reacts to the tracker change: collects the
deliverables (session directory, drafts, item comments), merges the
session branch, closes the pane. The loop never infers completion
from a round artifact, because the operator may iterate a plannotator
or lavish round as many times as they want. Construction sessions are
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
never auto-stall.

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

## Open questions (three)

- R1 The exact GitHub signal for "operator marks a design session
  done": a state label the operator sets, a board Status, or closing
  the items — pick one so the loop has one filter.
- R2 Verify's go-fix rounds: is two-then-pause right, and does the
  operator want the session's questions relayed live (dispatch DM) or
  batched on the item?
- R3 The bolt-adversarial rename and the two-programs split are
  mechanical but touch schemas, skills, profiles, and the fleet
  driver — one machinery bolt for the whole cutover, or staged?
