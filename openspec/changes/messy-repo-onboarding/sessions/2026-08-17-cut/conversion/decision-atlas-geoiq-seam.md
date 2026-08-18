# Decision: the Atlas/GEOIQ seam — atlas3 owns the contract, GEOIQ owns the semantics

> **Staged conversion, not a landed record.** This file is what the
> converter would write to
> `willdan-blueprints/openspec/changes/kb-spike-import/decisions/atlas-geoiq-seam.md`.
> It is reproduced here because cross-org landing (#267) is open. Its
> subject belongs to WilldanGroup, not to agentplot.

## Decision

The sidecar machinery the knowledge-base spike proved client-side
splits across the atlas3/GEOIQ platform boundary in three layers:

- **atlas3 owns the contract** — what a sidecar is, where it lives,
  how it is addressed: the path convention
  `_<family>/<item prefix>/extractor=<t>/schema=<vN>/fp=<fp>/`, the
  bytes-only fingerprint (paths excluded), the `_manifest.json` schema
  and its append-only writer, and consumer addressing
  (`derive_sidecars` / `list_sidecars` / `sidecar_path`).
- **atlas3 owns the dispatch** — always-on tag dispatch at the publish
  seam, funnelled through `finalize_manifest`, failure-isolated so
  derivation can never fail a publish; third parties register families
  through the `atlas3.derivers` entry-point group.
- **GEOIQ owns the semantics** — the `kb` family's extractors,
  `extraction.yml` params and LLM lanes; kb-central
  (inbox/staged/rejections/catalog/releases); review; release-create;
  and both build lanes.

Two consequences of the split were settled with it:

- **GEOIQ reaches sidecars through SDK methods only, never path
  globs.** The path template is atlas3's private implementation
  detail; the contract is `list_sidecars`/`sidecar_path` plus the
  manifest schema. The same rule holds on the write side, so
  append-only enforcement stays framework-owned.
- **"Build a KB from sidecars" lives in GEOIQ, as two lanes of one
  CLI.** `geoiq kb build --from-sidecars` is the data plane —
  warehouse `_kb/` mirrors read directly, no kb-central, no review.
  `geoiq kb build --release <r>` is the control plane — kb-central
  `staged/` joined to a release manifest, downstream of review. Same
  worker, same row shape, different admission gate.

The framework stays schema-agnostic about row content: the deriver
family owns its parquet row schema and atlas3 writes whatever table the
deriver returns. That is why atlas3 can never grow a `kb` verb — the
moment it interprets one family's rows, the SPI split dies.

Dependency arrows: GEOIQ → atlas3; atlas3 → nothing.

## Context

- **Settled 2026-07-23**, during the knowledge-base spike.
- **Source artifact:** `WilldanGroup/knowledgebase-spike` at
  `ba4b385a`, `SPIKE.md` L1585–L1644, heading
  `# Design — the Atlas/GEOIQ seam: sidecar contract vs KB lifecycle (settled)`.
  The ownership table is L1595–L1608; the two answered questions are
  L1614–L1632.
- **Corroborating evidence named in the source, outside the corpus:**
  `atlas-framework#239` specified the split and **PR #240 merged it to
  atlas3 main at `cf001b32`**. The decision was therefore already
  executed in code when the spike recorded it — the spike is the
  record, not the origin.
- **Rendered view of the same material:**
  `reports/web-lane-design.html` and `reports/atlas-grounding.html`
  are derived from `SPIKE.md`, which the corpus itself declares the
  only source of truth (`reports/spike-roadmap.html`, standing rules:
  "SPIKE.md is the only source of truth").

## Consequences

- **The books already say this.** See the books-verdict beside this
  file (`books-verdict.md`): the rule is stated in
  `books/geo-iq/src/admission.md`, `books/geo-iq/src/substrate-boundaries.md`
  and `books/atlas-kit/src/sidecars.md`. This record captures the
  decision's provenance and date; it does not ask for a book edit.
- **The source section's `## Writeback hook` (L1633–L1644) is not part
  of this decision.** It is forward work and is cut to the live-work
  lane: relocate the `geoiq` package to the geoiq platform repo at
  spike-exit, reduce `poc/*.py` to delegating shims, and register the
  extractor registry as the real `kb` deriver. Settled terminology
  that *did* land: the release verb is `release create`, and the
  generalized name for a sidecar is atlas3's *derived companion
  artifact*.
- **The corpus's declared writeback destination does not exist.**
  `SPIKE.md` L1094 names `../willdan-blueprints/books/knowledgebase`
  (`commissioning.md` + `contracts/commissioning.yaml`) as the source
  book. There is no `books/knowledgebase/` suite. The material landed
  in `books/geo-iq` and `books/atlas-kit` instead. Any importer that
  trusts the corpus's own statement of where its history belongs will
  aim at a directory that was never created.
