# Decision: flywheel-intent gets its stubbed loop: block

## Decision

`schemas/flywheel-intent/schema.yaml` gains a `loop:` block,
parsed-but-unbuilt — the DECLARE-rung stub the bolt-type schemas
already carry. Its content is the design loop's configurable surface,
the `_flywheel_intent.TYPES` table externalized:

    loop:
      types:
        planning:    {profile: design, model: fable, operator_round: true,  worktree: true}
        interactive: {profile: interactive, model: fable, operator_round: true, worktree: true}
        handoff:     {profile: design, model: opus, operator_round: true,  worktree: true}
        research:    {profile: design, model: "opus[1m]", operator_round: false, worktree: false}
        prototype:   {profile: design, model: opus, operator_round: false, worktree: true, alone: true}
        writeback:   {profile: design, model: opus, operator_round: false, worktree: true}
      hooks: []

The wiring — `TYPES` reading the block — stays unbuilt until the
DECLARE rung is built for the bolt types too.

## Context

- Produced by: `../sessions/2026-08-14-loop-program-decisions/round.md`
  §4, approved by the operator in the plannotator round of 2026-08-16.
- The record's ladder (DECLARE / SCRIPT / FORK) makes a schema `loop:`
  block the end-user channel and says the surface is "STUBBED now and
  built later"; the bolt types honor that
  (`schemas/bolt-quick/schema.yaml:33`), the intent schema silently
  did not — so a repo could shadow a bolt type's config but not the
  design loop's. Queued as #88.

## Consequences

- The build is #209: the schema edit, plus a `schemas/README.md`
  mention if it documents the blocks.
- #88 closes on the ruling.
