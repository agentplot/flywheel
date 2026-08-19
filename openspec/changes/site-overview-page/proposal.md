## Why

Unit 1 stripped the operator reference out of `site/index.html` — the actor
table, the write-scope diagram, the bolt state machine, and the "working on
the flywheel itself" block — on `decisions/page-teaching-order.md`'s ruling
that the home page addresses the stranger and demotes operator content to a
link. The content went nowhere. It is preserved in git history and in this
unit's brief, and the topbar's "Overview" link currently points at the project
README by absolute URL as a stand-in, with a comment in `site/index.html`
saying so:

> The Overview destination. Until site/overview.html exists this is the
> README by absolute URL; that page, when it lands, re-points this one href
> and nothing else.

`sessions/2026-08-18-beats-and-tour/README.md` records the operator's answer
to Q2: Overview lives as **a second page, `overview.html`, linked from the
topbar** — chosen over deferring to README anchors precisely so the diagrams
stay rendered, linkable and styled. This change builds that page and re-points
that one href.

## What Changes

- **`site/overview.html` is new** — a plain scrolling reference page in the
  site's design system, addressing the operator rather than the stranger. It
  carries the four things the home page shed, in this order: the actors (the
  write-scope diagram and the actor table), inside a bolt (the state
  sequence), working on the flywheel itself (the `--plugin-dir` loop), and
  where the rest of it is written down.
- **The moved content is brought level with this tree's README.** The page's
  job is to be the operator reference, so every claim on it traces to a
  section of `README.md` as it stands on this branch; where the markup unit 1
  removed and the README disagree, the README wins. The removed actor table
  is the loser in two places — it lists a `spec / apply / testing` row the
  README's table no longer has, and it omits the interactive session profile.
- **The wording rule reaches the moved copy.** Per
  `decisions/coupling-word.md`, the coupling is *approval*; *gate* and
  *release* survive only inside a quoted literal machinery name. The removed
  bolt-state caption said "the merge gate, the acceptance suites and the
  release gate never relax" and the removed actor prose said "released it" —
  both are rewritten. The state names themselves (`to-spec`, `specced`,
  `in-review`, `approved`, `building`, `built`, `verified`, `merged`) are
  literal machinery vocabulary and stay.
- **The two diagrams stay diagrams.** The write-scope flowchart and the bolt
  state diagram are `pre.mermaid` blocks rendered against `vendor/mermaid.min.js`
  with the same `mermaid.initialize` configuration `site/index.html` uses, so
  `node scripts/check-site.mjs` parses them with the bundle the reader renders
  with. That was the whole cost basis of the operator's Q2 answer.
- **The fragment ids `#actors` and `#bolt` resolve again**, on
  `overview.html` rather than on the home page. Unit 1's proposal recorded
  their loss as its one BREAKING note; this change gives them an address.
- **`site/index.html` changes by exactly one href** — the topbar's Overview
  link becomes the relative `overview.html`, and the comment above it, now
  spent, goes with it. Nothing else on the home page is touched: unit 1 owns
  that file's structure and this unit's card names the topbar link as its
  only write there.
- **The design system is carried as an inline `<style>` subset, not a shared
  stylesheet.** `site/` is plain static files with no build step, and
  extracting a stylesheet would rewrite the head of a file unit 1 has just
  landed. See `design.md` decision 1.

## Capabilities

### New Capabilities

- `site-overview-page`: what `site/overview.html` carries, who it addresses,
  and the conditions under which it stays true — the destination for the
  operator reference the home page demotes.

### Modified Capabilities

- `site-home-page`: the requirement "The page links to no file the repository
  does not yet hold" fixes the Overview destination as "the project README by
  absolute URL" *until `overview.html` exists*. It exists as of this change,
  so the destination becomes the relative `overview.html` and the rule that
  produced the stand-in — point at a not-yet-built file by absolute URL or
  unlinked text — keeps applying to the tour pages unit 3 has not built.

## Impact

- `site/overview.html` — new file, the whole of this change's weight.
- `site/index.html` — one `href` and the three-line comment above it.
- `openspec/specs/site-home-page/spec.md` — one requirement modified at
  archive time.
- `node scripts/check-site.mjs` — this bolt's named merge criterion. It gains
  a second page to walk: two more mermaid blocks to parse, and every relative
  reference on the new page to resolve. Its `classDef` coverage rule is
  all-or-nothing on flowcharts and the moved write-scope diagram classes every
  node it declares, so it arrives satisfying that rule; the state diagram is
  not a flowchart and the rule does not reach it.
- No dependency, tooling or manifest change. `vendor/mermaid.min.js` and
  `site/fonts/` are reused where they sit.
