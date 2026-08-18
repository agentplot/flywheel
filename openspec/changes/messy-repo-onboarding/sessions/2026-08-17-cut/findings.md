# Findings — the first measurement over a real corpus

Item #270 on `intent/messy-repo-onboarding`. Corpus:
`WilldanGroup/knowledgebase-spike` at `ba4b385a`, local checkout
`~/Code/clients/github_willdan/knowledgebase-spike.geoiq-sdk`.
Destination books: `WilldanGroup/willdan-blueprints` at `2a7c8327`.

These are the findings the measurement produced that the promise
(`../../decisions/onboarding-promise.md`) could not have anticipated
from the survey alone. Each is a fact with a pointer, and each names
the clause or successor item it bears on.

---

## F1 — The corpus is 45 files, not ~105. Sixty of the "files" are a vendored virtualenv.

**Bears on:** the carrier skill's inventory step (#266).

`#195`'s survey — the grounding evidence the promise cites — states
"~105 `.md`/`.html` files in total". The figure is reproducible and
wrong:

```
$ find . -path ./.git -prune -o \( -name '*.md' -o -name '*.html' \) -print | wc -l
105
$ git ls-files '*.md' '*.html' | wc -l
45
```

The 60-file difference is almost entirely
`poc/.venv/lib/python3.12/site-packages/**` — `numpy` licence files,
`fastapi` skill references, `ibis` backend READMEs — plus
`packages/geoiq/.pytest_cache/README.md`. None of it is corpus. The
real corpus is **45 git-tracked `.md`/`.html` files, 11,538 lines.**

The remedy is one line in the carrier skill and it is not optional:
**the inventory is `git ls-files`, never `find`.** A survey that walks
the filesystem inflates the corpus by 2.3× here, and the inflation is
the kind that makes an import look too expensive to start.

---

## F2 — "No marker saying which is which" is half true, and the wrong half was generalized.

**Bears on:** clause 3, and the cut step of the carrier skill (#266).

The promise's grounding says the corpus shows "settled and unsettled
material interleaved by section with **no marker saying which is
which**." Measured against `SPIKE.md`, the claim holds for one region
and fails for the rest.

`SPIKE.md` is not one document. It is nine top-level `#` documents
concatenated:

| span | lines | document | marker |
| --- | --- | --- | --- |
| L1–L18 | 18 | Knowledge-base spike | preamble |
| L19–L1078 | 1060 | PoC directive | **none** |
| L1079–L1119 | 41 | Writeback to the design book | — |
| L1120–L1404 | 285 | Design — resolution: one value per KEY (Phase 6b) | `(Phase 6b)`, and `## Still open`, `## Phase 6b asserts (when picked up)` inside |
| L1405–L1494 | 90 | Design — station admission through the pair | `(Phase 6c candidate)` |
| L1495–L1584 | 90 | Design — coverage areas ARE H3 cells | `(settled)` |
| L1585–L1644 | 60 | Design — the Atlas/GEOIQ seam | `(settled)` |
| L1645–L1722 | 78 | Discussion — how should Create KB treat stations? | `(next step)` |
| L1723–L1759 | 37 | Deferred — forked data stores | `Deferred … LAST priority` |

**Six of the nine top-level documents carry an explicit lane marker in
the header.** The unmarked region is the PoC directive (L19–L1078,
1060 lines, 60% of the file) — and even there, §7 Phasing (L421–L492)
marks every phase `DONE (§12, <date>)` or leaves it forward, and §12
Findings (L575–L1078) is by construction a settled-findings sink whose
subsections carry `LIVE, <date>` stamps.

Outside `SPIKE.md` the markers are near-universal. Every standalone
design document in the corpus opens with a status line, unprompted:

| file | its own marker, quoted |
| --- | --- |
| `docs/investigation-station-item-shape.md` L3 | "**STATUS 2026-07-24 — largely SETTLED; this brief is background, not an open question.**" |
| `docs/web-discovery-dedup-design.md` L3 | "**Status:** design." |
| `packages/geoiq/docs/inbox-design.md` L3 | "Status: design (spike). Gates PR #10." + an explicit "Open questions" section |
| `docs/graphrag-toolkit-eval.md` L3 | "Research note. Source: … read 2026-07-20." |
| `docs/overture-tiles-eval.md` L3 | "Evaluated 2026-07-23 for the UI prototype's **Tiles** section" |
| `.claude/spike/bedrock-surface.md` L3–L4 | "**Nothing here is asserted against the account yet** … This is the map, not the territory." |
| `docs/design-timeline.md` L3 | "This is the **narrative record** of the spike … deliberately a timeline, not a spec." |
| `archive/README.md` L3 | "Closed spikes, kept for their findings" — with a one-line verdict per archived spike |
| `docs/book-supervisor-log.md` | dated sweep entries, promoted / tracked / escalated |

So the honest statement is: **the corpus marks its own lanes wherever
someone wrote a document, and marks nothing inside the running
specification.** That is a much cheaper problem than "no markers
anywhere", and it changes the cut step's instruction from *read
everything with equal suspicion* to *harvest the markers first, then
spend the reading budget on the unmarked region* — here, one 1060-line
region out of 11,538 lines.

The caution that goes with it, and it is not optional: **a marker
states the author's intent at the time of writing, not the current
truth.** `docs/web-discovery-dedup-design.md` still says "Status:
design" while `SPIKE.md` §12 L1024 records that lane LIVE with four
green asserts. Harvest markers to route the reading budget; confirm
them against the source of truth before laning. See F8.

---

## F3 — The cut is a function of two inputs, not one. Reading only the corpus produces a wrong cut.

**Bears on:** clause 2 (the books-verdict), clause 3, #266, #267.
**This is the largest finding of the session.**

The promise describes the cut as something a session produces by
reading the corpus. It is not sufficient. The `settled-history` lane
silently contains two populations that need opposite treatment:

- material **not yet in the destination books** — convert it; and
- material **already written into the destination books** — record its
  provenance and point at the chapter; converting it duplicates a
  chapter that exists.

Nothing in the corpus distinguishes them. Worse, the corpus asserts
the opposite of the truth. `SPIKE.md` L1094 names the writeback
destination as `../willdan-blueprints/books/knowledgebase`
(`commissioning.md` + `contracts/commissioning.yaml`) and calls the
writeback "post-PoC" — owed, not done.
`reports/spike-roadmap.html` L150 repeats it in the close-out step:
"Findings promote candidate → settled in
`willdan-blueprints/books/knowledgebase/`".

Both are false as of `willdan-blueprints@2a7c8327`:

- there is **no `books/knowledgebase/` suite** — the suites are
  `atlas-kit`, `geo-iq`, `gvc-kit`, `cortex-kit`, `rocs-kit`,
  `overview`, `aidlc-design`, `commissioning-template`, `flywheel`;
- and the material **was written back anyway**, into `books/geo-iq`
  and `books/atlas-kit`. The seam design at `SPIKE.md` L1585–L1644 is
  in `books/geo-iq/src/admission.md` L56–L79 and
  `books/geo-iq/src/substrate-boundaries.md`; the contract half is in
  `books/atlas-kit/src/sidecars.md`, whose title —
  "Sidecars — derived companion artifacts" — is verbatim the naming
  generalization that section's writeback hook asked for.

An importer reading only what it was handed would have converted that
artifact as unwritten history. The measured claim-by-claim verdict is
`conversion/books-verdict.md`.

**Consequence for the carrier skill:** the inventory step takes two
arguments — the corpus and the destination books — and the cut's
`settled-history` lane is not assignable until the books have been
read. Where the destination books do not exist yet, the lane is still
assignable; where they do, skipping them produces duplication that
looks like successful work.

---

## F4 — Section granularity is too coarse. A section marked `(settled)` carried a live tail.

**Bears on:** clause 2's "file-or-section granularity", #266.

`SPIKE.md` L1585–L1644 is titled `(settled)` and dated
`Settled 2026-07-23`. Its last subsection, `## Writeback hook`
(L1633–L1642), is forward work: relocate the `geoiq` package to the
platform repo at spike-exit, reduce `poc/*.py` to delegating shims,
register the extractor registry as the real `kb` deriver. None of it
was done.

The same shape recurs: `# Design — resolution … (Phase 6b)`
(L1120–L1404) is 285 lines of settled reasoning ending in three
forward subsections — `## What has to change` (L1349),
`## Phase 6b asserts (when picked up)` (L1362),
`## Still open — needs the operational workflow` (L1384).

This is not disorder; it is the natural shape of a design document —
conclusion first, then what the conclusion obliges. **The pattern is
predictable enough to instruct against**: a settled design block's
trailing "hook"/"what has to change"/"still open"/"when picked up"
subsections are live work, and the cut should look for them by name
rather than inherit the parent's lane.

The promise's "file-or-section granularity" should read
**file-or-section, and below a section wherever a trailing subsection
changes lane.** Two rows for one section is normal, not an exception.

---

## F5 — The corpus contains its own work-list, three times over, under names nobody asked for.

**Bears on:** #269 (bulk triage), #266.

`#195` recorded that the `workplan.md` the import request named "does
not exist anywhere in the tree", and treated that as the corpus being
disordered. It is more accurately a naming miss. The work-list exists
in two independent, mutually consistent renderings:

- **`SPIKE.md` §7 Phasing** (L421–L492) — every phase either
  `DONE (§12, <date>)` with a pointer to its finding, or forward.
  Forward: Phase 3 (Query + tools), Phase 5 (Web lane), Phase 7
  (Verdict + teardown, then Atlas SDK wiring and the serverless
  approval app "post-spike").
- **`reports/spike-roadmap.html`** — the same set as a rendered page,
  under the headings "Proven — don't re-prove", "Next — in this order"
  (P3, then P5), and "Then close it out" (P7).

A third rendering turned up later and is the machine-readable one:
`docs/book-supervisor-state.json`'s `tracking[]` array, seven entries
of forward work with their blockers named (F10).

**Instruction for the carrier:** do not go looking for the file the
operator named. Ask what the corpus's own progress ledger is — a
phasing section, a roadmap page, a findings sink, a state file — and
read that. The operator's pointer is seed evidence (clause 1), and a
seed that misses is not a corpus defect.

The three renderings disagree, which is itself the answer to how to
use them: **the one the corpus names as its source of truth wins**
(here `SPIKE.md`, by its own standing rule), and the disagreement
between the others is triage evidence rather than noise — see F8.

---

## F6 — The reports are *mostly* derived views. The exception is the one that matters, and only a per-report check finds it.

**Bears on:** the pricing question `#195` raised, #266.

`#195` observed that the 11 HTML reports "are already in the shape
flywheel's own interactive sessions emit" and asked whether adopting
them as session deliverables is cheaper than re-deriving their content
as items. Measured:

- **They are hand-written, not generated.** Each of the 11 carries its
  own inline `<style>` block; there is no shared stylesheet, no
  template, no generator signature common to the set.
- **They are the spike's product.** `reports/index.html`: "Shareable
  design sketches and findings from the knowledge-base spike. A
  throwaway spike commissioned for learning; **these pages are its
  written product**."
- **The corpus declares them downstream.** `reports/spike-roadmap.html`
  L150's standing rules: "**SPIKE.md is the only source of truth** —
  Part A current design, §12 append-only findings".
- **Three of the eleven are unreachable one way or another.**
  `search-api-aup-survey.html` and `web-lane-design.html` are not
  linked from `index.html`; and `index.html` itself lists only eight.

So the answer to the pricing question is: **adopt them as session
deliverables** — finished, shareable, expensive to re-render — and
**do not mine them for cut rows**, because laning a rendering of
`SPIKE.md` independently double-counts the corpus.

**Except that "rendering of `SPIKE.md`" is a claim, and it is false for
one of them.** `SPIKE.md` references only **two** reports in 1758
lines (L365 `sticker-roundtrip.html`, L454
`search-api-aup-survey.html`). The other nine were matched to it by
subject — which is inference, not evidence. Testing the match:

```
$ grep -ic "sqlrooms" SPIKE.md   → 0     (2 reports carry it)
$ grep -ic "pmtiles" SPIKE.md    → 0     (1 report carries it)
$ grep -ic "zuplo" SPIKE.md      → 0     (1 report carries it)
```

`reports/stations-workbench.html` is 695 lines — a capability
inventory across ten surfaces, a two-plane architecture ("httpfs
straight to S3 — one endpoint is the whole contract"), two named
boundaries (a design-system collision, S3 CORS with short-lived
credentials), and a PoC plan — and **`SPIKE.md` covers none of it.**
It is the newest artifact in the corpus (2026-07-24) and it is a sole
holder. Treating the reports as a uniformly derived class would have
dropped it.

A weaker version of the same applies to
`search-api-aup-survey.html`: `SPIKE.md` L464–L465 restates its eight
gaps *by name*, so the list survives — but the survey evidence behind
the list does not.

**What the carrier needs:** the "derived view" disposition is per
artifact and requires the same restatement check F12 argues for. A
class-level judgement about a directory — *these are all renderings* —
is exactly the shortcut that loses the one that was not.

---

## F7 — A fourth thing exists that is not discard, history, or live work: operating documentation.

**Bears on:** clause 2's three-way cut, #266.

The three lanes assume every artifact is either dead, a record of
something concluded, or work still to do. The corpus holds a class
that is none of the three: documentation that describes **how to
operate the thing as it currently stands** — `README.md` (quick
start), `CLAUDE.md` (agent instructions for the repo), `poc/README.md`,
`scripts/README.md`, `ui/README.md`, `ui/app/README.md`,
`transcripts/README.md`.

It is not discard: it is accurate and load-bearing while the repo
lives. It is not settled history: it records no decision. It is not
live work: nobody has to do anything.

For a **throwaway** corpus like this one the residue resolves — the
repo is scheduled for teardown and archive, so operating docs die with
it and `discard` is correct. But that resolution depends on a fact
about the corpus's future that the cut cannot read off the artifacts,
and it will not hold for the case the promise is really aimed at: a
live repo whose planning docs are being onboarded while the repo keeps
running.

**The cut needs a stated rule, not a fourth lane:** operating
documentation is `discard` **when the corpus is being retired**, and
is out of scope for the cut entirely when it is not — an import
converts planning history, it does not adopt a repo's operating
manual. Which case applies is a question for the operator (clause 3),
asked once per corpus rather than once per file.

---

## F8 — "Settled" is not "currently true". The corpus says so itself, and the cut has no column for it.

**Bears on:** clause 2's conversion step, clause 3's verdicts, #266.

`SPIKE.md` §12 Findings opens with its own warranty disclaimer
(L578–L583):

> *This is a dated, append-only log: blocks reference the design as it
> stood when written — earlier blocks cite a former §13 "Forward
> direction" section whose content now lives in §§1–2, and pre-4b
> blocks reference the since-replaced `disposition` column and
> snapshot-era mechanics.*

So the corpus's own settled-findings sink warns that its earlier
entries describe a design that has since been replaced. Every one of
those blocks is unambiguously `settled-history` by the promise's
definition — a finding that was proved, dated, closed. And converting
several of them faithfully would write superseded mechanics into the
books as though current.

The same fault shows up between artifacts, not only within one. §12
records `### Phase 5 — web lane LIVE as Atlas pipelines on Firecrawl
(2026-07-22)` (L1024) — done, with four green asserts. Both §7 Phasing
(L452) and `reports/spike-roadmap.html`'s "Next — in this order" still
list Phase 5 as forward work. Git resolves it: the roadmap was last
touched 2026-07-22 and `SPIKE.md` 2026-07-24, and the corpus's own
standing rule says "SPIKE.md is the only source of truth". **The
roadmap is stale, and mining it for live-work items would have queued
work that was already done.**

Two consequences, both cheap:

- **The cut needs a currency column beside the lane.** `settled-history`
  splits again into *still true* and *true when written*. The
  conversion of a stale finding is a historical record with a dated
  caveat, never a books update.
- **Git is triage evidence and the survey never used it.** One command
  (`git log -1 --format=%ad -- <path>`) dates all 45 files; the corpus
  spans 2026-07-15 to 2026-07-24, and the date clusters map almost
  perfectly onto the lanes — everything last touched 07-15/07-16 is
  SPIKE-01/02-era and superseded, everything at 07-23/07-24 is the
  live edge. A derived artifact older than the source it derives from
  is stale by construction. The carrier skill should date the
  inventory as a matter of course.

---

## F9 — The corpus already contains a working design for the carrier we are about to write, and it has been run.

**Bears on:** #266 directly. **Read `docs/book-supervisor.md` before
writing the carrier skill.**

`docs/book-supervisor.md` (107 lines, last touched 2026-07-23) is
titled "Book supervisor — the hourly writeback loop" and describes,
in full, a session that "sweeps this spike once an hour and writes
what has settled into the design books at
`../willdan-blueprints/books/`". Its purpose statement is the
messy-repo promise in one sentence: "to make sure nothing proven here
dies with the throwaway repo… instead of waiting for one big post-PoC
rewrite."

It is not a sketch. It carries, already earned:

| supervisor's part | the promise's part |
| --- | --- |
| classify each delta **promote / track / escalate** (L81–L83) | settled-history / live-work / a question, never a silently chosen lane (clauses 2 and 3) |
| "**Promote only what SPIKE.md marks settled.** A GREEN finding block or an explicit maturity disposition is the bar" (L40–L42) | the marker harvest of F2, stated as a rule |
| "**Route by owner, not by habit** … not everything to `knowledgebase` by default", against a seven-row routing table in `book-boundaries.md` L136–L146 | the books-verdict's routing (clause 2) |
| "**Book conventions govern** (`books/CLAUDE.md`): destination-only voice, full rewrite of wrong sections, no change narration" (L49–L52) | flywheel's own writeback rules, independently arrived at |
| "Never `git add -A` in blueprints… Staging is always the explicit list of watched books it edited" (L71–L74) | flywheel's commit-by-pathspec rule, independently arrived at |
| `docs/book-supervisor-state.json` — "The state file is what makes the loop restartable: any fresh session pointed at this doc can resume from `state.spike_sha` with zero handoff" (L94–L96) | clause 2's processed ledger: "so the original is recoverable and the import can stop and resume" |
| escalate "contradictions between SPIKE.md and the book, session-mined decisions with no SPIKE.md trace" to the operator in Discord (L101–L107) | clause 3's queued questions |
| **tri-file consistency** — a maturity change must touch all three of the yaml, the table, and the prose, "the trap the rule exists for" (L53–L61) | a rule flywheel does not have and should consider |

It also differs from the promise in one way that vindicates the
promise: the supervisor is **incremental and continuous** (hourly,
against a live spike), where the promise is a **one-shot import of a
finished corpus**. And its ledger is a single watermark — see F10 —
not the artifact-by-artifact record clause 2 insists on. The
supervisor's own sweep log shows the failure mode: the one recorded
sweep (2026-07-23T02:02Z) promoted an entire new `architecture.md`
chapter plus four rewritten files in one batch, with no per-artifact
record of what came from where.

This finding also explains F3. The seam design is in `books/geo-iq`
because a supervisor sweep put it there, while `SPIKE.md`'s own
writeback section — never updated — still says the writeback is owed.

---

## F10 — The corpus's own progress ledger exists, names the exact unconverted delta, and the survey's file filter dropped it.

**Bears on:** #266 (where the processed ledger lives, and the
inventory's file scope).

`docs/book-supervisor-state.json` is tracked in git and holds:

```json
{ "last_sweep": "2026-07-23T02:02:38Z",
  "spike_sha": "31e8a8c",
  "blueprints_sha": "fc6a63f",
  "session_scan_ts": null,
  "tracking": [ … 7 entries … ] }
```

Three things follow, each checkable in one command.

**The unconverted delta is computable exactly.** The corpus is at
`ba4b385a`; the last sweep read `31e8a8c`.

```
$ git rev-list --count 31e8a8c..ba4b385a
30
$ git diff --name-only 31e8a8c..ba4b385a -- '*.md' '*.html' '*.json'
docs/book-boundaries.md  docs/book-supervisor-log.md
docs/book-supervisor-state.json  docs/book-supervisor.md
docs/investigation-station-item-shape.md  docs/overture-tiles-eval.md
packages/geoiq/docs/inbox-design.md  poc/README.md
reports/index.html  reports/stations-workbench.html
reports/vintage-resolution.html  SPIKE.md  …
```

**Thirty commits and twelve documents have landed since anything was
written back.** That is the real conversion work-list for this corpus,
and it was derivable in seconds — not by reading 11,538 lines.

**Its `tracking[]` array is a live-work list somebody already wrote.**
Seven entries, including "Phase 3 query+tools not started —
eval-harness blocked behind it" and "T1–T7 cross-book tensions await
chuck's calls; biggest writeback debts: rocs KB chapters vs
knowledgebase substrate (T2), atlas-framework missing
sidecar/staging-contract/mutability findings (T1/T7)". Those are
queued items with provenance, in all but format.

**And the inventory would have missed it.** This session's own scope
rule — `git ls-files '*.md' '*.html'`, 45 files, the rule F1 argues
for — excludes `.json` and therefore excludes the single most
load-bearing artifact in the corpus. `#195`'s survey missed it the
same way, for the same reason.

The lesson is not "add `.json`". It is that **a file-type filter is a
guess about where meaning lives, and this corpus keeps its
import-state in a file type nobody would have listed.** The inventory
step should enumerate every tracked file, classify by type, and
report what it is setting aside — so the operator can see the
exclusion rather than inherit it. Cheap: `git ls-files | wc -l` on
this corpus is a number a session can eyeball.

---

## F11 — `discard` has a subclass that must be discarded on purpose: live infrastructure identifiers.

**Bears on:** clause 2, #266, #267.

`SPIKE.md` §10 Guardrails (L550–L567) names, in its heading and body, a
live AWS account number, a region, an admin profile name, a specific
VPC id described in the same breath as the production VPC it must not
touch, and the exact IAM grants the spike holds.
`.claude/spike/aws-account-guardrails.md` carries the same class of
material. The identifiers are deliberately not reproduced here — see
below.

By the promise's three lanes this is `discard` — ephemeral, dead when
the spike is torn down. But `discard` in the promise means "the row is
the record that it was seen", which is right for a superseded design
document and wrong here: the material is not merely worthless
downstream, it is **material an import must not carry forward** into
books, tracker items, or a change directory that will be read by
people and agents who never had access to that account.

An import that faithfully converts everything is a data-exfiltration
path with good intentions — and it is exactly the shape a foreign-org
corpus takes, which makes it a live concern for #267 rather than a
hypothetical one.

**What the carrier needs:** the cut's `discard` lane splits into
*discard* and *withhold*, and a `withhold` row records that the
material was seen, what class it is (account identifier, network
identifier, credential path, IAM grant), and nothing else — never a
quote, never a line range that invites someone to go look. Detecting
the class is judgment, like everything else in the cut; what is
written down once is that the class exists and that quoting is
forbidden in its rows.

This session's own cut obeys the rule: the row for §10 in `cut.md`
names the class and the line range and quotes nothing, and this
finding names the class and quotes nothing. Copying those identifiers
into an agentplot-owned file — which is what a normal evidence-bearing
row would have done, and what the first draft of this finding did —
would have moved them across the org boundary that #267 exists to
settle. That near-miss is the argument.

---

## F12 — A summary that exists is not the same as the content being restated, and the archive lane is where that bites.

**Bears on:** clause 2, #266. Caught by re-checking this session's own
row, which is why it is written down rather than quietly fixed.

`archive/` looks like the easiest call in the corpus. Four superseded
spike documents, 3,903 lines; a README that gives each a one-line
verdict and a pointer; a `design-timeline.md` that arranges them into
an arc; and `SPIKE.md` calling them "**Closed spikes** … kept for
their findings" (L11). Every signal says *the summary survives, the
body is detail* — and this session's first cut laned all four
`cite-only` on exactly that reading.

The check that overturned it is one command:

```
$ grep -n "SPIKE-0[1-4]\|archive/" SPIKE.md
7:  … the historical `spike-commissioning` findings are in `archive/`
11: **Closed spikes:** `archive/` — SPIKE-01/02/03, kept for …
609: - **Relation-quality caveat (the SPIKE-02 reliability question …
1087: … preserved at `archive/SPIKE-04-partB-commissioning-findings.md`
1102: … Prior work: `archive/SPIKE-01` …
```

Five hits, and **every one is a pointer**. The live document restates
the *verdicts* and never the findings. L609 comes closest and borrows
SPIKE-02's reliability *question*, not its matrix. The Disposition
table (L1104–L1106) retires three requirements with the words
"Findings archived." So the archive bodies are not detail behind a
surviving summary — they are the **sole holders** of the evidence, in
a repo whose roadmap ends "repo archives beside SPIKE-01/02/03".

Laning them `cite-only` would have been a disposition that discarded
the only copy of 3,903 lines while looking like diligence. It is worse
than a plain `discard` mistake, because `discard` invites an argument
and `cite-only` sounds like the material is safe.

**It was not a one-off.** Once the check existed, running it across
the corpus found sole holders in three different directories, each of
which a class-level judgement had already mis-laned:

| artifact | what a class judgement said | what the check found |
| --- | --- | --- |
| `archive/SPIKE-01..04` (3,903 lines) | superseded; summary survives | `grep -n "SPIKE-0[1-4]\|archive/" SPIKE.md` → 5 hits, all pointers |
| `reports/stations-workbench.html` (695) | a rendering of `SPIKE.md`, like its ten siblings | `sqlrooms` 0, `pmtiles` 0, `zuplo` 0 in `SPIKE.md` |
| `docs/overture-tiles-eval.md` (68) | a dated eval, content folded into the design | `planetiler` 0, `pmtiles` 0 in `SPIKE.md` |
| `packages/geoiq/docs/inbox-design.md` (222) | design body restating §6 | `contributions` 0, `gateway-side` 0 in `SPIKE.md` |

**4,888 lines — 42% of the corpus** — sat in dispositions that would
have let it die with the repo, and every one of those dispositions was
reached by a reasonable-sounding inference from a summary, a directory
name, or a sibling. (An upper bound: `inbox-design.md` is only partly
unrestated, and its section-level read is still owed.) The point does
not rest on the exact figure — it rests on the fact that no amount of
care in the *inference* would have caught any of them, and one `grep`
caught all four.

**What the carrier needs:** *restated* is a claim to verify, never one
to infer from the presence of a summary. The check is cheap — grep the
live document for references to the artifact and read whether they
carry the content or only name it — and it belongs in the cut step as
a step, not as advice. The lane it protects is worth naming too:
`sole-holder` material has to survive the corpus somewhere before
teardown, which is a different act from conversion. Nobody has to read
it today; losing it is irreversible.

---

## F13 — Machinery observation (not a tracker item)

The research session type is configured `worktree=False`
(`bin/_flywheel_intent.py` L117), documented as "Research is the type
that reads: the finding is the item comment and the report; nothing is
built." That is right for most research. This item's charge, though,
is a **durable triage report committed in the intent's change
directory** — clause 2 of the promise requires it — so the session had
to write files with no worktree and no `sess/*` branch for the loop's
merge gate to pick up. The files were written and committed by
pathspec in the launch directory (`main`), which is the only path
where they survive.

Routed to the report only, per the finding-routing rule.
