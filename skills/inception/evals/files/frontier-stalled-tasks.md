# tasks.md — intent `widget-loop` (openspec/changes/widget-loop/tasks.md)

Fixture for the stall eval. Every task below is unblocked: no task depends
on another, and no decision they need is still open.

## Design

- [x] design: settle the widget registry owner
- [x] design: settle the scout's charge

## Writeback

- [ ] writeback: rewrite `books/aidlc-design/src/widget-loop.md`
- [ ] writeback: rewrite `books/aidlc-design/src/widget-registry.md`
- [ ] writeback: move the `widget-scout` and `widget-registry` nodes on
      `context-map/maps/target.js` to `active`

## Handoff

- [ ] handoff: the widget gateway endpoint → `atlas-kit`
- [ ] handoff: the registry client → `atlas-kit`
- [ ] handoff: the scout's config schema → `cortex-kit`
- [ ] handoff: the widget fixtures → `rocs-kit`
