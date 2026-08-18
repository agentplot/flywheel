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

One design session, five parallel readers over disjoint clusters
(`SPIKE.md`; `reports/`; `docs/` + `.claude/spike/`; `archive/` +
READMEs + fixtures; and the corpus-versus-books overlap audit), each
returning rows in this schema with its own evidence. The session
judged the lanes, reconciled the readers, and owns every row. No row
was accepted that the session could not check.
