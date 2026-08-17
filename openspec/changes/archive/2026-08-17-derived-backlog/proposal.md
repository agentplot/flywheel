# Derived backlog

## Why

Bolt 2 of the approved 2026-08-17 plan
(`design/plans/2026-08-17/02-derived-backlog.md`), building on
`board-surface`. The bolt planner does not exist: nothing charges a
planning run, nothing files plan cards, and board approval of a plan
reaches no machinery. This change builds the path end to end —
planning run, plan cards, reconcile triggers, expansion, and the
builds-on defer — per `books/flywheel/src/bolt-planning.md`,
`server-and-fleet.md`, `tracker-protocol.md`, and `lifecycles.md`.

## What Changes

- The fleet manifest gains `books:` bindings (system → book checkout,
  built repo, team, settle window); the server reads them.
- The reconcile pass marks unapproved plan cards stale against their
  recorded input commits, and charges a planning run when a system's
  cards are missing or stale once its book has settled — or on a
  landing, or the operator's ask.
- A `flywheel-bolt-planner` profile hosts the run; the bolt-planning
  skill's board mode files one card per proposed bolt.
- The bolt loop's first pass expands a Ready plan card: milestone,
  card becomes the unit, one work item per plan task, Ready status
  consumed, plan copied into the bolt's charter. A card without Team
  pauses `needs-operator`; a card blocked by an unlanded predecessor
  defers.

## Impact

- Affected specs: `flywheel-derived-backlog` (new)
- Affected code: `bin/_flywheel_inbox.py`, `bin/_flywheel_server.py`,
  `bin/_flywheel_bolt_loop.py`, `bin/flywheel`,
  `agents/flywheel-bolt-planner.md`, `skills/bolt-planning/SKILL.md`,
  tests
