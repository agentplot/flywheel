# Add the flywheel loops

## Why

Design work and construction work run as two disconnected practices. Design
sessions produce lavish artifacts and book rewrites with no durable
tracking; construction orchestration (conduct, and kb-spike's
super-conduct) is bound to one repo's configuration and invents its own
vocabulary. Nothing connects a settled design to the work that builds it,
and nothing returns construction findings to the design record.

## What Changes

OpenSpec is the foundation of both loops, as three schemas in one
hierarchy — **intent** (design) → **bolt** (construction tracking) →
**construction** (plain spec-driven changes in built repos):

- **flywheel-intent schema** — one change per design intent on blueprints
  main: `intent.md`, `decisions/`, `sessions/` (one directory per design
  session), `design.md` (the catalog of design output), `prototypes/`, typed
  `tasks.md` (Design / Writeback / ADR / Handoff).
  Landed: `openspec/schemas/flywheel-intent/` + sample intent
  `rocs-record-split` + real intents `spike-context-cleanup`,
  `atlas-data-formats-chapter`.
- **flywheel-bolt schema** — one change per construction iteration on
  blueprints main: `bolt.md` (scope, per-repo bolt branches, merge
  criteria), `proposals.md` (registry: review mode agent|human,
  forward-only status), typed `tasks.md` (Spec / Review / Build / Test /
  Merge). Landed: `openspec/schemas/flywheel-bolt/` + sample bolt
  `bolt-rocs-records`.
- **The actor model** — intake agent (singleton), intent conductors and
  bolt conductors (one per change, sole writers, on blueprints main; bolt
  conductors cut long-lived bolt branches + worktrees in each involved
  built repo, with construction on nested worktrees), design sessions,
  spec/apply/testing agents. Messaging is herdr prompts when a conductor
  runs and change-local `inbox/` files when it does not. The operator's
  word is the phase gate from design to construction.
- **Skills** — `flywheel-inception` (design loop) and
  `flywheel-construction` (bolt loop, repo-readiness audit folded in),
  with the authoring rules mirrored into the schemas' artifact
  instructions and `openspec/config.yaml` so opsx sessions get the
  practice without the skills. Landed.
- **Monitoring is OpenSpec UI** on blueprints@main — intents and bolts are
  changes on its board with task progress. No custom dashboard.
- **Review surfaces** — plannotator for written artifacts (proposals,
  plans, diffs), lavish for built interactive surfaces.
- **aidlc-design book rewrite** — `conducting` and `authoring-capabilities`
  become the actor-model design; `spec-driven-construction` absorbs
  pipeline-stage testing; `catalog` and `agent-workspaces-plugin` archive;
  `system-design-inception` and `openspec-construction` content merges
  into the flywheel skills' chapters.
- **Books convention change** — `books/CLAUDE.md` retires the per-book
  `proposals.md` chapter requirement; the build list lives in intents'
  handoff tasks and generated proposals cite chapters directly.

## Non-Goals

- Moon adoption in the kit repos (sequenced by
  `research/kit-reorg-roadmap.md`; the construction skill names the task
  tiers but does not install moon).
- A custom dashboard. Deferred gap, revisit only if felt in use: a
  cross-intent release queue with ripple prediction.
- Discord/webhook machinery — a conductor may be a named bot the operator
  talks to, but agent-to-agent messaging stays herdr + inbox files; the
  bridge-trigger question is an investigation task only.
- Marketplace publication (local prototyping first; move when stable).
- Renaming spec-driven → construction (only if we ever customize it).

## Impact

- New: `openspec/schemas/flywheel-{intent,bolt}/`,
  `.claude/skills/flywheel-{inception,construction}/`, `flywheel/E2E.md`
- Changed: `openspec/config.yaml`, `books/aidlc-design/src/` (rewrites +
  archive set), `books/CLAUDE.md` (proposals-chapter retirement), root
  `CLAUDE.md` (flywheel entry points)
- Existing per-book `src/proposals.md` chapters retire as intents take
  over their role; removal rides the per-book edits, not this change.
