# Session: blast-radius-inventory

## Charge
- Change: work-object-vocabulary
- Type: research (read-only — no worktree, no branch, no file writes in the tree)
- Directory: sessions/2026-08-12-blast-radius-inventory/
- Items: #18
- Goal: produce the exhaustive, driveable inventory of the work-object
  rename across tree and tracker, so #13's coupled naming call is made
  against real cost rather than a survey. Do not propose a winner.

Run as the conductor's `/opsx:apply` dynamic workflow, run ID
`wf_34827627-076`: seven parallel read-only surface surveys (site+README,
`skills/**` including directory names, `schemas/**`, `agents/*.md`,
`openspec/**`, evals, `bin/`+`tools/`+`scripts/`+workflows), one tracker
and rename-semantics survey, one synthesis agent.

## Produced
- No files. The session read only; its deliverable is the inventory
  comment on item #18, posted by the synthesis agent:
  <https://github.com/agentplot/flywheel/issues/18#issuecomment-5270769621>

## Delivered

**The inventory.** Counts per surface at tree `2e707e9`, each hit
classified as work-object use, batch-kind use, IDENTIFIER (label value,
directory name, CLI flag value, schema artifact id, command name,
filename, requirement-heading key) or incidental, with a one-line cost
read per surface and an identifier migration list.

**Four measurements in #13's and this change's prose are wrong.** The
survey re-ran each disputed count with ripgrep to settle it:
`openspec/specs/**` is 119 uses across eight files, not the "~105 across
six" that `questions/work-object-names.md` and #18's body carry.

**Two facts the item asked for, established:**

- A GitHub label rename is rename-in-place: the label object keeps its
  id, every attached issue follows automatically including closed ones,
  zero per-issue edits. Only historical `labeled` timeline events keep
  the old string, because that payload carries a denormalised, id-less
  label snapshot — so the old vocabulary is unerasable from tracker
  history. The evidence is structural (stable label id, id-bearing
  association in the issue payload, the PATCH-shaped endpoint, and the
  docs' one-sided warning that *deleting* detaches); GitHub's docs state
  it nowhere.
- The tracker migration is **not** one operation. The label strings are
  hard-coded in `bin/` where a label rename cannot reach — `flywheel-batch`
  (`--kind` choices, and the flag value written through verbatim as the
  label name), `flywheel` (the reconcile predicate that decides a
  milestone has a batch), `flywheel-setup` (the label definitions),
  `flywheel-migrate`. `bin/flywheel-setup`'s `ensure_labels` is
  create-if-missing and never renames, so a tracker migrated ahead of the
  code silently regrows the old label beside the new one. The code edit
  is a prerequisite of the tracker edit staying done, not a follow-up.

**The live tracker weight is almost nil.** Of the five candidate-word
labels, three have never been applied to any issue — `unit` among them.
The whole live migration is #12 (closed, follows automatically), #17 and
#19. No project field, option, view filter, workflow, or milestone title
names a candidate word.

**Ten items of new work surfaced**, queued rather than worked: see the
items filed against this milestone and the milestone-less ones left for
dispatch to triage, listed in the closing comment on #18.
