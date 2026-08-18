# Assertion: overview.html carries the operator reference the home page sheds

- **Repo:** agentplot/flywheel — `site/overview.html`
- **Item:** #306
- **Raised by:** the handoff session `sessions/2026-08-18-bolt-plan/`, from
  the operator's answer to Q2 in
  `../sessions/2026-08-18-beats-and-tour/README.md` (item #284).

## The claim

`site/overview.html` exists, is linked from the topbar of every page in
`site/`, links back to the home page, and renders in the same design system
as `site/index.html` — same tokens, same vendored fonts, same plate
geometry, no network fetches. It carries, rendered rather than linked away:

- the actors and their write scopes, including the write-scope diagram;
- the bolt state machine;
- "working on the flywheel itself" — the plugin-dev material;
- the deep links into the README for anything past reference depth.

It addresses the reader who has already decided to look inside — depth is
allowed here, and it is the only page where it is. Its mermaid blocks parse
under the bundle in `site/vendor/`, so `node scripts/check-site.mjs` passes.

## Why

The decision `../decisions/page-teaching-order.md` demotes operator content
off the home page behind "one Overview/docs link"; the operator's round
chose the second-page form over README-only so the diagrams stay rendered
and linkable (Q2, `../sessions/2026-08-18-beats-and-tour/README.md`). The
content itself is not rewritten by this claim — it is the home page's
current `#actors` and `#bolt` sections, moved.

## Boundaries

Does not restructure the home page — that is `home-page-five-beats.md`,
which removes this material from `index.html`; the two are one move and land
in the same bolt. Does not cover the tour pages. Does not rewrite the
README, which stays the reference of record.
