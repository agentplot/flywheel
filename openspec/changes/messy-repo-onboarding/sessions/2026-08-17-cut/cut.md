# The cut — `WilldanGroup/knowledgebase-spike` @ `ba4b385a`

The durable triage report clause 2 of the promise asks for: every
piece of the corpus assigned to a lane, with a one-line reason and a
pointer that settles it. Method, scope and lane definitions:
`method.md`. What the exercise taught: `findings.md`.

**Lanes.** `discard` · `withhold` (discard that must not be quoted
forward — `findings.md` F11) · `settled-history` · `live-work`.
Two qualifiers, both added by the measurement and neither in the
promise: **coverage** (does the destination book already carry it) and
**currency** (`current`, or `as-written` — true when written, since
superseded).

---

## A. `SPIKE.md` — 1758 lines, nine concatenated top-level documents

### A1. Front matter and the PoC directive (L1–L1078)

| anchor | lines | lane | reason | evidence |
| --- | --- | --- | --- | --- |
| `#Knowledge-base spike` | L1–L18 | discard | Repo preamble and reading order; no decision, no work. | L3 orients the reader to Part A / Part B; superseded by `README.md`. |
| `#PoC directive` (preamble) | L19–L42 | settled-history · current | States the design as decided, and the five source-control moves the whole system is built on. | L39 "This is **not a list of open questions** — it is the design we intend to prove"; L29–L31 the extract=commit / release=tag mapping. |
| `##1. The spine` | L43–L93 | settled-history · current | The separable extract/build split and the schema-v2 staging row contract — the federation contract everything else assumes. | L45 "source-verified 2026-07-20, notebook `02-Separate-Extract-and-Build`"; the row shape at L59–L64. |
| `##2. The lifecycle` (intro + pattern names) | L94–L102 | settled-history · current | Central/distributed split declared settled, with the pattern names it borrows. | L96 "**Central vs distributed, settled:**". |
| `##2 › The sidecar convention` | L103–L126 | settled-history · covered | Sidecar path convention, idempotency-by-fingerprint, GC-with-primary. | Corpus L107–L115; book `books/atlas-kit/src/sidecars.md` §"The address". |
| `##2 › Review — disposition is positional` | L127–L145 | settled-history · current | `pending = inbox − staged − rejections`; approval IS the copy; rejection is a tombstone. | L132 "**Computed, never stored:**"; L135 "**approved** = **the promotion itself.**" |
| `##2 › The central store — kb-central` | L146–L166 | settled-history · current | The four-prefix layout and the push-only rule. | L164 "**Push-only holds everywhere:** central never reaches out". |
| `##2 › The loop — releases and prebuilds` | L167–L181 | settled-history · current | Five-step extract → prebuild → review → mint → build cycle. | The numbered loop, L168–L181. |
| `##2 › Selection is a BUILD-side selector` | L182–L191 | settled-history · current | Scoping is the builder's job; every exclusion named. | L189–L190 "Every exclusion is **named, never silent**." |
| `##2 › Three build row-sources` | L192–L212 | settled-history · covered | release / prebuild / sidecar, and which plane each belongs to. | Corpus table L197–L201; book `books/geo-iq/src/admission.md` §"The build verbs" L66–L79, which also adds the caveat the corpus lacks. |
| `##2 › The symmetry — a KB-build Atlas integration` | L213–L222 | **live-work** | Explicitly an open question about where KB build lives. | L217 "**Open research:** build extract/build *into* Atlas … vs a separate KB service". |
| `##2 › Approval service — serverless sketch` | L223–L239 | settled-history · as-written | A concrete AWS sketch for the approval service; never built, and the platform around it moved. | Labelled "serverless sketch" in the heading at L223; `docs/book-supervisor-state.json` `tracking[]` lists it nowhere as done. |
| `##2 › Iceberg / S3 Tables: deliberately not now` | L240–L247 | settled-history · current | A rejection with its reasons — the useful kind of settled decision. | L240 "**Iceberg / S3 Tables: deliberately not now.**" and the two-part argument following. |
| `##3. What we prove — and what we do NOT test` | L248–L280 | settled-history · current | The proof obligations, each already annotated with its outcome; plus the platform facts taken as given. | L252 "*(Proven — §12 Phases 0/1, 4.)*"; L263 "**NOT under test (settled):**". |
| `##3 › the unannotated proof bullets` | L253–L255, L258–L259 | live-work · **stale** | Two obligations carry no "Proven" mark — but §12 records Phase 4b green, so only Phase 3 is really open. | L255 "*(Phase 4b.)*" and L259 "*(Phase 3.)*" against L252's "*(Proven — §12 Phases 0/1, 4.)*"; Phase 4b proven at L760. |
| `##4. Where immutability lives` | L281–L296 | settled-history · current | `staged/` + manifest are the version-of-record; nothing mutates; the keep-honest rebuild test. | L287 "**`staged/` + the release manifest are the version-of-record.**" |
| `##5. The graph schema` | L297–L333 | settled-history · current | The node/edge overlay and the provenance rule. | The schema block L302–L322; L324 "every node traces to its catalog item (URN) and fingerprint". |
| `##5 › Open choice: out-of-selection edge targets` | L329–L333 | **live-work** | A named undecided choice with a trigger. | L329 "**Open choice:** … Keep … or drop out-of-selection edges — decide when clone semantics firm up." |
| `##6. Content types, readers, feedback loop` | L334–L347 | settled-history · current | The four content types and their paths into staging. | The table L336–L341, each row annotated "proven". |
| `##6 › The ingestion rule` | L348–L362 | settled-history · current | No source of truth outside a catalog; sidecars always derived; the one sanctioned web deviation. | L350–L352, bolded as the rule. |
| `##6 › What a clone is` | L363–L420 | settled-history · current | Clone = manifest + graph; pair publish; joint admission; two front doors, one door for graphs. | L396 "**Two front doors for primaries, one door for graphs:**"; proven by Phase 6 at L868. |
| `##6 › Deferred: bulk data-authoring in sessions` | L409–L414 | **live-work** | Explicitly deferred with a named trigger. | L409 "**Deferred, with a named trigger:** bulk data-*authoring* in sessions". |
| `##7. Phasing` | L421–L492 | **split — see reason** | The corpus's own progress ledger: each phase is either `DONE (§12, <date>)` or forward. Rows: Phases 0/1, 2, 4, 4b, 4c, 6, 6c → settled-history (pointers to §12); **Phases 3, 5, 7 → live-work**. | L423 "**Phase 0/1 — extract half.** DONE (§12, 2026-07-20)" vs L427 "**Phase 3 — Query + tools.**" with no DONE. |
| `##7 › Phase 5` | L452–L467 | live-work · **contested** | Listed as forward here; `§12` L1024 records the same lane LIVE with four green asserts. | See `findings.md` F8; resolved in favour of §12 by the corpus's own source-of-truth rule. |
| `##8. The harness` | L493–L521 | discard | Command and scenario inventory for a repo scheduled for teardown; describes how to run the spike, not what it decided. | `reports/spike-roadmap.html` L150 close-out: "repo archives beside SPIKE-01/02/03". |
| `##9. Fixture spec` | L522–L549 | discard | Local fixture layout, regenerable and gitignored. | L526 "gitignored/regenerable via `seed_catalog.py`". |
| `##10. Guardrails` | L550–L567 | **withhold** | Live account, region, admin profile, a VPC id, and the IAM grant set. Class recorded; nothing quoted. | `findings.md` F11. Do not carry forward. |
| `##11. Teardown` | L568–L574 | **withhold** | Same class — the teardown sweep names the account's resource identifiers. | `findings.md` F11. |

### A2. `##12. Findings` (L575–L1078) — the settled-findings sink

The whole section is `settled-history`. Its preamble is also the
corpus's own currency warning, and it applies to every row below it.

| anchor | lines | lane | reason | evidence |
| --- | --- | --- | --- | --- |
| `##12` preamble | L575–L583 | settled-history · current | Declares the log append-only and dated, and warns that early blocks describe a since-replaced design. | L578–L583, quoted in `findings.md` F8. |
| `###Phase 0/1 — extract half of the spine` | L584–L626 | settled-history · **as-written** | Proven, dated LIVE; pre-4b, so it references the retired `disposition` column per the preamble. | Header "(LIVE, 2026-07-20)"; preamble L582. |
| `###Phase 2 — build half + hierarchy anchoring` | L627–L655 | settled-history · as-written | Proven and dated; same pre-4b caveat. | Header "(LIVE, 2026-07-20)". |
| `###Phase 4 — catalog staging prototype, offline half` | L656–L686 | settled-history · as-written | Proven; built against the fake catalog that Phase 4c deleted. | Phase 4c L822 "the fake catalog is gone". |
| `###Phase 4 — build_kb LIVE on Neptune Analytics` | L687–L713 | settled-history · current | Backend-parity result: NA and FalkorDB censuses identical. | Header "(2026-07-21)"; §7 L433 cites it as the DONE evidence. |
| `###Phase 4 — build_kb on FalkorDB + anchor-builder root cause` | L714–L749 | settled-history · current | A root-caused negative — the most valuable kind, per the section's own rule. | L580 "A negative is a valid finding — record it without spin." |
| `###Snapshots demote to a cache` | L750–L759 | settled-history · current | A decision stated as a finding: NA snapshots are a fast-restore cache, never the record. | Restated as design at §4 L286–L288. |
| `###Phase 4b — sidecar staging + promote-on-approve loop` | L760–L821 | settled-history · current | The loop's four asserts, twice green. | §7 L436–L442 "All four asserts pass via `scenarios/approve-reject-loop.sh`". |
| `###Phase 4c — Atlas grounding: the loop runs on a REAL catalog` | L822–L867 | settled-history · current | The fake catalog is retired; the loop is green on a real Atlas3 warehouse. | L822 header, and §7 L443–L451. |
| `###Phase 6 — the sticker round trip` | L868–L913 | settled-history · current | Five asserts green; three named sub-findings (bytes-only fp, producer re-encode, inbox identity). | §7 L468–L477. |
| `###Phase 6c — station admission through the pair` | L914–L953 | settled-history · current | Five asserts green; station manifest is a primary, resolution is a deterministic extraction. | §7 L478–L491. |
| `###Phase 4d — sidecar-direct build: the data-plane path is real` | L954–L1023 | settled-history · current | Proves the third row-source; **not listed in §7's phasing at all**. | Present at L954; absent from §7 L421–L492 — a finding reachable only from §12. |
| `###Phase 5 — web lane LIVE as Atlas pipelines on Firecrawl` | L1024–L1078 | settled-history · current | The web lane ran end-to-end with the incremental gate proven live; contradicts §7 and the roadmap. | L1034–L1035 "**\"2 skipped as fresh-and-unchanged\"**"; `findings.md` F8. |

### A3. The design documents (L1079–L1758)

| anchor | lines | lane | reason | evidence |
| --- | --- | --- | --- | --- |
| `#Writeback to the design book` | L1079–L1096 | settled-history · **as-written** | Records dropping the `spike-commissioning` contract machinery and why; its statement of *where* the writeback goes is now false. | L1084 "That machinery is **dropped for this PoC**"; destination claim at L1094 disproved in `findings.md` F3. |
| `##Disposition of the 7 original candidate requirements` | L1097–L1108 | settled-history · current | Seven requirements, each with an explicit disposition — settled / superseded / folded / dead. | The table L1099–L1108, e.g. L1101 "`embedding-model` \| **SETTLED — carries forward.**" |
| `##Settled byproduct — embedding-model` | L1109–L1119 | settled-history · current | A measured contract: model id, dimension, normalization, bit-identical reproducibility. | L1112–L1116 "dim `== 1024`, L2-normalized (`1.000000`), bit-identical run-to-run (`max\|Δ\| = 0`)". |
| `#Design — resolution: one value per KEY (Phase 6b)` — L1120–L1348 | L1120–L1348 | settled-history · current | The vintage-resolution design: the collision, three clocks, identity, the rule, the operating model, the rejected mechanism, the two grains, the station item. | L1184 `## The rule`; L1251 `## Rejected as the mechanism: hierarchical releases + tenant-filtered queries` — a decision with its alternative recorded. |
| `##What has to change` | L1349–L1361 | **live-work** | Named implementation changes the settled rule obliges. | The heading itself; nothing in §12 records them done. |
| `##Phase 6b asserts (when picked up)` | L1362–L1383 | **live-work** | The proof obligations for a phase not started. | "(when picked up)" in the heading. |
| `##Still open — needs the operational workflow` | L1384–L1404 | **live-work** | Explicitly open, with the assumption being run on meanwhile. | "Still open — needs the operational workflow, assumed meanwhile". |
| `#Design — station admission through the pair (Phase 6c candidate)` | L1405–L1482 | settled-history · current | Titled "candidate" but proven: §12 Phase 6c green on 2026-07-22 with five asserts. | L1433 `## The two questions, answered`; proof at L914. **Marker stale — see `findings.md` F2.** |
| `##Writeback hook` (6c) | L1483–L1494 | **live-work** | The forward tail of a settled section. | `findings.md` F4. |
| `#Design — coverage areas ARE H3 cells (settled)` | L1495–L1571 | settled-history · current | Explicitly settled; states the design and what the PoC does about it. | Header "(settled)"; L1503 `## What the design says`. |
| `##Finding — the 10k silent truncation` | L1572–L1584 | settled-history · current | A named negative worth carrying: a silent limit found in practice. | The heading; a sharp edge of exactly the class `book-supervisor.md` L62 routes to "Known sharp edges". |
| `#Design — the Atlas/GEOIQ seam (settled)` | L1585–L1632 | settled-history · **covered** | The ownership split, settled and already in the books. | **Converted end to end** — `conversion/`. Books-verdict: no change needed. |
| `##Writeback hook` (seam) | L1633–L1644 | **live-work** | The forward tail: relocate the package, shims, register the real deriver. | `findings.md` F4; `conversion/books-verdict.md`. |
| `#Discussion — how should Create KB treat stations? (next step)` — options and recommendation | L1645–L1703 | settled-history · current | Four options weighed, one recommended with three forcing arguments and a comparison table; (d) rejected on record. | L1665 "**Recommendation: (b) as the mechanism, (c) as the framing, (a) demoted … (d) rejected.**" |
| `##Minimal changes when picked up` | L1704–L1711 | **live-work** | Named API and UI changes, not made. | "when picked up" in the heading. |
| `##Open sub-questions (future probes)` | L1712–L1722 | **live-work** | Five named open questions. | The heading. |
| `#Deferred — forked data stores (branches). LAST priority` | L1723–L1759 | **live-work** | An explicitly deferred design, captured so it is not lost, with its own open sub-questions. | L1725 "**Explicitly behind everything else** … Captured so it isn't lost." |

---

## B. `reports/` — 11 hand-written HTML reports

Whole-file rows. Most of these restate `SPIKE.md`, so their
disposition is **adopt as a session deliverable**, not convert —
laning their content independently would double-count the corpus
(`findings.md` F6).

**But "derived" had to be checked per report, not assumed.**
`SPIKE.md` references only **two** of the eleven (L365
`sticker-roundtrip.html`, L454 `search-api-aup-survey.html`); the rest
were matched to it by subject. Testing the match by keyword found one
report whose subject `SPIKE.md` never touches at all — SQLRooms,
PMTiles and Zuplo appear zero times in it — so
`stations-workbench.html` is a **sole holder**, not a rendering. Same
error as section D, caught the same way (`findings.md` F12).

| anchor | lines | lane | reason | evidence |
| --- | --- | --- | --- | --- |
| `reports/index.html` | 73 | discard | A link page for eight of the eleven; navigational only. | Its own text: "Shareable design sketches and findings from the knowledge-base spike." |
| `reports/spike-roadmap.html` | 154 | **live-work · as-written** | The corpus's rendered work-list — and stale: it lists P5 as next, which §12 records LIVE. | L150 close-out step; `findings.md` F8. Mine P3 and P7 for items; do not mine P5. |
| `reports/spike-02-report.html` | 251 | settled-history · as-written | The shareable form of a closed spike's verdict. | `archive/README.md` calls SPIKE-02 "**PROVEN but limited**" and names this report as its shareable form. |
| `reports/extract-build-lifecycle.html` | 300 | settled-history · covered | Renders the §1 spine. | Restates `SPIKE.md` §1 L43–L93. |
| `reports/kb-staging-lifecycle.html` | 727 | settled-history · covered | Renders the §2 lifecycle end to end. | Restates `SPIKE.md` §2 L94–L247. |
| `reports/atlas-grounding.html` | 198 | settled-history · current | Renders the Phase 4c result — the loop on a real catalog. | Restates §12 L822–L867. |
| `reports/sticker-roundtrip.html` | 343 | settled-history · current | Renders the clone/pair/joint-admission round trip; `SPIKE.md` §6 L365 cites it as the diagram of record. | L365 "Diagrammed: [`reports/sticker-roundtrip.html`]". |
| `reports/vintage-resolution.html` | 406 | settled-history · current | Renders the Phase 6b vintage-resolution design. | Restates `SPIKE.md` L1120–L1348. |
| `reports/stations-workbench.html` | 695 | **live-work · sole-holder** | A SQLRooms capability inventory, a two-plane architecture, two named boundaries, and a PoC plan for a UI surface never built. `SPIKE.md` covers none of it. | Newest report (2026-07-24, commit `f6ee2d37`); `grep -ic sqlrooms SPIKE.md` → 0, likewise PMTiles and Zuplo. Headings include "httpfs straight to S3 — one endpoint is the whole contract" and "Two boundaries to name". |
| `reports/web-lane-design.html` | 279 | settled-history · current | Renders the web-lane design that §12 records LIVE. | Restates `docs/web-discovery-dedup-design.md`; proven at §12 L1024. **Orphaned** — not linked from `index.html`. |
| `reports/search-api-aup-survey.html` | 199 | settled-history · **sole-holder** | A 14-provider terms-of-service survey with verbatim clauses and per-1k prices. `SPIKE.md` restates the eight-gap *list* (L464–L465) and none of the reasoning that eliminated 13 alternatives. | `grep -ic` on `SPIKE.md` **and** `docs/`: `Tavily` 0/0, `Perplexity` 0/0, `Brave` 0/0, `SerpApi` 0/0, `hiQ` 0/0. **Orphaned** — not linked from `index.html`. |

---

## C. `docs/`, `packages/`, `.claude/spike/`

| anchor | lines | lane | reason | evidence |
| --- | --- | --- | --- | --- |
| `docs/book-supervisor.md` | 107 | **settled-history · absent** | The corpus's own writeback-loop design — prior art for the carrier skill this intent is about. **Read it before writing #266.** | `findings.md` F9. |
| `docs/book-supervisor-state.json` | 12 | **settled-history · absent** | The import's own progress ledger; its `tracking[]` is a pre-written live-work list, and its `spike_sha` names the exact unconverted delta. | `findings.md` F10. |
| `docs/book-supervisor-log.md` | 46 | settled-history · current | One dated sweep with promoted / tracked / escalated sections — the record of how the books got what they have. | The 2026-07-23T02:02Z entry. |
| `docs/book-boundaries.md` — `##The de-facto decomposition`, `##Where each book stands` | L11–L48 | settled-history · current | An audit of the destination books against what the spike built — the coverage input `findings.md` F3 says the cut needs. | The per-book "Reality check" table L41–L48. |
| `docs/book-boundaries.md` — `##The tensions (T1–T7)` | L50–L111 | **live-work** | Seven named cross-book seams awaiting the operator's calls — seven items with provenance. | `book-supervisor.md` L11–L16: "anything matching a tension escalates to chuck instead of being written". |
| `docs/book-boundaries.md` — `##Target-state responsibility map (proposal)` | L112–L135 | **live-work** | Explicitly a proposal. | The heading's "(proposal)". |
| `docs/book-boundaries.md` — `##Supervisor routing table` | L136–L146 | settled-history · current | The finding-class → book routing table the supervisor runs on. | The table itself. |
| `docs/design-timeline.md` | 148 | **settled-history · absent** | The narrative record of the whole decision arc, phase by phase, with a one-line verdict table. The single best conversion candidate for multi-session history. | L3 "This is the **narrative record** of the spike"; the arc table L141–L148. |
| `docs/investigation-station-item-shape.md` | 173 | settled-history · current | Background to a settled direction, and it says so in its own status line. | L3 "**STATUS 2026-07-24 — largely SETTLED; this brief is background, not an open question.**" |
| `docs/web-discovery-dedup-design.md` | 178 | settled-history · current | Says "Status: design", but §12 L1024 records the lane LIVE. Currency resolved in favour of §12. | `findings.md` F8. |
| `docs/graphrag-toolkit-eval.md` | 150 | settled-history · current | A dated build-vs-adopt evaluation with a stated take. | L3 "Research note. Source: … read 2026-07-20." |
| `docs/overture-tiles-eval.md` | 68 | settled-history · **sole-holder** | A dated tool evaluation for the Tiles surface — a product area `SPIKE.md` never covers. | L3 "Evaluated 2026-07-23 for the UI prototype's **Tiles** section"; `grep -ic planetiler SPIKE.md` → 0, `pmtiles` → 0. |
| `packages/geoiq/docs/inbox-design.md` | 222 | **split · part sole-holder** | §(a) topology, §(d) trust boundary, §(f) seams and §(h) cloud shape describe a gateway/contributions model absent from `SPIKE.md`; §(c) fp rule and §(g) sticker sim restate §6; §Open questions (L209) → live-work. | L3 "Status: design (spike). Gates PR #10."; `grep -ic` on `SPIKE.md` → `contributions` 0, `gateway-side` 0, "two central Atlas3 warehouses" 0. **Section-level read still owed** — laned on keyword absence, not a full read. |
| `.claude/spike/bedrock-surface.md` | 135 | discard | Docs-derived notes on a managed-Bedrock surface the design abandoned, and unasserted by its own admission. | L4 "**Nothing here is asserted against the account yet**"; the abandonment at `SPIKE.md` L1082–L1086. |
| `.claude/spike/mcp-wiring.md` | 64 | discard | Tooling wiring for the `spike-commissioning` plugin that was dropped. | `SPIKE.md` L1084 "That machinery is **dropped for this PoC**". |
| `.claude/spike/spike-workspace-shape.md` | 76 | **discard · stale** | Describes a scaffold generator's output, and does not match this repo: its tree lists a `writeback.md` that `.claude/spike/` does not contain. | L15 `│       └── writeback.md`; the directory holds four files and that is not one of them. |
| `.claude/spike/aws-account-guardrails.md` | 82 | **withhold** | Account-scoping and credential-handling material. Class recorded; nothing quoted. | `findings.md` F11. |

---

## D. `archive/` — four superseded spike documents, 3,903 lines

The corpus has already done half this triage: `archive/README.md`
gives a verdict and a findings pointer for each. But the verdicts are
all that has been restated. **`SPIKE.md` never restates the findings
themselves — it points at the archive instead**, and the Disposition
table retires three requirements with the words "Findings archived."

**And the archive is not uniform.** Three of the four are sole
holders of real proved findings; the largest is not, and holds
nothing. Laning the directory as a class — in either direction — is
wrong:

| document | lines | what a full read found |
| --- | --- | --- |
| SPIKE-01 | 482 | 2 surviving findings: the empty-graph gate with its controlled receipt, and that KB ingestion reads only the sidecar/CSV/inline metadata — never S3 tags or user-metadata |
| SPIKE-02 | 433 | **11 surviving findings** — the richest settled-history document in the corpus; see below |
| SPIKE-03 | 2142 | **none.** 20 of 22 finding sections end "Does not settle …" |
| SPIKE-04 | 846 | 2 surviving findings: a prod-fence gap that was acted on, and probe-zero tooling facts |

**SPIKE-02 is the one to convert.** Measured, unrestated detail:
metadata lands as prefixed per-key chunk properties rather than a
blob; a retrieval filter is genuinely selective; `includeForEmbedding:
true` buys no structural upgrade; prose in the body is the only lever
that mints a traversable entity; the chunker does not strip
front-matter; extraction reliability tracks phrasing not file type;
extracted entity names are not normalized; the coverage tradeoff
(the prose entity attaches only to the chunk holding the sentence,
while the metadata tag rides every chunk); post-ingestion graph writes
are retrieval-safe but destroyed by re-ingestion. `SPIKE.md` returns
**zero** for `metadata_`, `includeForEmbedding`, `stitch`, `Haiku`,
`GetInferenceProfile` and `non-empty`.

**And `archive/README.md`'s verdict for SPIKE-03 is not proved by
SPIKE-03.** It asserts "A is short of the need — metadata rollup
filters but cannot *traverse* the network, so a self-managed graph (B)
is required", and no probe in that document ever measured
county→state rollup: the one that tried was interrupted before
retrieval returned, and the Approach-B probe never ran. **The
architecture decision the entire active PoC rests on was reasoned, not
evidenced.** Any record that captures it has to carry that caveat
rather than inherit the README's "Verdict:" framing — which is a
books-verdict question, not a cut question, and belongs to whoever
converts it.

Disposition: **convert the verdict, carry the body** — for SPIKE-01,
-02 and -04. A third option beside convert and discard: the summary
becomes a record, and the body has to survive the corpus somewhere or
the import loses the only copy. SPIKE-03 discards.

| anchor | lines | lane | reason | evidence |
| --- | --- | --- | --- | --- |
| `archive/README.md` | 25 | settled-history · absent | Three closed spikes, each with a one-line verdict and a pointer to its findings section. Convert this. | L3 "Closed spikes, kept for their findings (the product of a learning spike)." |
| `archive/SPIKE-01-graphrag-hierarchy.md` | 482 | settled-history · **sole-holder** | Verdict restated in the README and the timeline; the §10 findings behind it are restated nowhere. | `archive/README.md` "**Verdict: DISPROVEN at the attach gate** … Findings in its §10"; `SPIKE.md` L11 "kept for their findings", L1102 cites it as "Prior work" and stops there. |
| `archive/SPIKE-02-managed-graph-influence.md` | 433 | settled-history · **sole-holder** | Same. Its shareable form is `reports/spike-02-report.html`, which is a rendering of the verdict, not of the matrix. | `archive/README.md` "**PROVEN but limited** … Full matrix in its §10"; the one `SPIKE.md` cross-reference (L609) borrows the reliability *question*, not the findings. |
| `archive/SPIKE-03-spatial-hierarchy.md` | 2142 | **discard** | **Holds no findings at all.** 20 of its 22 finding sections end in a "Does not settle …" paragraph; 16 are meta-process probes skipped as unsound before running, and the two that reached AWS were interrupted or gate-blocked. | `grep -c "Does not settle" archive/SPIKE-03-spatial-hierarchy.md` → **20** against `grep -c '^### '` → 22. Its two useful outputs are restated: the concurrency rule at `SPIKE.md` §10, the process lesson at `docs/design-timeline.md` L86–L88. |
| `archive/SPIKE-04-partB-commissioning-findings.md` | 846 | settled-history · **sole-holder** | The only record of the Part B probes, including all findings for the three requirements the corpus declares dead. | `SPIKE.md` L1086–L1087 "The full historical findings sink is preserved at `archive/SPIKE-04…`"; the Disposition table (L1104–L1106) retires `managed-retrieval-index`, `synthesis-flow` and `relational-store` with "Findings archived." |

**Why this row set changed.** These four were first laned
`cite-only` — convert the summary, leave the body — on the strength of
`archive/README.md`'s verdicts. Checking whether `SPIKE.md` restates
the findings (`grep -n "SPIKE-0[1-4]\|archive/" SPIKE.md`, five hits,
all pointers) showed it does not. `cite-only` would have been a
disposition that quietly discarded 3,903 lines of the only copy of
something — precisely the failure mode the promise exists to prevent.
Recorded rather than silently fixed, because the near-miss is the
evidence for how the lane should be written down in #266.

## E. Operating documentation, fixtures, and application files

Operating documentation is the residue class `findings.md` F7 names.
It resolves to `discard` **here** only because the repo is scheduled
for teardown — a fact about the corpus's future, not about the files.

| anchor | lines | lane | reason | evidence |
| --- | --- | --- | --- | --- |
| `README.md` | 115 | discard | Quick start for a repo scheduled to be archived. | `reports/spike-roadmap.html` L150 "repo archives beside SPIKE-01/02/03". |
| `CLAUDE.md` | 103 | **withhold** (+ operating doc) | Its guardrails name the client's production VPC by id, in the course of forbidding it. Class recorded; nothing quoted. The rest is repo operating instruction. | `findings.md` F11; two prod-network identifiers present. |
| `poc/README.md` | 117 | discard | How to run the harness. | Same; and `SPIKE.md` §8 already inventories the commands. |
| `scripts/README.md` | 52 | settled-history · **sole-holder** | Nine numbered, proved AWS platform gotchas — empty-graph requirement, no pause API, the IAM grants a KB role needs, accepted FM ids. `SPIKE.md` restates none. | The numbered list L20–L46; `grep -ic GetInferenceProfile SPIKE.md` → 0, `Haiku` → 0, `non-empty` → 0. |
| `ui/README.md`, `ui/app/README.md`, `ui/app/index.html` | 56 / 32 / 13 | discard | The scenario-lab UI's own operating docs and shell. | The UI is described as a scenario lab at `SPIKE.md` L911–L913. |
| `transcripts/README.md` | 13 | discard | A holder README for session transcripts. | Its own length and content. |
| `fixtures/spike-02/README.md`, `fixtures/spike-04/catalog-items/README.md` | 38 / 33 | discard | Describe fixture inputs, regenerable. | `SPIKE.md` §9 L537–L540 "Not a catalog — just inputs". |
| `fixtures/**` payload files (4 md/html) | 38 total | discard | Test fixture data. | `SPIKE.md` §9. |

---

## Unsettleable — questions for the operator, not lanes chosen quietly

Clause 3: where a session cannot settle a row it queues the doubt as a
question. Five.

1. **Is the corpus being retired, or does it keep running?** Every
   `discard` in section E depends on the answer. The roadmap says the
   repo archives at P7; nothing says P7 happened, and `packages/geoiq`
   has since become a real package (commit `2e67a0b9`, "SDK/CLI
   absorbing PoC KB lifecycle"). If the repo lives, operating
   documentation leaves the cut entirely rather than being discarded.
2. **Does `books/knowledgebase/` still owe a chapter, or did the
   rename absorb it?** The corpus targets a suite that does not exist;
   the material landed in `geo-iq` and `atlas-kit`. Whether the
   remaining unconverted material has a home or needs a new suite is
   the operator's call (`findings.md` F3).
3. **Are the T1–T7 cross-book tensions still open?** They were
   escalations awaiting the operator in July. Some appear resolved by
   the suite renames — T1 wanted the sidecar contract moved to
   `atlas-framework`, and `books/atlas-kit/src/sidecars.md` now owns
   it. Confirming each is cheap for the operator and expensive to
   guess.
4. **Does an import of a foreign-org corpus land in that org's
   fleet?** The promise's boundary assumes "the corpus's org has no
   fleet". WilldanGroup has one — `fleet.yaml`, a dispatch actor, and
   nine book suites. #267's framing may be answering a question this
   corpus does not ask.
5. **Is `reports/stations-workbench.html` a plan or a record?** It is
   the newest report, describes a PoC plan for a UI surface, and no
   §12 finding records it built. Laned `live-work` on that reading;
   one sentence from the operator settles it.

---

## Tally

**Corpus:** 45 tracked `.md`/`.html` files + 1 tracked `.json` the
file-type filter nearly lost, 11,538 lines.

| lane | rows | notes |
| --- | --- | --- |
| `settled-history` | 62 | 41 `current`, 7 `as-written`, **7 `sole-holder`** + 1 partial, 5 `covered` by the destination books, 4 `absent` |
| `live-work` | 17 | including 7 cross-book tensions, 2 unstarted phases, and 6 forward tails of settled sections |
| `discard` | 15 rows / 22 files | operating documentation, fixtures, the report index, 2 `stale`, and `archive/SPIKE-03` (2,142 lines that settle nothing) |
| `withhold` | 4 | `SPIKE.md` §10 and §11, `.claude/spike/aws-account-guardrails.md`, and `CLAUDE.md` — class recorded, nothing quoted |
| split | 2 | `SPIKE.md` §7 Phasing and `packages/geoiq/docs/inbox-design.md`, each laned per sub-part |
| unsettleable | 5 | queued as questions above, not laned |

**99 rows over 46 files**, 58 of them inside `SPIKE.md` alone.
Several `discard` rows bundle same-purpose files.

**Every row in this tally moved at least once.** The lane counts here
are the third revision, not the first: the session's own reading, then
a restatement check that overturned four rows, then a full read of the
regions the check could not judge, which overturned three more —
including one 2,142-line document the check had promoted. The revision
history is the finding (F12), not an embarrassment to be tidied out of
it.

**The conversion work-list, ranked.**

*Convert:* `docs/design-timeline.md` (the decision arc),
`docs/book-supervisor.md` + `docs/book-supervisor-state.json` (the
import machinery and its ledger), `archive/README.md` (the closed-spike
verdicts — with the SPIKE-03 caveat attached, see section D).

*Carry, do not convert:* the sole holders — `archive/SPIKE-02` first
(11 measured findings, the richest single document in the corpus),
then `SPIKE-01` and `SPIKE-04`, `reports/search-api-aup-survey.html`
(a 14-provider survey that exists nowhere else),
`reports/stations-workbench.html`, `scripts/README.md`'s nine platform
gotchas, and `docs/overture-tiles-eval.md`. They need somewhere to
live before the repo is torn down, which is a different act from
conversion: nobody has to read them today, and losing them is
irreversible.

*Adopt whole:* the five reports carrying 1,062 lines of hand-authored
SVG. A diagram cannot be restated in markdown, so adoption is the only
cheap correct move (`findings.md` F13).

**And the delta is computable without reading anything:** 30 commits
and twelve documents have landed since the last writeback sweep
(`findings.md` F10). That is where a second import session should
start.
