# Decision draft — the operator tour

Inherits #180 (closed on `intent/onboarding-first-run`, never worked).

## The decision

The operator tour is **a section of the site**, the operating half of
the site's tour: what the operator types, in which pane, and what
appears on the tracker and the board as a result — one normal turn of
the crank seen from the outside. Its sibling, the concept tour (the
page a stranger meets before installing anything), belongs to
`intent/site-teaches-the-system`; the two halves share the site's tour
frame.

**Form: show the thing, not a description of it.** The tour is built
from a real run of the quickstart path — actual prompts, the actual
tracker items and board rows that resulted — rendered as
transcript-and-result pairs, never as hand-written narrative about what
would happen. A tour whose examples were composed rather than recorded
drifts the first time the machinery changes and nobody notices.

## The boundary with the sibling intent

- **This intent owns the tour's content**: the sequence, the prompts,
  the shown results, their accuracy.
- **`intent/site-teaches-the-system` owns the page**: the frame both
  tours sit in, navigation, visual treatment.

Content lands in whatever frame the sibling settles; neither intent
blocks the other's drafting, and the seam is a coordination item only
if the frames diverge.

## Who writes into it

- Born from a `type:interactive` session (the #180 mockup, revived on
  this milestone) — the operator annotates a lavish mockup before
  anything lands on the site.
- Maintained by the same rule as the quickstart: a change that alters
  what the operator types or what comes back updates the tour's
  affected pair in the same change. The recorded-transcript form makes
  the staleness checkable — the pair either still reproduces or it
  does not.

## Consequences (queued items once the round closes)

- Revive #180 as a new `type:interactive` item on
  `intent/operating-docs`: mock up the operator tour from the
  quickstart's real transcript; blocked by the quickstart draft.
- A one-line coordination note to `intent/site-teaches-the-system`
  (through the report, not a raw relay): the operating tour's content
  arrives from this intent; the tour frame should expect two halves.
