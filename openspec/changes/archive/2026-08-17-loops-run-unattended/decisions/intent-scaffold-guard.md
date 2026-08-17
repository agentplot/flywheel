# Decision: The intent loop gets guard 0, as a program step

## Decision

The intent loop scaffolds a missing change dir itself — guard 0,
scaffold-if-missing, run first and idempotent like the bolt loop's —
and it needs no model: `openspec new change <slug> --schema
flywheel-intent --description …` is fully non-interactive (verified
against openspec 1.8.0), so the guard is a subprocess call plus a
commit. The three-guard list in `design/loop-programs.md` was an
omission, not a design: the schema's apply instruction
(`schemas/flywheel-intent/schema.yaml:233`) already lists guard 0.

## Context

- Produced by: `../sessions/2026-08-14-loop-program-decisions/round.md`
  §3, approved by the operator in the plannotator round of 2026-08-16.
- Live evidence: `openspec/changes/loops-run-unattended/` did not exist
  on any branch when the planning session started — the milestone was
  born at triage, nothing scaffolded it, and the session created the
  directory by hand. Triage creates intent milestones without
  inception; the loop is the only actor guaranteed to be there.
- Alternatives declined: making dispatch scaffold breaks its
  no-repo-writes seal; charging a session is a model asked to behave
  like code. Queued as #87.

## Consequences

- `design/loop-programs.md`'s intent-loop guard list gains guard 0
  (this session's branch).
- The build is #208: the guard in `_flywheel_intent.run_guards`, a
  subprocess seam the suite fakes, fixture coverage.
- #87 closes as "yes — omission, not design."
