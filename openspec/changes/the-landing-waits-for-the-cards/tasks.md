## 1. Read the tree before changing it

This change is task 3 of `bolt-of-units` and its three siblings —
`planner-owns-the-milestone`, `expansion-makes-a-unit` and
`the-bolt-job-filter` — are merged. Parts of the shape below are already
on disk, put there by the first of them. A task is done when the file
bears out the claim, not when it was edited.

- [ ] 1.1 Re-read `Bolt.run`'s tail in `bin/_flywheel_bolt_loop.py` —
      the block that computes `planned` from the snapshot's plan cards
      and returns before the landing — together with `landing_wanted`,
      `RunReport`, and `bin/flywheel-bolt-loop`'s report rendering.
      Done when you can name, from the file, which of the requirements
      in `specs/flywheel-derived-backlog/spec.md` the tree already
      satisfies and which it does not.

## 2. The hold

- [ ] 2.1 An open unit card on this bolt's milestone holds the landing:
      the loop returns before the landing's expectation gate and before
      any landing session, so no pending approval is written, nothing is
      verified against the bolt branch, nothing reaches the main branch,
      and no item is upgraded. The set is the snapshot's open
      `plan`-labelled cards whose own `bolt/*` milestone is this bolt's
      — a card elsewhere, or one naming no `bolt/*` milestone, is not in
      it — and an expanded unit, which carries `unit` rather than `plan`,
      is never in it.
- [ ] 2.2 The hold outranks a forced landing: it is evaluated without
      consulting the `land` argument, so `land="force"` reports the hold
      rather than landing over it.
- [ ] 2.3 A held run says so on its landing line: `RunReport.landing`
      carries a held statement naming each holding card by number, in
      place of its `"not attempted"` default. Done when
      `flywheel bolt-loop` prints that line and its `--json` carries the
      same string, and a run that simply had no landing to reach for
      still reports `not attempted`.
- [ ] 2.4 The run record keeps the note it writes today — the ledger
      note naming the held landing and its cards — and the observation
      report is still rendered on a held run.

## 3. The units the landing closes

- [ ] 3.1 The landing closes **every** open unit on the bolt's
      milestone, each `closed:done` with the landing SHA in its closing
      comment, plus a parent off the milestone reached through a landed
      item's parentage. Elaborations and already-closed issues are
      skipped, and no sub-issue's state or reason is touched. Done when
      the behaviour holds for a milestone carrying two units, and when
      `close_unit_parents`' own prose names the units rather than "the
      release's unit parent".

## 4. Tests

`sh scripts/test.sh` — stdlib `unittest`, no new dependency.

- [ ] 4.1 In `tests/test_bolt_loop.py`, cover the hold: an open card at
      Backlog holds a landing that is otherwise wanted; a Ready card not
      yet expanded holds it; a card on another milestone and a card with
      no `bolt/*` milestone hold nothing; an expanded unit holds
      nothing; a forced landing is held; and the held run's landing line
      names the card while a run with nothing to land still reads
      `not attempted`.
- [ ] 4.2 Cover the several-units close: a milestone carrying two
      expanded units, each with merged sub-issues, ends with both closed
      `closed:done` at the one landing, no sub-issue closed twice, and
      an elaboration on the same milestone untouched. Extend
      `LandingTest.with_unit`'s single-unit fixture rather than
      replacing what it pins.
- [ ] 4.3 Cover the boundary: a second unit expanded after an earlier
      unit's items merged puts released work on the milestone, the
      landing is declined while that work runs, and one landing follows.

## 5. Gates

- [ ] 5.1 `sh scripts/test.sh` green.
- [ ] 5.2 `devenv shell -- gates` green — `sh scripts/validate-manifests.sh`,
      `node scripts/check-paths.mjs`, `node scripts/check-site.mjs`.
- [ ] 5.3 `openspec validate the-landing-waits-for-the-cards --strict`
      still green after any spec edit made while building.
