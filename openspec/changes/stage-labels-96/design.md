## Context

See `proposal.md` — Why. What shapes the approach here is three properties
of the tree this lands in, all read on `bolt/stage-labels` at
`553c7e3`:

- **The loops are stateless by construction.** `bin/_flywheel_bolt_loop.py`
  opens with it: "every cycle re-reads the tracker and the records, and the
  guards are idempotent, so a server that restarts this process freely loses
  nothing", and the one fact that cannot be recomputed — a session's launch
  time — is written to the tracker as a marker and recovered from there. Any
  per-item stage state must therefore live on the tracker and be
  recomputable, or it becomes the loop's second piece of memory.
- **Stage outcomes are read from the world, never parsed out of a session's
  prose.** The same file: a merge-back succeeded when the branch is an
  ancestor of the bolt branch, "which `git merge-base` answers; a session
  saying 'green' is not evidence and is not read as any". The objective
  checks already exist as `change_validates`, `branch_has_commits` and
  `branch_merged`.
- **A filter never writes; guards write.** `bin/_flywheel_inbox.py` states
  it and the loops are built on it: the filters are pure functions over a
  snapshot, and the guard stage applies their plans. The dry-cycle property
  — two consecutive cycles against an unchanged tracker produce the same
  state and the second writes nothing — is a unit test because of that
  split.

The intent loop's side is a hole rather than a shape. `is_complete` returns
`None` when no completion signal is configured — "R1 unresolved — not False,
unknown" — and `R1_UNRESOLVED` is emitted on every such run. Three candidate
signals are implemented behind `COMPLETION_SIGNALS` (`closed`, `label`,
`board`) and none is the default.

## Goals / Non-Goals

**Goals:**

- One stage vocabulary for both loops, with the writer differing per edge.
- Stage labels that survive a stateless restart without the loop
  remembering anything: re-derived from git where git can answer.
- One completion signal for the intent loop, with no configuration needed
  to name it, and no third *unknown* state.
- One board row per bolt, with progress the platform computes.
- A fourth bolt type expressed as config, not as a branch in the loop's
  code.

**Non-Goals:**

- Any Board Status option for session completion — the specs forbid it.
- Reworking how sessions are supervised, batched, or named; the stall
  budget, the notify threshold and the andon path are untouched.
- The `bolt-adversarial` rename and the two-programs split (R3).
- Extensions attaching at hooks: `bolt-direct` declares its hooks, and
  nothing attaches to them, exactly as its three siblings do today.

## Decisions

### The stage set is one vocabulary, and `flywheel-setup` owns its enumeration

`bin/_flywheel_inbox.py`'s vocabulary block carries the comment "The
vocabulary. One enumeration, bin/flywheel-setup:57-90." The stage names
follow that existing split: the label definitions (name, colour,
description) go in `flywheel-setup`'s `LABELS`, and the constants the loops
compare against go in `_flywheel_inbox`.

*Alternative considered:* a `stage:` enum owned by the bolt loop, since it
writes four of the six. Rejected — the intent loop writes two of them and
the operator writes one, so an owner that is one loop would have the other
importing from it, and the tracker's vocabulary would stop having a single
place to read.

### Re-derivation covers exactly what git can answer

`stage:built` and `stage:merged` are reconciled every cycle from
`branch_has_commits` and `branch_merged` — the same two calls the boundary
writes use. `stage:planned` and `stage:verified` are written at their
boundary and not reconciled.

The asymmetry is the honest one. A validated spec is a durable property of
a change on disk, but the plan-mode path's `stage:planned` has no artifact
at all — the approved plan is the spec surrogate and lives in a pane — so
`planned` has no uniform witness. `verified` has none at any time: verify
being clean is a session's finding, and the only way a later cycle could
re-derive it is to re-run verify, which is running a stage rather than
reconciling a label.

`#96` names exactly the two re-derivable cases in its own text — "commit on
the item's branch → built, on the bolt branch → merged" — so this follows
the assertion rather than extending it.

*Alternative considered:* re-derive `planned` from `openspec validate
<change> --strict`. Rejected as a general rule for the plan-mode reason
above; a rule true for one path and silent for the other is worse than a
rule with a stated boundary.

### One `stage:*` label at a time, naming the leading edge

Writing a stage removes the previous one. Two reasons: the item object
already holds "exactly one `state:*`", so one `stage:*` is the shape a
reader expects; and a filter for `stage:built` that also returned merged
items would answer a different question than the one asked. `#92` describes
the parent's bar as tracking "the stage leading edge", which is the same
notion applied to the item.

*Alternative considered:* cumulative labels, so an item's history is
readable from its labels. Rejected — the history is the item's comments and
its timeline, which GitHub keeps for labels too; four labels on every merged
item buys a worse view of the same fact.

### The re-derivation is a guard, not a stage

It runs in `guards`, before anything is worked, and records its writes in
`actions` like every other guard. That keeps two properties the loop already
has: the dry-cycle test applies to it unchanged, and the STOP condition —
"nothing is ready and the guards wrote nothing" — keeps its meaning, since a
reconciliation that changed nothing appends nothing.

It also needs each item's branch name, which is `build/<batch slug>` and
comes from `analyse(items, snapshot, slug)` — the same grouping the cycle
uses to form batches. `analyse` "reads and writes nothing, and reasons about
nothing", so calling it from a guard is free of side effects.

### R1 takes the label option, and the other two implementations go

`COMPLETION_SIGNALS`' `closed` and `board` entries, the
`--completion-signal` / `--done-label` / `--done-status` parameters, their
`config_fault` checks, and `R1_UNRESOLVED` all exist to keep three options
open until the operator picked one. The operator has picked
(`#97`, `#92`), so they are removed rather than left as configuration.

Leaving them would preserve the state this change exists to eliminate: a run
that names no signal and therefore cannot finish a session. `is_complete`
becomes a two-valued predicate over one label, and
`test_no_signal_configured_is_unknown_rather_than_incomplete` and
`test_the_r1_note_is_on_every_run_that_names_no_signal` are removed with the
behaviour they pin.

### Per-item completion, session-scoped teardown

`#97` says "each item's stages advance and flip independently", which today
is false: `_done_label` returns False on the first item that is not done, so
the whole batch waits. The predicate becomes per-item, and the collect and
close run for each item that carries `stage:done`.

Merging `sess/*` and closing the pane stay session-scoped and wait for the
last item, because they are properties of the session's own resources: a
branch merged mid-session merges a half-finished tree, and a closed pane
destroys the work in it. `HerdrRunner.close`'s own docstring draws the same
line — "a session the loop will re-prompt … KEEPS its pane. Callers close
only what is done."

The per-session dispatch marker is written on `batch.first` today
(`DISPATCH_OPEN`, parsed back by `parse_dispatch`). That stays as it is: it
records the session's clock, which is genuinely per-session, and nothing in
`#97` asks for a per-item one.

### `bolt-direct` declares a stage set; the loop reads it

`LoopConfig` today carries `strategy`, `hooks`, `extensions` and
`plan_mode`, and the cycle's stage sequence is hard-coded. `bolt-direct`
adds a declared stage set to the `loop:` block, and the cycle runs the
stages the config names.

Expressing it as config rather than as `if config.name == "bolt-direct"`
is what makes the type "a named loop config" rather than a special case,
which is the claim `#99` makes and the shape `design/loop-programs.md`
already describes for the other three ("Types live in schema.yaml (`loop:`
block per schema)").

`parse_loop_block` is a hand parser that already handles flow lists
(`hooks: [post-spec, ...]`), so a `stages:` list needs no new parsing.

*Alternative considered:* a boolean `verify: false`. Rejected — it names the
one stage this type omits rather than the sequence it runs, so the next type
that varies the sequence adds a second boolean.

### The check-off is a merge-time close carrying `closed:merged`

`#98` says "A sub-issue checks off at `stage:merged`, never at landing;
`closed:done` remains the landing's signal." GitHub's native sub-issue
progress counts **closed** sub-issues, so checking off at `stage:merged`
means closing the item at merge — while `skills/_reference/tracker.md`
invariant 5 says an item closes "always with one `closed:*` reason" and
`#98` reserves the only fitting reason for the landing.

The operator ruled on `#118` (2026-08-14): **a new closure reason
`closed:merged`.** A construction sub-issue closes at merge-back with
`closed:merged`; the landing upgrades the label to `closed:done` with the
SHA in its closing comment. Invariant 5 stands verbatim — every close
carries exactly one `closed:*` reason at every moment. The bar advances at
merge, the Landed view (`closed:done`) stays exact, and `flywheel-setup`
gains the label. A merged-not-landed item leaving the In-flight view is
correct: it waits on the landing, not on anyone.

*Alternatives considered*, both put to the operator on `#118` and both
declined: closing at merge with **no** `closed:*` label and amending
invariant 5 to make `stage:merged` the reason — rejected because invariant 5
is what makes "whoever holds the evidence closes" true, and every skill
points at it; and keeping the items open at merge and **computing** a
progress figure — rejected because it contradicts `#98`'s "GitHub's native
progress bar" and makes the board a second store.

### Closing at merge takes the item out of the filters, so "in flight" has to say so

This is the consequence that costs code rather than vocabulary, and it is
load-bearing: `Tracker.snapshot` is built from `open_issues()`, so a
merge-closed item is invisible to everything downstream of it.

Three sites break without a rule, all read on this branch:

- `landing_wanted` returns False when `open_items` is empty — its own
  comment reads "nothing to close, nothing to land". Once the last batch
  merge-closes, that is exactly the state, and the bolt would never land.
- `land_stage` takes `[i for i in snapshot.on(milestone) if i.is_open]`, so
  the landing would upgrade nothing and comment no SHA.
- `server_inbox` needs "an open item labelled `state:ready` or
  `state:in-progress`" to see a job, so a loop killed between the last merge
  and the landing would never be restarted.

So `closed:merged` is specced as an in-flight state: the loop's picture of
its milestone carries those items, the landing runs over them, and the
server counts them as a job. The set that must not change is anything
reading `state:ready` — a closed item is not ready, and the ready set is
what the cycle works.

The alternative — leaving the item open at merge and closing only at the
landing — is the option the operator declined, and it is the one that would
have cost nothing here. The cost is named rather than hidden: this is what
the bar at merge-time buys.

### Re-derivation covers the close, because the merged edge is now two writes

`#96` asks for stages that self-heal on a stateless restart, and the merged
edge now writes a label and a close. A process killed between them leaves an
item that is half-merged in the tracker's eyes, so the guard reconciles
both: an item whose branch is an ancestor of the bolt branch ends the guard
at `stage:merged` and `closed:merged`, whichever half is missing.

That widens the guard's scope, which today reads the milestone's open
`state:in-progress` items, to also read its `closed:merged` ones — the item
whose label write died needs the first scope, and the item whose close died
needs the second. An item at `closed:done` is never walked back: the landing
is downstream of the merge, and reconciliation does not reverse it.

## Risks / Trade-offs

- **The stage guard runs git commands for every open item, every cycle** →
  the two checks are `git rev-list --count` and `git merge-base
  --is-ancestor` against a local worktree, which is what the loop already
  runs per batch at merge time; the item count on a bolt is tens, not
  thousands. If it ever matters, the reconciliation can skip items already
  at `stage:merged`, since that stage is terminal for the bolt branch.
- **A branch name that does not match `build/<slug>`** → re-derivation finds
  no commits and would walk a label back. Mitigated by deriving the branch
  from `analyse`, the same grouping that named it at spec time, rather than
  from a stored string; an item whose branch genuinely does not exist is
  correctly not built.
- **Removing `--completion-signal` is a breaking change to
  `bin/flywheel-intent-loop`'s interface** → nothing in the repo passes it
  outside the tests, and the flag exists only to name an unresolved choice.
  It is called out as **BREAKING** where the argument is removed.
- **Per-item collection could collect the same item twice** → guarded by
  `stage:collected`, which is exactly the label that says an item's
  deliverables are already gathered; the collect is skipped for an item that
  carries it.
- **A born-ready release now creates an issue that did not exist before** →
  the unit parent is one extra issue per bolt, and it is the object the
  board rule already expects ("whatever carries the approval sits on the
  board"). Existing born-ready bolts in flight keep their shape; this
  applies to releases made after it lands.
- **A failed landing leaves the items already closed** → under the previous
  shape a landing failure left everything open and obviously unfinished.
  Now the items are at `closed:merged`, which is the honest record — the
  work *is* on the bolt branch — and the bolt's state is carried by the
  milestone and the andon path, both unchanged. The loop's pause and its
  `needs-operator` label are what make a failed landing visible, not an
  open item.
- **A human may read a fully-checked bar as a landed bolt** → the bar means
  merged, and the Landed view means landed. The two are different questions
  and now have different answers on the board; invariant 9's milestone
  closure is the operator's act and the specs forbid reading a milestone as
  finished while any item sits at `closed:merged`.
- **The `stage:*` labels must exist before any item carries one** → a `gh
  issue edit --add-label` against an undefined label fails. The same holds
  for `closed:merged`, which the same convergence run creates. The bolt's merge
  criteria already name the `flywheel-setup` convergence run as a landing
  condition, and the task list runs it before the loops are changed.

## Migration Plan

1. `flywheel-setup` converges the `stage:*` labels onto `agentplot/flywheel`
   — before any loop writes one.
2. The loop changes land together on the bolt branch. Both loops tolerate
   items that carry no stage label: the bolt loop's re-derivation supplies
   `built`/`merged` on the first cycle, and the intent loop treats an item
   with no `stage:done` as not done, which is what it does today.
3. Items already in flight on other bolts acquire their labels from the
   first re-derivation cycle their loop runs. No backfill script is needed
   and none is written — that is what re-derivation is for. An item on
   another live bolt whose branch is already merged back is closed with
   `closed:merged` by that same cycle: the new shape applied to work that
   is genuinely at that point, and its landing upgrades it like any other.
4. Rollback is the branch: nothing in this change writes a state that a
   revert cannot leave behind harmlessly, since a stray `stage:*` label on
   an item is inert to every filter that exists before the change.
