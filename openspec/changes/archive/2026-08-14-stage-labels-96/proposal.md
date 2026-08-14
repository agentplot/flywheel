## Why

`state:in-progress` is one undifferentiated span from release to landing. On
`bolt/loop-server` some items had commits on the bolt branch while others had
none, and no GitHub view could tell them apart; items close only at the
landing, so a milestone's bar stays flat until the end. The only surface that
knew the difference was the run's workflow tree, which dies with the run.

The intent loop has the opposite hole. `is_complete` in
`bin/_flywheel_intent.py` returns **None** — not False, *unknown* — whenever no
completion signal is configured, and its `R1_UNRESOLVED` note says so on every
run: "the operator has not named the signal for 'design session done'". Design
sessions are dispatched and supervised, and nothing is collected, merged or
closed. The intent loop cannot finish a session at all until that signal is
named.

This change is the tracker half of both: one `stage:*` vocabulary refining
`state:in-progress`, written by whoever owns each transition, plus the
container that makes it visible on the board.

It derives from four released assertions on `bolt/stage-labels` — the item
bodies themselves are the proposals, there being no assertion record file for
any of them (`openspec/changes/stage-labels/bolt.md`, Sources: "None of the
five carries an assertion record file"):

- `agentplot/flywheel#96` — the bolt loop writes stage labels at the
  boundaries it drives
- `agentplot/flywheel#97` — intent items carry in-session, done, collected,
  and the operator's `stage:done` flip is the completion signal
- `agentplot/flywheel#98` — every release creates a unit parent, born-ready
  included
- `agentplot/flywheel#99` — `bolt-direct`, the fourth bolt type, no verify
  stage

## What Changes

- **A `stage:*` label set exists on the tracker and `flywheel-setup`
  converges it.** `bin/flywheel-setup`'s `LABELS` table today defines
  `type:*`, `state:*`, `closed:*`, `unit`, `elaboration` and
  `needs-operator` and no `stage:*` name; the bolt's own merge criteria
  require the labels to exist before any item carries one.
- **The bolt loop writes `stage:planned`, `stage:built`, `stage:verified`,
  `stage:merged`** at the four boundaries `BoltLoop.cycle` already drives,
  and **re-derives them from git every cycle** — a commit on the item's own
  branch means built, an ancestry relation with the bolt branch means merged
  — so the labels self-heal across the stateless restart the loop is built
  for. The objective checks this needs already exist as
  `change_validates`, `branch_has_commits` and `branch_merged`.
- **The intent loop writes `stage:in-session` at launch and
  `stage:collected` once deliverables are gathered; the operator writes
  `stage:done`.** That flip is what `is_complete` consumes, which
  **resolves R1** in `design/loop-programs.md` — the "state label the
  operator sets" option of its three. `R1_UNRESOLVED` and the unknown-third
  state go with it.
- **Each item's stages advance and flip independently** within a session
  that carries several. Today `_done_closed` / `_done_label` / `_done_board`
  each return False on the first item that is not done, so an operator who
  marks two of three items done gets nothing collected.
- **Board Status stays batch-approval only.** The operator's per-item
  session state lives in labels with every other signal the loops read; no
  Status option is added and `_done_board` is not the answer to R1.
- **Every release creates one unit parent issue** whose sub-issues are the
  released items — the handoff birth path and the born-ready operator
  release alike. Today only the handoff path composes a unit; a born-ready
  item goes on the board alone via `bin/flywheel-board`.
- **`bolt-direct` ships as a fourth named loop config** — strategy `ff`, the
  stages `spec, build, merge, land` and no verify — beside `bolt-quick`,
  `bolt-default` and `bolt-adversarial`. The repo's own merge gate still
  runs at merge and at landing: it belongs to the repo, not to the type.
  On a `bolt-direct` item `stage:verified` never appears.

- **A sub-issue checks off at merge-back, via a new closure reason
  `closed:merged`.** `#98` asks for GitHub's native progress bar, which
  counts **closed** sub-issues, and for the check-off to happen at
  `stage:merged`. So the loop closes each assertion with `closed:merged`
  when git confirms ancestry, and the landing upgrades that to
  `closed:done` with the SHA — invariant 5 standing verbatim, with exactly
  one `closed:*` reason on a closed item at every moment. Because closing
  removes an item from every filter built on open issues, a `closed:merged`
  item stays in flight for the loop, the landing and the server's job
  filter until the bolt lands.

## Capabilities

### New Capabilities

- `flywheel-stage-labels`: the `stage:*` vocabulary itself — the seven names,
  what each means, that they refine rather than replace `state:*`, that
  `closed:done` stays reserved for the landing, and that `flywheel-setup`
  converges the set onto a repo's tracker.
- `flywheel-construction-stages`: which of those labels the bolt loop
  writes, at which boundary, and the rule that every one of them is
  re-derived from observable git state each cycle rather than remembered.
- `flywheel-design-session-completion`: how a design session finishes — the
  loop's `stage:in-session` and `stage:collected`, the operator's
  `stage:done` as the one completion signal, per-item independence, and
  Board Status staying batch-approval only.
- `flywheel-release-unit-parent`: that every release, handoff birth and
  born-ready alike, creates one unit parent whose sub-issues are the
  released items.
- `flywheel-bolt-direct`: the fourth bolt type as a named loop config — its
  stage set, and that the repo's merge gate is never a function of type.

### Modified Capabilities

<!-- none: no capability under openspec/specs/ carries a requirement about
     the tracker's label vocabulary, either loop's stage transitions, what a
     release creates, or the set of bolt types. Checked against the ten
     directories under openspec/specs/ on this branch. -->

## Impact

- **`bin/flywheel-setup`** — the `LABELS` table grows the `stage:*` set and
  `closed:merged`.
  `ensure_labels` is already idempotent ("creates what is missing and never
  rewrites what exists"), so converging an existing tracker adds only the
  new names.
- **`bin/_flywheel_inbox.py`** — the vocabulary constants, whose header
  comment names `bin/flywheel-setup` as the single enumeration, and the
  intent loop's completion filter.
- **`bin/_flywheel_bolt_loop.py`** — a stage-label guard in `guards`, and
  the writes at `spec_stage` / `build_stage` / `verify_stage` /
  `merge_stage`. `LoopConfig` grows the stage set that lets `cycle` skip
  verify. The merge boundary gains the `closed:merged` close, `land_stage`
  the upgrade to `closed:done`, and `landing_wanted` — whose "nothing to
  close, nothing to land" test reads open items only — the merge-closed
  set.
- **`bin/_flywheel_inbox.py`'s `snapshot` and `server_inbox`** — a bolt
  milestone's `closed:merged` items are in flight, and `snapshot` is built
  from `open_issues()` today.
- **`bin/_flywheel_intent.py`** — `dispatch_batch`, `is_complete` /
  `COMPLETION_SIGNALS`, and `land`'s batch-wide predicate.
  `bin/flywheel-intent-loop`'s `--completion-signal` argument follows.
- **`bin/flywheel-board`** and the born-ready release path — a unit parent
  where today there is a lone item on the board.
- **`schemas/bolt-direct/`** — a new schema directory, published by
  `bin/install-schemas` like its three siblings. `schemas/README.md` lists
  the types and follows.
- **`design/loop-programs.md`** — R1 is answered, and the record is updated
  to say so.
- **`skills/_reference/tracker.md`** — the shared object-graph copy every
  skill points at; the state ladder and the board rule both move.
- **`tests/test_bolt_loop.py`, `tests/test_intent_loop.py`,
  `tests/test_inbox.py`** — the behavioural pins, including
  `test_a_settled_session_is_not_a_finished_one` and
  `test_the_r1_note_is_on_every_run_that_names_no_signal`, which asserts a
  note this change removes.
- **`skills/_reference/tracker.md`** — invariant 5's closing sentence, which
  today says the landing is the sole writer of a `closed:*` label on a
  construction item.
- Not in this change: any Board Status option; the `bolt-adversarial`
  rename and the two-programs split (R3).
