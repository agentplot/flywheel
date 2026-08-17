# Tasks

## 1. Retire the route and compose guards

- [x] 1.1 Remove `guard_route`, the `_ROUTE` parser, the route session charge
      and its `route` stage-model entry from `bin/_flywheel_bolt_loop.py`;
      remove `guard_compose` and its wiring in the cycle's guard order
- [x] 1.2 Retire their tests; add the inert-queued-item test: a cycle over a
      milestone holding a queued, unparented open item charges no session,
      creates no unit, and moves nothing
- [x] 1.3 Sweep the retired vocabulary the guards anchored — the
      merge-criteria-test prompt, "Work the discoveries queued on" — from
      `bin/` and `skills/`

## 2. Close every item at merge-back

- [x] 2.1 Drop the `is_assertion` filter in `close_merged` so every item of
      a merged batch closes `closed:merged` with the SHA commented
- [x] 2.2 Align the merge session's work order with the loop owning the
      close — no instruction to close or defer closing
- [x] 2.3 Tests: an expansion-born, `type:*`-less item closes
      `closed:merged` at merge-back; the after chain releases a successor on
      the closed predecessor

## 3. Dispatch authors plan cards

- [x] 3.1 Rewrite the dispatch profile's construction route: dictated work
      becomes a plan card — milestone created when none fits, title
      `Unit: <slug>`, unit document body (task table, type, price), `plan`
      label, board Backlog with the fleet's Team, never Status Ready
- [x] 3.2 Carry the same practice into the inception skill's triage section,
      replacing the retired quick-bolt route's remains
- [x] 3.3 Extend the vocabulary drift test so the retired born-ready phrasing
      cannot return to the profile or skill

## 4. Validation

- [x] 4.1 `openspec validate dispatch-to-bolt --strict` green
- [x] 4.2 Full suite green (`python3 -m unittest discover -s tests`)
