# Decision: An import never writes specs into the source repo

## Decision

An import never writes OpenSpec specs into the built source repo.
Settled history's destination is the org design repo's records —
sessions and decisions under intents, per the promise. If real
construction later happens in the source repo, specs are written
fresh at that point by the normal spec-writing lane, from the
imported records; provenance survives through the records.

The adjacent case is out of scope by the same shape as the promise's
operating-docs rule: a live source repo whose own team runs OpenSpec
natively writes its own specs — the team's act, not the import's.

## Context

- Item #268 (successor to the archived #198), closed by
  `../sessions/2026-08-18-import-shape/round.md` §3, approved
  2026-08-18.
- Rationale: a spec means something only where machinery reads it —
  sessions that build from it, a loop that gates it. The source repo
  has none; a spec dropped there rots into exactly the doc-shape the
  import exists to clean up.
