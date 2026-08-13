# Bolt: loop-server

## Scope

Cut the flywheel over from compile-then-run conductor agents to two loop
programs and a server that runs them. Six released assertions land in one
repo: `bin/flywheel-bolt-loop` runs construction as an ordinary program —
query+guards, spec by the type's strategy, apply, verify with go-fix
rounds, serialized merge through the gate, landing per `bolt.md`, items
closed with the SHA, STOP when nothing is ready and the guards wrote
nothing (#72); `bin/flywheel-intent-loop` runs design as a separate
program with its own guards, typed sessions, deliverable collection and
`sess/*` merges, its completion signal operator-driven rather than
inferred (#73); `flywheel server` is a daemon running a 60s reconcile
that starts one stateless loop process per milestone with a job, stops
those without, and runs a one-shot archive for a closed milestone (#74);
one session-runner abstraction — `launch`/`wait`/`collect`/`close` — backs
a herdr pane runner for supervised work and a headless `claude -p` runner
for unsupervised work, with the program owning every clock (#75); the
tracker's four inbox filters — server, bolt loop, intent loop, dispatch —
become the whole coordination model, with the andon cord as a structured
marker the loop recognizes as code rather than judgment (#76); and the
bolt types become named loop configs, `bolt-adversarial` replacing
`bolt-deep` everywhere, with the `loop:` block landing in `schema.yaml` as
a parsed-but-unbuilt stub (#77).

The cutover retires what runs it. The conductor agent profiles, their
fleet rows, the trigger phrase and launch-prompt machinery, and the
compile-then-run apply prose all go; `fleet.yaml` becomes server config
plus dispatch. Dispatch is the one standing agent that survives.

## Sources

- **`design/loop-programs.md`** (fc190e9 on `main`) — the ratified
  decision record, and the proposal every item here derives from. It is
  the only source: this bolt was released straight to construction on the
  operator's word, 2026-08-13, with no intent milestone, no handoff item
  and no bolt plan. There are no assertion record files; **each item's
  body IS its claim**, and each body already names the section of
  `design/loop-programs.md` it comes from.
- **Assertions — the six items on `bolt/loop-server`**, all born
  `state:ready` on the operator's word:
  - #72 · `bin/flywheel-bolt-loop` runs the construction loop as a program
    — record section "The bolt loop"
  - #73 · `bin/flywheel-intent-loop` runs the design loop as its own
    program — "The intent loop"
  - #74 · `flywheel server` starts and stops loop processes from a 60s
    reconcile — "Decision" and "Supersedes"
  - #75 · one session-runner abstraction launches herdr and headless
    sessions — "Sessions and runners"
  - #76 · the inbox filters are the whole coordination model — "Inboxes"
    and "The andon cord"
  - #77 · the bolt types are named loop configs; `bolt-adversarial`
    renames `bolt-deep` — "The bolt types" and "What the schemas remain
    for"
- **Three open questions the record itself carries, R1–R3.** R3 — one
  machinery bolt for the cutover or staged — is answered by the release
  that created this milestone: one bolt, this one. **R1 and R2 are open
  and this record does not close them.** R1 (the exact GitHub signal for
  "operator marks a design session done") is a precondition of #73's
  completion path, and R2 (two-then-pause on verify's go-fix rounds, and
  whether a session's questions relay live or batch on the item) is a
  precondition of #72's verify stage. Each is the operator's word to
  give; when either blocks, the question goes on its item with
  `needs-operator` and work continues on what it does not gate. Neither is
  answered by inference here.

## Repos

- **agentplot/flywheel** · bolt branch `bolt/loop-server` · worktree
  `~/.herdr/worktrees/.bare/bolt-loop-server`

The only repo, and the same repository as the org's tracker. This
checkout is bare at `/Users/chuck/Code/github_agentplot/flywheel/.bare`
with `main` a linked worktree, so bolt and construction worktrees are cut
from the bare path and herdr names the repo `.bare` in the worktree
layout. Neither the bolt branch nor its worktree exists yet — this record
is written on `main` at scaffold time, and cutting them is the loop's
first topological act.

**This bolt runs on the machinery it retires, and that is safe for a
mechanical reason worth stating.** The session driving it loads the
plugin from `~/.claude/plugins/cache/flywheel/flywheel/0.9.9/`, a release
artifact that updates only by releasing. Edits to `skills/`, `agents/`,
`schemas/` and `bin/` on the bolt branch therefore do not reach the
running conductor or its sessions mid-bolt; the cutover takes effect for
this org at the release that follows the landing, not at the merge. The
milestone's own note — that this bolt doubles as a live parallel test of
the 0.9.9 dynamic-workflow machinery — depends on exactly that
separation.

## Merge criteria

**This is a `bolt-quick` on the plan-mode path, and both halves of that
are the operator's choice at release, recorded in the milestone
description.** `bolt-quick` schedules no review step. The plan-mode path
means no spec-driven change is written in this repo for these items: each
build session starts in `--permission-mode plan`, and its plan — checked
against the item's claim before approval through the plan dialog — is the
spec surrogate. No session downgrades or upgrades either choice on its
own; a case for more scrutiny on a particular item is a question for the
operator, not a decision to take mid-bolt.

**The merge gate is this repo's three `[pre-merge]` hooks** in
`.config/wt.toml` — `sh scripts/validate-manifests.sh`,
`node scripts/check-paths.mjs`, `node scripts/check-site.mjs` — and it is
never suppressed: no `--no-hooks`, no `--no-verify`, no `--yes`, and
hand-running the three scripts is not a substitute for the tool running
them. Their grants are in place: `~/.config/worktrunk/approvals.toml`
holds `[projects."github.com/agentplot/flywheel"]` with four
approved-commands entries — the three checks plus `wt step copy-ignored`
— read today on this machine. An agent that nonetheless hits
`Cannot prompt for approval in non-interactive environment` stops and
reports rather than working around it.

**Acceptance on the bolt branch, before the landing:**

- **The programs run.** `bin/flywheel-bolt-loop`, `bin/flywheel-intent-loop`
  and `flywheel server` each start, parse arguments, and reach a clean
  no-work exit against the live tracker without writing anything —
  observed, not asserted, and named with the tree it ran on. A loop that
  can only be shown to work by doing work has not been accepted.
- **A dry cycle is genuinely dry.** The bolt loop's guards are
  writes-only and idempotent: two consecutive cycles against an unchanged
  tracker produce the same tracker state, and the second writes nothing.
  This is the property the whole stateless-process design rests on and it
  is exercised directly, not inferred from the code.
- **Tests exist and are green — and this repo has no harness today.**
  Verified at fc190e9: `package.json` declares no `test` script, and
  `git ls-files '*.py'` returns exactly one file, `bin/_flywheel_gh.py`.
  So a runner and the first unit tests are part of what #72 and #73 land,
  not a facility they can lean on; the record's claim that the loops are
  unit-testable is what those tests must make true. The bench findings
  the design record says carry into these tests are named by it and are
  the starting set.
- **The rename is complete, not mostly complete.** After #77, a
  case-sensitive search of tracked files finds no `bolt-deep` outside
  history and archived changes: `schemas/`, `skills/`, `agents/`, `bin/`,
  `site/` and `openspec/specs/` all read `bolt-adversarial`. The
  `schemas/bolt-deep/` directory is renamed, not copied, and the shipped
  manifests still validate.
- **Retirement leaves nothing dangling.** Where conductor profiles, fleet
  rows, the trigger phrase or the launch-prompt machinery are removed,
  nothing tracked still references them — the same search discipline as
  the rename. A reference found later is a new item, not a silent
  widening of an accepted one.
- **The repo's own three gates green on the tree that lands**, run by the
  gate rather than by hand.
- **No item lands closed while it still carries `needs-operator`.** An
  item under that label has a stage the operator's word gates, and
  closing it `closed:done` would put a false claim in its closing
  comment. This bites concretely today: #73's collect, merge, close and
  teardown stages are unexercised until R1 is answered — every earlier
  stage runs and is measured, but the loop stops before collecting, by
  its own design, and no `--completion-signal` is defaulted. So the
  landing session lands the branch and closes the items whose evidence
  it holds, and leaves any `needs-operator` item open with the landing
  SHA commented instead. The milestone then closes when that item does,
  not before.

**Landing: merge.** With the criteria above holding,
`bolt/loop-server` lands on `main` through the full gate, one writer to
main at a time, and each item closes `closed:done` with the landing SHA in
its closing comment.
