# Bolt: site-five-beats

## Scope

This bolt rebuilds the flywheel Pages site (`site/`, this repo) to the
five-beat teaching order intent/site-teaches-the-system settled: a
split-hero home page for the stranger (`site/index.html`), an
`overview.html` carrying the operator reference the home page sheds, and
three scrollytelling concept-tour pages — export backoff, onboarding
email order, dashboard dark theme — each one idea walked end to end.
Three units, five changes, one repo (agentplot/flywheel);
`scripts/check-site.mjs` stays green at every merge. This bolt takes the
plan-mode path `bolt-quick` makes available (`schemas/bolt-quick/schema.yaml`
marks `plan_mode` available on this type and no other, and a bolt opts in
through its milestone description, which this one does): no spec stage
runs — each unit binds straight to a plan-mode build, and the unit card
the operator approves, with its cited sources, is the plan.

## Sources

- intent/site-teaches-the-system — the milestone description states this
  bolt rebuilds the site to the teaching order this intent settled. Its
  three approved unit cards (#324 `home-page-five-beats`, #325
  `overview-reference-page`, #326 `concept-tour-pages`) each cite
  `openspec/changes/site-teaches-the-system/decisions/page-teaching-order.md`,
  `.../decisions/coupling-word.md`, and session artifacts under
  `sessions/2026-08-18-beats-and-tour/`, and each is marked "Derived
  from: session artifacts @ faedc0a." Verified on this tree:
  `page-teaching-order.md` is present at that path on `main` today, still
  in its pre-amendment wording ("the gate", "one word releases a whole
  batch" — `decisions/coupling-word.md`'s consequence 1 amends beat 4 to
  "Your approval — and how little it costs," not yet applied here).
  `coupling-word.md` is not on `main` at all: commit `faedc0a` (which adds
  it) sits on branch `sess/planning-site-teaches-the-system`
  (`git branch -a --contains faedc0a`), and `git merge-base
  --is-ancestor faedc0a HEAD` against this tree's `main` returns false.
  The unit cards were approved citing that commit's artifacts ahead of
  the record itself reaching `main` — construction sessions on this bolt
  read the cited files from the tree at build time, not from this note.

## Repos

- agentplot/flywheel · bolt branch `bolt/site-five-beats` · worktree
  `/Users/chuck/Code/github_agentplot/flywheel/.bare.bolt-site-five-beats`.
  Neither exists yet — `git worktree list` on this tree shows no entry
  for this slug; the path follows the `.bare.bolt-<slug>` pattern every
  other live bolt worktree in that listing uses. Cutting it is the loop's
  to do after this record is settled.

## Merge criteria

All three of this repo's pre-merge checks run automatically on every
merge to the bolt branch — `sh scripts/validate-manifests.sh`, `node
scripts/check-paths.mjs`, `node scripts/check-site.mjs` — wired as
`.config/wt.toml`'s `[pre-merge]` hooks and mirrored in
`.github/workflows/gates.yml` and the `devenv shell -- gates` command
(verified: `.config/wt.toml` lines 45-48; `AGENTS.md` "Gates" section).
This bolt's own charter names `scripts/check-site.mjs` specifically
because every change here touches `site/`; the other two apply
unconditionally to any change in this repo. `schemas/bolt-quick/schema.yaml`
declares `extensions: []` for this type, so no review step is scheduled
beyond that check — the check itself is always implied here and never
weakened. Beyond the automatic check, this bolt sets no further
suite: `scripts/check-site.mjs` is the one merge criterion the milestone
names, and it stays green at every merge as its own condition, not as a
review gloss on top of the check.

The coupling this bolt builds toward is named "approval" throughout —
never "gate," never "release," outside a quoted literal like the command
name above (`decisions/coupling-word.md`, cited in Sources).

Landing: merge
