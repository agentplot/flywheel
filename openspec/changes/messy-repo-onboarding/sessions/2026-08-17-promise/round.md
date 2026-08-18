# The messy-repo onboarding promise — round document (#264)

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
Every clause below is shaped by that fact.

## 1. What the user hands over

**A pointer and read access — nothing else required.** The corpus
stays where it is; no pre-sorting, no format, no restructuring.
Anything the operator volunteers in conversation ("that file is the
roadmap", "the archive/ dir is dead") is welcomed as seed evidence,
never required. Intake is dispatch-shaped: the pointer arrives as a
raw idea, dispatch opens an intent.

## 2. What comes back

**Three tiers, most certain first:**

1. **The cut — always, durable.** A triage report at file-or-section
   granularity: every piece assigned to **discard / settled history /
   live work**, one-line reason and pointer each, committed in the
   intent's change directory. The corpus gets read once and the
   reading is kept.
2. **From the live lane: queued tracker work.** Proposed intents and
   items, each with a provenance pointer into the corpus — all at
   Backlog. **Nothing arrives approved**: an import fills the funnel,
   it never turns the crank.
3. **From the settled lane: an index, not a book.** A map from settled
   claim to source location. Book writeback is a separately ordered
   follow-up, only when something will read it — default for settled
   history is *discard unless a named reader exists*.

## 3. How much reading a person must still do

**The operator reads the cut, not the corpus.** Sessions read the
whole corpus — that's the work being bought. The operator reviews
report rows and opens the source only where they dispute one. Where a
session can't settle a row, it queues a question naming the doubt —
**doubt surfaces as questions, never as a silently chosen lane.** If
an import makes the operator re-read the corpus to trust the cut, the
promise is broken.

## 4. Where the write-once line sits

**The process is written down once; the cut is judgment every time.**
Write-once: the process shape (inventory → cut → route), the report
format, the provenance convention, the routing rules. Judgment, per
corpus: the cut itself — kb-spike proves no rule can read a corpus.
So the durable carrier will be instructions that structure judgment
(skill or session type), never a tool that replaces it; which carrier
exactly is a deferred successor decision.

## 5. Deferred — named non-promises, each a successor item on this intent

- **Cross-org landing** (was #196): until settled, the promise for a
  corpus in a fleet-less org stops at the report tier.
- **The carrier** (was #197): skill vs session type vs tool.
- **Reverse-engineer keep-test** (was #198): does anything read
  OpenSpec written into an already-built repo, or is that lane
  discard-with-index?
- **Bulk triage mechanics** (was #199): dedupe, collision, provenance
  at roadmap volume.
- **First measurement** (was #195): run the cut over a real corpus —
  the first run is the test of clauses 2 and 3.
