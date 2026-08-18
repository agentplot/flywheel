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
| `settled-history` | a decision made and closed, or a finding proved | a session-under-intent record + decision record, carrying a books-verdict |
| `live-work` | forward work, open questions, unbuilt design | a queued tracker item with a provenance pointer, at Backlog |

Two columns qualify the lane and neither was in the promise:

- **coverage** — for `settled-history` only: is it already in the
  destination books (`covered`), partly (`partial`), or not
  (`absent`)? A `covered` row converts to a pointer, not to a chapter.
- **currency** — is the material still true, or true-when-written? The
  corpus's own findings log warns that its early blocks describe a
  since-replaced design (`findings.md` F8).

## Evidence rule

Every row cites a line in the artifact that settles the call, quoted
short. Where nothing in the text settles it, the row says `INFERRED`
and names what it was inferred from, or the row goes to
**unsettleable** and becomes a question for the operator rather than a
silently chosen lane — clause 3.

## Reading

Five parallel readers were dispatched over disjoint clusters
(`SPIKE.md`; `reports/`; `docs/` + `.claude/spike/`; `archive/` +
READMEs + fixtures; and a corpus-versus-books overlap audit). **None
returned before the session settled**, so every row here is the
session's own reading. That is worth stating rather than smoothing
over, because it bounds the rows two ways:

- **Read in full by the session:** all of `SPIKE.md` except the bodies
  of §12's finding blocks; `docs/book-boundaries.md`,
  `book-supervisor.md`, `book-supervisor-log.md`,
  `book-supervisor-state.json`, `archive/README.md`,
  `reports/spike-roadmap.html` and `reports/index.html`; the opening
  status block of every other `docs/` and `.claude/spike/` file; and
  the relevant chapters of `books/geo-iq` and `books/atlas-kit`.
- **Laned on the corpus's own evidence rather than a full read:** the
  four `archive/SPIKE-0*.md` bodies (3,903 lines) and nine of the
  eleven report bodies. Those rows cite the corpus's own summaries —
  `archive/README.md`'s per-spike verdicts, `reports/index.html`'s
  descriptions, `SPIKE.md`'s own citations of each report — which is
  real evidence and is named as such in the row, but it is weaker
  than a read, and a later session may sharpen those rows.

No row was accepted that the session could not check. Where the check
was a pointer rather than a reading, the row says so.

That the fan-out produced nothing usable is itself worth carrying into
#266: **an import session's reading is not obviously parallelisable.**
Most of what made this cut work — the marker harvest, the
corpus-versus-books coverage call, the stale-roadmap contradiction,
the ledger that named the delta — came from holding several artifacts
in view at once, which is exactly what splitting the corpus across
readers prevents.
