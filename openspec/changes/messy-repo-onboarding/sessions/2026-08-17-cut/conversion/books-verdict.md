# Books-verdict — `SPIKE.md` L1585–L1644, the Atlas/GEOIQ seam

**Verdict: NO CHANGE NEEDED — already written.**

Clause 2 of the promise requires that design material either update the
books or carry "an explicit verdict on whether the books should be
updated — a per-artifact books-verdict, never a silent discard." This
is that verdict for the converted artifact, with the evidence a
disputing operator would open.

Destination books: `WilldanGroup/willdan-blueprints`, working tree
`main` at `2a7c8327`, suites under `books/<suite>/src/`.

## Claim-by-claim

| corpus claim (`SPIKE.md`) | book chapter that carries it | verdict |
| --- | --- | --- |
| GEOIQ registers the `kb` family against atlas3's deriver SPI and owns the extractors and `kb:` policy tags (L1591–L1593, L1606) | `books/geo-iq/src/admission.md` L56–L64, §"The `kb` sidecar family": "GeoIQ registers the `kb` sidecar family with [`atlas-framework`](../atlas-kit/sidecars.md)'s deriver SPI and owns the `kb:` policy tags and the geo extractors" | covered |
| the framework transports and addresses, never interprets a `kb` row — "atlas3 can never grow a `kb` verb" (L1610–L1612) | `books/geo-iq/src/admission.md` L63: "The framework transports and addresses; it never interprets a `kb` row." | covered |
| two build lanes, data plane vs control plane, same worker and row shape, different admission gate (L1626–L1632) | `books/geo-iq/src/admission.md` L66–L79, §"The build verbs": "`geoiq kb build` is one command with two paths… they differ in which rows a build may read", then `--from-sidecars` = "the **data plane** path" and `--release <r>` = "the **control plane** path" | covered, and **sharpened** — the book adds the caveat the spike lacks: "Review is not bypassed — review governs what enters *shared* releases" |
| ownership split as a table of concerns (L1595–L1608) | `books/geo-iq/src/substrate-boundaries.md` L1–L28 — the same split rendered as a Boundary/Owner/Used-for table, opening "Geo IQ owns the [admission decisions](admission.md) and the `kb` sidecar family it registers against the framework's deriver SPI" (L3–L5) | covered |
| the path convention, bytes-only fingerprint, `_manifest.json` append-only writer, consumer addressing (L1598–L1602) | `books/atlas-kit/src/sidecars.md`, §"The address" (L12), §"The manifest and the writer" (L35), §"Derivers" (L49) | covered |
| terminology generalization — a sidecar is a "derived companion artifact" (L1643–L1644, in the Writeback hook) | `books/atlas-kit/src/sidecars.md` L1, the chapter title: "# Sidecars — derived companion artifacts" | covered — the writeback hook's naming instruction was carried out |

## What the verdict does not cover

- The **`## Writeback hook` paragraph** (L1633–L1642) is forward work,
  not design: relocate the `geoiq` package to the platform repo at
  spike-exit, reduce `poc/*.py` to shims, register the extractor
  registry as the real deriver. It is cut to live-work and is out of
  scope for any books question.
- `atlas-framework#239` / PR #240 (`cf001b32`) are outside both the
  corpus and the books. The verdict does not assert they are
  faithfully reflected in atlas3's code; it asserts the books state
  the rule.

## The consequence worth carrying

This verdict was **not reachable from the corpus**. Nothing in
`SPIKE.md` says the seam had been written into `books/geo-iq` — the
corpus's own statement (L1094) points at a `books/knowledgebase/` suite
that does not exist, and the roadmap's close-out step still lists the
writeback as owed ("Findings promote candidate → settled in
`willdan-blueprints/books/knowledgebase/`",
`reports/spike-roadmap.html` L150). Only reading the destination books
produced it.

An importer that reads only the corpus it was handed would have
converted this artifact as unwritten history and duplicated a chapter
that already exists. **The cut is a function of two inputs — the
corpus and the destination books — not one.**
