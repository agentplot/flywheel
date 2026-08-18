# Bolt: records-and-elaborations

## Scope

Two capabilities the operator gains once this bolt lands. First, a
system's whole design — chapters, an intent's questions and decisions,
and the charter and unit documents of every bolt cut from it — lives in
one repo and one history: the loops write their records onto the book
repo's main as the work happens, and the built repo holds only its own
construction changes and implemented specs, so a reader no longer
crosses repositories to find out why a change exists
(`a-systems-design-in-one-repo`, 2 changes, sequence 1 of 2). Second, a
design batch is ruled on two gestures made on the elaboration itself —
approving it to Ready and later marking it done — rather than on each
of its items in turn, so the loop collects the whole set on the second
gesture instead of the operator closing items one at a time
(`ruling-a-design-batch-once`, 2 changes, sequence 2 of 2, builds on the
first unit). Price: 4 changes, ~4 days.

## Sources

- intent-flywheel (agentplot/blueprints) — both units' cards carry
  "System: flywheel" and the milestone's own "Derived from: book
  52fafa6 · specs 6430df8" line. Verified: `52fafa6` is a
  `book(flywheel)` commit on blueprints' `main`
  (`git -C blueprints/main log -1 52fafa6`), and `6430df8` is a
  `chore(openspec)` commit on this repo's `main`
  (`git -C flywheel/main log -1 6430df8`); both are ancestors of their
  repo's current tip. I searched `intent-flywheel/tasks.md` in
  blueprints for either unit's slug and for this bolt's name and found
  no handoff task line naming them — the milestone reads as planned
  straight from the book-and-specs gap rather than routed through an
  enumerated task, so this entry names the intent, not a task.

## Repos

- agentplot/flywheel · bolt branch `bolt/records-and-elaborations` ·
  worktree `/Users/chuck/Code/github_agentplot/flywheel/.bare.bolt-records-and-elaborations`.
  Neither the branch nor the worktree exists yet — I checked
  `git worktree list` on this tree and found none for this slug; the
  path follows the `.bare.bolt-<slug>` pattern every other live bolt
  worktree in that listing uses, and cutting it is the loop's to do
  after this record is settled, not mine.

## Merge criteria

`devenv shell -- gates` green on the bolt branch as it would land —
rebased onto (or merged with) current main, not only in isolation. I
read `AGENTS.md` and `.config/wt.toml` on this tree: that command runs
the same three checks as `.config/wt.toml`'s `[pre-merge]` hooks
(`scripts/validate-manifests.sh`, `scripts/check-paths.mjs`,
`scripts/check-site.mjs`) and `.github/workflows/gates.yml`, so a green
claim means the same thing in all three places. This bolt is bound to
the `bolt-quick` schema, whose `schemas/bolt-quick/schema.yaml` declares
`extensions: []` — no review step is scheduled beyond that gate. The
merge gate itself — `wt merge` and the repo's hooks — is always implied
and never weakened.

Landing: merge
