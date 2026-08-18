# Decision: The messy-repo onboarding promise

## Decision

When a messy repo of planning docs arrives, flywheel promises:

1. **Hand-over is a pointer and read access, nothing else.** The
   corpus stays where it is — no pre-sorting, no format, no
   restructuring. Anything the operator volunteers is seed evidence,
   never a prerequisite. Intake is dispatch-shaped: the pointer
   arrives as a raw idea, dispatch opens an intent.
2. **What comes back is artifact-by-artifact conversion, tracked and
   recoverable.** First the cut — a durable triage report at
   file-or-section granularity (discard / settled history / live
   work, one-line reason and pointer each) committed in the intent's
   change directory. Then each artifact is thoroughly converted and
   marked processed in a ledger (likely flywheel local state) so the
   original is recoverable and the import can stop and resume.
   Settled history becomes flywheel-native records — decisions and
   design reports captured as sessions under intents — and design
   material updates the books or records an explicit per-artifact
   verdict on whether the books should be updated. Live work becomes
   queued tracker items with provenance pointers, all at Backlog:
   **nothing arrives approved**.
3. **The operator reads the cut and the verdicts, not the corpus.**
   Sessions read the whole corpus; the operator reviews rows and
   opens the source only to dispute one. Unsettleable rows surface as
   queued questions, never as a silently chosen lane.
4. **The process is written down once; the cut and conversions are
   judgment every time.** The durable carrier is a skill that
   structures the judgment — inventory → cut → convert → mark
   processed — run by design sessions that do the reading, never a
   tool that replaces it.

## Context

- Produced by: `../sessions/2026-08-17-promise/round.md`, approved by
  the operator in the plannotator round of 2026-08-17 (round 3;
  results r1–r3 beside it).
- Item: #264 on `intent/messy-repo-onboarding`. Inherits the
  never-worked question set of `intent/prior-art-import`
  (#195–#199; see `design/field-notes/2026-08-17-tracker-archive.md`).
- Round 1 reshaped clause 2 to the operator's objective: per-artifact
  conversion with a recoverable processed ledger, books updated or
  explicitly confirmed, history captured as sessions under intents.
- Grounding evidence: the kb-spike survey in #195's body — settled
  and unsettled material interleaved with no marker; the named
  workplan file did not exist.

## Consequences

Queued on `intent/messy-repo-onboarding`, each constrained by the
promise:

- Write the carrier skill (kind settled here; details and the
  processed ledger's home remain).
- Cross-org landing (was #196) — until settled, an import of a
  foreign-org corpus stops at the report tier.
- OpenSpec into the built repo (was #198).
- Bulk triage mechanics (was #199).
- First measurement over a real corpus (was #195) — the test of
  clauses 2 and 3 before the skill hardens.
