# Session 2026-08-18 — import shape

Planning session on `intent/messy-repo-onboarding`, items #266, #267,
#268, #269, #278: fold the first measurement's findings
(`../2026-08-17-cut/findings.md`) into the promise, settle the three
deferred decisions, and fix the carrier skill.

## Contents

- `round.md` — the round document, five sections; the round-3 text
  the operator approved.
- `carrier-skill.md` — the skill draft the round approved; landed
  verbatim at `skills/import/SKILL.md`.
- `plannotator-result-r1.json` / `-r2.json` / `-r3.json` — round 1
  **annotated** (the document was unreadable jargon; round 2 was the
  plain-language rewrite), round 2 **annotated** (six corrections:
  live work routes to books as well as tracker; move-not-copy with an
  originals state folder; the import runs in the corpus org's own
  flywheel; the #270 conversion into the public flywheel repo was a
  mistake; the items table carries session types; diagrams-whole
  approved), round 3 **approved** (2026-08-18).

## Outcome

All five items closed on round 3:

- **#278** — the promise amended in place:
  `../../decisions/onboarding-promise.md`.
- **#267** — `../../decisions/import-runs-in-own-org.md`: no
  cross-org case exists; each org's flywheel imports its own corpora.
  Cleanup of the mistaken #270 staging queued as #300.
- **#268** — `../../decisions/no-specs-into-source-repo.md`: never.
- **#269** — `../../decisions/bulk-triage.md`: the cut's
  proposed-items table, one operator pass, session types per row.
- **#266** — `skills/import/SKILL.md` landed from the approved draft;
  ledger committed in the change directory, originals in
  machine-local state.

## Round-holding note

The first two attempts to open round 2 died without annotations —
gated plannotator servers do not survive being backgrounded in this
environment. The round that worked ran in the foreground within the
600s window.
