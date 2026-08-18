# Session — 2026-08-18 beats-and-tour

Interactive session for intent/site-teaches-the-system, items #284 and #285,
briefed by the closed decision `../../decisions/page-teaching-order.md`.

- `site-mockups.html` — the one page carrying both decisions, opened for the
  operator with lavish-axi. Rendered in the site's own design system
  (palette, type and plate geometry from `site/index.html`) so every mockup
  shows the product as it would look.
  - **Decision 1 (#284)** — the restructured home page: today's fold beside
    two candidate five-beat folds (A: split hero; B: stacked, plate
    trimmed), the whole-page order side by side with today's, and the table
    of what leaves for Overview. Questions queued from the page: fold
    variant (Q1), where Overview lives (Q2), where the ratio cells go (Q3).
  - **Decision 2 (#285)** — the concept tour: a live, walkable 7-station
    stepper (dispatch → intent → session → decision → gate → bolt → merged),
    three candidate concepts (export backoff, onboarding email order,
    dashboard dark theme), each station showing the artifact it leaves.
    Questions: which concepts ship (Q4), which form the tour takes (Q5).
- `fonts/` — the four woff2 faces vendored from `site/fonts` (SIL OFL 1.1,
  licences beside them) so the committed page renders faithfully offline.

## Outcomes — the operator's round (one round, session ended by operator)

Answers, queued from the page's controls:

- **Q1 · beat-1 fold**: **variant A — split hero.** Plain sentence left with
  the deck riding under it, plate right at ~46% width, five-beat nav pinned
  in view.
- **Q2 · Overview's home**: **a second page, `overview.html`**, linked from
  the topbar — diagrams stay rendered and linkable.
- **Q3 · ratio cells**: **into beat 3's walk** as a closing row after the
  last step.
- **Q4 · tour concepts**: **all three ship** — export backoff, onboarding
  email order, dashboard dark theme.
- **Q5 · tour form**: **scrollytelling** — one tall page per concept, the
  rail pins and advances on scroll (the mock's stepper was demonstrative
  only).

Corrections folded into the page during the round:

- `proposal.md` → `intent.md` in the intent-step artifact trees.
- "station" (my coinage) → plain "step" throughout the tour.
- The walk's fifth step is labelled **approval**, not "gate"; its copy was
  de-jargoned (no "flip", no "release"). The operator asked whether
  "approval" should replace "gate" generally — that conflicts with
  `page-teaching-order.md`'s beat 4 ("the gate"), so it is queued as its own
  item rather than resolved here.
- The **design book** is named as the spec's source of truth (was "the
  decision record").
- The word "release" swept from all journey copy, including "each email
  releases the next" → "unlocks".
- The "whole page" comparison section gained a plain intro naming its
  point: the move plan for today's sections.

Item comments on #284/#285 point here; the loop promotes these closures.
