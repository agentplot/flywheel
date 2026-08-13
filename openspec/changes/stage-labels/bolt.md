# Bolt: stage-labels

## Scope

Give per-item construction progress a visible surface, and give every
release a native progress bar. The bolt loop's driver writes `stage:planned`,
`stage:built`, `stage:verified`, `stage:merged` on each item at the opsx
boundaries it already drives — spec/plan approval, apply, verify, merge to
the bolt branch — re-derived from observable git state every cycle (a
commit on the item's own branch means built, a commit on the bolt branch
means merged) so the labels self-heal across a stateless restart;
`closed:done` stays reserved for the landing, with the SHA, and
`stage:verified` never appears on a `bolt-direct` item. The intent loop
writes `stage:in-session` at session launch; the **operator's** `stage:done`
flip — in the pane or directly on GitHub, the same signal either way — is
what the intent loop's filter consumes to collect deliverables, merge
`sess/*`, close the pane, and close the item, resolving R1 in
`design/loop-programs.md`. Every release, handoff birth or born-ready alike,
creates one unit parent issue whose sub-issues check off at `stage:merged`,
giving the board a native "n of m" bar per bolt while `closed:done` remains
the landing's own signal. A fourth named loop config, `bolt-direct`
(strategy `ff`, no verify stage: spec, build, merge, land), ships alongside
`bolt-quick`/`bolt-default`/`bolt-adversarial`, with the repo's own merge
gate always implied and never a function of type. `flywheel-setup` converges
the new `stage:*` label set onto a repo's tracker labels.

## Sources

No source intent milestone. Released straight to `bolt/stage-labels`
(milestone #11) on the operator's word, 2026-08-13, from rulings made in a
design tuning session and recorded on the milestone's items: S1 (the
`bolt-direct` type and the bolt loop's four `stage:*` labels), S2/S4/I1/I2
(the intent loop's `stage:in-session`/operator-set `stage:done`, resolving
R1), S3 (the unit-parent-on-every-release rule). `agentplot/flywheel#92`
("Stage labels make per-item progress visible…", `closed:superseded`) carries
the full ruling narrative and cites `design/loop-programs.md` R1; it names
one release gate — "the exact stage names per loop and the consumer of each
filter" — settled by the milestone's items, which supersede it:

- #96 · "The bolt loop writes stage labels at the boundaries it drives"
- #97 · "Intent items carry in-session, done, collected — and the
  operator's stage:done flip is the completion signal"
- #98 · "Every release creates a unit parent, born-ready included"
- #99 · "bolt-direct: the fourth bolt type, no verify stage"
- #100 · unit parent for #96–#99, its sub-issues checking off at
  `stage:merged`

None of the five carries an assertion record file: no file under any
`openspec/changes/*/assertions/` in this tree references #96–#100, and each
item's own body is the assertion, `type:assertion` and `state:ready` on
#96–#99, `unit` on #100.

The milestone description names the suggested type — "Suggested type:
bolt-quick; the operator confirms the type before the crank turns" — and one
blocking condition, landing of `bolt/loop-server`, which is now satisfied:
`bolt/loop-server` is archived on `main`
(`openspec/changes/archive/2026-08-13-loop-server/`, commit `1056cec`),
shipped in release 0.10.0 (`b20a503`, "the loop programs and server ship,
the conductors retire"). The milestone description does not declare the
plan-mode path, so this record does not assume it.

## Repos

- agentplot/flywheel · bolt branch `bolt/stage-labels` · worktree
  `~/.herdr/worktrees/.bare/bolt-stage-labels`

Neither exists yet: `git branch -a` and `git worktree list` on this checkout
show no `bolt/stage-labels` branch and no `bolt-stage-labels` worktree as of
this scaffold. This repo is a bare checkout at `flywheel/.bare` with `main`
as a linked worktree (this session runs from `flywheel/main`), so herdr
names the repo `.bare` in the worktree layout — the same shape as this
repo's other bolts (`bolt-site-refresh`, `bolt-merge-gate-remedy`,
`bolt-loop-server`). The built repo and the org's tracker are the same
repository.

## Merge criteria

`bolt-quick` schedules no review step. What must hold before the bolt
branch lands on main, all against the tree that lands:

- The three `[pre-merge]` gates in this repo's `.config/wt.toml` green:
  `sh scripts/validate-manifests.sh`, `node scripts/check-paths.mjs`, `node
  scripts/check-site.mjs` — read from that file on `main` at scaffold time;
  `wt merge` runs them on the exact rebased tree, so the green is produced
  by the tool.
- The `stage:*` labels this bolt introduces exist on the tracker before any
  item carries one — `flywheel-setup`'s label convergence run clean against
  `agentplot/flywheel`. Checked at scaffold time: `gh api
  repos/agentplot/flywheel/labels` lists no `stage:*` label yet, and
  `bin/flywheel-setup`'s `ensure_labels` today defines only the `state:*`
  set.
- Whichever path an item takes — plan-mode, or a normal `/opsx:ff`
  spec-driven change landing in this repo's own `spec-driven`-schema change,
  beside this record and never inside it — the choice must be recorded on
  the milestone or an item before that item's build starts; this record
  makes no path assumption because none is declared yet.
- The full release gate at the landing: `wt merge` with full hooks, never
  weakened, one writer to main at a time.
