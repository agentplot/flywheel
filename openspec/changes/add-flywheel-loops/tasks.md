# Tasks

## 1. flywheel-intent schema and sample intent

- [x] 1.1 Create project-local `flywheel-intent` schema with artifacts
      intent / decisions / design / prototypes / tasks
- [x] 1.2 Prove per-change binding: `.openspec.yaml` with
      `schema: flywheel-intent` + `skip_specs: true`; validate green
- [x] 1.3 Populate sample intent `rocs-record-split` with realistic artifacts
- [x] 1.4 Push the actor rules into the schema instructions and
      `openspec/config.yaml` (single writer, inbox, handoff-as-request)
- [ ] 1.5 Review schema instructions with one fresh session (do the
      instructions alone produce correct artifacts?) and tighten wording

## 2. flywheel-bolt schema and sample bolt

- [x] 2.1 Create `flywheel-bolt` schema: bolt.md / proposals.md registry /
      typed tasks, with the practice in the artifact instructions
- [x] 2.2 Populate sample bolt `bolt-rocs-records` from rocs-record-split's
      staged handoffs; validate green; task progress on `openspec list`
- [x] 2.3 Prove the inbox round-trip: request file dropped, folded into
      tasks, deleted — one commit
- [ ] 2.4 Spot-check the openspecui board on blueprints@main renders
      intents and bolts usefully (kanban + task progress)

## 3. flywheel-inception skill

- [x] 3.1 Write the skill: intake three-way route, intent conductor as sole
      writer with handoff-as-request, design sessions, plannotator/lavish
      criteria
- [x] 3.1b Agent profiles for the actors (`.claude/agents/flywheel-*.md`),
      launched via `claude --agent` in herdr panes; launch lines wired
      into the skills and E2E
- [ ] 3.2 Run one real intent through the skill end to end
      (flywheel/E2E.md §1–§3) — in progress: spike-context-cleanup intake
      + research done; design session next

## 4. flywheel-construction skill

- [x] 4.1 Write the skill: bolt conductor on blueprints main, per-repo bolt
      branches + nested construction worktrees, registry-driven
      spec→review→build→test→merge, pipeline-stage invariants, long-lived
      posture, repo-readiness audit
- [ ] 4.2 Run one released handoff through a built repo end to end
      (flywheel/E2E.md §4–§7)
- [ ] 4.3 Salvage pass over kb-spike's super-conduct bundle (charges,
      progress-skeleton renderer, timeline.sh) before its skill archives —
      feeds from spike-context-cleanup's inventory

## 5. Book and conventions

- [ ] 5.1 Rewrite `books/aidlc-design/src/conducting.md` +
      `authoring-capabilities.md` as the actor-model design
- [ ] 5.2 Rewrite `spec-driven-construction.md` around pipeline stages; add
      the actor-and-branching figure
- [ ] 5.3 Archive `catalog.md` + `agent-workspaces-plugin.md` outside
      `books/`; merge system-design-inception + openspec-construction
      content into the flywheel chapters; update SUMMARY.md, vocabulary,
      walkthrough, index
- [ ] 5.4 `books/CLAUDE.md`: retire the proposals-chapter requirement
- [ ] 5.5 Root `CLAUDE.md`: add flywheel entry points (schemas, skills,
      actor model)

## 6. Investigations

- [ ] 6.1 Discord bridge: can a connected session trigger on any channel
      message or only @-mentions; is a webhook receiver worth having for
      remote intake (small; no machinery built from this change)
- [ ] 6.2 Plannotator as a design-session launcher: reviewing an intent's
      artifacts there covers most of a session's reading half — can its
      feedback path (delivered to the conductor that ran annotate) drive
      spawning the session against the intent?

## 7. Verification

- [ ] 7.1 `python3 books/preview.py --check` green after book edits
- [ ] 7.2 `node context-map/bin/map-check.mjs` green
- [ ] 7.3 Walk flywheel/E2E.md top to bottom; every command works as written
