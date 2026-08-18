# site-home-page Specification

## Purpose
What `site/index.html` teaches a stranger who has installed nothing, and in
what order — the five beats and their sequence, the split-hero fold, what the
page sheds to Overview, and the one word the page uses for the coupling.
## Requirements
### Requirement: The home page addresses the stranger, and teaches five beats in order

`site/index.html` SHALL present its content as five top-level beats in this
order, each earning the next:

1. What it is, in one plain sentence — above the fold.
2. The problem — why one conversation fails.
3. The mechanism, walked — one idea, end to end.
4. Your approval — and how little it costs.
5. Install — two commands, last.

No sixth top-level beat SHALL be added, and the order SHALL NOT be varied.
The problem precedes the mechanism (`decisions/page-teaching-order.md`,
settled sub-question Q3).

The page's in-page navigation SHALL name these five beats and no others,
replacing today's five tab labels ("Why two loops", "The two loops", "The
actors", "Inside a bolt", "Install" — located by those strings in `nav.tabs`,
never by line number).

#### Scenario: A stranger reads the page top to bottom

- **WHEN** a reader who has installed nothing scrolls `site/index.html` from
  the top
- **THEN** they meet a plain sentence saying what the thing is, then why one
  conversation fails, then one idea walked end to end, then what their own
  approval costs them, then how to install it
- **AND** they meet no other top-level section

#### Scenario: The nav names the beats

- **WHEN** the in-page nav strip is read
- **THEN** its entries are the five beats
- **AND** none of the five superseded tab labels appears

### Requirement: The fold is a split hero carrying a plain sentence and the plate

Beat 1 SHALL be a split hero: the plain-language identity sentence in the
left column with the poetic deck riding **under** it, and the ring plate in
the right column at approximately 46% of the hero's width.

The identity sentence SHALL name the system as **an AI-DLC harness**, in
substance: an AI-DLC harness for Claude Code — teams of agents on two coupled
loops, design and construction, built on OpenSpec. The deck MAY ride beside
the plain sentence; it SHALL NOT stand instead of it.

The five-beat nav SHALL be within view on beat 1's screen without scrolling.

The plate SHALL remain on the page as beat 1's illustration. It is the ONLY
architecture picture the home page carries; no second architecture diagram
SHALL be introduced by this change.

#### Scenario: The fold says what the thing is

- **WHEN** a reader loads the page and does not scroll
- **THEN** a plain sentence identifying the system as an AI-DLC harness is
  visible
- **AND** the ring plate is visible beside it
- **AND** the five-beat nav is visible

#### Scenario: The deck does not stand alone

- **WHEN** the hero copy is read
- **THEN** the poetic deck appears below the plain sentence, not in place of it

### Requirement: The ratio cells leave the fold and close beat 3's walk

The four ratio cells (`1 turn`, `1 : 2`, `1 : 6`, `1 : 24` — located by those
strings) SHALL NOT appear in the fold. They SHALL appear as the closing row
of beat 3's walk, after its last step.

#### Scenario: The numbers arrive after the journey that explains them

- **WHEN** a reader reaches the ratio figures
- **THEN** they have already read the seven-step walk
- **AND** the figures sit beneath that walk as its closing row

### Requirement: Beat 3 walks one idea end to end, naming the artifact each step leaves

Beat 3 SHALL walk **one raw sentence** through seven steps in this order —
dispatch, intent, session, decision, approval, bolt, merged — and each step
SHALL name the artifact it leaves behind.

The fifth step SHALL be titled **approval**.

The subject SHALL be one idea's journey, not the architecture of the loops.
Beat 3 SHALL NOT reproduce the flowchart of both loops that today's "The two
loops" panel carries.

#### Scenario: The walk is a journey, not a map

- **WHEN** beat 3 is read
- **THEN** it follows a single raw sentence through seven named steps
- **AND** each step shows what it leaves behind
- **AND** no diagram of the two loops' architecture appears

#### Scenario: The fifth step is named for the act

- **WHEN** the walk's fifth step is read
- **THEN** it is titled "approval"

### Requirement: The coupling is called approval, and "gate" and "release" leave the page

Every stranger-facing string in `site/index.html` SHALL render the coupling
as something the reader does — "your approval", "you approve a batch", "one
approval starts construction" — and never as a place or mechanism.

The words "gate" and "release" SHALL NOT appear in any string a reader sees,
including the `<meta name="description">` content and every `<text>` element
rendered inside the plate SVG. The two plate labels reading `GATE` SHALL be
relabelled.

The single exception is a quoted literal machinery name — a command,
filename, hook name or program output reproduced verbatim. Markup that no
reader sees (CSS class names, HTML comments, SVG element ids) is out of this
requirement's scope.

This requirement follows
`openspec/changes/site-teaches-the-system/decisions/coupling-word.md`, whose
Consequence 1 amends `decisions/page-teaching-order.md` beat 4 to "Your
approval — and how little it costs." That record was not present on this
branch when this spec was written and was read at commit `faedc0a`; the
implementing session SHALL re-read it and SHALL report which path and commit
it read.

#### Scenario: A reader never meets the old words

- **WHEN** every rendered string on the page is read, the meta description
  and the plate's SVG labels included
- **THEN** neither "gate" nor "release" appears
- **AND** the only occurrences anywhere in the file are in unrendered markup
  or inside a quoted literal machinery name

#### Scenario: Beat 4 carries the amended title

- **WHEN** beat 4's heading is read
- **THEN** it names the reader's approval and what it costs them, not a gate

### Requirement: Beat 4 teaches the reader's own place in the loop

Beat 4 SHALL tell the reader what they personally do and what it costs: that
plans and diffs open in a browser to annotate or approve, that one approval
covers a whole batch, and that past that approval the work runs without them.

This is the page's differentiator and SHALL be taught here, not in beat 1.

#### Scenario: The differentiator lands in beat 4

- **WHEN** beat 4 is read
- **THEN** the reader learns they annotate or approve in a browser, that one
  approval covers a batch, and that the work then proceeds unattended
- **AND** beat 1 does not carry that claim

### Requirement: Operator reference leaves the home page

`site/index.html` SHALL NOT carry the actor table, the write-scope diagram,
the bolt state machine, or the "Working on the flywheel itself" block. These
are operator reference and a stranger has no use for them at first contact.

Beat 5 SHALL carry the two install commands and the documentation links, and
nothing else.

#### Scenario: The stranger is not handed the operator's manual

- **WHEN** the page is read end to end
- **THEN** no actor table, write-scope diagram or bolt state machine appears
- **AND** the install beat carries only the two commands and the doc links

### Requirement: The page links to no file the repository does not yet hold

Every relative `href` and `src` in `site/index.html` SHALL resolve to a file
that exists in `site/`, so that `node scripts/check-site.mjs` reports no dead
reference.

Where the page points a reader at operator reference or at a deeper tour that
a later unit will build, it SHALL do so by absolute URL or by unlinked text —
never by a relative link to a file not yet on disk. The Overview destination
SHALL be reachable, and until `overview.html` exists that destination is the
project README by absolute URL.

#### Scenario: The merge criterion passes on this change alone

- **WHEN** `node scripts/check-site.mjs` runs against a tree carrying this
  change and neither `overview.html` nor any tour page
- **THEN** it reports every reference resolving, and exits 0

#### Scenario: The reader is never pointed at nothing

- **WHEN** a reader looks for the operator reference this page sheds
- **THEN** the page offers a destination that loads

