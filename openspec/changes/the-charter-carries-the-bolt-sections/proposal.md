## Why

The book makes `bolt.md` the bolt's charter: "the delivery statement, the
unit sequence and price, the merge criteria the landing verifies — born at
scaffold from the milestone's description, the planner's summary or the
operator's dictated words" (`books/flywheel/src/schemas.md`, "The bolt
schemas and the loop block"; the same sentence stands in
`books/flywheel/src/bolt-planning.md` under "From plan to board" and in
`books/flywheel/src/lifecycles.md` under "The bolt's changes"). The
schema's own template says the shape: `# Bolt: [name]`, then `## Scope`,
`## Sources`, `## Repos`, `## Merge criteria` with its `Landing:` line
(`schemas/bolt-default/templates/bolt.md`, and the same file under each of
the other three `bolt-*` schemas).

A planner-born charter carries none of it. `guard_scaffold` in
`bin/_flywheel_bolt_loop.py` drives a session whose work order says: "If
the milestone carries any `unit`-labeled issue, copy the LOWEST-NUMBERED
one's body into bolt.md verbatim, under a `# Unit: <slug>` heading naming
that unit — that one and no other". The session obeys, and the charter is
that unit's plan document and nothing else. Both planner-born charters in
this tree bear it out: `openspec/changes/loop-boundaries/bolt.md` and
`openspec/changes/archive/2026-08-17-matches-the-book/bolt.md` each open
at `# Unit: <slug>` and carry no `## Scope`, `## Sources`, `## Repos` or
`## Merge criteria` at all.

Two readers then read nothing. `merge_criteria()` searches for the first
`^## Merge criteria` and returns `""` for both files — run against them,
it does. The landing session's work order tells it to "VERIFY every one of
its Merge criteria on that branch, by running them" and there are none to
run. `landing_mode()` searches that same empty string for `Landing:` and
falls through to its `merge` default, so a bolt that meant to land by pull
request lands straight onto main instead — and the default is
indistinguishable from a declaration. The description the planner
authored, which the book names as the charter's source, is read by
`bin/flywheel-bolt-loop` for exactly one purpose — the plan-mode flag —
and never reaches the session that writes the charter.

`bolt/matches-the-book` is merged and waiting to land through this path.

## What Changes

- **The scaffold's charter opens with the bolt's own sections.** The
  session that writes `bolt.md` is asked for `## Scope`, `## Sources`,
  `## Repos` and `## Merge criteria` — the sections the bound schema's
  `bolt.md` template names — before any unit's document, with the
  `Landing:` line stated rather than left to the reader's default.
- **The milestone description reaches that session.** The description the
  planner authored is already read by `bin/flywheel-bolt-loop`; it is
  carried to the scaffold work order as the charter's stated source
  instead of being read once for the plan-mode flag and dropped.
- **Each expanded unit's plan document rides below the bolt's sections.**
  The first unit's document is still copied verbatim by the scaffold
  session, and `guard_charter` still appends later ones after whatever the
  charter already holds — so the bolt's `## Merge criteria` stays the
  first one in the file and no unit's subsection shadows it.
- **The scaffold guard checks the charter it got back.** Settling is no
  longer the whole test: the guard reads `bolt.md` and fails with a reason
  naming what is missing when the bolt-level sections are absent, rather
  than passing a charter the landing cannot read.
- **A landing refuses an unreadable charter.** When the bolt's `bolt.md`
  carries no bolt-level `## Merge criteria`, or carries an empty one, the
  landing fails with that reason ahead of any landing session: nothing is
  verified, nothing reaches the main branch, and no item is closed or
  upgraded. Verifying an empty criteria list is not a green landing.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `flywheel-derived-backlog`: "The bolt's charter carries every expanded
  unit's plan" gains its sibling — the charter's bolt-level sections, born
  at scaffold from the milestone's description, and the ordering that
  keeps a unit's document below them. This capability already owns the
  charter end to end.
- `flywheel-construction-stages`: the landing's preconditions, which this
  capability states, gain one more — a charter whose merge criteria cannot
  be read is not landable.

## Impact

- `bin/_flywheel_bolt_loop.py` — `guard_scaffold`'s work order and its
  post-settle check; `BoltParams`, which carries no milestone description
  today; `land_stage`, which reads `merge_criteria()` only through
  `landing_mode()` and never asks whether there were any.
- `bin/flywheel-bolt-loop` — `build_loop` already reads the milestone's
  `description` for `plan_mode_declared`; it passes it on.
- `tests/test_bolt_loop.py` — nothing exercises the scaffold work order's
  content or a charter without merge criteria; `LandingTest.program`
  stubs `merge_criteria` on every landing test.
- `schemas/*/templates/bolt.md` — read as the authority for the section
  set, and **not edited**: the bolt plan's "Left out" says so, and the
  template already names the sections.
- **Out of scope, and named here rather than fixed**: the two charters
  already on disk without these sections. `openspec/changes/loop-boundaries/bolt.md`
  is this bolt's own record and
  `openspec/changes/archive/2026-08-17-matches-the-book/bolt.md` is
  archived. This change makes the next charter right and makes an
  unreadable one refuse to land; repairing an existing charter in place is
  neither, and a guard that rewrites committed prose would contradict
  "durable prose in git outranks mutable tracker state".
- **Out of scope**: a change directory that exists without a `bolt.md` at
  all, and a unit title that parses no slug. Both are siblings in this
  same unit (`a-charterless-change-directory-gets-one`,
  `an-unparseable-unit-title-says-so`) and both build on the charter shape
  this change defines.
