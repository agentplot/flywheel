# Assertion: the home page teaches the five beats, opening on the split hero

- **Repo:** agentplot/flywheel — `site/index.html`
- **Item:** #305
- **Raised by:** the handoff session `sessions/2026-08-18-bolt-plan/`, from
  the closed decision `../decisions/page-teaching-order.md` and the operator's
  round recorded in `../sessions/2026-08-18-beats-and-tour/README.md`
  (items #284/#285).

## The claim

`site/index.html` presents five top-level sections, in this order, and
nothing else above them:

1. **What it is** — the fold, in the **variant-A split hero**: the plain
   identity sentence on the left ("An AI-DLC harness for Claude Code: teams
   of agents on two coupled loops, design and construction, built on
   OpenSpec."), the poetic deck riding under it, the ring plate on the right
   at roughly 46% of the fold's width, and the five-beat nav in view without
   scrolling at 1280×800.
2. **The problem** — why one conversation fails: two speeds, two masters.
   Today's `#why` prose roughly halved; its three cards survive.
3. **One idea, walked** — a compact seven-step walk of one raw sentence
   (dispatch → intent → session → decision → approval → bolt → merged), each
   step naming the artifact it leaves, closing with the ratio row
   (1 : 2 : 6 : 24) and links into the tour pages.
4. **Your word** — the approval as the reader's place in the system:
   annotate or approve in a browser, one word covers a whole batch, past it
   the work runs without you.
5. **Install** — the two commands and the doc links; nothing else.

The tab strip (`nav.tabs#walkthrough`) is gone, replaced by the five-beat
nav. The page keeps exactly one architecture picture — the hero plate. The
actor table, the write-scope diagram, the bolt state machine and the
"working on the flywheel itself" material are no longer on this page; each
is reachable through one Overview link in the topbar. Every stranger-facing
word follows the vocabulary closed by item #301. `node scripts/check-site.mjs`
passes.

## Why

`../decisions/page-teaching-order.md` closed the audience (the stranger who
has installed nothing), the five beats and their order, and what leaves the
page. The operator's round on the mock-ups settled the fold (variant A), the
ratio cells' home (into beat 3's walk) and the vocabulary corrections —
`intent.md` not `proposal.md`, "step" not "station", "approval" at step
five, no "release" in journey copy —
recorded in `../sessions/2026-08-18-beats-and-tour/README.md`. Today's page
opens on a poetic deck and five operator-reference tabs, which is the defect
the intent exists to fix.

## Boundaries

Does not cover `site/overview.html`, which receives the demoted operator
reference — that is `overview-page.md`. Does not cover the deep tour pages
beat 3 links into — that is `concept-tour-pages.md`; this assertion covers
only the compact strip on the home page and the links out of it. Does not
change the README.
