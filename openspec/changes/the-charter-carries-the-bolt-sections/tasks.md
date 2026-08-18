## 1. Read the tree before changing it

Part of this change's shape is already on disk: a build session applied
the charter half before the book's record split was derived. A task is
done when the file bears out the claim, not when it was edited.

- [ ] 1.1 Re-read `guard_scaffold`, `CHARTER_SECTIONS`, `guard_charter`,
      `UNIT_HEADING`, `merge_criteria`, `landing_mode` and `land_stage`
      in `bin/_flywheel_bolt_loop.py`, `BoltParams.description`, and the
      `bolt` artifact block in each of the four `schemas/bolt-*/schema.yaml`.
      Done when you can name, from the files, which requirements in this
      change's spec deltas the tree already satisfies and which it does
      not. `design.md` — Context states what those files bore out at spec
      time; where it no longer holds, say so in the report rather than
      building over it.
- [ ] 1.2 Confirm `schemas/bolt-default/templates/bolt.md` carries the
      four sections and nothing else, and that only that member's
      template shows a `Landing:` line. Done when no task below edits any
      `schemas/*/templates/bolt.md`.

## 2. Verify the charter half already on disk

These are requirements of record that the tree already meets. Change
nothing unless the file contradicts the claim; report it if it does.

- [ ] 2.1 `BoltParams` carries the milestone description and
      `bin/flywheel-bolt-loop` passes it the value it reads for
      `plan_mode_declared`; a loop built under `--fixture` holds the
      empty string.
- [ ] 2.2 `guard_scaffold`'s order names the four charter sections, asks
      for the `Landing:` line under every schema, and carries the
      description when there is one — with the no-description branch
      still asking for all four sections.
- [ ] 2.3 The post-settle check calls `merge_criteria()` — the same
      reader the landing uses, not a second regex — and fails with a
      reason naming the change directory and what is missing.
- [ ] 2.4 `land_stage` refuses a charter that states no criteria, sitting
      with the live-wait and `branch_advanced` refusals rather than the
      release conditions, so a force reaches it; and the run's landing
      line carries the refusal distinguishably from `not attempted`.

## 3. The schemas declare both artifacts

- [ ] 3.1 All four `bolt-*` schemas declare a `unit` artifact generating
      `units/<slug>.md` alongside `bolt` → `bolt.md`. Its instruction
      states that the loop writes it at expansion, verbatim from the
      approved card's body, and that no session composes or edits it.
      Done when `bolt-default`, `bolt-quick`, `bolt-adversarial` and
      `bolt-direct` all declare both — the record's shape is not a
      function of the type.
- [ ] 3.2 The `bolt` instruction in all four members stops at the four
      sections: the paragraph beginning "What follows those four
      sections…" is gone, and nothing else in the instruction directs a
      unit's plan document into `bolt.md`. The instruction names the bolt
      milestone's description as the charter's source.
- [ ] 3.3 `bash scripts/validate-manifests.sh` passes over the edited
      schemas and `bin/install-schemas` still copies each member whole.

## 4. The scaffold's order stops at the charter

- [ ] 4.1 The "BELOW them: … copy the LOWEST-NUMBERED one's body into
      bolt.md verbatim, under a `# Unit: <slug>` heading …" paragraph
      leaves `guard_scaffold`'s order, along with the clause about the
      bolt's `## Merge criteria` staying the first such heading — there
      is nothing below it to shadow it any more. The four sections are
      the whole charter, whether or not the milestone carries unit cards.

## 5. Each expanded unit gets its own file

- [ ] 5.1 `guard_charter` writes
      `openspec/changes/<slug>/units/<unit-slug>.md` per expanded unit —
      the card body verbatim, the slug from `PlanCard.slug` — instead of
      appending a `# Unit:` section to `bolt.md`. It commits by pathspec
      on the branch carrying the bolt's record, never `-a` and never
      `add -A`. `UNIT_HEADING` and the append go with it.
- [ ] 5.2 Its idempotency test is the record's committed state — which
      files exist under `units/` at HEAD, against the `unit`-labeled
      issues on the milestone — so a pass with nothing newly expanded
      writes nothing and commits nothing.
- [ ] 5.3 A torn write is repaired, not read as done: a unit file on disk
      but not at HEAD keeps its content and has its add and commit
      re-run. A unit file already at HEAD is never rewritten, whether the
      loop or a hand wrote it.
- [ ] 5.4 A record in the older shape needs no migration step: because
      the test is whether `units/<slug>.md` exists, a bolt whose unit
      prose sits in `bolt.md` gets its unit file written by this same
      path, and the stale `# Unit:` section is left exactly where it is.
- [ ] 5.5 The guard still skips itself under `--dry-run` and under
      `FixtureTracker`, reporting what it would write in the first case
      and touching no tree in the second.

## 6. The reader takes the charter's region

- [ ] 6.1 `merge_criteria()` reads the file up to the first `# Unit:`
      heading, and the whole file when there is none, so a
      `## Merge criteria` inside a stale unit section is never returned
      as this bolt's criteria. Its docstring stops explaining the
      lookahead by the append that no longer happens.
- [ ] 6.2 `landing_mode()` is unchanged: it reads a declared `Landing:`
      line on a charter that states one, and a charter that states none
      reaches the refusal rather than a default.

## 7. Tests

- [ ] 7.1 The scaffold work order's content: it names the four sections
      with and without a description, and no order mentions copying a
      unit's document into `bolt.md`. Update the tests the build added
      that assert the unit-copy clause.
- [ ] 7.2 The unit artifact: first unit written and committed; second
      unit written without disturbing the first or the charter; a pass
      with every unit file at HEAD writing nothing; a torn write
      re-committed; an existing unit file never overwritten; `--dry-run`
      and `FixtureTracker` writing nothing.
- [ ] 7.3 A record in the older shape — `bolt.md` carrying a `# Unit:`
      section with its own `## Merge criteria` and no charter above —
      gets its unit file written, keeps that section untouched, and reads
      back no merge criteria, so both the guard's check and the landing's
      refusal fire on it.
- [ ] 7.4 The landing refusal reached through the real `merge_criteria()`
      rather than a stub, with the charter written into a temporary
      worktree: the empty cases, the forced landing, and one test that a
      charter stating criteria still lands.
- [ ] 7.5 Replace `ReadingTest`'s real-reader test, which reads an
      archived path and so takes its `skipTest` branch on any current
      worktree, with one that writes its own charter.
- [ ] 7.6 `python3 -m unittest discover tests -v` green, and the repo's
      gates — `node scripts/check-paths.mjs`, `node scripts/check-site.mjs`,
      `bash scripts/validate-manifests.sh` — green.

## 8. Record

- [ ] 8.1 `openspec validate the-charter-carries-the-bolt-sections --strict`
      green, and every task above checked off against what the files bear
      out rather than what was edited.
