## 1. Read the tree before changing it

- [ ] 1.1 Re-read `guard_scaffold`, `guard_charter`, `merge_criteria`,
      `landing_mode` and `land_stage` in `bin/_flywheel_bolt_loop.py`,
      and `build_loop` in `bin/flywheel-bolt-loop`. Done when you can
      name, from the files, where the milestone description is read and
      where it stops, and which of this change's requirements the tree
      already satisfies. `design.md` — Context states what those files
      bore out at spec time; if any of it no longer holds, say so in the
      report rather than building over it.
- [ ] 1.2 Read `schemas/bolt-default/templates/bolt.md` and confirm the
      section set the work order will name matches it. Done when the four
      headings and the `Landing:` line in the order are the template's
      own, and no task in this change edits any
      `schemas/*/templates/bolt.md`.

## 2. The description reaches the charter's session

- [ ] 2.1 `BoltParams` carries the bolt milestone's description.
      `build_loop` in `bin/flywheel-bolt-loop` already reads it for
      `plan_mode_declared`; the same value is passed to `BoltParams`.
      Done when a loop built from a milestone with a description holds
      it, one built under `--fixture` holds the empty string, and
      `plan_mode_declared` still reads what it reads today.

## 3. The scaffold writes a charter, not a unit

- [ ] 3.1 `guard_scaffold`'s work order asks for the bolt-level sections
      the schema template names — scope, sources, repos, and merge
      criteria with the `Landing:` line stated — written from the
      milestone description, before any unit's plan document; the
      lowest-numbered unit's body still follows verbatim under its
      `# Unit: <slug>` heading, and the no-unit-card fallback keeps its
      sections too. Done when the order names those sections and points
      the session at `openspec instructions bolt --change <slug>` rather
      than inlining the template, and when the description is in the
      order's text when there is one.
- [ ] 3.2 After the scaffold session settles, the guard confirms the
      charter is readable: `bolt.md` exists and `merge_criteria()`
      returns a non-empty body. It calls that same reader, never a second
      regex. A charter that fails returns a guard error naming the change
      directory and what is missing, and the cycle stops there.
- [ ] 3.3 The guard's dry-cycle property is unchanged: a pass that finds
      the change directory already present returns before the check and
      writes nothing, and `--dry-run` still only reports what it would
      scaffold.

## 4. A landing refuses an unreadable charter

- [ ] 4.1 `land_stage` refuses when `merge_criteria()` is empty — no
      section, an empty body, or no `bolt.md` at all — before any landing
      session is driven and before anything reaches the main branch. The
      outcome names the charter's path and says its merge criteria could
      not be read; no item is closed, upgraded, or paused by it.
- [ ] 4.2 The refusal sits with the landing's existing two refusals (the
      live operator wait, and `branch_advanced`), not with the release
      conditions, so a forced landing reaches it and is refused by it.
      Done when a forced landing over a charter with no criteria is
      refused and a forced landing over a charter with criteria still
      runs.
- [ ] 4.3 The run's landing line carries the refusal, so
      `flywheel bolt-loop` prints it and its `--json` carries the same
      string — distinguishable from `not attempted`.

## 5. Tests

- [ ] 5.1 The scaffold work order's content: a milestone with a
      description produces an order naming the four sections and carrying
      that description; a milestone without one still names the sections.
- [ ] 5.2 The post-settle check: a session that settles leaving a
      `# Unit:`-only charter fails the guard with a reason naming the
      missing sections; a session that settles leaving a charter with
      merge criteria passes and records its action.
- [ ] 5.3 The landing refusal, reached through the real
      `merge_criteria()` rather than a stub — the charter written to a
      temporary worktree — for all three empty cases and for the forced
      landing, plus one test that a charter with criteria still lands.
- [ ] 5.4 The ordering invariant: a charter carrying the bolt's merge
      criteria followed by a `# Unit:` section whose body contains its
      own `##` subsections reads back the bolt's criteria, and
      `guard_charter`'s append still lands below them.
- [ ] 5.5 `python3 -m unittest tests.test_bolt_loop -v` green, and the
      repo's gates — `node scripts/check-paths.mjs` and
      `node scripts/check-site.mjs` — green.

## 6. Record

- [ ] 6.1 `openspec validate the-charter-carries-the-bolt-sections
      --strict` green, and every task above checked off against what the
      files bear out rather than what was edited.
