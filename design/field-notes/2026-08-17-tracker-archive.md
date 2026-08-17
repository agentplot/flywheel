# Tracker archive — 2026-08-17

The operator reset the tracker after the first extended live fire of the
flywheel on its own repo. Every open issue (104 of 211) and every open
milestone was closed on this date; this file is the digest that licensed
the close. Closed issues remain readable on GitHub — nothing was
deleted — but nothing on the tracker is live work anymore.

Why: running the machinery on itself filled its own bus with findings
about the machinery, until work items and evaluation output were
indistinguishable. The replacement discipline is in
`design/observer.md`: the machinery never files issues about itself;
loop runs are judged through observer reports.

What survives in git regardless of this archive: the openspec change
directories (`decisions/`, `assertions/`, `questions/`, `sessions/`),
every landed commit, and the plugin releases 0.10.1-0.11.0.

## The backlog that lives only here now

The bolded **worth keeping** rows in the milestone tables below are
substance that existed nowhere but the tracker. Thematically:

- **Live bugs in the machinery** — #86 (gh() sys.exit kills the
  daemon), #91 (parent_batch never filled; every item reads as orphan),
  #152 (closed blockers block forever), #61 (empty token posts as the
  operator — the big one), #126 (release bumps plugin.json not
  marketplace.json; gate red on main every release), #78 (openspec
  fork erases loop: blocks), #80 (install-schemas never prunes), #57
  (nothing gates direct commits to main), #170 (no pane reaper), #174
  (no batch ordering/provenance), #177 (session-born items skip the
  operator), #203 (emptied handoff still charges a session), #52, #58.
- **Test and eval infrastructure** — #171 (full-loop eval against
  fixture-tracker JSON; would have caught most of the week's live
  defects), #83 (wire the suite into merge gate and CI), #103 (one
  unit test spawns a real herdr session), #95/#93/#79 (conductor-era
  evals and specs never re-cast).
- **Settled but unbuilt** — the work-object landing pass (#30/#31/#32,
  gated by sequencing call #20); the loops-run-unattended decisions
  #208-#211 (records in git, code unbuilt); #62 (move a measured fact
  into a durable question record).
- **Operator rulings not yet in the instructions** — #202/#206 (repo
  work is type:assertion, never type:build; dispatch stops using
  type:build), #63 (permission prompts never batch-approved), #71 (the
  operator's nested-round design that kills idle top-tier panes), #69
  (price the ceremony: model tiers per role).
- **Untouched threads** — board-views-ux (#184-#193, with #193's
  measured board-blindness evidence), prior-art-import (#195-#199),
  onboarding-first-run (#179-#183), plus doc-drift items on
  machinery-self-desc (#50-#84 range, see table).

Everything else below is landed, settled with a git-side record,
superseded, or noise.


## intent/prior-art-import

Freshly opened intent (2026-08-14) on importing the kb-spike corpus (`WilldanGroup/knowledgebase-spike`) into the flywheel process: inventory the ~105-file corpus, then settle four decisions (cross-org landing, what carries an import, the reverse-engineer lane, bulk dispatch triage). Nothing was ever worked — every item is still `state:queued`. Archiving loses the entire thread; no prose exists in git for it.

| # | title | disposition |
|---|---|---|
| **195** | **Inventory the kb-spike corpus and cut it into discard / reverse-engineer / load** | **worth keeping** — body carries a real, dated survey of the corpus (SPIKE.md structure, 11 HTML reports, no workplan.md exists) that blocks the other four items. |
| **196** | **Decide where imported work lands when the source repo is in another org** | **worth keeping** — the fork (source-org tracker vs importing-org tracker vs staging) gates both import lanes and is nowhere else recorded. |
| **197** | **Decide what carries an import: skill, session type, tool, or nothing durable** | **worth keeping** — the mechanical-vs-judgment boundary question, unanswered. |
| **198** | **Decide the reverse-engineer lane: OpenSpec into a repo with no flywheel** | **worth keeping** — no path exists today for specs to land in kb-spike; also asks whether the lane is really "discard". |
| **199** | **Decide how dispatch triages an imported roadmap in bulk** | **worth keeping** — bulk dedupe/collision/provenance questions distinct from one-at-a-time triage. |
| 201 | Work the queued design items on prior-art-import | noise (elaboration container) |

## intent/onboarding-first-run

Second untouched intent (2026-08-14): make flywheel learnable — two tour mockups, a quickstart, a site restructure, and a decision on flywheel's own design book. All still queued; the only activity is a cross-reference noting the quickstart must address (or exclude) the prior-art-import path.

| # | title | disposition |
|---|---|---|
| **179** | **Mock up the concept tour: how flywheel works, walked not described** | **worth keeping** — half of the planned site tour section, never started. |
| **180** | **Mock up the operator tour: what to type, where, what to expect back** | **worth keeping** — the other tour half. |
| **181** | **Restructure the site: nav tabs below the fold, too much detail for home** | **worth keeping** — operator's concrete layout complaint + proposal (few top-level sections, detail under Overview). |
| **182** | **Decide the quickstart: shortest honest path from install to first crank turn** | **worth keeping** — plus the comment linking it to the import lane for users arriving with an existing corpus. |
| **183** | **Decide flywheel's own design book: where it lives, what writes into it** | **worth keeping** — flywheel runs writeback for others but captures none of its own design; may belong to machinery-self-desc. |
| 185 | Work the queued design items on onboarding-first-run | noise (elaboration container) |

## intent/relay-delivery

The operator-signal lifecycle thread: four defects in `needs-operator` (undeliverable relay invisible #43, delivered relay re-nudged #45, escalation silently cleared #159, answered andon never retired #166). #159 and #166 were fixed and shipped (plugin 0.10.12, commit 7248857). #43/#45 remain open with their questions recorded in git (`openspec/changes/relay-delivery/questions/`) but the decision never made; the tracker holds hard measurements not in git. #51 and #68 describe conductor-era behavior the loop-server rewrite overtook.

| # | title | disposition |
|---|---|---|
| **43** | **A relay dispatch cannot deliver is visible, not silent** | **worth keeping** — open decision (where undeliverability surfaces); question prose is in git but the call was never made. |
| **45** | **reconcile re-nudges dispatch for a relay already delivered** | **worth keeping** — open decision with tracker-only evidence: 10/14 dispatch turns no-op one day, 5 identical re-nudges 08-14→16, plus the "question vs operator-executed task" distinction. |
| 46 | Settle how the loop knows a relay was delivered | noise (elaboration container for #43/#45) |
| 51 | reconcile re-nudges settled conductor for Ready unit | superseded — flip-consume-on-QUERY was built into the loop programs (#72/#76) |
| 68 | One run lineage per bolt: resume, not rebuild | superseded — conductor-rulings-end-runs premise retired by the loop-server rewrite |
| 104 | Work the queued design items on relay-delivery | noise (elaboration container) |
| 159 | Settling session silently clears needs-operator it did not set | landed — fixed 0.10.12 @ 7248857, pinned by test |
| 160 | Plan the bolt for settled assertions on relay-delivery | noise (handoff container; its one member #159 shipped out-of-band) |
| 166 | Answered andon cannot be told from raised one; batch re-pauses forever | landed — ANDON-ANSWERED marker shipped 0.10.12 @ 7248857 |

## intent/schema-distribution

How a schema reaches a machine and stays correct there — three open items, none worked. All three are live bugs/decisions made urgent by the landed bolt-deep→bolt-adversarial rename (#77): stale names still resolve on installed machines today.

| # | title | disposition |
|---|---|---|
| **27** | **Decide whether flywheel needs a versioned schema install path before breaking renames** | **worth keeping** — gates the work-object-vocabulary identifier pass (#30); migration-window question unanswered. |
| **78** | **openspec schema fork erases a schema's loop: block** | **worth keeping** — confirmed upstream bug (zod strip mode + fork re-serialization, openspec 1.8.0 measured); forked bolt types silently lose loop config. |
| **80** | **bin/install-schemas never prunes; renamed schema keeps resolving under old name** | **worth keeping** — live on any machine that installed pre-rename; prune needs a whose-schemas-may-it-touch rule. |
| 108 | Work the queued design items on schema-distribution | noise (elaboration container) |

## bolt/loop-server

The big cutover: conductors retired, the two loops became ordinary Python programs (`flywheel-bolt-loop`, `flywheel-intent-loop`) plus a `flywheel server` daemon reconciling every 60s, on a shared substrate (session runners #75, inbox filters #76), with bolt types as named loop configs and bolt-deep renamed bolt-adversarial (#77). All six assertions plus the eval recast (#101) built, merged, and landed on main at `44795b3` with 206 tests green; the conductor vocabulary fully purged. The R1 completion-signal question migrated to #97 (bolt/stage-labels).

| # | title | disposition |
|---|---|---|
| 72 | flywheel-bolt-loop runs the construction loop as a program | landed @ 44795b3 |
| 73 | flywheel-intent-loop runs the design loop as its own program | landed @ 44795b3 (R1 carried to #97) |
| 74 | flywheel server starts/stops loop processes from 60s reconcile | landed @ 44795b3 |
| 75 | One session-runner abstraction: herdr + headless + cloud stub | landed @ 44795b3 |
| 76 | The inbox filters are the whole coordination model | landed @ 44795b3 |
| 77 | Bolt types are named loop configs; bolt-adversarial renames bolt-deep | landed @ 44795b3 |
| 94 | Plan-mode session waits on operator, nothing tells the loop | noise — withdrawn (closed:declined); premise false, loop has an approver session |
| 101 | Seven construction eval prompts still cast the retired conductor | landed @ 44795b3 |

## bolt/merge-gate-remedy

Closed the silent-green merge hole: checks moved from `[pre-commit]` to `[pre-merge]` so clean fast-forwards get gated (#34), herdr.md gate prose corrected including a false CI-on-push claim (#35), operator granted the hook approvals interactively (#33), and `flywheel up` now checks approvals as a start precondition with careful two-file fault attribution (#36). Landed on main at `140e8c5`; the landing itself failed the gate first (jsdom cold worktree) and proved the fail-closed design.

| # | title | disposition |
|---|---|---|
| 33 | Grant this repo's wt hook approvals — operator, interactive | landed @ 140e8c5 |
| 34 | Move merge gate to [pre-merge] + warm worktrees with copy-ignored | landed @ 140e8c5 |
| 35 | Correct gate prose in herdr.md, add missing-approval rule | landed @ 140e8c5 |
| 36 | Check hook approvals at flywheel up, document onboarding grant | landed @ 140e8c5 |

## bolt/site-refresh

Quick bolt (no intent, no spec — plan mode as spec surrogate): rebuilt the Pages landing site on the operator's settled hero, tabbed walkthrough, vendored fonts, repo homepage pointed at the published URL. Landed at `134e177`, verified against the deployed artifact, bolt archived. Its one discovery (fast-forward merges skipping the gate) was filed as #14 and became the merge-gate-remedy thread.

| # | title | disposition |
|---|---|---|
| 12 | Rebuild the Pages landing site, point repo homepage at it | landed @ 134e177, archived |

## bolt/stage-labels

Construction bolt for four released assertions from the design-center review: stage labels written at loop boundaries (#96), the operator's stage:done flip as completion signal (#97), a unit parent for every release (#98), and the bolt-direct type (#99). Verify and code-review rounds queued ~20 discoveries (unit #138) — stale prose, label-sweep edges, guard bugs — all fixed in-bolt. Two rulings landed en route: `closed:merged` as the merge-back closure reason (#118) and catch-up-by-merge-never-rebase (#194). The bolt landed on main as 5089367 with every assertion closed:done.

| # | title | disposition |
|---|---|---|
| 96 | Bolt loop writes stage labels at boundaries | landed |
| 97 | Intent items carry in-session/done/collected; operator flip signals completion | landed |
| 98 | Every release creates a unit parent | landed |
| 99 | bolt-direct: fourth bolt type, no verify | landed |
| 100 | Unit: stage labels, unit parents, bolt-direct | landed |
| 118 | When a unit sub-issue checks off | settled (operator ruled `closed:merged`; implemented in 0.10.x) |
| 119 | marketplace.json stale vs plugin.json | landed (61ac7a5) |
| 120 | Discoveries unit | landed |
| 121 | Duplicate discoveries unit | noise |
| 133 | Landing pause/andon silent after closed:merged | landed |
| 134 | Intent loop accumulates stage labels | landed |
| 135 | Schema prose stale on loop: block / landing | landed |
| 136 | Nothing refuses skip-verify on other types | landed |
| 138 | Discoveries unit (19 items) | landed |
| 142 | release-unit-parent requirement contradicts handoff shape | landed |
| 143 | Bolt-loop record describes pre-closed:merged landing | landed |
| 144 | Pane stage:done doesn't sweep previous label | landed |
| 145 | Pane flip missing from six design-session skills | landed |
| 146 | Block-style stages: ignored not refused | landed |
| 147 | Nothing closes a unit parent | landed |
| 148 | Andon/stall pauses undone a cycle later | landed |
| 149 | Late stage:done flip never merges sess/* | landed |
| 150 | Stage set says six, enumerates seven | landed |
| 151 | --type outranks binding; stages: unvalidated | landed |
| 154 | Coverage gaps: bolt-direct strategy, teardown merge | landed |
| 155 | Stage-writer edges: skipped sweep, stale _added | landed |
| 156 | unittest.main() placement skips six tests | landed |
| 157 | Session-scoped merge fires on wrong item set | landed |
| 158 | Flipped sibling collected under stall/andon | landed |
| 163 | Work-less bolt introduces no stage label | superseded (by #164's fix) |
| 173 | guard_stages re-derives stage:merged from ancestry | landed |
| 175 | Raw stage:done flip leaves two stage labels | landed |
| 176 | Three spec-text gaps vs built tree | landed |
| 194 | Bolt no longer rebases onto main, no landing tree | landed (ruling: catch-up is merge, never rebase) |

## intent/loops-run-unattended

The intent making both loops survive unattended operation. First-boot and live-run defects (session runner, filters, stall detector, relaunch markers, vacuous landings) were fixed through releases 0.10.1–0.10.15; five planning sessions settled decisions now recorded in `openspec/changes/loops-run-unattended/decisions/` (scaffold guard, intent loop: block, restart-reattach, unit-parent brief, module home). The thread ended mid-flight: a 14-assertion handoff (#204/#205) was in-session at archive time, so most of the open set is real, unbuilt work — bugs found live plus operator ideas that exist nowhere but this tracker.

| # | title | disposition |
|---|---|---|
| 81 | Server inbox filter blind to handoff/compose-only milestones | settled (session dir + decisions in change dir) |
| **83** | **Wire unit suite into merge gate and CI** | **worth keeping** |
| 85 | Home for shared modules: bin/_*.py vs tools/ | settled (decision record in change dir) |
| **86** | **gh() sys.exits on any failure — kills the 60s reconcile daemon** | **worth keeping** |
| 87 | Does intent loop need scaffold guard 0? | settled (decisions/intent-scaffold-guard.md) |
| 88 | flywheel-intent schema lacks loop: block | settled (decisions/intent-loop-declare-block.md) |
| 89 | Restarted intent loop doesn't re-attach | settled (decisions/restart-reattach.md) |
| **91** | **parent_batch never filled from live tracker — every item reads as orphan** | **worth keeping** |
| **103** | **A unit test launches a real herdr session** | **worth keeping** |
| 109 | Elaboration container | noise |
| 111 | Runner reads never-launched agent as settled | landed (0.10.1) |
| 112 | Ready filter empty while server sees items | landed (0.10.1) |
| 113 | Orphan compose sweep unpartitioned | landed (4e45533) |
| 114 | Elaboration container | superseded |
| 125 | Unit sub-issue check-off timing | superseded (dup of #118, ruled there) |
| 129 | Elaboration container | superseded |
| 139 | Stall detector measures time since launch | landed (0.10.14) |
| 140 | Session commenting before re-prompt judged silent forever | landed (0.10.10) |
| 141 | Handoff for #140 (set closed before dispatch) | noise (degenerate; spawned #203) |
| **152** | **Closed blockers invisible in snapshot — items blocked forever** | **worth keeping** |
| **153** | **Three code comments state facts the tree no longer bears out** | **worth keeping** |
| **162** | **Items never join the org Project — In-Flight board is blind** | **worth keeping** |
| 164 | Empty branch reads as merged; vacuous landing over andon | landed (0.10.12) |
| 167 | Verify stage roams beyond the change | landed (0.10.15) |
| 168 | Fresh relaunch born stalled from dead session's marker | landed (0.10.14) |
| 169 | Undelivered pane wedges every later launch | landed (0.10.14) |
| **170** | **Nothing reaps inspection panes — corpses accumulate** | **worth keeping** |
| **171** | **Eval bolt: full loop run against fixture-tracker JSON** | **worth keeping** |
| **172** | **Rewrite bolt-loop record as guards-then-loop pseudocode** | **worth keeping** |
| **174** | **No batch ordering — discovery batches fork from trees missing their base** | **worth keeping** |
| **177** | **Sessions file discoveries born state:ready, skipping the operator** | **worth keeping** |
| **202** | **type:build on intent milestones is a dead end** | **worth keeping** |
| **203** | **A handoff item outlives its set — emptied handoff still charges a session** | **worth keeping** |
| 204 | Handoff planning item (in-session) | noise |
| 205 | Handoff unit container | noise |
| 207 | Elaboration container | noise |
| 208 | Intent loop scaffolds missing change dir | settled (decisions/intent-scaffold-guard.md; unbuilt) |
| 209 | flywheel-intent carries stubbed loop: block | settled (decisions/intent-loop-declare-block.md; unbuilt) |
| 210 | Restarted loop re-attaches / escalates dead sessions | settled (decisions/restart-reattach.md; unbuilt) |
| 211 | Compose writes operator brief into unit body | settled (decisions/unit-parent-brief.md; unbuilt) |

Worth-keeping substance, one line each:

- **#83** — scripts/test.sh is deliberately not a [pre-merge] hook yet; the plan (take the worktrunk approval, then wire wt.toml + gates.yml) exists only here.
- **#86** — `bin/_flywheel_gh.py:41-43` sys.exits on any gh failure; the server needs a raising read path to survive transient GitHub errors.
- **#91** — `Item.from_api` reads a `parent_batch` key GitHub never sends and `snapshot` never fills it, so live guards see only orphans.
- **#103** — the suite violates its own no-world contract: one test spawns a live herdr session.
- **#152** — `open_blockers` treats unseen blockers as open, but the snapshot omits closed issues, so a satisfied blocker blocks forever.
- **#153** — three specific comment sites in `bin/_flywheel_inbox.py` etc. assert measurements the tree no longer bears out.
- **#162** — only `flywheel-batch` adds its parent to the org Project; members and guard/session-born items never join, blinding every board view.
- **#170** — fix direction named: a reaper on the server reconcile pass for idle panes matching no live batch.
- **#171** — operator idea: an end-to-end eval driving a full loop run against scripted fixture-tracker JSON; would have caught most of the week's live defects.
- **#172** — operator's verbatim shape for the bolt-loop record: major conditionals as guards first, then the loop, in plain pseudo-code English.
- **#174** — real design question with operator correction folded in: batches need a provenance field and a defer predicate, not strict serialization.
- **#177** — session-born state:ready discoveries self-admit past route, compose, and the operator; fix is instructions plus sweep.
- **#202** — operator ruling not yet in the instructions: repo work is `type:assertion`, never `type:build`; dispatch must stop using type:build.
- **#203** — handoff sets go stale between birth and dispatch; a dispatched handoff whose set has closed still burns an opus session and an operator round.

## intent/work-object-vocabulary

Settled one vocabulary for the loops' work objects: the released claim is the **assertion**, the construction batch is the **unit**, the design batch is the **elaboration** — decided on a lavish page over #18's measured blast radius, recorded in `openspec/changes/work-object-vocabulary/decisions/work-object-names.md` + `landing-pass-licence.md` (landed 141f81d). The landing pass itself — 253 `proposal` occurrences across identifiers, prose, and this repo's specs — was authorized as assertions #30/#31/#32 but **never executed**; #32 is still blocked on the unmade sequencing call #20. A late operator ruling (#206) that dispatch never files `type:build` is also unlanded.

| # | title | disposition |
|---|---|---|
| 13 | Settle one vocabulary for the loops' work objects | settled (decisions/work-object-names.md, 141f81d) |
| 18 | Inventory the blast radius of the rename | landed (inventory folded into questions/work-object-names.md) |
| 19 | Settle the vocabulary: inventory then call | landed |
| 21 | Hero's "Units become bolts" contradiction | superseded (folded into #31 via landing-pass-licence) |
| **20** | **Sequence rename vs add-flywheel-loops' active deltas** | **worth keeping** |
| 28 | Elaboration wrapper for #20 | noise |
| **30** | **Identifier migration, code before labels** | **worth keeping** |
| **31** | **Prose pass outside openspec/specs (incl. hero rewrite)** | **worth keeping** |
| **32** | **Specs pass per settled vocabulary** | **worth keeping** |
| 37 | Handoff wrapper for the landing pass | noise (machinery-born, regenerable) |
| 38 | Unit wrapper for the landing pass | noise (sequencing rule restated in #30's record) |
| 106 | Elaboration wrapper (empty) | noise |
| **206** | **Dispatch triage: repo work is type:assertion, never type:build** | **worth keeping** |

Keepable substance: #30/#31/#32 are the settled-but-unbuilt landing pass (assertion records survive in git under `assertions/`, but nothing drives the work once the tracker dies); #20 is the unmade call on whether the specs pass covers `add-flywheel-loops`' active deltas — and flags that no spec pins the current artifact model; #206 carries the operator's verbatim ruling ("retype the seven, and dispatch stops using type:build"), which exists nowhere but the tracker until it lands in the dispatch triage guidance.

## intent/board-views-ux

A design thread to settle each of the six org Project views (Kanban, Roadmap, Triage, Waiting On Me, In Flight, Landed) from the operator's seat — nothing was ever worked; every item is open and queued, so archiving kills the whole thread. The per-view charges share one template and could be re-derived from the intent change, but #193's measured evidence is unique: a bolt with 19 in-progress items reads 0% on the board, the Kanban filter excludes in-flight work by construction, and `state:*` label vs Status column disagree on the same card.

| # | title | disposition |
|---|---|---|
| **184** | **Inventory what each board view returns today** | **worth keeping** |
| **186** | **Settle the Kanban view** | **worth keeping** |
| **187** | **Settle the Roadmap view** | **worth keeping** |
| **188** | **Settle the Triage view** | **worth keeping** |
| **189** | **Settle the Waiting On Me view** | **worth keeping** |
| **190** | **Settle the In Flight view** | **worth keeping** |
| **191** | **Settle the Landed view** | **worth keeping** |
| 192 | Elaboration wrapper (empty) | noise |
| **193** | **No instrument for work in flight: 19 in-progress items read 0%** | **worth keeping** |

Keepable substance: #193's three measured faults (binary Sub-issues progress bar; Ready column vs `state:queued` label authority conflict; Kanban filter `is:open -status:Todo,"In Progress",Done` excludes moving work) plus the tie to the `stage:*` ladder on bolt/stage-labels; #184–#191 are the unstarted per-view design program — regenerable as templates, but bold here because the entire milestone is otherwise lost.

## intent/gated-merge-guarantee

The core thread landed: #14 proved by experiment that `[pre-merge]` hooks run on every merge shape while `[pre-commit]` skips fast-forwards, and two decisions closed on the operator's word — checks move to `[pre-merge]` alone, and hook approvals are an operator onboarding grant checked by the fleet (`decisions/gate-runs-under-pre-merge.md`, `decisions/approvals-are-an-onboarding-grant.md`). Bolt `merge-gate-remedy` built and merged the remedy (#42's items #34–#36 closed done). Six real follow-ons raised by the bolt's own conductors are still open and unacted.

| # | title | disposition |
|---|---|---|
| 14 | Merge gate silently skips fast-forward merges | settled (decisions/gate-runs-under-pre-merge.md, c7697d6) |
| 16 | How wt hook approvals get granted | settled (decisions/approvals-are-an-onboarding-grant.md) |
| 17 | Elaboration: ff hole + missing approvals | landed |
| 22 | validate --all red: missing skip_specs | landed (fixed at 86a8404) |
| 41 | Plan the bolt for the merge-gate remedy | landed (bolt-plan.md, 2776613) |
| 42 | Land the merge-gate remedy (unit) | landed (#34–#36 closed done; unit left open) |
| **54** | **Does the approval check cover reconcile's conductor starts** | **worth keeping** |
| **55** | **Does the approval check cover project aliases** | **worth keeping** |
| 56 | Stale merge-gate phrasing in add-flywheel-loops/design.md | superseded (sentence became true when #34 landed; residual is cosmetic) |
| **57** | **Gate does not cover direct commits to main** | **worth keeping** |
| **62** | **Upgrade table-move keying claim from provisional to measured** | **worth keeping** |
| **65** | **Two contradictory hook.md copies, both 1.0.0** | **worth keeping** |
| 105 | Elaboration wrapper (empty) | noise |
| **126** | **Release step doesn't bump marketplace.json — gate red on main** | **worth keeping** |
| 128 | Handoff wrapper for #126 | noise (machinery-born, regenerable) |
| 130 | Handoff twin | superseded (eventual-consistency bug, fixed 0.10.9) |
| 131 | Elaboration wrapper (empty) | noise |
| 132 | Elaboration twin | superseded (same 0.10.9 bug) |

Keepable substance: #126 is an unfixed bug — whatever cuts a release bumps `plugin.json` but not `marketplace.json`, so the manifest gate goes red on main every release (the stronger fix: make the two versions one source); #57 is the unscoped hole — conductors, intent loops, and dispatch all commit straight to main and no check runs, so "everything on main went through the gate" is false; #54 is the residual design question of how `reconcile` should behave unattended when the approval precondition fails (the mechanism itself was covered at the actor-start seam); #55 is the unmade scope call on aliases (arguments recorded in fleet-approval-check design.md Non-Goals); #62 asks that the measured verbatim-template-keying fact be moved from the archivable bolt record into `questions/hook-approvals-never-granted.md` before it decays back to "provisional"; #65 records that the two `hook.md` copies contradict each other on pre-* ordering and the answer must come from measurement, not the docs.

## intent/machinery-self-desc

The "make the machinery's self-description true" intent: a large queue of drift findings — specs, skills, evals, and reference prose (`herdr.md`) that still describe retired conductors, claim gates that never fire, or give instructions measured false. About a third got assertion/question records written into git under `openspec/changes/machinery-self-desc/` (those survive archiving); the rest sit `state:queued`, never released to a bolt. Only #53 shipped. Archiving loses the unrecorded majority of the queue.

| # | title | disposition |
|---|---|---|
| **#95** | Eval suites test judgment that has moved | **worth keeping** |
| **#93** | Spec baseline still describes conductors, in nine capabilities | **worth keeping** |
| **#84** | Point schemas'/skills' andon prose at the structured marker | **worth keeping** |
| **#82** | herdr.md rename-confirm poll unreliable when agent is working | **worth keeping** |
| **#79** | bolt-conductor eval fixture not the verbatim copy it claims | **worth keeping** |
| **#71** | Operator rounds as workflow stages (nested cycle, no idle panes) | **worth keeping** |
| **#70** | Bare `openspec validate --strict` validates nothing, reads green | **worth keeping** |
| **#69** | Price the ceremony: bolt-type cost at handoff, model tiers per role | **worth keeping** |
| **#67** | "on every push" CI claim false in AGENTS.md/README.md | **worth keeping** |
| **#66** | Stale no-lifecycle-hooks rationale in --no-hooks requirement | **worth keeping** |
| **#64** | Measure the trailing -C hazard (wt merge still unmeasured) | **worth keeping** |
| **#63** | Permission-flag ownership; never batch-approve permission prompts | **worth keeping** |
| **#61** | Tracker writes fail closed when flywheel-token can't mint | **worth keeping** |
| **#59** | herdr.md squash claim false (`[merge] squash = false`) | **worth keeping** |
| **#58** | Bolt woken by loose ready items inherits no Team | **worth keeping** |
| **#52** | Prompt-delivery verification false negatives on slow init | **worth keeping** |
| **#50** | Set worktree-path so worktrees stop landing under `.bare.*` | **worth keeping** |
| #110 | Work the queued design items (elaboration) | superseded |
| #107 | Work the queued design items (elaboration) | noise |
| #102 | Machinery's own record still names the conductor (unit) | noise |
| #53 | Scaffold-missing launch prompt buries the trigger line | landed |
| #49 | Settle fix-or-retire for evals gate / proposals registry (elab.) | noise |
| #48 | Make the self-description true (unit container) | noise |
| #47 | Plan the bolt for the corrections (handoff, set #52 #61 #79) | noise |
| #44 | Conductor names fit herdr's 32-char limit | settled — `assertions/conductor-name-length.md` |
| #40 | flywheel-batch --repo wants bare name, owner/repo 404s | settled — `assertions/batch-repo-arg.md` |
| #39 | herdr.md teardown destroys shared workspace | settled — `assertions/teardown-by-provenance.md` |
| #29 | Workflow args-as-string arrives undefined | settled — `assertions/workflow-args-warning.md` |
| #26 | proposals.md registry names artifact no schema declares | settled — `questions/proposals-registry.md` (question open) |
| #25 | openspec/config.yaml context prose false | settled — `assertions/config-context-prose.md` |
| #24 | Four "verbatim copy" eval fixtures diverged | settled — `assertions/profile-fixture-recopy.md` |
| #23 | CI evals gate has never fired (glob mismatch) | settled — `questions/evals-gate.md` (question open) |

Worth-keeping substance, one line each:

- #95 — the open design question: sort eighteen conductor-protagonist eval cases into code/operator/session buckets; #74's re-cast was deliberately shallow.
- #93 — nine `openspec/specs/` capabilities (with hit counts tabulated in the body) still SHALL-require conductor agents that no longer exist; gates a loop-server merge criterion.
- #84 — eight named schema/skill sites restate the andon rule without citing the structured marker; format drift risk.
- #82 — measured fact: the spinner glyph defeats the prescribed `.terminal_title_stripped` poll; the fix (launch with `-n <name>`) is known, herdr.md never corrected.
- #79 — fifth mixed-generation fixture; decide once for all five: generate from `agents/*.md` or declare frozen (pairs with #24's record).
- #71 — operator's own design proposal: sessions return round content as JSON and settle; the run holds the round — kills hours of idle top-tier panes.
- #70 — pin `openspec validate <change> --strict` everywhere; the bare form is a quotable false green (upstream exit-code question noted as not ours).
- #69 — cost governance: state bolt-type session count/cost at handoff; cheap models for glue, top tier only where judgment earns it.
- #67 — two-line doc fix plus a decide-once across four sites; pushes to `build/*` fire no CI at all.
- #66 — one stale rationale sentence in a published capability spec, falsified by the repo's first lifecycle hook.
- #64 — half-measured silent-failure hazard; `wt merge` with trailing `-C` is the unmeasured case that matters for merge-back evidence.
- #63 — safety rule to write down: who sets skip/plan per session, and permission prompts answered one at a time, never by pattern loop.
- #61 — the big one: empty `GH_TOKEN` silently posts as the operator; four+ live instances; severity raised to "an agent can appear to answer an open needs-operator question"; remedy ranked toward a `flywheel-gh` wrapper since prose instructions were proven insufficient.
- #59 — herdr.md's squash claim is measured false; every agent cargo-cults `--no-squash`; fix by re-measuring, not deleting.
- #58 — routing gap: custody-move bolts get team=None; candidate rule is route on the parent unit's Team.
- #52 — three live false "never went to work" exit-1s from start_actor's verification window; matters under `--interval`.
- #50 — one-line `worktree-path` config fix; body notes it worsens with every session (seven dotted `.bare.*` worktrees and counting).

## Unmilestoned / triage

Two populations. Issues #115–#200 are the shakedown log of the loop-server/stage-labels live runs — each an observed-live defect (compose fragmentation, token expiry, wrong-cwd validation, restart blindness, container-routing loops, pane-scrape handoffs) fixed and shipped within a day across plugin 0.10.1–0.10.16; all landed with regression tests. Issues #1–#15 plus #60/#90/#92 are sandbox smoke tests and threads folded into successors. Nothing here is lost by archiving.

| # | title | disposition |
|---|---|---|
| #200 | Verify hands off through a file, not a pane scrape | landed (cfae845) |
| #178 | Deterministic session ids, resume instead of pause | landed (0.10.16) |
| #165 | Later settle clears a needs-operator it never raised | superseded (→ #159, diagnosis carried) |
| #137 | Compose fragments / handoff births twice | landed (0.10.9) |
| #127 | Long-lived loop dies on hourly Bad credentials | landed (0.10.8) |
| #124 | change_validates runs in the wrong checkout | landed (0.10.7) |
| #123 | Restarted loop can't see its in-progress items | landed (0.10.6) |
| #122 | Route guard wraps a kept unit in a new unit every cycle | landed (0.10.5) |
| #117 | Loop is the worktree orchestrator; status tells run/held/waiting | landed (0.10.3) |
| #116 | Stranded rename concatenates with work order in composer | landed (0.10.2) |
| #115 | Compose guard births a batch every restart | landed (0.10.1) |
| #92 | Stage labels for per-item progress | superseded (released as bolt/stage-labels, #96–#100) |
| #90 | Wire scripts/test.sh into merge gate and CI | superseded (→ #83) |
| #60 | flywheel-token failing silently posts as operator | superseded (→ #61, mechanism carried) |
| #15 | test | noise |
| #11 | demo: batch 1 — gateway validation and SDK retries | noise |
| #10 | demo: SDK retries idempotent calls | noise |
| #9 | demo: gateway validates tokens locally | noise |
| #8 | the fixture released line | noise |
| #7 | sandbox migrate fixture | noise |
| #6 | sandbox: batch composed by flywheel-epic | noise |
| #5 | sandbox: batch composed by flywheel-epic | noise |
| #4 | sandbox: epic test batch | noise |
| #3 | sandbox: item B for epic test | noise |
| #2 | sandbox: item A for epic test | noise |
| #1 | sandbox: tracker smoke test — epic | noise |
