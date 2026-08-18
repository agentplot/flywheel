# Decision: An import runs inside the corpus org's own flywheel

## Decision

An import always runs in the fleet of the org that owns the corpus:
its dispatch opens the intent, its design sessions do the reading,
records land in its design repo, items on its tracker, originals in
its state folder. Corpus content never crosses into another org's
repos, public or private. What is shared across orgs is the import
skill in the flywheel plugin — the process, never the material.

Where the corpus org's fleet lacks a piece of tracker machinery (a
`tracker:` entry, the app install, `flywheel-setup`), that is a
setup-checklist step done when the import runs — not a reason to land
the work elsewhere.

## Context

- Item #267 (successor to the archived #196), closed by
  `../sessions/2026-08-18-import-shape/round.md` §2, approved
  2026-08-18. Round 2 corrected the framing premise: willdan has its
  own flywheel pointing at willdan-blueprints, so the kb-spike import
  is willdan's own, and the "importing org" of #196's forks does not
  exist.
- The #270 measurement staged converted willdan content in
  `agentplot/flywheel` — a public repo. The operator ruled it a
  mistake (round 2, annotation 5); cleanup is #300. That near-miss is
  the argument for the boundary: an org's import writing into another
  org's tree is an exfiltration path even with good intentions (see
  also F11, `../sessions/2026-08-17-cut/findings.md`).

## Consequences

- #300: remove the quoted willdan conversion content from the public
  flywheel tree; re-conversion happens later inside the willdan
  flywheel as that import's own work.
- The willdan import's checklist gap: no `tracker:` in willdan's
  fleet.yaml yet.
