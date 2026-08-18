# Decision draft: where the context-map system code lives (item #317)

The system context map was built inside willdan-blueprints: checker and
tooling (`context-map/bin/map-check.mjs`, `context-map/README.md`)
co-located with the map data (`context-map/maps/current.js`,
`target.js`) in the one blueprint repo. The decision
`the-close-writes-the-destination` makes the map a first-class
writeback destination for every org, so org-agnostic code sitting in
one org's blueprint repo is now a misplacement. The operator proposed
moving the code into flywheel or a new agentplot project, with the map
JSON living in the blueprint repo it describes.

Annotated by the operator 2026-08-18: **option (a) approved**.
Closure recorded in `../../decisions/context-map-code-lives-in-the-plugin.md`.

**One split is settled by the dictation itself and every option below
honors it: data lives with the repo it describes, code lives with the
machinery that checks it.** The question is only where the code goes.

## Option (a) — into the flywheel plugin  **[recommended]**

The map system ships inside the flywheel plugin (e.g. `tools/context-map/`),
versioned with the machinery, present wherever the plugin is —
exactly how the books gates already travel. Sessions invoke it as
`node "${CLAUDE_PLUGIN_ROOT}"/tools/context-map/bin/map-check.mjs
--write` against the repo's `context-map/maps/`; the writeback skill's
gate list and the merge-gate hooks point at the plugin copy.

- **For**: one copy, one version, zero per-org install; the gates a
  session must pass and the code that runs them upgrade together; the
  skills already resolve `${CLAUDE_PLUGIN_ROOT}` at load, so the wiring
  pattern exists.
- **Against**: the plugin grows a subsystem; a map consumer outside
  flywheel (a standalone viewer, another toolchain) has to reach into a
  plugin for a library. Mitigation: extraction to its own package later
  is cheap and one-directional — start co-located, split when a second
  consumer is real rather than imagined.

## Option (b) — a new agentplot project (own repo, own package)

`agentplot/context-map` as a standalone package the plugin (and anyone
else) depends on.

- **For**: clean dependency direction; independently versioned;
  consumable outside flywheel from day one.
- **Against**: a repo, a release process, and a version skew surface —
  the merge gate would pin one version while the plugin documents
  another — bought for a second consumer that does not yet exist. The
  standing rule for that trade is to pay it when the consumer appears.

## Option (c) — stay in willdan-blueprints

- **Against, decisively**: org-agnostic machinery placed in one org's
  data repo; every other org's blueprint repo would vendor or reach
  across orgs for its own gate. Kept only as the do-nothing baseline.

## Consequences of (a), to queue on approval

1. Assertion: move the context-map system out of willdan-blueprints
   into the flywheel plugin; `map-check` invoked via
   `${CLAUDE_PLUGIN_ROOT}`; willdan-blueprints keeps only its
   `context-map/maps/` data (this touches the willdan repo — its
   removal leg routes through that org's own tracker).
2. Assertion: the writeback skill's gate list and the blueprint repos'
   `[pre-merge]` hooks point at the plugin copy.
3. `agentplot/blueprints` gains its `context-map/maps/` when its first
   map writeback lands — no empty scaffold ahead of content.
