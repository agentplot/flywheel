## Why

`site/index.html` is the flywheel's first contact with a stranger, and today
it teaches the wrong thing in the wrong order. The fold carries a poetic deck
and no plain sentence saying what the thing *is*; the four ratio cells put
numbers in front of a reader who has nothing to attach them to; and three of
the five tabbed panels — "The actors", "Inside a bolt", and the
"Working on the flywheel itself" block inside Install — are operator reference
that a stranger has no use for on first contact.

`decisions/page-teaching-order.md` settled what the page teaches and in what
order: five beats, the stranger as the only audience, operator content demoted
to a link. This change is beat-for-beat that restructure applied to
`site/index.html`. It is unit 1 of 3 in bolt/site-five-beats and every other
unit hangs off it — `overview.html` (unit 2) exists to receive what this
change removes, and the concept-tour pages (unit 3) exist to be what beat 3
links into.

## What Changes

- **The fold becomes variant A — a split hero.** The plain AI-DLC-harness
  sentence takes the left column with the poetic deck riding under it, the
  ring plate takes the right at ~46% width, and a five-beat nav is in view
  without scrolling. The plate stays; it is beat 1's illustration.
- **The four ratio cells leave the fold** and fold into beat 3's walk as its
  closing row.
- **The page's top-level order becomes the five beats**: what it is · the
  problem · one idea walked · your approval · install. The tab strip's five
  labels are replaced by the five beat labels.
- **"Why two loops" moves up and shrinks** into beat 2. Its three cards
  survive; its prose halves.
- **"The two loops" is recast as beat 3** — a compact seven-step walk of one
  raw sentence (dispatch → intent → session → decision → approval → bolt →
  merged), each step naming the artifact it leaves, with the ratio cells as
  the closing row.
- **Three sections are removed from the home page**: "The actors" (actor table
  and write-scope diagram), "Inside a bolt" (the bolt state machine), and the
  "Working on the flywheel itself" block inside Install. Their destination is
  `overview.html`, which unit 2 builds.
- **Beat 4 is new** — "Your approval — and how little it costs": annotate or
  approve in a browser, one approval covers a whole batch, past it the work
  runs without you.
- **Install becomes beat 5**, trimmed to the two commands and the doc links.
- **The coupling is named "approval" throughout.** "gate" and "release" do not
  appear in stranger-facing copy outside a quoted literal machinery name.
- **BREAKING (in-page anchors only)**: the fragment ids `#actors` and `#bolt`
  stop resolving on the home page; `#why`, `#loops` and `#install` are
  replaced by beat ids. Nothing outside `site/index.html` itself links to
  them — verified on this tree: `grep -rn 'index.html#'` and
  `grep -rn '#actors\|#bolt\|#loops\|#why\|#install'` across `*.md` and
  `*.html` return no hit outside this change's own artifacts.

## Capabilities

### New Capabilities

- `site-home-page`: what `site/index.html` teaches a stranger and in what
  order — the five beats and their sequence, the split-hero fold, what the
  page sheds to Overview, and the wording rule for the coupling. No spec has
  covered `site/` before this change; the prior site work
  (`openspec/changes/archive/2026-08-12-site-refresh/`) ran the no-spec path
  and set `skip_specs: true`, so there is no existing capability to modify.

### Modified Capabilities

None. No requirement in `openspec/specs/` describes `site/`; the seventeen
spec files there all cover `flywheel-*` machinery capabilities.

## Impact

- **`site/index.html`** — the only file whose content this change rewrites.
  935 lines on this tree; the restructure touches the `<meta name="description">`
  line, the topbar, the hero block, the `nav.tabs` strip, and all five
  `section.panel` elements.
- **`scripts/check-site.mjs`** — the merge criterion this bolt names, and the
  binding constraint on sequencing. It fails the build on any relative `href`
  or `src` that does not resolve to a file on disk. `overview.html` and the
  three tour pages **do not exist on this tree** (verified: `ls site/` shows
  `fonts/`, `index.html`, `vendor/` and nothing else). A relative link to
  either from this change would be a `dead reference` failure and the merge
  gate would block it. This change therefore may not link to files units 2
  and 3 have not yet built — see `design.md`, which settles how the Overview
  and tour destinations are referenced from unit 1.
- **Mermaid** — check-site parses every `pre.mermaid` block under the bundle
  the page ships, and enforces all-or-nothing `classDef` coverage on
  flowcharts. Removing "The actors" and "Inside a bolt" removes their
  diagrams; any diagram beat 3 introduces is subject to both rules.
- **No machinery, skill, schema or `bin/` file changes.** `scripts/check-paths.mjs`
  and `sh scripts/validate-manifests.sh` are unaffected but still run at merge.
- **Unit 2 (`overview-reference-page`) inherits a debt**: the sections this
  change removes have no rendered home until it lands.
