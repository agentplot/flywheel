# The messy-repo onboarding promise — round document (#264), round 2

A user arrives with a repo full of planning docs — spike notes,
roadmaps, design prose, HTML reports, half-finished requirement lists —
and wants flywheel without abandoning that history. This round settles
what flywheel **promises** them, before any mechanism is designed.
Four clauses; annotate each. Detailed options and evidence are in
`decision-drafts.md` beside this file.

Grounding: the one corpus ever actually read under this thread
(kb-spike, surveyed in #195) showed ~105 files where settled and
unsettled material interleave by section with **no marker saying which
is which**, and where the file the import request named did not exist.

## 1. What the user hands over — approved round 1

**A pointer and read access — nothing else required.** The corpus
stays where it is; no pre-sorting, no format, no restructuring.
Anything the operator volunteers in conversation ("that file is the
roadmap", "the archive/ dir is dead") is welcomed as seed evidence,
never required. Intake is dispatch-shaped: the pointer arrives as a
raw idea, dispatch opens an intent.

## 2. What comes back

**Artifact-by-artifact conversion, tracked and recoverable:**

1. **The cut — first, durable.** A triage report at file-or-section
   granularity: every piece assigned to **discard / settled history /
   live work**, one-line reason and pointer each, committed in the
   intent's change directory. The cut is the work-list the conversion
   then walks.
2. **Each artifact thoroughly converted, then marked processed.** A
   processed ledger — likely in flywheel's local state — records what
   has been converted and where it went, so the original is
   recoverable and the import can stop and resume. Processed vs
   remaining is the progress measure. History is not recreated
   wholesale; it is converted one artifact at a time.
3. **Settled history becomes flywheel-native records.** Decisions,
   design reports, and findings are captured as **sessions under
   intents** — session directories and decision records, the same
   shape flywheel's own design work leaves. For design material, the
   conversion **updates the books, or at minimum records an explicit
   verdict on whether the books should be updated** — a per-artifact
   books-verdict, never a silent discard.
4. **Live work becomes queued tracker items.** Proposed intents and
   items, each with a provenance pointer into the corpus — all at
   Backlog. **Nothing arrives approved**: an import fills the funnel,
   it never turns the crank.

## 3. How much reading a person must still do

**The operator reads the cut and the verdicts, not the corpus.**
Sessions read the whole corpus — that's the work being bought. The
operator reviews report rows and books-verdicts, and opens the source
only where they dispute one. Where a session can't settle a row, it
queues a question naming the doubt — **doubt surfaces as questions,
never as a silently chosen lane.** If an import makes the operator
re-read the corpus to trust the cut, the promise is broken.

## 4. Where the write-once line sits

**The process is written down once; the cut and the conversions are
judgment every time.** Write-once: the process shape (inventory → cut
→ convert → mark processed), the report format, the processed-ledger
convention, the provenance convention, the routing rules into sessions
/ decisions / books / items. Judgment, per corpus: the cut itself and
each artifact's conversion — kb-spike proves no rule can read a
corpus. So the durable carrier will be instructions that structure
judgment (skill or session type), never a tool that replaces it; which
carrier exactly is a deferred successor decision.

## 5. Deferred — named non-promises, each a successor item on this intent

- **Cross-org landing** (was #196): until settled, the promise for a
  corpus in a fleet-less org stops at the report tier.
- **The carrier and the ledger's home** (was #197): skill vs session
  type vs tool, and where the processed ledger lives in local state.
- **OpenSpec into the built repo** (was #198): whether specs are ever
  written into the source repo itself, beyond the flywheel-side
  records clause 2 promises.
- **Bulk triage mechanics** (was #199): dedupe, collision, provenance
  at roadmap volume.
- **First measurement** (was #195): run the cut and a first conversion
  over a real corpus — the test of clauses 2 and 3.
