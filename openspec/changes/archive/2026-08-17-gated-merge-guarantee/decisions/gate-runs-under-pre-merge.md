# Decision: the merge gate runs under `[pre-merge]`, alone

- **Closes:** #14 · **Question record:**
  `../questions/fast-forward-gate-hole.md`
- **Decided by:** the operator, 2026-08-12, annotating
  `../sessions/2026-08-12-gate-remedy/draft-ff-gate-remedy.md` in a
  plannotator round.
- **Evidence behind the option set:**
  `../sessions/2026-08-12-ff-gate-facts/finding.md` — authoritative here is
  the decision; the measurements are provisional and cited to that finding.

## The decision

1. **The repo's three checks — `manifests`, `paths`, `site` — move from
   `[pre-commit]` to `[pre-merge]`, alone.** `[pre-commit]` keeps no copy.
   `[pre-merge]` hooks run on every shape of `wt merge` — the clean
   fast-forward included — after the rebase, in the source worktree, with
   `HEAD` equal to the sha that lands, and a failure aborts with nothing
   landed. That is the tree the loop's guarantee is about, and one table
   means one copy of each command: nothing to drift, one grant per template.

2. **No standing explicit gate step.** `wt merge` aborting on failure *is*
   the gate once `[pre-merge]` exists. The reference's retry path after a
   gate failure — the worktree's agent fixes and re-runs
   `wt hook pre-merge`, then the conductor merges again — stays, and becomes
   genuinely functional with this decision (today it prints
   `No pre-merge hooks configured` and exits 0).

3. **New worktrees are warmed by a `[post-start]` hook running
   `wt step copy-ignored`** — worktrunk's eliminate-cold-starts pattern,
   copying gitignored files (`node_modules`, caches) from an existing
   worktree — rather than a fresh `npm ci`. Worktrees cut with
   `wt switch --create` get it automatically; herdr-created worktrees fire
   no `wt` lifecycle hooks, and the reference's existing instruction to run
   `wt -C <path> hook post-start` after creating one covers them with the
   same hook.

## What was declined, and why

- **Both tables** (the same commands under `[pre-commit]` and `[pre-merge]`)
  bought only an earlier failure on the rare shapes where `wt` itself writes
  a commit, at the cost of a second copy that can drift — and a drifted copy
  re-keys its approval while the other keeps the old grant.
- **A routine explicit `wt hook pre-merge` before every merge** would run
  the checks twice on every shape and reintroduce a conductor-asserted
  green beside the tool-produced one.
- **A fresh `npm ci` in `post-start`** pays an install per worktree that a
  copy avoids.
- `ff = false`, an upstream fix, and `verify` as a selector were already
  dead on the lab's evidence and were not re-litigated.

## Residuals, named

- `wt step copy-ignored` carries what the source worktree has. A machine
  whose primary checkout lacks `node_modules` still surfaces
  `scripts/check-site.mjs` exiting 2 (`jsdom not installed`) — fail closed,
  remedied by one `npm ci` in the primary checkout.
- The `[post-start]` hook is a fourth template needing approval; it joins
  the grant that `approvals-are-an-onboarding-grant.md` settles.

## Consequences

- **#34** — the `.config/wt.toml` edit: the table move, the `[post-start]`
  hook, and the rewrite of the head comment block (wrong in two places:
  "during `wt merge` before the commit, on the exact tree that lands", and
  "All four are independent" over three checks).
- **#35** — the `skills/_reference/herdr.md` corrections, in the same pass
  as #34: the "runs the repo's `.config/wt.toml` checks on the exact
  rebased tree that lands" claim rewritten to name the `[pre-merge]`
  mechanism, and the `wt hook pre-merge` retry instruction kept.
- **Ordering:** #34 must not land before #33 (the operator's approvals
  grant). The first `[pre-merge]` configuration is the first thing that
  ever demands an approval here, and unapproved hooks abort every merge.
