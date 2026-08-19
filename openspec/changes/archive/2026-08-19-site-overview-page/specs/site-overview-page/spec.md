## Purpose

`site/overview.html` is the destination for the operator reference the home
page demotes: the actors and their write scopes, the states a bolt's work
moves through, and how to work on the flywheel itself. It addresses the reader
who has already installed the plugin, and it exists so the home page can
address the stranger without the shed content going missing.

## ADDED Requirements

### Requirement: The overview page addresses the operator, and the home page keeps the stranger

`site/overview.html` SHALL exist and SHALL carry the operator reference
`decisions/page-teaching-order.md` demotes off the home page: the actors —
write-scope diagram and actor table — the states a bolt's work moves through,
"working on the flywheel itself", and where the rest of it is written down.

It SHALL address a reader who has installed the plugin. It SHALL NOT re-teach
the five beats, and SHALL NOT carry the hero plate, the ratio cells or the
beat-3 walk — those are the home page's, and a second copy of them would make
two pages that must be kept true about the same thing.

#### Scenario: The demoted content has an address

- **WHEN** a reader follows the site's Overview link
- **THEN** the actor table, the write-scope diagram, the bolt state sequence
  and the `--plugin-dir` instructions are all on the page that loads
- **AND** none of them requires reading the repository to find

#### Scenario: The overview page does not duplicate the home page

- **WHEN** `site/overview.html` is read end to end
- **THEN** it carries no hero plate, no five-beat nav, no ratio cells and no
  seven-step walk

### Requirement: Every claim on the page traces to this tree's README

The overview page is reference, so it SHALL be true of the machinery as this
branch documents it. Every factual claim on the page — each row of the actor
table, each edge of the write-scope diagram, each state in the bolt sequence —
SHALL trace to a section of `README.md` on the branch the change lands on.

Where the markup unit 1 removed from `site/index.html` and `README.md`
disagree, `README.md` SHALL win: it is the reference of record, and the
removed markup is a summary of it that has drifted. The overview page SHALL
NOT amend `README.md` to close a disagreement — the README's own accuracy is
not this page's to settle.

#### Scenario: The actor table matches the reference of record

- **WHEN** the actor table on `site/overview.html` is compared row for row
  against the actor table in `README.md` under "The actors"
- **THEN** every actor named in the README's table appears, including the
  interactive session profile
- **AND** no row names an actor the README's table does not carry

#### Scenario: A drifted claim is dropped rather than shipped

- **WHEN** the moved markup asserts something `README.md` contradicts
- **THEN** the page carries the README's version
- **AND** the README is left unedited by this change

### Requirement: The coupling is called approval on this page too

The wording rule `decisions/coupling-word.md` sets for the site SHALL hold on
`site/overview.html` exactly as it holds on the home page: the coupling is
named **approval**, and "gate" and "release" SHALL NOT appear in rendered copy
except inside a quoted literal machinery name — a command, a file name, a
state name, a hook name.

The bolt state names (`to-spec`, `specced`, `in-review`, `approved`,
`building`, `built`, `verified`, `merged`) are literal machinery vocabulary
and SHALL be carried unchanged. Prose about them is copy and SHALL follow the
rule: the checks that run before a merge are named for what they are, not
called a gate.

#### Scenario: The banned words do not reach the reader

- **WHEN** the rendered text of `site/overview.html` is searched for "gate"
  and "release"
- **THEN** every hit is inside a quoted literal machinery name, an HTML
  comment, or a script
- **AND** no hit is prose the reader is asked to understand

#### Scenario: The state sequence survives the rule

- **WHEN** the bolt state diagram is read
- **THEN** it still names `to-spec`, `specced`, `in-review`, `approved`,
  `building`, `built`, `verified` and `merged`

### Requirement: Both diagrams render as diagrams, from the shipped bundle

The write-scope diagram and the bolt state diagram SHALL be `pre.mermaid`
blocks rendered client-side from `site/vendor/mermaid.min.js` — the bundle the
repository ships — and SHALL NOT be replaced by prose, an image or a table.
Keeping them rendered, linkable and styled is the reason
`sessions/2026-08-18-beats-and-tour/README.md` records for choosing a second
page over README anchors, and a page that flattens them has not paid for
itself.

They SHALL render under the same `mermaid.initialize` configuration
`site/index.html` uses, so that the theme, fonts and colours match the site and
so the diagram `node scripts/check-site.mjs` parses is the diagram the reader
sees.

No diagram SHALL be laid out inside a hidden container at render time.

#### Scenario: The merge criterion parses both diagrams

- **WHEN** `node scripts/check-site.mjs` runs against a tree carrying this
  change
- **THEN** it reports two pages and every diagram parsing
- **AND** it exits 0

#### Scenario: The flowchart satisfies the coverage rule

- **WHEN** the write-scope flowchart declares any `classDef` assignment
- **THEN** every node it declares carries a class

#### Scenario: A diagram is never measured at zero width

- **WHEN** the page renders its diagrams
- **THEN** every diagram's container is laid out and measurable at that moment

### Requirement: The page is reachable from the home page and reachable into

`site/index.html` SHALL reach `site/overview.html` by relative link from the
topbar, and that link SHALL be the only change this capability makes to the
home page.

`site/overview.html` SHALL offer the reader a way back to the home page, and
SHALL give its sections stable fragment ids — including `actors` and `bolt`,
the two the home page gave up when the content left it — so that a reader or a
document can link to a section rather than to the top of the page.

#### Scenario: The topbar link resolves to a file

- **WHEN** the topbar's Overview link on `site/index.html` is followed
- **THEN** it is a relative reference to `overview.html`
- **AND** `node scripts/check-site.mjs` resolves it to a file on disk

#### Scenario: The lost fragments have an address again

- **WHEN** `overview.html#actors` or `overview.html#bolt` is opened
- **THEN** the page scrolls to the actors section and the bolt states section
  respectively

#### Scenario: The reader can get back

- **WHEN** a reader arrives on `site/overview.html` from anywhere
- **THEN** the page offers a link to the home page

### Requirement: The page is self-contained and ships no new dependency

`site/overview.html` SHALL load nothing from a network origin: the fonts,
the mermaid bundle and every style it uses SHALL come from files already in
`site/`. It SHALL NOT add a build step, a package dependency, or a vendored
file that is not already there.

Every relative `href` and `src` on the page SHALL resolve to a file that
exists, so `node scripts/check-site.mjs` reports no dead reference. Where the
page would point at something a later unit builds — a tour page — it SHALL do
so by absolute URL or by unlinked text, never by a relative link to a file not
yet on disk.

#### Scenario: Nothing is fetched from a CDN

- **WHEN** the page's `href` and `src` references are listed
- **THEN** every one of them is either a relative path into `site/` or an
  absolute URL to a page a reader chooses to visit
- **AND** no stylesheet, script or font is loaded from a third-party origin

#### Scenario: The page does not block on unit 3

- **WHEN** `node scripts/check-site.mjs` runs against a tree carrying this
  change and no tour page
- **THEN** it reports every reference resolving, and exits 0

### Requirement: The page is legible on a phone and in a keyboard

`site/overview.html` SHALL be readable at 390px wide without the document
scrolling horizontally: content wider than the viewport — a diagram, a wide
table — SHALL scroll inside its own container rather than widening the page.

Interactive elements SHALL be reachable by keyboard with a visible focus
indicator, and the page SHALL remain a readable scrolling document with
JavaScript disabled, degrading to unrendered diagram source rather than to a
blank region.

#### Scenario: The document never scrolls sideways

- **WHEN** the page is measured at 1440, 1280, 1024 and 390 CSS pixels wide
- **THEN** the document's scroll width equals its client width at each

#### Scenario: The page survives without JavaScript

- **WHEN** the page is loaded with scripting disabled
- **THEN** every section's prose, table and link is present and readable
