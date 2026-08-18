# Decision drafts — the messy-repo onboarding promise (#264)

One decision, four clauses. The item charges this session to settle the
promise before any mechanism: what the user hands over, what comes
back, how much reading a person must still do, and where the line sits
between what can be written down once and what needs someone reading
the corpus.

Evidence base: the one real corpus ever surveyed under this thread —
`WilldanGroup/knowledgebase-spike` at `ba4b385a`, surveyed 2026-08-14
and recorded in #195's body. Its facts recur below as "the kb-spike
survey." The inherited question set is #195–#199 (all closed
`state:queued`, never worked — see
`design/field-notes/2026-08-17-tracker-archive.md`).
`intent/onboarding-first-run` settled the empty start; this intent is
the repo that arrives full.

---

## Clause 1 — What the user hands over

**Options**

- **(a) A pointer and read access, nothing else.** Flywheel reads the
  corpus where it lives. No pre-sorting, no format demands, no
  restructuring of the source repo.
- **(b) A pointer plus a conversation.** The operator also tells
  dispatch what they know — which doc is the roadmap, what is dead,
  what still matters.
- **(c) A pre-sorted corpus.** The user cleans up first, flywheel
  imports the clean result.

**Recommendation: (a) as the floor, (b) as a welcomed accelerant,
(c) rejected.**

The kb-spike survey is the argument against any structural
requirement: the file the request named (`workplan.md`) did not exist,
the actual roadmap lived in an HTML report, and settled and unsettled
material interleaved by section with no marker. A promise that asks
the user to pre-sort contradicts the premise — the repo is messy
precisely because nobody sorted it. But anything the operator
volunteers at hand-over is seed evidence for the cut, never a
prerequisite: the normal case is an operator who knows the repo is
messy but not where the bodies are.

**Consequence.** The intake is dispatch-shaped: a pointer arrives as a
raw idea, dispatch opens an intent. No new intake surface.

## Clause 2 — What comes back

**Options**

- **(a) A triage report and nothing durable.** Cheapest; but every
  later session re-reads the corpus, and the reading — the expensive
  part — is thrown away.
- **(b) Full conversion.** A design book plus intents and items
  covering the whole corpus. Maximal; writes books nobody asked for
  and floods the tracker with the corpus's volume.
- **(c) Tiered: report always, tracker items from the live lane,
  index from the settled lane.**

**Settled (operator's direction, round 1): (c) reshaped as
artifact-by-artifact conversion, tracked and recoverable.**

1. **The cut, first, durable.** A triage report at file-or-section
   granularity assigning every piece to a lane — **discard**,
   **settled history**, **live work** — with a one-line reason and a
   pointer each, committed under the onboarding intent's change
   directory. The cut is the work-list the conversion then walks.
2. **Per-artifact conversion with a processed ledger.** Each artifact
   is thoroughly converted, then marked processed in a ledger — likely
   in flywheel's local state — recording what was converted and where
   it went, so the original is recoverable and the import can stop and
   resume. Processed vs remaining is the progress measure; history is
   never recreated wholesale.
3. **Settled history becomes flywheel-native records.** Decisions,
   design reports, and findings are captured as sessions under intents
   — session directories and decision records, the same shape
   flywheel's own design work leaves. Design material updates the
   books, or at minimum records an explicit verdict on whether the
   books should be updated — a per-artifact books-verdict, never a
   silent discard.
4. **From the live lane: queued tracker work.** Intents and items
   proposed onto the tracker, each carrying a provenance pointer into
   the corpus. Everything lands queued / Backlog. **Nothing arrives
   approved** — the operator's Ready flip stays the only release;
   an import fills the funnel, it never turns the crank.

## Clause 3 — How much reading a person must still do

**Recommendation: the operator reads the cut, not the corpus.**

- The sessions producing the cut read the whole corpus; that is the
  work being bought.
- The operator reviews report rows — lane, one-line reason, pointer —
  and opens the source only where they dispute a row.
- Where a session cannot settle a row, it queues a question naming the
  specific doubt. **Doubt surfaces as questions, never as a silently
  chosen lane.**

So the reading scales as: machine O(corpus), person O(report), with
the person's depth self-chosen per row. This is the measurable clause
of the promise: if an import makes the operator re-read the corpus to
trust the cut, the promise is broken.

## Clause 4 — The write-once / judgment line

**Recommendation: the process is written down once; the cut is
judgment, every corpus, every time.**

Write-once (mechanical, durable):

- the process shape: inventory → cut → route;
- the report format and its lane vocabulary;
- the provenance convention (how a tracker item points into a corpus);
- the routing rules (which lane feeds which tracker object).

Never write-once (judgment, per corpus):

- the cut itself. The kb-spike survey is the proof: settled and
  forward material interleave by section with no structural marker,
  so no rule reads a corpus — someone does.

**Consequence.** The durable carrier is *instructions that structure
judgment* — a skill or session type — never a tool that replaces it;
mechanical residue (file inventory, counts, report scaffold) may be
tooling inside it. Which carrier exactly is the #197 successor's
decision; this clause only fixes which side of the line each part
sits on.

## What this intent queues next (each a successor item, constrained by the promise)

- **Write the carrier** (#197 successor): clause 4 settles its kind —
  a skill that structures the judgment, run by design sessions that do
  the reading. The item writes the skill and fixes its details,
  including the processed ledger's home in local state.
- **Cross-org landing** (#196 successor): where imported work lands
  when the corpus's org has no fleet. Gates the live-work lane's
  tracker tier for foreign corpora; until settled, the promise for a
  foreign corpus stops at the report — a promise boundary, not an
  open design.
- **OpenSpec into the built repo** (#198 successor): whether specs are
  ever written into the source repo itself, beyond the flywheel-side
  records clause 2 promises.
- **Bulk triage mechanics** (#199 successor): dedupe, collision, and
  provenance at roadmap volume.
- **First measurement** (#195 successor): run the cut and a first
  conversion over a real corpus; a process designed without reading a
  corpus is fiction, and the first run is the test of clauses 2 and 3.
