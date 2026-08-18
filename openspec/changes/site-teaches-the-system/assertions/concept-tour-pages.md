# Assertion: three scrollytelling tour pages walk one idea end to end

- **Repo:** agentplot/flywheel — `site/tour-*.html`
- **Item:** #TBD
- **Raised by:** the handoff session `sessions/2026-08-18-bolt-plan/`, from
  the operator's answers to Q4 and Q5 in
  `../sessions/2026-08-18-beats-and-tour/README.md` (item #285).

## The claim

Three tour pages ship under `site/`, one per concept, each linked from beat
3 of the home page and each carrying the shared topbar:

- "Exports fail when the API rate-limits us."
- "Onboarding emails arrive out of order."
- "Give the dashboard a dark theme."

Each is **scrollytelling**: one tall page whose rail pins and advances as the
reader scrolls past each step — no controls to learn, and no step hidden
behind a click. Each walks the same seven steps in the same order —
dispatch, intent, session, decision, approval, bolt, merged — and each step
shows the artifact it leaves behind. The steps never vary between the three
pages; only the idea does, and that constancy is the lesson the pages teach.
The subject of every page is one idea's journey, never the architecture.

Copy follows the round's corrections: `intent.md` (never `proposal.md`),
"step" (never "station"), "approval" at step five, the design book named as
the spec's source of truth, and no "release" or "flip" in stranger-facing
copy. The pages read top to bottom with JavaScript disabled — the scroll
rail is enhancement, not the content. `node scripts/check-site.mjs` passes.

## Why

`../decisions/page-teaching-order.md` makes beat 3 the mechanism walked, with
the tour pages as its depth. The operator's round shipped all three concepts
and chose scrollytelling over the mock's stepper and over an all-visible rail
(Q4, Q5 — `../sessions/2026-08-18-beats-and-tour/README.md`); the live
stepper in `../sessions/2026-08-18-beats-and-tour/site-mockups.html` was
demonstrative of the content, not of the form.

## Boundaries

Does not cover the compact seven-step strip on the home page, or the links
into these pages — those are `home-page-five-beats.md`. Does not cover
architecture tours: the decision rules them out of brief.
