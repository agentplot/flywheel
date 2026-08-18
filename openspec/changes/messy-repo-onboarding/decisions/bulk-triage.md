# Decision: The cut is the bulk-triage artifact

## Decision

Imported live work never reaches the tracker one item at a time. The
carrier's cut report ends in a proposed-items table — per row: title;
provenance (repo, commit, file, lines); destination (design books vs
tracker item); and the session type that will work it, or "book
material — reaches construction via bolt planning, no item". The
operator reviews that one table, once; on approval a session creates
the items in bulk, all at Backlog.

Before a row reaches the table:

- **The corpus's own bookkeeping runs first.** Its progress ledger —
  a phasing section, a roadmap page, a findings sink, a state file —
  plus the currency qualifier drop already-done work without a full
  corpus read.
- **Collision with open items is judged, not string-matched.** One
  query pulls the tracker's open items; a proposed row that is the
  same work under another name becomes a pointer comment on the
  existing item, never a duplicate.
- **Provenance is in the body, identity in the milestone.** No new
  label taxonomy.

## Context

- Item #269 (successor to the archived #199), closed by
  `../sessions/2026-08-18-import-shape/round.md` §4, approved
  2026-08-18; the table shape approved with the session-type column
  added by the operator's round-2 annotation 6.
- Evidence: F5, F8, F10 in `../sessions/2026-08-17-cut/findings.md`
  — the corpus's own ledgers name the forward list, and a stale
  roadmap would have re-queued a finished phase.
