# How this cut was produced

So the rows can be disputed on method as well as on content.

## Inputs

| input | identity |
| --- | --- |
| corpus | `WilldanGroup/knowledgebase-spike` @ `ba4b385a`, checkout `~/Code/clients/github_willdan/knowledgebase-spike.geoiq-sdk` |
| destination books | `WilldanGroup/willdan-blueprints` @ `2a7c8327`, `books/<suite>/src/*.md` |
| promise | `../../decisions/onboarding-promise.md` (#264) |

The second input is not in the promise's description of the cut. It
turned out to be load-bearing — see `findings.md` F3.

## Scope

The corpus is **`git ls-files '*.md' '*.html'` — 45 files, 11,538
lines**, not the 105 a filesystem walk reports. Sixty of those 105 are
`poc/.venv/lib/python3.12/site-packages/**` and
`packages/geoiq/.pytest_cache/`. Nothing untracked was read.

Code, fixtures' payload data, and the `ui/` application are outside a
planning-document import and are laned but not read line by line.

## Granularity

- **File** where the whole file shares a lane.
- **Section** (`#` / `##`) where it does not — `SPIKE.md` is nine
  concatenated top-level documents and had to be cut at section level
  throughout.
- **Below a section** where a trailing subsection changes lane, which
  turned out to be the normal shape of a settled design block rather
  than an exception (`findings.md` F4).

## The lanes

| lane | means | becomes |
| --- | --- | --- |
| `discard` | superseded and restated elsewhere, duplicated, ephemeral, or dead with the repo | nothing; the row is the record that it was seen |
| `withhold` | live infrastructure identifiers, credentials-adjacent material | a row naming the class and quoting nothing (`findings.md` F11) |
| `settled-history` | a decision made and closed, or a finding proved | a session-under-intent record + decision record, carrying a books-verdict |
| `live-work` | forward work, open questions, unbuilt design | a queued tracker item with a provenance pointer, at Backlog |

Two columns qualify the lane, and neither was in the promise:

- **coverage** — for `settled-history` only: `covered` (the
  destination books already state it — convert to a pointer, not a
  chapter), `absent` (they do not), or **`sole-holder`** (nothing
  anywhere else holds it — it has to survive the corpus before
  teardown, which is a different act from conversion).
- **currency** — is the material still true, or true-when-written?
  The corpus's own findings log warns that its early blocks describe a
  since-replaced design (`findings.md` F8). `stale` marks a row whose
  own status line is contradicted by the source of truth.

## Evidence rule

Every row cites a line in the artifact that settles the call, quoted
short. Where nothing in the text settles it, the row says `INFERRED`
and names what it was inferred from, or the row goes to
**unsettleable** and becomes a question for the operator rather than a
silently chosen lane — clause 3.

## Reading

Five parallel readers were dispatched over disjoint clusters
(`SPIKE.md`; `reports/`; `docs/` + `.claude/spike/`; `archive/` +
READMEs + fixtures; and a corpus-versus-books overlap audit). **Three
returned, well after the session had produced and committed a complete
cut of its own; two (`SPIKE.md`, the overlap audit) never delivered.**

So the cut has two layers, and the rows say which they rest on:

- **The session's own reading** — all of `SPIKE.md` except the bodies
  of §12's finding blocks; `docs/book-boundaries.md`,
  `book-supervisor.md`, `book-supervisor-log.md`,
  `book-supervisor-state.json`, `archive/README.md`,
  `reports/spike-roadmap.html` and `index.html`; the opening status
  block of every other `docs/` and `.claude/spike/` file; and the
  relevant chapters of `books/geo-iq` and `books/atlas-kit`. This is
  the only layer covering `SPIKE.md`, since that reader never
  returned.
- **Full reads by the returning readers**, folded after verification —
  all 11 reports, all 13 `docs/` + `.claude/spike/` files, and all 20
  archive/README/fixture files including section-level rows for the
  four `archive/SPIKE-0*.md` bodies.

**Every folded claim was re-checked against the corpus before it
changed a row.** One did not survive: a reader reported that
`spike-02-report.html`'s cited source file "does not exist in this
repo". The report cites the bare filename
`SPIKE-02-managed-graph-influence.md`; the file is present at
`archive/SPIKE-02-managed-graph-influence.md`. The citation does not
resolve from where it is written, which is a real defect and a much
smaller one than a missing file. That row was not changed.

## What the fan-out was worth

Both things are true and neither is the obvious one.

**The split cost the session its best material for a while.** Every
call that carried the cut — the marker harvest, the coverage call
against the destination books, the stale roadmap contradicting the
findings log, the ledger that named the delta — came from holding
several artifacts in view at once, which is exactly what handing one
cluster to each reader prevents. None of it came from a reader.

**And the readers caught what a single pass could not afford.** The
regions they read in full are the regions the session had laned on
summaries — and three of those rows were wrong, in both directions:
`archive/SPIKE-03` promoted when it settles nothing (2,142 lines),
`scripts/README.md` and the 14-provider survey discarded when they are
sole holders.

The reading that produced judgement did not parallelise; the reading
that produced coverage did. That is the trade #266 is choosing
between, and it is not a trade between speed and quality — it is a
trade between two different kinds of correctness.