# Problems observed running the willdan fleet — 2026-08-31

One day of driving `bolt/switchboard-stage1` (WilldanGroup, tracker
`willdan-blueprints`, built repo `switchboard-kit`) through real
construction surfaced the problems below. Each entry is written to task
an agent: symptom, evidence, root cause where established, and the fix
shape. 1–15 are fixed on this repo's `main` (1 with an open residual:
guard-closed items skip the pane reaper); 16 is open. Running loops
pick fixes up on their next server respawn.

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
Extended by `f73f47c9`: the pane now closes at build-settle (the
session stays resumable by its deterministic id; `go_fix` and a red
merge gate resume it in a fresh pane), with the merge-site close kept
as the backstop reaper.
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

**Fixed:** `daddf6cd` — `agent start` gets the fleet driver's 300s
(`839387a2` had only reached `bin/flywheel`); not_ready and startup
timeout retry with backoff like pane_busy, with a roster check first
(an agent that came up behind a failed start is adopted, not
re-started); launch reuse is health-checked — a blocked pane that never
reached its composer is reaped and relaunched, one whose composer is
live is a real question and is reused. Pinned by
`LaunchRobustnessTest` / `ReuseHealthTest`.

### 4. The loop cannot seed workspace trust for new worktrees

**Symptom:** every fresh `build-<slug>` worktree path blocks Claude Code
at the trust dialog on first launch → `agent_blocked` /
`agent_not_ready` until a human seeds it. The operator's session
hand-seeded ~15 paths into `~/.claude.json`
(`projects.<path>.hasTrustDialogAccepted: true`) across the day; each
newly planned item re-created the problem (#66–#69 all failed their
first spec launch).

**Fixed:** `daddf6cd` — `seed_workspace_trust()` in
`_flywheel_sessions.py`, called by both the herdr and headless launch
paths with the spec's cwd: atomic read-modify-write of
`~/.claude.json`, idempotent, best-effort (an unwritable config just
means the dialog may appear). Pinned by `TrustSeedTest`.

### 5. Settle detection can fire while the session is still working

**Symptom:** `build-codebuild-fleet`'s branch was collected and merged
~25 minutes **before** the session printed its final report ("Sautéed
for 1h 3m"); the tracker item closed while the session went on to run
suites and report a finding. Later, the guard demoted the item because
the branch had "moved past" the merge.

**Root cause (probable):** the herdr wait reads `agent_status`, and a
momentary `idle` between turns reads as settled.

**Fixed:** `daddf6cd` — `HerdrRunner.wait` believes settled-done only
after it holds across three spaced roster reads (`settle_reads` /
`settle_gap_s`); blocked and gone still return on the first read.
Pinned by `SettleDebounceTest`. The artifact-witness half (a
done-marker the session writes) stays open as a possible second layer
for long-reporting sessions.

---

## Guard and tracker semantics

### 6. Stage derivation uses SHA ancestry; wt's rebase-merges break it

**Symptom:** guard writes like `#54 stage:merged -> stage:built
(re-derived from build/codebuild-fleet)` on items that were genuinely
merged — `git cherry` shows every branch commit patch-equivalent on the
bolt branch, but the SHAs were rewritten by the rebase, so
`merge-base --is-ancestor` says unmerged.

**Fixed:** `f73f47c9` defused the cause (the merge rebases the
feature, not the bolt branch; `--no-squash` lands commits as
themselves), and `2afb194e` closed the remainder: a green merge
records `refs/flywheel/merged/<branch>` (durable witness), and
`batch_merged` answers witness-first, then ancestry, then `git cherry`
patch-equivalence — all three callers inherit it.

### 7. An item carrying `needs-operator` can still be auto-closed

**Symptom:** #66 (`zudoku-portal-deployed`) was closed `closed:merged`
while it carried `needs-operator` and its build session had explicitly
held half the work on an andon. The operator had to reopen it.

**Fixed:** `2afb194e` — `close_merged` skips any item carrying
`needs-operator` or an unanswered andon, the same check the landing
already made. Pinned by `MergeCloseTest`'s needs-operator and andon
counter-cases.

### 8. Andons raised from built-repo worktrees never reach the tracker

**Symptom:** two build sessions raised well-formed andons
(`<!-- flywheel:andon -->` blocks) **in-pane only**; the items showed
nothing, so the operator discovered them by reading panes. One session
also reported it could not comment on its own item from the
switchboard-kit worktree.

**Fixed:** `2afb194e`, both halves — (a) `flywheel-setup --built-repo`
checks each built repo against the App installation and warns on a
miss; (b) `settle()` parses the andon marker out of the settled pane's
collect, posts the canonical `format_andon` to the item, and pauses
the batch — tracker-as-truth for idempotence, so an already-posted or
operator-ANSWERED andon in scrollback never re-posts or re-pauses. The
construction profile now says the report marker counts.

### 9. Batch dependencies are snapshotted at cycle start

**Symptom:** #67 closed mid-cycle; #68/#69 (`after: 1` on it) still
waited out the rest of that cycle plus the whole next planning pass.

**Fixed:** `16962147` — every merged batch re-splits the held set
against a fresh snapshot (`release_after`) and appends the released
batches to the same drive; the sibling runs in the cycle its blocker
merges. Pinned by
`test_a_mid_cycle_merge_releases_a_held_after_sibling_same_cycle`.

---

## Fleet and setup

### 10. Per-org credentials live only under `dispatch.env`

**Symptom:** `bin/flywheel-token` defaults to the agentplot app; the
willdan bolt planner had to read `fleet.yaml`'s `dispatch.env` block to
find `FLYWHEEL_GH_APP_ID=4562912` / the pem path. Every non-dispatch
actor repeats this.

**Fixed:** `29474f2f` — fleet.yaml's top-level `credentials:` block,
exported by the server at the socket seam (daemon + loop processes +
in-process tracker calls) and written to
`~/.config/flywheel/orgs/<org>.env`, which `flywheel-token --org`
sources as an overlay — a session in any worktree mints the right
org's token. **Operator action:** move willdan's `FLYWHEEL_GH_*` out
of `dispatch.env` into `credentials:` and restart the fleet.

### 11. `flywheel-setup` doesn't converge Project views

**Symptom:** the willdan Flywheel Project (#2) had converged fields but
a single default table view; the operator couldn't see the board. The
GraphQL API now has `createProjectV2View` / `updateProjectV2View`
(create takes name+layout, filter lands via update) — the willdan board
was converged by API today: Kanban (board), Roadmap (roadmap), Triage /
Waiting On Me / In Flight / Landed / Bolt Unit Tracker / Intent
Elaboration Tracker (tables), filters copied from the agentplot
template project.

**Fixed:** `29474f2f` — `ensure_views` converges the project's views
on the template's set by name (create by name+layout, converge
filters; layouts/renames left to the operator), on both the
fresh-copy and pre-existing paths; mutation shapes verified against
the live schema and the board-surface spec amended. The
`linkProjectV2ToRepository` permission gap was already a documented
soft-skip in `ensure_link`; the one manual click stands documented.

### 12. Backlog batches aren't delivered to dispatch

The drafted issue body exists in the willdan operator session's
scratchpad (`backlog-nudge-issue.md`): plan cards parked at Backlog
never surface in a round unless the operator notices them.

**Fixed:** `1b406685` — `dispatch_inbox` gains a `round` queue (the
same Backlog predicate as `round_inbox`), the server pokes dispatch on
it with the standard dedupe, and the plan surface renders derived
Backlog rows as an **approvals** container: grouped by milestone with
a set-all per group, routed `leave | ready | drop`, seeded `leave` —
`ready` flips the board, `drop` closes `closed:declined` for good.
The full trigger map is `design/dispatch-flow.md`.
**Residual (found on live repair, 2026-09-01):** every open willdan
elaboration parent (#13/#27/#47/#72/#74) sat at **no board Status at
all** — never placed at Backlog by whoever filed it — and a
no-Status parent is invisible to the Backlog predicate, exactly as
invisible as before the fix. Repaired by hand (`flywheel-board
--status Backlog`). Fix shape: a guard that puts an open
elaboration/unit parent with no board Status at Backlog, so a missed
board write degrades to a one-pass delay instead of a silent stall.

### 13. Server restarts strand `stage:in-session` ghosts

**Symptom:** loops killed mid-charge leave items marked in-session that
no session owns; the operator reset #24/#25 by hand early in the day.

**Fixed:** `16962147` — `resume_in_session` runs before collection on
every intent-loop cycle: an open item at in-progress + in-session
whose dispatch-marker session is GONE from the roster is reset to
ready (stage dropped, comment says why); the next cycle redispatches,
resuming the conversation by its deterministic id. Live sessions and
operator-touched items are left alone.

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
  truncated form the roster actually carries. `f73f47c9` replaced the
  bolt loop's lossy right-cut with a digest tail, so two long slugs
  sharing a prefix can no longer collapse into one name.

### 14. Backoff holds outlive the operator's unpause

**Symptom:** after the operator repaired a paused batch (labels cleared,
branch merged by hand), the four affected panes sat idle for minutes —
the server was `holding 55s/119s — it exited with the tracker unchanged`
from the *previous* run and could not see that the tracker had changed.

**Fixed:** `16962147` — the hold's fingerprint is the job reason PLUS
a milestone tracker digest (item number/state/labels + board status)
from the snapshot the pass already holds; an operator repair the
reason string cannot see releases the hold next pass. The planner
hold is fingerprinted over its cards' number/status/staleness the same
way.

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

**Fixed:** `f73f47c9` — `merge_stage` runs `wt merge <bolt-branch>
--no-squash --no-remove` from the build worktree: the feature is what
gets rebased, the bolt branch is append-only, the conflict aborts moved
with it, and `--no-squash` lands branch commits as themselves — which
is what makes problem 6's ancestry checks sound again. `--no-remove`
stays because the guard still re-derives stages from the `build/<slug>`
branch. The construction skill had documented this direction all along;
the code now matches it.

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
