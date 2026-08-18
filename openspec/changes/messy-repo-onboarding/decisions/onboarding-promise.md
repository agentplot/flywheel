# Decision: The messy-repo onboarding promise

## Decision

When a messy repo of planning docs arrives, flywheel promises:

1. **Hand-over is a pointer and read access, nothing else — and the
   import runs inside the corpus org's own flywheel.** No
   pre-sorting, no format, no restructuring. Anything the operator
   volunteers is seed evidence, never a prerequisite. Intake is
   dispatch-shaped: the pointer arrives as a raw idea, dispatch opens
   an intent — in the fleet of the org that owns the corpus. Corpus
   content never crosses into another org's repos; what is shared
   across orgs is the process, not the material.
2. **What comes back is artifact-by-artifact conversion — a move,
   not a copy — tracked and recoverable.** First the cut: a durable
   triage report committed in the intent's change directory, read
   against **two inputs** — the corpus and the destination books; no
   settled-history row is assignable until the books are read.
   Granularity is file-or-section, and below a section wherever a
   trailing subsection changes lane. Four lanes:
   - **discard** — the row is the record that it was seen;
   - **withhold** — seen and never carried forward (live
     infrastructure identifiers, credentials, grants): the row
     records the class and quotes nothing;
   - **settled-history** — converted under two qualifiers:
     **coverage** (already in the books → cite the chapter, convert
     nothing; unwritten → convert) and **currency** (still true →
     may update the books; superseded → a historical record with a
     dated caveat, never a books update);
   - **live-work** — routed by kind: design-level direction goes
     into the design books, where bolt planning carves bolt unit
     plans on demand; only already-concrete actionable work becomes
     queued tracker items, all at Backlog — **nothing arrives
     approved**.
   Any row may carry the **sole-holder** flag — the corpus is the
   only copy — whose consequence is adoption whole into the
   destination design repo before the corpus can be retired.
   *Restated elsewhere* is checked, never inferred: a restatement
   filter (do the references carry the content or merely name it)
   and then a read of what passes; a diagram is a sole holder by
   construction. Operating documentation resolves by one operator
   question per corpus: out of scope while the repo lives, removed
   and preserved when it is retired. A lane is a disposition for the
   corpus, never a judgment about whether anyone should read the
   thing. Each processed artifact is **removed from the source
   repo**, its untouched original stored under
   `$XDG_STATE_HOME/flywheel/<org>/imports/<repo>/originals/`, and
   marked processed in a **committed ledger** in the intent's change
   directory (`import/<repo>/processed.jsonl`), so the original is
   recoverable and the import can stop and resume on any machine.
   Settled history becomes flywheel-native records — decisions and
   design reports captured as sessions under intents — and design
   material updates the books or records an explicit per-artifact
   verdict, "already written, here is the chapter" being first-class.
3. **The operator reads the cut and the verdicts, not the corpus.**
   Sessions read the whole corpus; the operator reviews rows and
   opens the source only to dispute one. The live-work lane meets the
   operator as one proposed-items table — destination and session
   type per row — reviewed in one pass before bulk creation.
   Unsettleable rows surface as queued questions, never as a silently
   chosen lane.
4. **The process is written down once; the cut and conversions are
   judgment every time.** The durable carrier is the plugin's
   `skills/import/` skill — inventory → cut → convert → mark
   processed — run by design sessions that do the reading, never a
   tool that replaces it.

## Context

- Produced by: `../sessions/2026-08-17-promise/round.md`, approved
  2026-08-17 (#264); amended by
  `../sessions/2026-08-18-import-shape/round.md`, approved 2026-08-18
  (#278), folding the first real-corpus measurement
  (`../sessions/2026-08-17-cut/findings.md`, #270).
- The measurement's largest lessons: the cut needs the destination
  books as a second input (F3); "settled" is not "currently true"
  (F8); a summary's existence does not mean the content is restated
  (F12, 42% of the test corpus was sole-holder); withheld
  identifiers must never be quoted (F11); an import is a move whose
  originals are preserved in state (round 2 of #278's round).

## Consequences

- Cross-org landing (#267): resolved — there is no cross-org case;
  each org's flywheel imports its own corpora
  (`import-runs-in-own-org.md`).
- Specs into the source repo (#268): resolved — never
  (`no-specs-into-source-repo.md`).
- Bulk triage (#269): resolved — the cut's proposed-items table is
  the one review pass (`bulk-triage.md`).
- The carrier (#266): `skills/import/SKILL.md`, landed from the
  approved draft.
- Queued: #300 — remove the quoted willdan conversion content from
  the public flywheel tree; the re-conversion belongs to the willdan
  flywheel's own import.
