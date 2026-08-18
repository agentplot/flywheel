# Session: 2026-07-23 — the Atlas/GEOIQ seam

> **Staged conversion, not a landed record.** This file is what the
> converter would write to
> `willdan-blueprints/openspec/changes/kb-spike-import/sessions/2026-07-23-atlas-geoiq-seam/README.md`.
> It is reproduced here because cross-org landing (#267) is open.

## Charge

- Change: `kb-spike-import` (the intent an import of
  `WilldanGroup/knowledgebase-spike` would open)
- Type: imported — reconstructed from a corpus artifact, not run live
- Directory: `sessions/2026-07-23-atlas-geoiq-seam/`
- Goal (as the original work framed it): settle how the sidecar
  machinery the knowledge-base spike proved client-side splits across
  the atlas3/GEOIQ platform boundary, and answer two questions — how
  GEOIQ reaches sidecars, and where "build a KB from sidecars" lives.

## Provenance

| field | value |
| --- | --- |
| corpus | `WilldanGroup/knowledgebase-spike` |
| commit | `ba4b385a` |
| artifact | `SPIKE.md` L1585–L1644 |
| heading | `# Design — the Atlas/GEOIQ seam: sidecar contract vs KB lifecycle (settled)` |
| content sha256 (first 16) | `0c3dded91634b7d8` |
| original date | Settled 2026-07-23 |
| converted by | agentplot/flywheel #270, `sessions/2026-08-17-cut` |

The original session is not recoverable as a transcript — the corpus
records its **outcome**, dated and marked settled, not its running.
This record therefore reconstructs the session from its written
product, which is the most an import of a finished corpus can honestly
claim. The distinction matters and should not be smoothed over: a
converted record says *what was settled and when*, never *how the room
got there*.

## Produced

- `../decisions/atlas-geoiq-seam.md` — the decision record.
- The books-verdict below.

## Delivered

**The split, settled.** atlas3 owns the sidecar contract (address,
fingerprint, manifest, writer) and the dispatch (always-on at the
publish seam, failure-isolated, `atlas3.derivers` SPI); GEOIQ owns the
`kb` family's semantics and everything downstream of the sidecar.
Dependency arrows: GEOIQ → atlas3; atlas3 → nothing. Full statement in
the decision record.

**Two questions answered.** GEOIQ reaches sidecars through SDK methods
only, never path globs — the path template is atlas3's private
implementation detail. "Build a KB from sidecars" lives in GEOIQ as
two lanes of one CLI: `--from-sidecars` is the data plane,
`--release <r>` the control plane; same worker and row shape,
different admission gate.

**Executed before it was recorded.** The source names
`atlas-framework#239` as the spec and PR #240 (`cf001b32`) as the merge
to atlas3 main. The spike section is the record of a decision already
carried out in code, not its origin — which is why the conversion
treats it as history rather than as a proposal.

## Books-verdict

**NO CHANGE NEEDED — already written.** Every claim in the artifact is
already stated in the destination books:
`books/geo-iq/src/admission.md` §"The `kb` sidecar family" (L56–L64)
and §"The build verbs" (L66–L79),
`books/geo-iq/src/substrate-boundaries.md` (L1–L28), and
`books/atlas-kit/src/sidecars.md` (whose title, "Sidecars — derived
companion artifacts", is the exact naming generalization the artifact's
writeback hook asked for). The book is in one place *sharper* than the
corpus: it adds "Review is not bypassed — review governs what enters
*shared* releases", a caveat the spike section never states.

Claim-by-claim evidence: `books-verdict.md` beside this file.

## Residue cut to live-work

`## Writeback hook` (L1633–L1642) is forward work, not design, and is
queued rather than converted: relocate the `geoiq` package to the geoiq
platform repo at spike-exit, reduce `poc/*.py` to delegating shims,
register the extractor registry as the real `kb` deriver. A section
marked `(settled)` carried a live tail — see `../findings.md`.

## Marked processed

`ledger-entry.jsonl` beside this file, keyed on the artifact span and
its content hash so a re-run of the import skips it and a changed
corpus does not.
