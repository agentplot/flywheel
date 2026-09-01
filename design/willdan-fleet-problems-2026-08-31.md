# Problems observed running the willdan fleet — 2026-08-31

One day of driving `bolt/switchboard-stage1` (WilldanGroup, tracker
`willdan-blueprints`, built repo `switchboard-kit`) through real
construction surfaced the problems below. Each entry is written to task
an agent: symptom, evidence, root cause where established, and the fix
shape. Two are already fixed on this repo's `main`; the rest are open.

The operating context that shaped all of them: the org uses per-unit
`Type: bolt-direct` (no verify stage), `wt merge` (worktrunk) as the
merge engine — which **rebases before it merges** — and herdr panes as
the session runner. Loops are stateless processes the server respawns;
a respawned loop holds no launch handles from its predecessor.

---

## Fixed on main (verify, then close out)

### 1. Build panes leaked — no close site on bolt-direct, and handles die with the loop

**Symptom:** finished build sessions accumulated as open herdr panes all
day; the operator repeatedly asked why "done" sessions were still there.

**Root cause (two halves):** `runner.close(handle)` was called only in
`verify_stage`, and `bolt-direct` declares `stages: [spec, build, merge,
land]` — no verify, so no close site ever ran. Independently, `close`
needs the launch handle (`handle.ref["tab_id"]`), which only the process
that launched the pane holds — every server respawn orphaned the
predecessor's panes even on types with verify.

**Fixed:** `3b6b676a` — `close_named()` on the runners (reap by the
deterministic session name, guarded against still-working panes) and
`close_build_pane()` called at the three verify sites **and after every
landed merge**. Pinned by
`test_a_bolt_direct_merge_reaps_the_build_pane`. First live proof: the
respawned loop reaped `build-appsync-api-stack` at its merge.
**Residual:** the guard can close an item before its batch is driven
(stage re-derived from a hand-merged branch); those paths skip every
close site, so guard-closed items still leak their panes — reap on
guard-close too.

### 2. Merge-conflict handling stranded the bolt worktree mid-rebase

**Symptom:** one merge conflict cascaded into a paused cycle: every
subsequent batch's merge red-gated with `Cannot merge: not on a branch
(detached HEAD)`. Happened **three times in one day** (zudoku,
connection-template, swb-dagger conflicts).

**Root cause:** `merge_stage`'s conflict path ran `git merge --abort`,
but `wt merge` fails mid-**rebase** — the abort was a no-op and the
worktree stayed detached mid-rebase.

**Fixed:** `36f70715` — abort the rebase too (both aborts are no-ops
when their operation is not in progress). Note the running loop only
picks this up on respawn; until then the operator repairs by hand
(`git rebase --abort` in the bolt worktree).

---

## Open — launch and session lifecycle

### 3. Transient launch failures cost a full cycle and are never retried

**Symptom:** repeatedly, one per cycle:

- `agent_not_ready — blocked during startup` (herdr pane exists or is
  mid-startup)
- `agent_pane_busy — target pane w1:p4N is not an available shell`
- `timeout — timed out waiting for agent startup`
- `agent_blocked — requires interactive input` on a `prompt` to a
  same-name pane left over from an earlier failed launch

Each failure marks the stage `failed` and the batch waits a whole cycle
(and the next cycle often hits a different transient).

**Fix shape:** retry with backoff inside the launch path; on
`agent_not_ready`/`pane_busy` for a pane bearing the target session
name, adopt or close-and-relaunch that pane rather than erroring. The
deterministic session id makes relaunch safe — `go_fix` already relies
on exactly that.

### 4. The loop cannot seed workspace trust for new worktrees

**Symptom:** every fresh `build-<slug>` worktree path blocks Claude Code
at the trust dialog on first launch → `agent_blocked` /
`agent_not_ready` until a human seeds it. The operator's session
hand-seeded ~15 paths into `~/.claude.json`
(`projects.<path>.hasTrustDialogAccepted: true`) across the day; each
newly planned item re-created the problem (#66–#69 all failed their
first spec launch).

**Fix shape:** before launching into a worktree, the loop (or the
launcher in `_flywheel_sessions.py`) writes `hasTrustDialogAccepted`
for that path. Do it at worktree creation time, in one place.

### 5. Settle detection can fire while the session is still working

**Symptom:** `build-codebuild-fleet`'s branch was collected and merged
~25 minutes **before** the session printed its final report ("Sautéed
for 1h 3m"); the tracker item closed while the session went on to run
suites and report a finding. Later, the guard demoted the item because
the branch had "moved past" the merge.

**Root cause (probable):** the herdr wait reads `agent_status`, and a
momentary `idle` between turns reads as settled.

**Fix shape:** settle on an artifact the session writes when actually
done (the report/marker comment pattern already exists —
`<!-- flywheel:session ... -->`), or require N consecutive idle reads,
or both. The pane status is a hint, not a verdict.

---

## Open — guard and tracker semantics

### 6. Stage derivation uses SHA ancestry; wt's rebase-merges break it

**Symptom:** guard writes like `#54 stage:merged -> stage:built
(re-derived from build/codebuild-fleet)` on items that were genuinely
merged — `git cherry` shows every branch commit patch-equivalent on the
bolt branch, but the SHAs were rewritten by the rebase, so
`merge-base --is-ancestor` says unmerged.

**Fix shape:** derive merged-ness by patch-id (`git cherry` /
`git patch-id`) or by the recorded merge evidence, not raw ancestry.

### 7. An item carrying `needs-operator` can still be auto-closed

**Symptom:** #66 (`zudoku-portal-deployed`) was closed `closed:merged`
while it carried `needs-operator` and its build session had explicitly
held half the work on an andon. The operator had to reopen it.

**Fix shape:** `needs-operator` (and an unanswered andon) must block
close/merge bookkeeping for that item, full stop.

### 8. Andons raised from built-repo worktrees never reach the tracker

**Symptom:** two build sessions raised well-formed andons
(`<!-- flywheel:andon -->` blocks) **in-pane only**; the items showed
nothing, so the operator discovered them by reading panes. One session
also reported it could not comment on its own item from the
switchboard-kit worktree.

**Two halves:** (a) org App installations must include every built repo
(operator action, but `flywheel-setup` could verify and warn); (b) the
loop should collect an andon block from a settled session's output and
post it to the item itself — the session should not need tracker access
for its andon to count.

### 9. Batch dependencies are snapshotted at cycle start

**Symptom:** #67 closed mid-cycle; #68/#69 (`after: 1` on it) still
waited out the rest of that cycle plus the whole next planning pass.

**Fix shape:** re-evaluate `after:` gates when a batch completes within
the cycle, or at least at merge bookkeeping time.

---

## Open — fleet and setup

### 10. Per-org credentials live only under `dispatch.env`

**Symptom:** `bin/flywheel-token` defaults to the agentplot app; the
willdan bolt planner had to read `fleet.yaml`'s `dispatch.env` block to
find `FLYWHEEL_GH_APP_ID=4562912` / the pem path. Every non-dispatch
actor repeats this.

**Fix shape:** hoist credentials to a fleet-level block (`fleet.env` or
per-org `credentials:`), resolved by every actor the manifest launches.

### 11. `flywheel-setup` doesn't converge Project views

**Symptom:** the willdan Flywheel Project (#2) had converged fields but
a single default table view; the operator couldn't see the board. The
GraphQL API now has `createProjectV2View` / `updateProjectV2View`
(create takes name+layout, filter lands via update) — the willdan board
was converged by API today: Kanban (board), Roadmap (roadmap), Triage /
Waiting On Me / In Flight / Landed / Bolt Unit Tracker / Intent
Elaboration Tracker (tables), filters copied from the agentplot
template project.

**Fix shape:** add view convergence to `flywheel-setup` using the
template project's view set as the source of truth. Also:
`linkProjectV2ToRepository` needs a permission the App lacks
(`Resource not accessible by integration`) — either add the permission
to the App manifest or document the one manual click.

### 12. Backlog batches aren't delivered to dispatch

The drafted issue body exists in the willdan operator session's
scratchpad (`backlog-nudge-issue.md`): plan cards parked at Backlog
never surface in a round unless the operator notices them.

### 13. Server restarts strand `stage:in-session` ghosts

**Symptom:** loops killed mid-charge leave items marked in-session that
no session owns; the operator reset #24/#25 by hand early in the day.

**Fix shape:** on loop start, re-derive in-session items against the
live roster; re-charge or reset stale ones.

---

## Environment notes that interacted with all of the above

- **prek** (`j178/prek#1672`): `prek install` bakes the installing
  worktree's absolute `--config` path into the shared
  `.bare/hooks/pre-commit`, breaking commits from every other worktree
  ("failed to create walker: path not inside the tree root"). Fleet-side
  workaround landed in switchboard-kit's `devenv.nix` enterShell (rewrite
  to `--config="$(git rev-parse --show-toplevel)/..."` on every
  activation). A flywheel-side sanity check before merge bookkeeping
  would have named the cause instead of "gate red after refix" ×N.
- **Session-name truncation:** herdr names truncate
  (`spec-writing-zudoku-portal-deplo`, `build-switchboard-edge-through-f`)
  — harmless today, but name-based reaping (fix 1) must match on the
  truncated form the roster actually carries.

### 14. Backoff holds outlive the operator's unpause

**Symptom:** after the operator repaired a paused batch (labels cleared,
branch merged by hand), the four affected panes sat idle for minutes —
the server was `holding 55s/119s — it exited with the tracker unchanged`
from the *previous* run and could not see that the tracker had changed.

**Fix shape:** the hold's purpose is to avoid re-driving unchanged
paused work, so key it to tracker state: re-snapshot before honoring a
hold, or clear the hold when the snapshot differs from the one the held
run exited on (cheap: compare the needs-operator set and updated-at
cursors).

### 15. The loop runs `wt merge` in the inverted direction

**Symptom (umbrella for 2 and 6):** the bolt branch's history is
rewritten at every landing (the same devenv commit existed as a6bae91,
74a0001, 74420d8 across the day), rebases grow with the branch (29
picks) and emit "skipped previously applied commit", merge conflicts
strand the shared bolt worktree rather than the one feature branch, and
in-flight sibling branches — never restacked — all conflict at their own
merge.

**Root cause:** `wt merge`'s contract is "merge *current* branch into
TARGET — squash & rebase, fast-forward the target", designed to run from
the feature worktree with the integration branch as target. `merge_stage`
runs `wt merge build/<slug> --no-remove` **from the bolt worktree**, so
wt rebases the bolt branch onto the build branch — the integration line
is the thing rewritten, every time.

**Fix shape:** run the merge from the build worktree with the bolt
branch as TARGET (`cwd=build worktree, wt merge <bolt-branch>`), so the
feature is what gets rebased and the bolt branch is append-only. That
also makes problem 6's ancestry checks sound again and confines a
conflict strand to the feature worktree. Decide squash policy explicitly
(`--no-squash` to keep per-commit history).

### 16. Batches for never-specced items claim spec=done, build=done, then fail merges silently

**Symptom:** #56 (`catalog-index`) and #57 (`closer-reference-first-build`)
have no change directory in any worktree and no `build/<slug>` branch —
yet their batches logged `spec · done · the change already validates —
nothing to spec`, `build · done · settled` / `already built — the tree
proves it`, then `merge · paused · merge conflict` — and **no tracker
write of any kind landed on either item** (no pause comment, no
needs-operator, no session comment).

**Evidence against the obvious cause:** `openspec validate catalog-index
--strict` exits 1 ("Unknown item") in the bolt worktree, in a fresh
build worktree base, and in the blueprints repo-dir — every cwd
`change_validates` (bin/_flywheel_bolt_loop.py:1171) could plausibly use.
So the short-circuit at :2224 fired on something else — suspects: the
loop's `shell()` failing in a way that reads as returncode 0 in its
environment, or batch.change resolving to a different name than the
item's `Change:` line. The silent pauses (no comment/label) suggest the
same write path failed too.

**Why it matters:** a ready item can sit forever "in progress" with the
loop believing it is built, while nothing was ever created — invisible
unless someone greps branches.

**Fix shape:** reproduce with the loop's own environment; make
`change_validates` fail closed only on a *validated* change (distinguish
"invalid" from "unknown"/command failure); make `pause()` failures loud;
assert a `build/<slug>` branch exists before `build=done` can be claimed.
