## Context

This is unit 2 of 3 in `bolt/site-five-beats`. Unit 1 (`site-home-five-beats`,
merged to the bolt branch as `d988e03`) removed the operator reference from
`site/index.html`; this change gives it a home. Four constraints on this tree
shape the approach, and each was read from disk while writing this document.

1. **The site is plain static files with no build step.** `openspec/config.yaml`
   says so of `site/`, and the tree bears it out: `site/` holds `fonts/`,
   `index.html` and `vendor/` — no stylesheet, no bundler config, no
   `package.json` script that produces the page. `site/index.html` carries its
   whole design system in one inline `<style>`.

2. **`scripts/check-site.mjs` walks every `.html` under `site/` except
   `vendor/`.** Its `htmlFiles` walker skips `vendor` and dotfiles and takes
   everything else, so a second page is picked up with no registration. It
   parses `pre.mermaid` blocks against `site/vendor/mermaid.min.js` under
   jsdom, applies an all-or-nothing `classDef` coverage rule to flowcharts
   only, and resolves every `href`/`src` that does not match
   `^(https?:|mailto:|data:|#|//)`. It does **not** resolve CSS `url()` — the
   comment in `site/index.html`'s head says as much, which is why the fonts
   are also `<link rel="preload">`ed.

3. **`decisions/coupling-word.md` is still not on this branch.**
   `git merge-base --is-ancestor faedc0a HEAD` returns false and
   `git branch -a --contains faedc0a` names only
   `sess/planning-site-teaches-the-system`. Its text was read at that commit.
   `decisions/page-teaching-order.md` **is** present here and still carries
   the pre-amendment beat 4 ("the gate", "one word releases a whole batch").
   Unit 1 resolved this the same way and shipped the amended wording; this
   change follows it.

4. **The removed markup has drifted from `README.md`.** The actor table unit 1
   removed carries a `spec / apply / testing` row and omits the interactive
   session; `README.md`'s table under "The actors" names seven actors
   including `flywheel-interactive-session` and has no such row. The removed
   bolt-state caption says "the merge gate, the acceptance suites and the full
   release gate never relax" — two words the wording rule bans.

## Goals / Non-Goals

**Goals:**

- Settle how the site's design system reaches a second page when there is no
  stylesheet and no build step.
- Settle which text wins where the removed markup and `README.md` disagree, so
  the build session is not left arbitrating.
- Settle how the two diagrams render on a page with no tab layer, given that
  `site/index.html`'s mermaid setup exists specifically to work around hidden
  containers.
- Settle how far into `site/index.html` this change reaches.

**Non-Goals:**

- Restructuring `README.md`. The unit card's "Left out" says it stays the
  reference of record, and correcting it is not a construction session's.
- Building any tour page. Unit 3 owns those.
- Removing `vendor/mermaid.min.js` and the mermaid CSS from
  `site/index.html`, which now has zero diagrams. Unit 1's build session
  flagged the dead weight and left it deliberately; it is a home-page edit,
  not this unit's, and this change's write to `site/index.html` is one href.
- Extracting a shared stylesheet. See decision 1.
- Restyling. The palette, type scale and mermaid theme are reused as they
  stand.

## Decisions

### 1. The design system is copied into `overview.html` as an inline subset, not extracted to a shared stylesheet

`site/overview.html` carries its own `<style>` block holding the parts of the
home page's design system it actually uses: the `@font-face` rules, the
`:root` custom properties, the ground and grid on `html, body`, `.wrap`, link
and focus styles, the topbar, and the panel, table, figure, caption, code
block and `.mermaid` theme rules. It does not carry the hero, plate, tab
strip, walk strip or ratio-cell rules — the page has none of those
components.

The `@font-face` block and the `:root` block are copied **verbatim** from
`site/index.html`, byte for byte, so drift between the two pages' palettes
shows up as a diff rather than as a colour that is subtly wrong.

*Why:* a shared `site/site.css` is the better end state and is the wrong move
in this change. Extracting it rewrites the whole head of `site/index.html` —
a file unit 1 landed minutes ago and unit 3 has not finished with — for a
benefit that is invisible to the reader, and it does it inside the one unit
whose card names its home-page write as "topbar link". Two pages is also the
point at which duplication is cheapest to carry and hardest to justify
paying down; the case gets stronger at five pages, which is where unit 3
leaves the site.

*Alternatives considered:*

- **Extract `site/site.css` and link it from both pages.** One source of
  truth, and `check-site` resolves a `<link href>` so the reference stays
  under the merge criterion. Rejected here for scope: it is a refactor of
  unit 1's file, it collides with unit 3's work on the same head, and it is
  worth its own item where it can be reviewed as a refactor rather than
  riding in as a side effect of building a page.
- **Copy the entire `<style>` block unedited.** Simpler to write and simpler
  to diff, but it ships ~200 lines of rules for components the page does not
  have, and the next reader cannot tell which rules are load-bearing.
- **Write a minimal bespoke stylesheet.** Rejected: the unit card says "in
  the site's design system", and a page that merely looks similar is the
  failure mode the operator's Q2 answer was buying against.

### 2. Where the removed markup and `README.md` disagree, the README wins

The page is reference, and its truth condition is the machinery, not the
markup it inherited. The build session reproduces the demoted sections but
checks each claim against `README.md` on the branch, and takes the README's
version wherever they differ. Concretely, on this tree: the actor table is
rebuilt from the README's table (seven actors, including
`flywheel-interactive-session`; no `spec / apply / testing` row), and the
README's three "load-bearing consequences" replace the older single paragraph
about dispatch.

*Why:* the alternative is a page that is false on the day it lands. The
demoted markup was already a lossy summary of the README, written earlier;
copying it verbatim would ship a reference page contradicting the reference of
record two clicks away, and the drift would be invisible to every check this
repo runs.

*Alternative considered:* **carry the markup verbatim and open an item for the
correction.** Rejected — it knowingly ships a wrong page and pays for the fix
twice. The README's own inaccuracies are a different matter and are left
alone; see Risks.

### 3. The wording rule is applied to prose and stops at literal machinery names

"Approval" replaces "gate" in every sentence a reader is asked to understand.
The bolt state names are carried unchanged, because they are the literal
strings the machinery uses and `decisions/coupling-word.md` exempts quoted
literal machinery output. The removed caption's "the merge gate, the
acceptance suites and the full release gate never relax" becomes a sentence
naming the checks for what they are — this repo's pre-merge checks, its
acceptance run, and the checks that run before a bolt lands.

*Why:* the rule's own text draws the line at "quoted literal machinery
output", and a state named `approved` in a diagram of states is exactly that.
Renaming the states to satisfy a copy rule would make the page disagree with
the machinery it documents.

### 4. Diagrams render with `startOnLoad: false` and one explicit `mermaid.run()`

`overview.html` reuses `site/index.html`'s `mermaid.initialize` configuration
verbatim — same theme, same `themeVariables`, same font family — and then
calls `mermaid.run({ querySelector: "pre.mermaid" })` once. It runs no tab
layer, so no diagram is ever inside a hidden container and nothing measures
zero width.

*Why:* the home page's elaborate ordering exists to solve the hidden-panel
problem, which this page does not have — but the *configuration* is what makes
the diagram the reader sees match the diagram `check-site` parses, and that
reason applies to every page on the site. Splitting the two lets the page drop
the machinery it does not need and keep the part that is load-bearing.

*Alternative considered:* **`startOnLoad: true`.** Fewer lines, and correct on
a page with no hidden containers. Rejected narrowly: the failure it invites is
silent (a diagram laid out before its container is sized renders collapsed),
the site already has one page whose comments explain that failure at length,
and an explicit `run()` costs three lines.

### 5. `site/index.html` changes by one href and the comment above it

The topbar's `href="https://github.com/agentplot/flywheel#readme"` on the
Overview link becomes `href="overview.html"`, and the three-line comment above
it — which exists only to explain the stand-in — is removed with it. The
footer's separate "Docs" link to the README is left alone: it points at the
README on purpose and is not the Overview destination.

*Why:* unit 1's `design.md` named this exact edit as unit 2's — "unit 2
re-points it" — and the unit card names the contention on `site/index.html` as
"the rebuild there, the topbar link here". Anything more makes this change a
second author on a file that already has one.

## Risks / Trade-offs

- **`README.md` and `skills/_reference/tracker.md` do not agree about how a
  bolt tracks its work, and this page follows the README.** The README
  describes "a registry of proposals" whose rows move
  `to-spec → specced → in-review → approved → building → built → verified →
  merged`; `skills/_reference/tracker.md` — the plugin's own shared reference,
  which never uses the word "registry" — describes tracker items carrying one
  `stage:*` label each, written by the bolt loop as `stage:planned`,
  `stage:built`, `stage:verified`, `stage:merged`. Decision 2 makes the README
  the arbiter, so the page ships the registry sequence. That is a design-level
  question about which document is right, it belongs to the design loop, and
  this change does not settle it. It is reported to the operator rather than
  fixed here. *Mitigation:* the page's claims are traceable to a named README
  section, so when the README is corrected the page's correction is mechanical.

- **Two inline copies of the palette can drift.** Mitigated by decision 1's
  verbatim-block rule: a divergence is a diff between two identical blocks,
  which review can see. Not eliminated — a shared stylesheet is the real fix
  and is deferred to its own item.

- **`check-site` proves a diagram parses, never that it renders.** The same
  gap unit 1 hit. Mitigated the same way: the build session opens both pages
  in a real browser and confirms the diagrams have non-zero geometry, rather
  than resting on a green check.

- **The page inherits whatever the README gets wrong.** Accepted deliberately:
  a construction session correcting the machinery's public description is a
  design act, and the unit card leaves the README out.

## Migration Plan

None. `site/overview.html` is a new file, and the one edit to
`site/index.html` replaces an absolute URL with a relative one that resolves
in the same commit. The bolt's named merge criterion,
`node scripts/check-site.mjs`, is green before and after: before this change
it reports one page, after it reports two. No reader-facing URL is retired —
`#actors` and `#bolt` stopped resolving on the home page in unit 1 and start
resolving on `overview.html` here.

## Open Questions

None blocking the build. The README/tracker divergence under Risks is
recorded for the operator and does not gate this change: the page is
buildable, checkable and internally consistent under decision 2 whichever way
that question is later settled.
