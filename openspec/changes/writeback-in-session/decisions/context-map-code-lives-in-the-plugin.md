# Decision: the context-map code lives in the plugin

## Decision

The context-map system — checker, tooling, README — moves out of
willdan-blueprints and into the flywheel plugin (e.g.
`tools/context-map/`), versioned and shipped with the machinery the way
the books gates already are; sessions and merge-gate hooks invoke it
via `${CLAUDE_PLUGIN_ROOT}`. Map data stays with the repo it describes:
each blueprint repo keeps only its `context-map/maps/`, and a blueprint
repo gains that directory when its first map writeback lands, never as
empty scaffold. Extraction to a standalone package is deferred until a
second consumer outside flywheel is real.

## Context

- Chapter: the flywheel book at `agentplot/blueprints` (write rides
  #320's writeback)
- Produced by: sessions/2026-08-18-chaining-and-map-home/context-map-home-draft.md,
  annotated by the operator 2026-08-18 ("approved option a")

## Consequences

- Assertion: move the code into the plugin and point the writeback
  skill's gate list and blueprint-repo `[pre-merge]` hooks at the
  plugin copy. The willdan-blueprints removal leg routes through that
  org's own tracker.
