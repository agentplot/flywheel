# Bolt: teardown-rings-the-bell

## Scope

When a loop closes a supervised session's pane through teardown, the pane
closes the moment the work settles — ahead of the herdr bell that would
have told the operator, so the completion is lost. This bolt makes
teardown emit a herdr notification instead, naming the session and what
it settled as, before the pane closes, so the completion still reaches
the operator. The seam is `HerdrRunner.close` in
`bin/_flywheel_sessions.py`: every supervised session either loop runs
closes through it, so one change covers both. The pane-keeping branch
already documented on that method — a session the loop will re-prompt
keeps its pane — is not a teardown and must not notify. The milestone
prices this at one change, spec + build + verify, so this record does not
assume the plan-mode path.

## Sources

No source intent. The milestone (`bolt/teardown-rings-the-bell`, #24) and
its unit parent (#236, "Unit: teardown-rings-the-bell") and sole item
(#234, "the-teardown-notification") were each milestoned straight to
`bolt/teardown-rings-the-bell` on creation, 2026-08-17T20:14 — verified
against each issue's tracker timeline: one `milestoned` event apiece,
both to this milestone, no prior `intent/*` milestone. #234 carries no
assertion-record pointer to any `openspec/changes/*/assertions/` file in
this tree; its own issue body is the claim, the no-intent quick-bolt
shape `skills/_reference/tracker.md`'s "quick bolt" section describes.
#236's body — "Released at triage on the operator's word — this unit is
born approved" — confirms a triage release rather than an intent
handoff. #234's one comment records the operator's framing at triage and
the triage-time verification of the mechanism (`HerdrRunner.close` emits
no notification today; herdr's `notification show` command exists to
call).

## Repos

- agentplot/flywheel · bolt branch `bolt/teardown-rings-the-bell` ·
  worktree `/Users/chuck/Code/github_agentplot/flywheel/.bare.bolt-teardown-rings-the-bell`

Neither exists yet: `git branch -a` and `git worktree list` from this
checkout (git-common-dir `/Users/chuck/Code/github_agentplot/flywheel/.bare`)
show no `bolt/teardown-rings-the-bell` branch or worktree as of this
scaffold. This repo's other live bolts are cut the same way — sibling
`.bare.bolt-<slug>` worktrees beside `main` (`.bare.bolt-flywheel-plugin`,
`.bare.bolt-matches-the-book`, `.bare.bolt-sandbox-loop`, and four more,
present on disk at scaffold time) — rather than under
`~/.herdr/worktrees/`, which on this host holds a different repo's bolts
(`~/.herdr/worktrees/.bare/bolt-plugin-shape` resolves, via `git
remote -v`, to `willdan-blueprints`, not this repo). The built repo and
the org's tracker are the same repository: `agentplot/flywheel`, per the
org `fleet.yaml`'s `tracker:` line.

## Merge criteria

`bolt-quick` schedules no review step (`schemas/bolt-quick/schema.yaml`:
`extensions: []`). What must hold before the bolt branch lands on `main`,
checked against this repo's `.config/wt.toml` on `main` at scaffold time:

- The three `[pre-merge]` hooks green on the tree that lands:
  `sh scripts/validate-manifests.sh`, `node scripts/check-paths.mjs`,
  `node scripts/check-site.mjs`.
- The milestone's own price — spec + build + verify — holds for #234;
  the plan-mode path is not declared and this record does not assume it.
- The full release gate at the landing: `wt merge` with full hooks,
  never weakened, one writer to `main` at a time.
