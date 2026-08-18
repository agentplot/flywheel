# Session 2026-08-18-handoff — handoff, item #290

Plans the bolt for the settled assertions on `intent/operating-docs`
(#287, #288) and moves custody to construction. Unit: #291.

- `bolt-plan.md` — one bolt, `bolt/quickstart-and-book-link`, on the
  standard handoff template: type, landing, owner, repo, the two
  assertions with their decision records, the sequencing to wire, and
  the merge criteria the bolt record inherits.

Round: one blocking `plannotator annotate bolt-plan.md` pass. The plan
is rewritten in place on what comes back; the custody move — milestone
`bolt/quickstart-and-book-link`, `state:ready`, the blocked-by wiring —
runs only on approval.
