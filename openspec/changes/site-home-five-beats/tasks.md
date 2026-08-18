## 1. Read the sources before touching the page

- [ ] 1.1 Re-read `openspec/changes/site-teaches-the-system/decisions/page-teaching-order.md` from disk. Done when the five beats, the "at most one architecture picture" rule and settled Q1–Q3 are in hand from the file, not from this task list.
- [ ] 1.2 Re-read `decisions/coupling-word.md`. It was absent from this branch at spec time; check the working path first, and fall back to `git show faedc0a:openspec/changes/site-teaches-the-system/decisions/coupling-word.md`. Done when the wording rule is read AND the path-and-commit actually used is written down for the item comment.
- [ ] 1.3 Re-read `sessions/2026-08-18-beats-and-tour/README.md` "Outcomes" (Q1 split hero, Q2 `overview.html`, Q3 ratio cells into the walk) and the move-plan table plus the `.cwalk` block in `sessions/2026-08-18-beats-and-tour/site-mockups.html`. Done when the target fold and walk shapes are known from the mock, which renders in the site's own design system.
- [ ] 1.4 Record the baseline: `node scripts/check-site.mjs` green on the untouched tree, and the current `site/index.html` line count. Done when both are captured, so any later failure is attributable to this change.

## 2. Beat 1 — the split hero

- [ ] 2.1 Restructure the hero into two columns: identity sentence and deck left, plate right at ~46% width. Done when the plate renders beside the copy at desktop width and stacks without overflow at narrow width.
- [ ] 2.2 Write the plain identity sentence — an AI-DLC harness for Claude Code: teams of agents on two coupled loops, design and construction, built on OpenSpec — and place the existing deck beneath it. Done when the deck no longer stands alone.
- [ ] 2.3 Move the four ratio cells and the `.foot` strip out of the hero. Done when the hero carries no ratio figure.
- [ ] 2.4 Relabel the two `GATE` `<text>` labels in the plate SVG's `<!-- ====== gates ====== -->` group, widening or re-centring the 76×28 rects (x=180 and x=644) as the new label needs. Done when neither box reads "GATE" and the ring geometry is visually unchanged.

## 3. The five-beat navigation and section ids

- [ ] 3.1 Replace the five `nav.tabs` labels and hrefs with the five beats, keeping the strip's existing sticky mechanism and markup shape. Done when the nav names the beats and nothing else.
- [ ] 3.2 Give each `section.panel` its beat id; retire `#why`, `#loops`, `#actors`, `#bolt`, `#install` without alias anchors. Done when every nav href resolves to a section on the page.
- [ ] 3.3 Confirm the nav is within view on beat 1's screen without scrolling at a common laptop viewport. Done when observed, not assumed.

## 4. Beat 2 — the problem, moved up and shrunk

- [ ] 4.1 Move today's "Why two loops" content into beat 2's position and halve its prose, keeping its three cards. Done when the section is beat 2 and its prose is materially shorter.
- [ ] 4.2 Rewrite any copy in it that names a gate or a release, per the wording rule. Done when the section's strings pass the sweep in task 7.1.

## 5. Beat 3 — one idea, walked

- [ ] 5.1 Build the seven-step walk as a CSS strip in the page's existing idiom — dispatch, intent, session, decision, approval, bolt, merged — each step naming the artifact it leaves, following the mock's `.cwalk` shape. No mermaid diagram. Done when the seven steps and their artifacts render.
- [ ] 5.2 Write the walked sentence the steps carry (the mock walks "Exports fail when the API rate-limits us."). Done when one raw sentence is visibly the subject of all seven steps.
- [ ] 5.3 Add the four ratio cells as the walk's closing row. Done when the figures sit beneath the last step.
- [ ] 5.4 Add the "go deeper" affordance as unlinked text — the tour pages are unit 3 and do not exist. Done when no relative href points at a tour page.
- [ ] 5.5 Delete today's "The two loops" panel, including its mermaid flowchart of both loops. Done when the architecture flowchart is gone and the page's only architecture picture is the plate.

## 6. Beat 4, beat 5, and what leaves

- [ ] 6.1 Write beat 4, "Your approval — and how little it costs": annotate or approve in a browser, one approval covers a whole batch, past it the work runs without you. Done when the section exists and beat 1 carries no version of that claim.
- [ ] 6.2 Delete the "The actors" section (actor table and write-scope diagram) and the "Inside a bolt" section (bolt state machine). Done when neither appears in the file.
- [ ] 6.3 Delete the "Working on the flywheel itself" block from Install and trim Install to the two commands and the doc links, as beat 5. Done when beat 5 carries nothing else.
- [ ] 6.4 Point the topbar's Overview/Docs affordance at the project README by absolute URL, with no relative `overview.html` href. Done when the destination is absolute and unit 2 has a single link to re-point.

## 7. The wording sweep

- [ ] 7.1 Sweep every rendered string for "gate" and "release", the `<meta name="description">` content and every SVG `<text>` included. Done when `grep -in 'gate\|release' site/index.html` returns only unrendered markup (CSS class names, HTML comments, element ids) and quoted literal machinery names, and each surviving hit has been eyeballed and justified.
- [ ] 7.2 Confirm no phrasing renders the coupling as a place or mechanism rather than an act. Done when each remaining mention reads as something the reader does.

## 8. Gates and hand-off

- [ ] 8.1 `node scripts/check-site.mjs` green — every reference resolves and every remaining mermaid block parses with all-or-nothing `classDef` coverage. Done when it exits 0.
- [ ] 8.2 `node scripts/check-paths.mjs` and `sh scripts/validate-manifests.sh` green. Done when both exit 0.
- [ ] 8.3 Open the page in a browser at desktop and narrow widths and read it as a stranger would. Done when the five beats read in order and nothing overflows.
- [ ] 8.4 Commit by pathspec — `git add -- site/index.html` then `git commit -- site/index.html` — with a `Refs: #331` footer. Never `-a`, never `add -A`. Done when the commit carries only the paths this change wrote.
- [ ] 8.5 Report in the item comment: which path and commit `coupling-word.md` was read from, and the fact that `page-teaching-order.md` on this branch still carries the pre-amendment beat 4. Done when both are stated rather than left for a reader to infer.
