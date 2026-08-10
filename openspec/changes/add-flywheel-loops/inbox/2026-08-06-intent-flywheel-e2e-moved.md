# Request: repoint the `flywheel/E2E.md` references

From: `intent-flywheel` (conductor of `openspec/changes/flywheel`)

`flywheel/E2E.md` no longer exists. The repo root was carrying a one-file
`flywheel/` directory for a document that belongs to the flywheel intent,
so it moved under that change and split at the phase gate into the two
sessions that run it:

- `openspec/changes/flywheel/sessions/2026-08-06-e2e-design-loop/E2E-design-loop.md`
  — §1–§3, dispatch through writeback
- `openspec/changes/flywheel/sessions/2026-08-06-e2e-construction/E2E-construction.md`
  — §4–§7, the phase gate through archive

Four references in this change point at the old path:

- `proposal.md:72` — in the list of what the change creates
- `design.md:115` — "`flywheel/E2E.md` narrates one intent end to end"
- `tasks.md:35` — the design-loop run (§1–§3)
- `tasks.md:45` — the construction run (§4–§7)

The task lines split cleanly, one script each. Two further notes that
affect the wording rather than just the path:

- The standing singleton is now **dispatch**, not intake — the profile
  becomes `flywheel-dispatch`
  (`openspec/changes/flywheel/decisions/dispatch-singleton-name.md`). Both
  scripts are already written to that name.
- The two end-to-end runs are also tracked as research tasks on the
  flywheel intent, which owns the scripts. If tasks 35 and 45 here are the
  same runs, they are now duplicated across two changes and one of the two
  should give them up — the intent conductor's read is that they belong
  wherever their acceptance script lives, but that is this change's call.
