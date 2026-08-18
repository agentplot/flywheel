## Context

See `proposal.md` — Why. Three constraints on this tree shape the approach,
and each was read from disk while writing this document:

1. **`scripts/check-site.mjs` fails the merge on a dead relative reference.**
   Its link pass collects every `href`/`src`, skips anything matching
   `^(https?:|mailto:|data:|#|\/\/)`, and fails when a relative path does not
   resolve to a file. `site/` today holds `fonts/`, `index.html` and
   `vendor/` — no `overview.html`, no tour pages. This change is unit 1 of 3;
   its destinations do not exist yet.
2. **The amending decision is not on this branch.** `decisions/coupling-word.md`
   is absent from `openspec/changes/site-teaches-the-system/decisions/` here;
   `git merge-base --is-ancestor faedc0a HEAD` returns false and
   `git branch -a --contains faedc0a` names only
   `sess/planning-site-teaches-the-system`. Its text was read at that commit.
   `page-teaching-order.md` **is** present on this tree and still carries the
   pre-amendment beat 4 — the heading "Your place in it — the gate, and how
   little it costs" and the phrase "one word releases a whole batch".
3. **The hero plate renders the word GATE.** The `<!-- ====== gates ====== -->`
   group inside the plate SVG draws two 76×28 boxes with `<text>` reading
   `GATE`. The decision keeps the plate as beat 1's illustration, so the
   wording rule reaches inside it.

## Goals / Non-Goals

**Goals:**

- Settle how unit 1 refers to destinations units 2 and 3 have not built, in a
  way that passes `check-site` unchanged.
- Settle which wording the build follows where the two decision records
  disagree, and record why.
- Settle the form beat 3's walk takes, so the build does not reach for a
  diagram the decision excludes.

**Non-Goals:**

- Building `overview.html` or any tour page. Unit 2 and unit 3 own those; the
  unit card's "Left out" says so.
- Relocating the removed sections' content anywhere. This change removes it
  from the home page; it is preserved in git history and in unit 2's brief,
  and this change does not stage it in a holding file.
- Restyling. The palette, type scale, plate geometry and `nav.tabs` sticky
  mechanism are reused as they stand; this is a restructure, not a redesign.
- Amending `page-teaching-order.md`. That record belongs to the design loop —
  see Risks.

## Decisions

### 1. Overview and the tour are reached by absolute URL in unit 1, not by relative link

The topbar gains no relative `overview.html` href in this change. The
existing topbar "Docs" link — an absolute
`https://github.com/agentplot/flywheel#readme` — is the destination for the
operator reference this change sheds, and beat 3's "go deeper" affordance is
written as text without a relative href until unit 3 lands.

*Why:* `check-site` treats a relative href to a non-existent file as a `dead
reference` failure, and it is this bolt's named merge criterion. A relative
link to `overview.html` would block unit 1's own merge on unit 2's work,
serializing the bolt on a technicality and making unit 1 unmergeable in
isolation.

*Alternatives considered:*

- **Ship a stub `overview.html` in unit 1.** Rejected: the unit card lists the
  Overview destination under "Left out" as unit 2's, and a stub would be a
  second author's half-built page for unit 2 to inherit or delete.
- **Omit the affordance entirely.** Rejected: `page-teaching-order.md` says
  operator content demotes to a link, not to nothing, and the decision's own
  wording — "moved behind one Overview/docs link **or deferred to the
  README**" — makes the README a sanctioned destination.
- **Relative link plus a `check-site` exemption.** Rejected: weakening the
  merge criterion to land a change is the one thing this bolt's charter says
  is never done.

*Unit 2 re-points it.* When `overview.html` exists, the topbar link moves from
the README URL to the page. That is unit 2's task, not a debt hidden here.

### 2. Beat 4 follows `coupling-word.md`, and the build states where it read it

Beat 4 is titled **"Your approval — and how little it costs."** The coupling
is "approval" throughout; "gate" and "release" appear only inside a quoted
literal machinery name.

*Why:* `coupling-word.md` is the later closure (item #301, the operator's
plannotator round) and its Consequence 1 says in terms that
`page-teaching-order.md` beat 4 "is amended with this closure". The assertion
this change specs carries the amended wording, and the unit card names the
rule. The two records do not conflict on the merits — one supersedes the
other, and the superseding one has simply not reached this branch.

*Alternative considered:* **follow the record present on this tree** ("the
gate"). Rejected: it would build the page the operator explicitly overturned,
and the correction would come back as a finding on the built page.

*The provenance is stated, not assumed.* The build session re-reads both
records at build time. If `coupling-word.md` has reached the branch by then,
it reads it in place; if it has not, it reads it at `faedc0a` and the fact
that it did so is reportable, not silent.

### 3. Beat 3's walk is a CSS strip, not a mermaid diagram

The seven-step walk is markup and CSS in the page's existing idiom — a row of
step cells, each carrying the step name and the artifact it leaves — with the
four ratio cells as a closing row beneath it.

*Why:* `page-teaching-order.md` says the home page keeps **at most one
architecture picture: the hero plate**. A mermaid flowchart of the journey is
a second one. The mock-up's own `.cwalk` block is a CSS grid for the same
reason, and a CSS strip is also outside `check-site`'s mermaid parse and
`classDef`-coverage rules, so it cannot fail them.

*Alternative considered:* **reuse the existing `#loops` mermaid flowchart,
trimmed.** Rejected: that diagram is the architecture of both loops, which is
precisely what the decision says beat 3 is not about — "The tour's subject is
one idea's journey, not the architecture."

### 4. The plate's GATE labels become approval labels

The two `GATE` boxes inside the plate SVG are relabelled. The rects are 76
units wide for a four-character word; a longer word needs the rect widened
and the `<text>` re-centred on the new box, or the label shortened. The build
picks the fit that keeps the plate's geometry — the geometry is the
illustration, and the label serves it.

*Why:* the plate stays on the page as beat 1's illustration, the labels are
rendered text a stranger reads, and the wording rule has no carve-out for
text inside an SVG. `<text>` inside the plate is not quoted machinery output.

### 5. The five beats own the page's fragment ids

The `nav.tabs` strip keeps its sticky mechanism and its markup shape and
gains the five beat labels; each `section.panel` takes a beat id. The old ids
`#why`, `#loops`, `#actors`, `#bolt`, `#install` do not survive as aliases.

*Why:* nothing outside `site/index.html` links to them (verified — see
`proposal.md` — What Changes), so alias anchors would be dead weight added to
a page whose whole point is shedding weight.

## Risks / Trade-offs

- **`coupling-word.md` never reaches `main`, and the built page cites a
  decision the repo does not hold** → The build session records in its item
  comment which path it read the record from and at which commit. The record
  reaching `main` is the design loop's to land; this is reported to the
  operator as a finding from the spec stage, not resolved here.
- **`page-teaching-order.md` on this branch keeps saying "the gate" after the
  page stops saying it** → Left standing deliberately. A decision record is
  the design loop's artifact and a construction session does not edit one;
  `coupling-word.md` Consequence 1 already records the amendment as owed. The
  divergence is visible rather than papered over.
- **Unit 2 slips and the shed operator reference stays only in git history** →
  The content is recoverable from `site/index.html` at this change's parent
  commit, and unit 2's card carries the move-plan table naming every piece.
  The topbar README link means the page never points at nothing in the
  meantime.
- **The walk reads as a list rather than a journey** → The mock-up's
  `.cwalk` renders each step as *name → artifact it leaves*, which is what
  makes it a walk rather than a table of contents; the build follows that
  shape. Whether it lands is the kind of thing the operator sees on the built
  page, and a finding there is cheap.
- **Widening the plate's label boxes disturbs the ring geometry** → The boxes
  sit at x=180 and x=644 on a 900-wide viewBox, clear of the ring paths; a
  wider rect grows into empty space. If it cannot be made to fit, the fallback
  is a shorter label, never the old word.
