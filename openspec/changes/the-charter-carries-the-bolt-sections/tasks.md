## 1. Read the tree before changing it

- [ ] 1.1 Re-read `guard_scaffold`, `guard_charter`, `UNIT_HEADING`,
      `merge_criteria`, `landing_mode` and `land_stage` in
      `bin/_flywheel_bolt_loop.py`; `build_loop` in
      `bin/flywheel-bolt-loop`; and the `bolt` artifact block in
      `schemas/bolt-default/schema.yaml`. Done when you can name, from
      the files, where the milestone description is read and where it
      stops, and which of this change's requirements the tree already
      satisfies. `design.md` — Context states what those files bore out
      at spec time; if any of it no longer holds, say so in the report
      rather than building over it.
- [ ] 1.2 Read `schemas/bolt-default/templates/bolt.md` and confirm it
      already carries the four sections and nothing else. Done when no
      task below edits any `schemas/*/templates/bolt.md`.

## 2. The schemas declare both artifacts

- [ ] 2.1 All four `bolt-*` schemas declare a `unit` artifact generating
      `units/<slug>.md` alongside `bolt` → `bolt.md`. Its instruction
      states that the loop writes it at expansion, verbatim from the
      approved card's body, and that no session composes or edits it.
      Done when `schemas/bolt-default`, `bolt-quick`, `bolt-adversarial`
      and `bolt-direct` all declare both, since the record's shape is not
      a function of the type.
- [ ] 2.2 The `bolt` artifact instruction in all four members stops at
      the four sections: the paragraph beginning "What follows those four
      sections…" is gone, and nothing else in the instruction directs a
      unit's plan document into `bolt.md`. The instruction names the bolt
      milestone's description as the charter's source.
- [ ] 2.3 `bash scripts/validate-manifests.sh` and the repo's own gates
      still pass over the edited schemas, and `bin/install-schemas` still
      copies each member whole.

## 3. The description reaches the charter's session

- [ ] 3.1 `BoltParams` carries the bolt milestone's description;
      `build_loop` in `bin/flywheel-bolt-loop` passes it the value it
      already reads for `plan_mode_declared`. Done when a loop built from
      a milestone with a description holds it, one built under
      `--fixture` holds the empty string, and `plan_mode_declared` reads
      exactly what it reads today.

## 4. The scaffold writes a charter, and only a charter

- [ ] 4.1 `guard_scaffold`'s work order asks for the four sections —
      scope, sources, repos, and merge criteria with the `Landing:` line
      stated — written from the milestone's description, and asks for no
      unit's plan document. The clause telling the session to copy the
      lowest-numbered unit's body under a `# Unit: <slug>` heading is
      gone. Done when the order names the sections, points the session at
      `openspec instructions bolt --change <slug>` rather than inlining
      the schema's text, and carries the description when there is one.
- [ ] 4.2 After the scaffold session settles, the guard confirms the
      charter is readable: `bolt.md` exists and `merge_criteria()`
      returns a non-empty body. It calls that same reader, never a second
      regex. A charter that fails returns a guard error naming the change
      directory and what is missing, and the cycle stops there.
- [ ] 4.3 The guard's dry-cycle property is unchanged: a pass finding the
      change directory already present returns before the check and
      writes nothing, and `--dry-run` still only reports what it would
      scaffold.

## 5. Each expanded unit gets its own file

- [ ] 5.1 `guard_charter` writes `openspec/changes/<slug>/units/<unit-slug>.md`
      per expanded unit — the card body verbatim, the slug from
      `PlanCard.slug` — instead of appending a `# Unit:` section to
      `bolt.md`. It commits by pathspec on the branch carrying the bolt's
      record, never `-a` and never `add -A`. `UNIT_HEADING` and the
      append go with it.
- [ ] 5.2 Its idempotency test is the record's committed state: which
      files exist under `units/` at HEAD, compared against the
      `unit`-labeled issues on the milestone. A pass with nothing newly
      expanded writes nothing and commits nothing.
- [ ] 5.3 A torn write is repaired, not read as done: a unit file on disk
      but not at HEAD keeps its content and has its add and commit
      re-run. A unit file already at HEAD is never rewritten, whether the
      loop or a hand wrote it.
- [ ] 5.4 A record in the older shape needs no migration step: because
      the test is whether `units/<slug>.md` exists, a bolt whose unit
      prose sits in `bolt.md` gets its unit file written by this same
      path, and the stale `# Unit:` section in `bolt.md` is left exactly
      where it is.
- [ ] 5.5 The guard still skips itself under `--dry-run` and under
      `FixtureTracker`, reporting what it would write in the first case
      and touching no tree in the second.

## 6. The readers find what they read for

- [ ] 6.1 `merge_criteria()` reads the charter's own region — the file up
      to the first `# Unit:` heading, and the whole file when there is
      none — so a `## Merge criteria` inside a stale unit section is
      never returned as this bolt's criteria.
- [ ] 6.2 `landing_mode()` is unchanged in behaviour and now reads a
      declared `Landing:` line on a charter that states one; a charter
      that states none reaches the refusal below rather than a default.

## 7. A landing refuses an unreadable charter

- [ ] 7.1 `land_stage` refuses when `merge_criteria()` is empty — no
      section in the charter's region, an empty body, or no `bolt.md` at
      all — before any landing session is driven and before anything
      reaches the main branch. The outcome names the charter's path and
      says its merge criteria could not be read; no item is closed,
      upgraded, or paused by it.
- [ ] 7.2 The refusal sits with the landing's existing two refusals (the
      live operator wait, and `branch_advanced`), not with the release
      conditions, so a forced landing reaches it and is refused by it.
      Done when a forced landing over a charter with no criteria is
      refused and a forced landing over a charter with criteria still
      runs.
- [ ] 7.3 The run's landing line carries the refusal, so
      `flywheel bolt-loop` prints it and its `--json` carries the same
      string — distinguishable from `not attempted`.

## 8. Tests

- [ ] 8.1 The scaffold work order's content: a milestone with a
      description produces an order naming the four sections and carrying
      that description; a milestone without one still names the sections;
      no order mentions copying a unit's document into `bolt.md`.
- [ ] 8.2 The post-settle check: a session that settles leaving a charter
      with no merge criteria fails the guard with a reason naming what is
      missing; one that settles leaving a charter with them passes and
      records its action.
- [ ] 8.3 The unit artifact: first unit written and committed; second
      unit written without disturbing the first or the charter; a pass
      with every unit file at HEAD writing nothing; a torn write
      re-committed; an existing unit file never overwritten.
- [ ] 8.4 A record in the older shape — `bolt.md` carrying a `# Unit:`
      section and no charter sections — gets its unit file written, keeps
      that section untouched, and reads back no merge criteria.
- [ ] 8.5 The landing refusal reached through the real `merge_criteria()`
      rather than a stub, with the charter written into a temporary
      worktree: all three empty cases, the forced landing, and one test
      that a charter stating criteria still lands.
- [ ] 8.6 Replace `ReadingTest`'s real-reader test, which reads an
      archived path and so takes its `skipTest` branch on any current
      worktree, with one that writes its own charter.
- [ ] 8.7 `python3 -m unittest discover tests -v` green, and the repo's
      gates — `node scripts/check-paths.mjs`, `node scripts/check-site.mjs`,
      `bash scripts/validate-manifests.sh` — green.

## 9. Record

- [ ] 9.1 `openspec validate the-charter-carries-the-bolt-sections --strict`
      green, and every task above checked off against what the files bear
      out rather than what was edited.
