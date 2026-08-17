# Book-gap audit — flywheel design book vs tracker archive 2026-08-17

Sources: `design/field-notes/2026-08-17-tracker-archive.md` (agentplot/flywheel)
vs the 13 chapters under `books/flywheel/src/`.

## Book gaps

Design questions the live fire proved matter, on which the destination book is
silent or under-specified. Ordered by severity.

1. **#61 (and #60) — identity fail-closed.** When `flywheel-token` cannot mint
   the App identity, does every tracker write fail closed, or does it silently
   fall through to the ambient credential and post as the operator? Four-plus
   live instances; an agent appeared to answer an open `needs-operator`
   question. The book asserts "every tracker write names its author"
   (server-and-fleet.md, Identities; tracker-protocol.md) but never states the
   failure mode or the fail-closed rule — and the digest ranked the remedy
   toward a wrapper because prose alone was proven insufficient. **Chapter:
   server-and-fleet.md (Identities), echoed in tracker-protocol.md.**

2. **#57 — nothing gates direct commits to main.** The book's claim that main
   only advances through the merge gate is stated for sessions
   (sessions.md, Worktrees) but nothing enforces it for the machinery itself —
   and server-and-fleet.md itself has the server committing straight to main
   (the one-shot archive: `openspec archive`, "then a commit"). Live fire
   showed loops and dispatch committing to main with no check running. What
   enforcement (branch protection, a gate on the archive commit, an explicit
   carve-out) makes "everything on main went through the gate" true? **Chapter:
   construction-loop.md (Merge) plus server-and-fleet.md (the archive step).**

3. **#58 — Team routing for bolts.** The Team field routes a milestone to a
   host (server-and-fleet.md, Multi-host), but nothing says who sets Team on a
   planner-filed plan card or what the expanded `bolt/<slug>` milestone
   inherits. Live fire: custody-move bolts got team=None and ran nowhere/
   anywhere. The candidate rule (inherit from the parent batch) needs its
   destination form: does the planner set Team, does the card inherit a
   system default, or is an unset Team a refusal at expansion? **Chapter:
   tracker-protocol.md (The org Project) or server-and-fleet.md (Multi-host).**

4. **#69 — cost governance / model tiers.** No chapter says which model tier a
   session type runs or where a bolt's ceremony cost is stated. The operator's
   ruling: cheap models for glue, top tier only where judgment earns it, and
   the cost of a bolt type (session count × tier) stated at approval time —
   which in the new design means on the plan card the operator reads.
   **Chapter: sessions.md (tier per profile/type) and bolt-planning.md (cost
   stated in the plan document).**

5. **#63 — permission-mode ownership.** Who sets skip-permissions / plan mode
   per session, and the safety rule that permission prompts are answered one
   at a time, never batch-approved by pattern. The book describes launches,
   runners, and waiting (sessions.md) but is silent on permission posture —
   an operator ruling that exists nowhere but the dead tracker. **Chapter:
   sessions.md.**

6. **#71 — operator rounds and idle panes.** sessions.md rules "a session in
   an operator round never auto-stalls," which leaves a top-tier pane idling
   for hours while the operator takes their time — exactly the cost #71's
   nested-round design kills (session returns the round content and settles;
   the run holds the round; the answer resumes it). The book's deterministic
   session ids / resume mechanics would support this, but the book never
   decides it. **Chapter: sessions.md (Runners / One name, one session), with
   the annotation round in design-loop.md.**

7. **#27 / #80 — schema rename lifecycle.** schemas.md covers the fork hazard
   (#78: copy, never fork) and same-name replacement (`<name>.replaced`), but
   not renames: `install-schemas` never prunes, so a renamed schema's old name
   keeps resolving on every previously-installed machine (live today from
   bolt-deep→bolt-adversarial), and no migration-window/versioned-install
   policy exists before a breaking rename. The prune needs the
   whose-schemas-may-it-touch rule. **Chapter: schemas.md (Installation and
   distribution).**

8. **#43 / #45 — relay delivery state.** The server nudges dispatch whenever
   `needs-operator` items await relay (server-and-fleet.md), but nothing
   distinguishes awaiting-relay from delivered-and-awaiting-answer, so a
   delivered relay is re-nudged every pass (measured: 5 identical re-nudges
   over two days), and a relay dispatch *cannot* deliver is silent — the book
   names no surface where undeliverability shows. **Chapter:
   tracker-protocol.md (`needs-operator` semantics) and the dispatch-nudge
   paragraph of server-and-fleet.md.**

9. **#170 — pane reaping.** The pane is disposable and stall evidence "leaves
   the pane open" (sessions.md), but nothing ever reaps panes matching no live
   job, so corpses accumulate without bound. The named fix direction — a
   reaper on the server's reconcile pass — is a reconcile responsibility the
   book doesn't assign, including when evidence panes expire. **Chapter:
   server-and-fleet.md (The reconcile pass).**

10. **#174 — defer predicate between bolts.** The plan is "sequenced," with
    the reason a task sits in this bolt rather than a later one, and cards
    carry provenance (the book/spec commits they derived from) — that half
    landed in the book. Missing: what happens when the operator approves a
    later card before its predecessor lands, or two approved bolts share a
    base — does the loop run, defer, or refuse? The operator's correction was
    explicit: a defer predicate, not strict serialization. **Chapter:
    bolt-planning.md (Board approval and expansion) or construction-loop.md.**

11. **#54 — approval precondition, unattended.** `flywheel status` reports
    per-repo merge-gate readiness, but nothing says how the reconcile pass
    behaves when it would start a loop in a repo whose hook approvals are
    missing — start and fail late, refuse and label, or hold. **Chapter:
    server-and-fleet.md.**

12. **#194 — bolt-branch catch-up policy.** The operator ruled catch-up is
    merge, never rebase (a rebase destroys the landing tree / merge-back
    evidence); the book describes the bolt branch and the landing but never
    states how a long-lived bolt branch stays current with main. **Chapter:
    construction-loop.md (minor).**

13. **#195–#199 — the import lane.** Dispatch triages raw ideas one at a time;
    nothing covers a pre-existing corpus arriving in bulk — cross-org landing
    (source-org vs importing-org tracker), what durable thing carries an
    import, the reverse-engineer lane into a repo with no flywheel, and bulk
    dedupe/provenance at triage. Possibly a deliberate scope exclusion, but
    the destination is silent rather than declining. **Chapter: design-loop.md
    or the dispatch section of sessions.md (flag for the operator to scope in
    or out).**

## Construction details

Bugs and tasks the planner will find by diffing book vs code; the book
correctly omits them.

- #86 `gh()` sys.exits, kills the reconcile daemon (needs raising read path)
- #91 `parent_batch` never filled from the live tracker
- #152 closed blockers invisible in snapshot — items blocked forever
- #126 release bumps `plugin.json` not `marketplace.json` (one version source)
- #83 wire the unit suite into merge gate and CI (verification.md already states it runs per-merge)
- #103 one unit test spawns a real herdr session (violates stage-1 hermeticity the book mandates)
- #171 full-loop eval against fixture-tracker JSON — this is verification.md stage 2; build it
- #172 rewrite bolt-loop record as guards-then-loop pseudocode
- #153 three stale code comments; #59 / #64 / #65 / #66 / #67 / #82 doc-drift and unmeasured-claim items in herdr.md/AGENTS.md/hook.md
- #70 pin `openspec validate <change> --strict` everywhere (book already uses the pinned form)
- #79 / #24 eval-fixture verbatim-copy policy (generate vs freeze, decide once for five)
- #93 / #95 specs and eval suites still cast retired conductors — exactly the book-vs-specs gap the planner reads
- #52 prompt-delivery verification false negatives on slow init
- #55 approval-check scope over project aliases
- #50 `worktree-path` config so worktrees stop landing under `.bare.*`
- #162 org Project membership — book's answer is auto-add (tracker-protocol.md); wire it
- #193 board-view faults — the six view filters in tracker-protocol.md already answer all three measured faults; build them
- #177 sweep/instructions enforcing commitment 3 (session-born items skipping the operator)
- #30/#31/#32 identifier-and-prose landing pass — re-derive under the current vocabulary (assertion/proposal both retired now)
- #179–#182 site tours, quickstart, nav restructure (docs work, not book content)
- #119 marketplace.json staleness (landed variant of #126)

## Retired

Only made sense under the assertion/handoff/conductor machinery; correctly
absent.

- #202 / #206 — `type:build` vs `type:assertion` dispatch ruling: both types
  are gone; dispatch files questions only (tracker-protocol.md, Who writes what)
- #203 — emptied handoff still charges a session: handoffs are gone; the
  stateless loops re-read the tracker before charging
- #51 / #68 — conductor-era re-nudge and run-lineage behavior, overtaken by
  the loop-server rewrite (per the digest itself)
- #84 — andon-prose pointing at the structured marker: andon vocabulary gone;
  `needs-operator` semantics carry it in the book
- #62 — move a measured fact from a bolt record into a question record: both
  record kinds reshaped; measurements now land in decision files/chapters
- #20 — sequencing the rename vs `add-flywheel-loops` deltas: the renamed
  vocabulary is itself retired
- #92 / #90 / #60 — superseded threads (folded into #96–#100, #83, #61)
- #183 — "decide flywheel's own design book": resolved — this book is it
