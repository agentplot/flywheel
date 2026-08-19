## 1. Read the sources before writing the page

- [ ] 1.1 Re-read `openspec/changes/site-teaches-the-system/sessions/2026-08-18-beats-and-tour/README.md` "Outcomes" from disk — Q2 in particular: Overview is a second page, `overview.html`, linked from the topbar, chosen so the diagrams stay rendered, linkable and styled. Done when the answer and its stated cost basis are in hand from the file, not from this task list.
- [ ] 1.2 Re-read the move-plan table in the same directory's `site-mockups.html` — the "What leaves the home page, and where it lands" table, and the `Overview` block that summarises it as "actors + write scopes · bolt state machine · plugin-dev". Done when the four items destined for this page are known from the mock.
- [ ] 1.3 Re-read `decisions/page-teaching-order.md` from disk for the "What leaves the home page" paragraph. Done when the demotion list is read at source.
- [ ] 1.4 Re-read `decisions/coupling-word.md`. It was absent from this branch at spec time; check the working path first, and fall back to `git show faedc0a:openspec/changes/site-teaches-the-system/decisions/coupling-word.md`. Done when the wording rule is read AND the path-and-commit actually used is written down for the item comment.
- [ ] 1.5 Recover the demoted markup: `git show 8a8e468^:site/index.html`, sections `#actors` and `#bolt` and the "Working on the flywheel itself" and "Where the rest of it is written down" blocks inside `#install`. Done when the source markup is in hand rather than reconstructed from memory.
- [ ] 1.6 Read `README.md`'s "The construction loop — a bolt", "The actors", "Install" and "Working on the flywheel itself" sections. Done when the differences between the README and the recovered markup are listed — the spec's decision 2 makes the README the arbiter, so this list is the page's content plan.
- [ ] 1.7 Record the baseline: `node scripts/check-site.mjs` on the untouched tree, and its reported page and diagram counts. Done when captured, so any later failure is attributable to this change.

## 2. The page shell

- [ ] 2.1 Create `site/overview.html` with the head and the topbar: title and `<meta name="description">` addressing the operator, the favicon data URI, the `<link rel="preload">` for the faces the page paints, and a topbar whose mark links back to `index.html`. Done when the page loads standalone and offers a way home.
- [ ] 2.2 Copy the `@font-face` block and the `:root` custom-property block **verbatim** from `site/index.html` into the page's inline `<style>`. Done when the two blocks are byte-identical to their originals and a diff of the two files shows them as identical regions.
- [ ] 2.3 Carry the rest of the design system as a subset: ground and 28px grid on `html, body`, `.wrap`, link and focus styles, topbar, `section.panel`, `h2`/`h3`/`.sub`/`.caption`, `table`, `.figure`, `pre.block` and the `.mermaid` theme rules. Do not carry hero, plate, tab-strip, walk-strip or ratio-cell rules. Done when the page uses every rule it ships and ships no rule for a component it lacks.
- [ ] 2.4 Give each section a stable id, `actors` and `bolt` among them. Done when `overview.html#actors` and `overview.html#bolt` both land on the right section.

## 3. The actors

- [ ] 3.1 Carry the write-scope flowchart as a `pre.mermaid` block. Done when it parses and every node it declares carries a class — `check-site`'s `classDef` coverage rule is all-or-nothing on flowcharts.
- [ ] 3.2 Check the diagram's actors and edges against `README.md` "The actors" and correct where they disagree. Done when every box and arrow traces to a README claim.
- [ ] 3.3 Rebuild the actor table from `README.md`'s table — seven actors including `flywheel-interactive-session`, and no `spec / apply / testing` row. Done when the two tables name the same actors and no row asserts a write scope the README does not.
- [ ] 3.4 Carry the caption explaining that grey boxes are write scopes, and the README's three load-bearing consequences: a session closes what it was charged with while the loop opens what it discovered; dispatch is the only actor bridged to a human; nothing messages anything else, the tracker is the only bus. Done when all three are on the page.

## 4. Inside a bolt

- [ ] 4.1 Carry the bolt state diagram as a `pre.mermaid` `stateDiagram-v2` block, with the state names unchanged: `to-spec`, `specced`, `in-review`, `approved`, `building`, `built`, `verified`, `merged`. Done when it parses and the sequence matches `README.md` "The construction loop — a bolt".
- [ ] 4.2 Rewrite the caption. It carried "the merge gate, the acceptance suites and the full release gate never relax" — name the checks for what they are instead. Keep the point that what is bounded is *reading*: a bounced review returns a row to `to-spec` once, and after that the row takes one call on the evidence in hand and builds. Done when the caption says the same thing without the two banned words.

## 5. Working on the flywheel itself, and where the rest is written down

- [ ] 5.1 Carry the `--plugin-dir` block and its explanation from `README.md` "Working on the flywheel itself" — point Claude Code at a checkout and `/reload-plugins`, no publish and no version bump between an edit and trying it. Done when the two commands and the reason are on the page.
- [ ] 5.2 Carry the "Where the rest of it is written down" list — the README, `skills/`, `agents/`, `schemas/` — as absolute GitHub URLs. Done when each link resolves to a real path in the repository, checked rather than assumed.

## 6. The wording sweep

- [ ] 6.1 Sweep every rendered string on `site/overview.html` for "gate" and "release", the `<meta name="description">` and every diagram label included. Done when `grep -in 'gate\|release' site/overview.html` returns only unrendered markup, a quoted literal machinery name, or a state name, and each surviving hit has been eyeballed and justified.
- [ ] 6.2 Confirm no phrasing renders the coupling as a place or a mechanism rather than an act the reader performs. Done when each remaining mention reads as something someone does.

## 7. The one edit to the home page

- [ ] 7.1 In `site/index.html`, change the topbar Overview link's `href` from `https://github.com/agentplot/flywheel#readme` to `overview.html`, and delete the three-line comment above it that explains the stand-in. Done when the diff on `site/index.html` is those lines and nothing else.
- [ ] 7.2 Leave the footer's "Docs" link to the README alone — it is not the Overview destination. Done when the footer is unchanged.

## 8. Checks and hand-off

- [ ] 8.1 `node scripts/check-site.mjs` green, reporting **two** pages and both new diagrams parsing with every reference resolving. Done when it exits 0 and the page count has gone from the 1.7 baseline to 2.
- [ ] 8.2 `node scripts/check-paths.mjs` and `sh scripts/validate-manifests.sh` green. Done when both exit 0.
- [ ] 8.3 Open `site/overview.html` in a real browser. Confirm both diagrams render with non-zero geometry rather than as collapsed or blank boxes, and that the console is clean. `check-site` proves a diagram parses, never that it renders. Done when observed, not assumed.
- [ ] 8.4 Confirm `document.scrollWidth == clientWidth` at 1440, 1280, 1024 and 390 CSS pixels wide — wide tables and diagrams scroll inside their own containers, never the document. Done when measured at all four.
- [ ] 8.5 Load the page with scripting disabled and confirm it reads as a scrolling document: prose, tables and links all present, diagrams degrading to their source rather than to a blank region. Done when observed.
- [ ] 8.6 Follow the topbar Overview link from `site/index.html` and the way back. Done when both resolve in a browser, not only under `check-site`.
- [ ] 8.7 Commit by pathspec — `git add -- site/overview.html site/index.html openspec/changes/site-overview-page/tasks.md` then `git commit -- <those paths>` — with a `Refs: #347` footer. Never `-a`, never `add -A`. Done when the commit carries only the paths this change wrote.
- [ ] 8.8 Report in the item comment: which path and commit `coupling-word.md` was read from; every place the README overrode the demoted markup, per decision 2; and any claim the README and `skills/_reference/tracker.md` disagree about that the page had to take a side on. Done when each is stated rather than left for a reader to infer.
