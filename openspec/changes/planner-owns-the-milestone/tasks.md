## 1. The surfaces a planning run reads

The planner is a prose-driven session: the requirement's implementation
is the two files a run loads, and nothing else executes it. Re-read each
from disk before editing — both were moved toward this shape ahead of
this change (commit `af35150`), so parts may already be true, and a task
below is done when the file bears out the claim, not when it was edited.

- [x] 1.1 `skills/bolt-planning/SKILL.md`, the **Delivery** section's
      *Board* bullet, states the whole filing contract in one place:
      create the `bolt/<slug>` milestone if it does not exist with the
      bolt summary as its description; then file exactly one card per
      proposed unit ON that milestone — title `Unit: <slug>`, label
      `plan`, the unit document as the body with a `System: <name>`
      line, the card added to the org Project at Status Backlog with
      the work order's Team, each "builds on" claim mirrored as a
      blocked-by relationship between the unit cards; unapproved plan
      cards from earlier runs closed `closed:superseded`; and nothing
      else — no `state:*` label, no work items, no other issue,
      comment, or label. At writing time this bullet already reads
      "create the `bolt/<slug>` milestone if it does not exist, with
      the bolt summary as its description" and "title `Unit: <slug>`";
      confirm against disk and repair whatever has drifted.
- [x] 1.2 The same file's **The plan documents** section names the bolt
      summary's three parts, so what lands in the milestone description
      is determined: what the bolt delivers, the unit sequence one line
      each, and the bolt's total price. At writing time it reads "One
      short **bolt summary** (it becomes the milestone description)".
- [x] 1.3 `agents/flywheel-bolt-planner.md` carries the same contract in
      its own voice: the tracker-writes bullet names the bolt milestone
      **and** the plan cards as the only writes, and the **Card
      conventions** bullet names the milestone-with-summary, `Unit:
      <slug>`, the body's `System:` line and provenance footer, Status
      Backlog with the work order's Team, and blocked-by between unit
      cards. At writing time both bullets already read that way.
- [x] 1.4 No surface a planning run reads still tells it to title a
      filed card `Bolt: <slug>` or to leave it unmilestoned. Grep
      `skills/`, `agents/`, and `design/` for `Bolt: ` and confirm every
      remaining hit is a plan document under `design/plans/` (historical
      records of runs already made) or an OpenSpec bolt template under
      `schemas/*/templates/bolt.md` (a different object entirely) — not
      an instruction to the planner.

## 2. Hold the contract with a record-consistency check

The suite's `RecordConsistencyTest` pattern in `tests/test_inbox.py` is
the precedent: "A behaviour with no record is a behaviour the next
reader undoes." A prose-driven session's requirement can only be held by
reading its prose.

- [x] 2.1 Add a test class to `tests/test_derived_backlog.py` that reads
      `skills/bolt-planning/SKILL.md` and `agents/flywheel-bolt-planner.md`
      from disk and asserts, for each: the card title form `Unit: <slug>`
      appears; the milestone is created by the planner and carries the
      bolt summary as its description; the cards are filed on that
      milestone; Team is set at filing; "builds on" is mirrored as
      blocked-by; earlier unapproved cards are closed
      `closed:superseded`.
- [x] 2.2 The same test asserts the retired proposition is gone: neither
      surface tells the planner to title a card `Bolt: <slug>`, and
      neither says the card it files is milestone-less. Pin the
      proposition, not every mention — the phrasing may be rewritten,
      and a check that breaks on a synonym is a check nobody keeps.
- [x] 2.3 The new test fails against the pre-change text of at least one
      surface. Verify by reverting one sentence in a scratch copy (never
      committed) and watching it go red; a record check that passes on
      the old text holds nothing.

## 3. Gates

- [x] 3.1 `sh scripts/test.sh` green — the whole suite, not just the new
      class.
- [x] 3.2 `node scripts/check-paths.mjs` and `node scripts/check-site.mjs`
      green, per the project instructions in `openspec/config.yaml`.
- [x] 3.3 `openspec validate planner-owns-the-milestone --strict` green.
- [x] 3.4 Commit by pathspec (`git add -- <paths>`, `git commit -- <paths>`)
      — never `-a`, never `add -A`; a sibling session may share this tree.
